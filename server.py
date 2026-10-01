"""Local pilot application. Python 3.13+, no external dependencies."""
import argparse, hashlib, hmac, json, os, secrets, sqlite3, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from http.cookies import SimpleCookie
from contextlib import contextmanager

ROOT = Path(__file__).parent
DB = Path(os.environ.get('APP_DB', str(ROOT / 'data' / 'app.sqlite3')))
ORIGIN = os.environ.get('APP_ORIGIN', 'http://127.0.0.1:8080')
SECURE = ORIGIN.startswith('https://')

@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()

def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'participant', state TEXT NOT NULL DEFAULT 'triagem_pendente');
        CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires REAL NOT NULL, csrf TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), kind TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), started REAL NOT NULL, completed REAL, followup REAL, plan TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS plans(user_id INTEGER PRIMARY KEY REFERENCES users(id), content TEXT NOT NULL, clinician INTEGER REFERENCES users(id), updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS assignments(user_id INTEGER PRIMARY KEY REFERENCES users(id), clinician INTEGER REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor INTEGER REFERENCES users(id), target INTEGER REFERENCES users(id), action TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS protocol_policies(user_id INTEGER PRIMARY KEY REFERENCES users(id), config TEXT NOT NULL, clinician INTEGER REFERENCES users(id), updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS calibrations(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), pain INTEGER NOT NULL, sleep INTEGER NOT NULL, stress INTEGER NOT NULL, mode TEXT NOT NULL, snapshot TEXT NOT NULL, policy_updated REAL NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS lesson_sessions(session_id INTEGER PRIMARY KEY REFERENCES sessions(id), calibration_id INTEGER REFERENCES calibrations(id), module INTEGER NOT NULL, mode TEXT NOT NULL, snapshot TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT, 'append only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT, 'append only'); END;
        ''')

def password(value, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def audit(db, actor, target, action):
    db.execute('INSERT INTO audit(actor,target,action,created) VALUES(?,?,?,?)', (actor,target,action,time.time()))

MODULES = [
    {'id':1,'name':'Respirar e Soltar','clinical':'Alicerce Neuromotor','weeks':'Semanas 1 a 3'},
    {'id':2,'name':'Ativar e Proteger','clinical':'Religamento e Estabilidade','weeks':'Semanas 4 a 6'},
    {'id':3,'name':'Mover com Confiança','clinical':'Estruturação e Força','weeks':'Semanas 7 a 9'},
    {'id':4,'name':'Vida Real','clinical':'Autonomia e Complexidade','weeks':'Semanas 10 a 12'}
]

def validate_policy(config):
    if not isinstance(config,dict) or type(config.get('module')) is not int or config['module'] not in range(1,5): raise ApiError(400,'Informe módulo de 1 a 4.')
    if config.get('targetSessions') is not None and (type(config['targetSessions']) is not int or not 1<=config['targetSessions']<=100): raise ApiError(400,'Meta de acompanhamento deve estar entre 1 e 100 sessões.')
    if config.get('betweenInstruction') is not None and (not isinstance(config['betweenInstruction'],str) or len(config['betweenInstruction'])>2000): raise ApiError(400,'Orientação entre sessões deve ter até 2000 caracteres.')
    if config.get('effortProtection') is not None and (type(config['effortProtection']) is not int or not 0<=config['effortProtection']<=10): raise ApiError(400,'Limite individual de esforço deve estar entre 0 e 10.')
    for field in ('painProtection','sleepProtection','stressProtection','painAdvance','sleepAdvance','stressAdvance'):
        max_value=10 if field.startswith('pain') else 3
        if type(config.get(field)) is not int or not 0<=config[field]<=max_value: raise ApiError(400,'Preencha todos os limites da política autoral.')
    if config['painAdvance']>=config['painProtection'] or config['sleepAdvance']<=config['sleepProtection'] or config['stressAdvance']>=config['stressProtection']: raise ApiError(400,'Faixas de proteção e avanço não podem se sobrepor.')
    if type(config.get('allowAdvance')) is not bool: raise ApiError(400,'Informe a autorização de desafio.')
    for field in ('preparation','maintenance','protection','challenge'):
        steps=config.get(field)
        if not isinstance(steps,list) or len(steps)>12 or (field!='challenge' and not steps): raise ApiError(400,'Cadastre preparação e versões principal e de proteção.')
        for step in steps:
            if not isinstance(step,dict) or not 2<=len(str(step.get('title','')))<=150 or not 3<=len(str(step.get('instruction','')))<=1500: raise ApiError(400,'Cada etapa precisa de título e orientação individual.')
            if type(step.get('seconds')) is not int or not 5<=step['seconds']<=1800: raise ApiError(400,'Tempo da etapa deve ser de 5 a 1800 segundos.')
            video=step.get('video','')
            if not isinstance(video,str) or (video and (not video.startswith('/media/') or '..' in video or '?' in video or '#' in video)): raise ApiError(400,'Use um vídeo local em /media/.')
            for key in ('objective','version','alternative'):
                if key in step and (not isinstance(step[key],str) or len(step[key])>1500): raise ApiError(400,'Objetivo, versão e alternativa devem ser textos de até 1500 caracteres.')
    if config['allowAdvance'] and not config['challenge']: raise ApiError(400,'Cadastre o desafio autorizado.')
    return config

def lesson_snapshot(policy, pain, sleep, stress, previous_effort=None):
    # Policy is authorial and approved for this person; no validated clinical score is inferred.
    protect=pain>=policy['painProtection'] or sleep<=policy['sleepProtection'] or stress>=policy['stressProtection'] or previous_effort=='dificil' or (type(previous_effort) in (int,float) and policy.get('effortProtection') is not None and previous_effort>=policy['effortProtection'])
    advance=policy['allowAdvance'] and pain<=policy['painAdvance'] and sleep>=policy['sleepAdvance'] and stress<=policy['stressAdvance'] and previous_effort!='dificil'
    mode='protection' if protect else 'advance' if advance else 'maintenance'
    blocks=[{'name':'Preparação','steps':policy['preparation']},{'name':'Seu movimento de hoje','steps':policy['protection'] if protect else policy['maintenance']}]
    if mode=='advance': blocks.append({'name':'Desafio de hoje','steps':policy['challenge']})
    return mode, {'module':policy['module'],'mode':mode,'blocks':blocks,'policyVersion':'authorial-1'}

class ApiError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self, status, body, cookie=None, mime='application/json'):
        body = json.dumps(body, ensure_ascii=False).encode() if mime == 'application/json' else body
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie: self.send_header('Set-Cookie', cookie)
        self.end_headers(); self.wfile.write(body)
    def auth(self, db):
        cookie = SimpleCookie(self.headers.get('Cookie',''))
        token = cookie.get('session')
        row = db.execute('SELECT u.*,t.csrf,t.hash AS token_hash FROM users u JOIN tokens t ON u.id=t.user_id WHERE t.hash=? AND t.expires>?', (hashlib.sha256(token.value.encode()).hexdigest() if token else '', time.time())).fetchone()
        if not row: raise ApiError(401,'Entre na sua conta para continuar.')
        if self.command == 'POST' and not hmac.compare_digest(self.headers.get('X-CSRF-Token',''), row['csrf']): raise ApiError(403,'Sessão inválida. Atualize a página.')
        return row
    def do_GET(self): self.dispatch()
    def do_POST(self): self.dispatch()
    def dispatch(self):
        try:
            if self.command=='GET' and self.path=='/api/health':
                return self.send(200,{'ok':True,'storage':'sqlite','mode':'fictional-pilot'})
            if self.command=='GET' and self.path.startswith('/media/'):
                with connect() as db:
                    user=self.auth(db)
                    if user['state']!='ativo': raise ApiError(403,'Sessões indisponíveis.')
                    snapshots=[r['snapshot'] for r in db.execute('SELECT snapshot FROM calibrations WHERE user_id=? ORDER BY id DESC LIMIT 1',(user['id'],))]
                    snapshots += [r['snapshot'] for r in db.execute('SELECT l.snapshot FROM lesson_sessions l JOIN sessions s ON s.id=l.session_id WHERE s.user_id=? AND s.completed IS NULL',(user['id'],))]
                    allowed={step.get('video','') for snapshot in snapshots for block in json.loads(snapshot)['blocks'] for step in block['steps']}
                    if self.path not in allowed: raise ApiError(403,'Vídeo não atribuído.')
                media_root=(ROOT/'media').resolve(); file=(media_root/self.path.removeprefix('/media/')).resolve()
                if not file.is_relative_to(media_root) or not file.is_file() or file.suffix.lower() not in ('.mp4','.webm'): raise ApiError(404,'Vídeo indisponível.')
                size=file.stat().st_size; start,end=0,size-1; partial=False
                range_header=self.headers.get('Range','')
                if range_header:
                    import re
                    match=re.fullmatch(r'bytes=(\d+)-(\d*)',range_header)
                    if not match: raise ApiError(416,'Intervalo inválido.')
                    start=int(match[1]);end=min(int(match[2]) if match[2] else start+4*1024*1024-1,size-1);partial=True
                    if start>end: raise ApiError(416,'Intervalo inválido.')
                self.send_response(206 if partial else 200);self.send_header('Content-Type','video/mp4' if file.suffix.lower()=='.mp4' else 'video/webm');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
                if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                self.end_headers()
                with file.open('rb') as stream:
                    stream.seek(start);remaining=end-start+1
                    while remaining:
                        chunk=stream.read(min(65536,remaining))
                        if not chunk:break
                        self.wfile.write(chunk);remaining-=len(chunk)
                return
            if self.command == 'GET' and not self.path.startswith('/api/'):
                files = {'/':'index.html','/app.js':'app.js','/protocol.js':'protocol.js','/care.js':'care.js','/staff.js':'staff.js','/style.css':'style.css','/brand.css':'brand.css'}
                name = files.get(self.path)
                if not name: raise ApiError(404,'Não encontrado')
                return self.send(200,(ROOT/'web'/name).read_bytes(),mime='text/css' if name.endswith('.css') else 'text/javascript' if name.endswith('.js') else 'text/html')
            body = {}
            if self.command == 'POST':
                if self.headers.get('Origin') != ORIGIN: raise ApiError(403,'Origem não permitida.')
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 16384: raise ApiError(400,'Conteúdo inválido.')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body,dict): raise ApiError(400,'Conteúdo inválido.')
            with connect() as db:
                if self.command == 'POST':
                    db.execute('BEGIN IMMEDIATE')
                if self.path in ('/api/login','/api/register') and self.command == 'POST':
                    email = str(body.get('email','')).strip().lower()
                    pwd = str(body.get('password',''))
                    key = hashlib.sha256((self.client_address[0]+email).encode()).hexdigest()
                    now = time.time()
                    db.execute('DELETE FROM attempts WHERE expires<?',(now,))
                    db.execute('INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',(key,now+900))
                    db.commit()
                    if db.execute('SELECT count FROM attempts WHERE key=?',(key,)).fetchone()[0]>20: raise ApiError(429,'Muitas tentativas. Aguarde 15 minutos.')
                    if self.path == '/api/register':
                        if not 2<=len(str(body.get('name','')).strip())<=100 or '@' not in email or len(email)>254 or not 12<=len(pwd)<=256 or body.get('consent') is not True: raise ApiError(400,'Informe nome, e-mail, senha de 12 a 256 caracteres e aceite o uso dos dados no piloto.')
                        try: db.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)',(body['name'].strip(),email,password(pwd)))
                        except sqlite3.IntegrityError: raise ApiError(409,'Cadastro não disponível para este e-mail.')
                        user = db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                        default_clinician=os.environ.get('DEFAULT_CLINICIAN_EMAIL','').strip().lower()
                        if default_clinician:
                            clinician=db.execute("SELECT id FROM users WHERE email=? AND role='clinician'",(default_clinician,)).fetchone()
                            if not clinician: raise ApiError(503,'A equipe responsável ainda não foi configurada. Tente novamente após a configuração do serviço.')
                            db.execute('INSERT INTO assignments VALUES(?,?)',(user['id'],clinician['id']))
                            audit(db,clinician['id'],user['id'],'pilot enrollment assignment')
                        db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(user['id'],'consent',json.dumps({'version':'pilot-1','purpose':'acompanhamento local'}),now))
                    else:
                        user = db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                        if not user or len(pwd)>256 or not hmac.compare_digest(password(pwd,user['password'].split(':')[0]),user['password']): raise ApiError(401,'E-mail ou senha inválidos.')
                    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
                    db.execute('DELETE FROM tokens WHERE user_id=?',(user['id'],))
                    db.execute('INSERT INTO tokens VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],now+28800,csrf))
                    audit(db,user['id'],user['id'],'login')
                    return self.send(200,{'ok':True},cookie=f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if SECURE else ''))
                user = self.auth(db); uid = user['id']
                if self.path == '/api/admin/accounts' and self.command=='GET':
                    if user['role']!='admin': raise ApiError(403,'Acesso de administração necessário.')
                    return self.send(200,[dict(r) for r in db.execute('SELECT u.id,u.name,u.email,u.role,u.state,a.clinician FROM users u LEFT JOIN assignments a ON a.user_id=u.id ORDER BY u.name')])
                if self.path in ('/api/admin/role','/api/admin/assign') and self.command=='POST':
                    if user['role']!='admin': raise ApiError(403,'Acesso de administração necessário.')
                    supplied=str(body.get('password',''))
                    attempt_key=f'admin-reauth-{uid}'
                    previous=db.execute('SELECT count,expires FROM attempts WHERE key=?',(attempt_key,)).fetchone()
                    if previous and previous['expires']>time.time() and previous['count']>=10: raise ApiError(429,'Muitas tentativas de confirmação. Aguarde 15 minutos.')
                    if len(supplied)>256 or not hmac.compare_digest(password(supplied,user['password'].split(':')[0]),user['password']):
                        count=previous['count']+1 if previous and previous['expires']>time.time() else 1
                        db.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET count=excluded.count,expires=excluded.expires',(attempt_key,count,time.time()+900));db.commit()
                        raise ApiError(403,'Confirme sua senha de administrador.')
                    db.execute('DELETE FROM attempts WHERE key=?',(attempt_key,))
                    target=body.get('id')
                    account=db.execute('SELECT * FROM users WHERE id=?',(target,)).fetchone()
                    if not account or target==uid: raise ApiError(400,'Escolha outra conta válida.')
                    if self.path.endswith('/role'):
                        role=body.get('role')
                        if role not in ('participant','clinician') or account['role']=='admin': raise ApiError(400,'Papel não permitido.')
                        if role=='participant' and db.execute('SELECT 1 FROM assignments WHERE clinician=?',(target,)).fetchone(): raise ApiError(409,'Reatribua os participantes antes de remover o papel profissional.')
                        if role=='clinician' and (db.execute('SELECT 1 FROM assignments WHERE user_id=?',(target,)).fetchone() or db.execute('SELECT 1 FROM sessions WHERE user_id=?',(target,)).fetchone()): raise ApiError(409,'Crie uma conta profissional separada da conta de participante.')
                        db.execute('UPDATE users SET role=? WHERE id=?',(role,target));db.execute('DELETE FROM tokens WHERE user_id=?',(target,))
                        audit(db,uid,target,'admin role changed: '+role)
                    else:
                        clinician=body.get('clinician')
                        if account['role']!='participant' or not db.execute("SELECT 1 FROM users WHERE id=? AND role='clinician'",(clinician,)).fetchone(): raise ApiError(400,'Selecione um participante e um profissional válido.')
                        db.execute('INSERT INTO assignments VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET clinician=excluded.clinician',(target,clinician))
                        # Assignment does not preserve an old clinical release under a new professional.
                        db.execute("UPDATE users SET state='em_revisao' WHERE id=?",(target,))
                        db.execute('DELETE FROM protocol_policies WHERE user_id=?',(target,))
                        audit(db,uid,target,'admin assignment changed')
                    return self.send(200,{'ok':True})
                if self.path == '/api/pause' and self.command == 'POST':
                    db.execute("UPDATE users SET state='suspenso' WHERE id=?",(uid,))
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'pause',json.dumps({'notes':'Pausa solicitada pelo participante.'}),time.time()))
                    audit(db,uid,uid,'participant requested pause')
                    return self.send(200,{'ok':True})
                if self.path == '/api/message' and self.command == 'POST':
                    note=str(body.get('notes','')).strip()
                    if not 3<=len(note)<=2000: raise ApiError(400,'Escreva uma mensagem de 3 a 2000 caracteres.')
                    target=body.get('id',uid)
                    if user['role']=='clinician':
                        if not db.execute('SELECT 1 FROM assignments WHERE user_id=? AND clinician=?',(target,uid)).fetchone(): raise ApiError(403,'Participante não atribuído.')
                    elif user['role']!='participant' or target!=uid: raise ApiError(403,'Mensagem não permitida.')
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(target,'message',json.dumps({'notes':note,'sender':user['role'],'author':user['name']}),time.time()))
                    audit(db,uid,target,'message recorded')
                    return self.send(200,{'ok':True})
                if self.path == '/api/between' and self.command == 'POST':
                    activity=body.get('activity')
                    if activity not in ('descanso','caminhada','bicicleta','outra'): raise ApiError(400,'Escolha como foi seu dia.')
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'between',json.dumps({'activity':activity,'notes':str(body.get('notes',''))[:2000]}),time.time()))
                    return self.send(200,{'ok':True})
                if self.path == '/api/triage/draft' and self.command == 'POST':
                    payload={k:str(body.get(k,''))[:1000] for k in ('duration','newSymptoms','goal','symptoms','care','function','preference')}
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'triage_draft',json.dumps(payload),time.time()))
                    return self.send(200,{'ok':True})
                if self.path == '/api/protocol' and self.command == 'GET':
                    policy=db.execute('SELECT * FROM protocol_policies WHERE user_id=?',(uid,)).fetchone()
                    calibration=db.execute('SELECT * FROM calibrations WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
                    valid=bool(policy and calibration and calibration['created']>time.time()-86400 and calibration['policy_updated']==policy['updated'])
                    progress={r['module']:r['count'] for r in db.execute('SELECT l.module,count(*) AS count FROM lesson_sessions l JOIN sessions s ON s.id=l.session_id WHERE s.user_id=? AND s.completed IS NOT NULL GROUP BY l.module',(uid,))}
                    last=db.execute('SELECT l.*,s.completed FROM lesson_sessions l JOIN sessions s ON s.id=l.session_id WHERE s.user_id=? ORDER BY s.id DESC LIMIT 1',(uid,)).fetchone()
                    ongoing=last if last and not last['completed'] and user['state']=='ativo' else None
                    return self.send(200,{'modules':MODULES,'module':json.loads(policy['config'])['module'] if policy else 1,'targetSessions':json.loads(policy['config']).get('targetSessions') if policy else None,'configured':bool(policy),'active':user['state']=='ativo','calibrated':valid,'progress':progress,'lesson':json.loads(ongoing['snapshot']) if ongoing else json.loads(calibration['snapshot']) if valid else None,'ongoing':ongoing['session_id'] if ongoing else None})
                if self.path == '/api/checkin' and self.command == 'POST':
                    pain,sleep,stress=body.get('pain'),body.get('sleep'),body.get('stress')
                    if any(type(v) is not int for v in (pain,sleep,stress)) or not 0<=pain<=10 or not 1<=sleep<=3 or not 1<=stress<=3: raise ApiError(400,'Responda dor, sono e disposição.')
                    policy=db.execute('SELECT * FROM protocol_policies WHERE user_id=?',(uid,)).fetchone()
                    if user['state']!='ativo' or not policy: raise ApiError(403,'Sua equipe ainda precisa preparar a aula individual.')
                    latest=db.execute('SELECT completed,followup FROM sessions WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
                    if latest and (latest['completed'] is None or latest['followup'] is None): raise ApiError(409,'Retome sua sessão ou preencha o acompanhamento anterior.')
                    previous=db.execute("SELECT payload FROM records WHERE user_id=? AND kind='session' ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
                    effort=json.loads(previous['payload']).get('effort') if previous else None
                    mode,snapshot=lesson_snapshot(json.loads(policy['config']),pain,sleep,stress,effort)
                    db.execute('INSERT INTO calibrations(user_id,pain,sleep,stress,mode,snapshot,policy_updated,created) VALUES(?,?,?,?,?,?,?,?)',(uid,pain,sleep,stress,mode,json.dumps(snapshot),policy['updated'],time.time()))
                    audit(db,uid,uid,'daily calibration: '+mode)
                    return self.send(200,{'ok':True})
                if self.path == '/api/policy' and self.command == 'POST':
                    target=body.get('id')
                    if user['role']!='clinician' or not db.execute('SELECT 1 FROM assignments WHERE user_id=? AND clinician=?',(target,uid)).fetchone(): raise ApiError(403,'Participante não atribuído a você.')
                    policy=validate_policy(body.get('config'))
                    db.execute('INSERT INTO protocol_policies VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET config=excluded.config,clinician=excluded.clinician,updated=excluded.updated',(target,json.dumps(policy),uid,time.time()))
                    audit(db,uid,target,'authorial protocol policy updated')
                    return self.send(200,{'ok':True})
                if self.path == '/api/me' and self.command == 'GET':
                    data = {k:user[k] for k in ('id','name','email','role','state','csrf')}
                    data['records'] = [dict(r) for r in db.execute('SELECT * FROM records WHERE user_id=? ORDER BY created DESC',(uid,))]
                    data['sessions'] = [dict(r) for r in db.execute('SELECT * FROM sessions WHERE user_id=? ORDER BY started DESC',(uid,))]
                    plan = db.execute('SELECT * FROM plans WHERE user_id=?',(uid,)).fetchone()
                    data['plan'] = dict(plan) if plan else None
                    assigned=db.execute('SELECT u.name FROM assignments a JOIN users u ON u.id=a.clinician WHERE a.user_id=?',(uid,)).fetchone()
                    data['careTeam']=dict(assigned) if assigned else None
                    policy=db.execute('SELECT config FROM protocol_policies WHERE user_id=?',(uid,)).fetchone()
                    data['betweenInstruction']=json.loads(policy['config']).get('betweenInstruction') if policy else None
                    return self.send(200,data)
                if self.path == '/api/logout' and self.command == 'POST':
                    db.execute('DELETE FROM tokens WHERE hash=?',(user['token_hash'],))
                    return self.send(200,{'ok':True},cookie='session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                if self.path == '/api/triage' and self.command == 'POST':
                    if not isinstance(body.get('duration'),str) or not body['duration'] or body.get('newSymptoms') not in ('sim','nao','nao_sei'): raise ApiError(400,'Responda todas as perguntas.')
                    payload = {'duration':body['duration'][:100],'newSymptoms':body['newSymptoms'],'goal':str(body.get('goal',''))[:1000],'version':'pilot-2',**{k:str(body.get(k,''))[:1000] for k in ('symptoms','care','function','preference')}}
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'triage',json.dumps(payload),time.time()))
                    db.execute("UPDATE users SET state='em_revisao' WHERE id=?",(uid,))
                    audit(db,uid,uid,'triage submitted')
                    return self.send(200,{'ok':True})
                if self.path == '/api/session/start' and self.command == 'POST':
                    plan = db.execute('SELECT content FROM plans WHERE user_id=?',(uid,)).fetchone()
                    if user['state']!='ativo' or not plan: raise ApiError(403,'Aguarde orientação profissional.')
                    latest = db.execute('SELECT * FROM sessions WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
                    if latest and (latest['completed'] is None or latest['followup'] is None): raise ApiError(409,'Conclua a sessão ou seu acompanhamento antes de iniciar outra.')
                    policy=db.execute('SELECT * FROM protocol_policies WHERE user_id=?',(uid,)).fetchone()
                    calibration=None
                    if policy:
                        calibration=db.execute('SELECT * FROM calibrations WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
                        if not calibration or calibration['created']<time.time()-86400 or calibration['policy_updated']!=policy['updated']: raise ApiError(409,'Faça a calibração de hoje antes de começar.')
                    cursor = db.execute('INSERT INTO sessions(user_id,started,plan) VALUES(?,?,?)',(uid,time.time(),plan['content']))
                    if calibration:
                        snapshot=json.loads(calibration['snapshot'])
                        db.execute('INSERT INTO lesson_sessions VALUES(?,?,?,?,?)',(cursor.lastrowid,calibration['id'],snapshot['module'],snapshot['mode'],calibration['snapshot']))
                    audit(db,uid,uid,'session started')
                    return self.send(200,{'id':cursor.lastrowid})
                if self.path in ('/api/session/complete','/api/session/followup') and self.command == 'POST':
                    session = db.execute('SELECT * FROM sessions WHERE id=? AND user_id=?',(body.get('id'),uid)).fetchone()
                    if not session: raise ApiError(404,'Sessão não encontrada.')
                    skipped=body.get('skipped') is True
                    pain = None if skipped else body.get('pain')
                    if not skipped and (isinstance(pain,bool) or not isinstance(pain,(int,float)) or not 0<=pain<=10): raise ApiError(400,'Dor deve estar entre 0 e 10, ou registre que não respondeu.')
                    effort=None if skipped else body.get('effort')
                    if body.get('newSymptoms','nao_sei') not in ('sim','nao','nao_sei'): raise ApiError(400,'Informe se houve sintoma novo ou diferente.')
                    if effort is not None and effort not in ('leve','moderado','dificil') and (isinstance(effort,bool) or not isinstance(effort,(int,float)) or not 0<=effort<=10): raise ApiError(400,'Esforço deve estar entre 0 e 10.')
                    followup = self.path.endswith('followup')
                    if followup:
                        if not session['completed'] or time.time()<session['completed']+86400: raise ApiError(409,'Acompanhamento disponível 24 horas após a conclusão.')
                        if session['followup']: return self.send(200,{'ok':True})
                        if not skipped: db.execute('UPDATE sessions SET followup=? WHERE id=?',(time.time(),session['id']))
                    else:
                        if session['completed']: return self.send(200,{'ok':True})
                        if not skipped and db.execute('SELECT 1 FROM lesson_sessions WHERE session_id=?',(session['id'],)).fetchone() and effort is None: raise ApiError(400,'Informe como sentiu o esforço.')
                        db.execute('UPDATE sessions SET completed=? WHERE id=?',(time.time(),session['id']))
                        lesson=db.execute('SELECT mode FROM lesson_sessions WHERE session_id=?',(session['id'],)).fetchone()
                        if lesson and lesson['mode']=='advance':
                            policy=db.execute('SELECT config FROM protocol_policies WHERE user_id=?',(uid,)).fetchone()
                            config=json.loads(policy['config']);config['allowAdvance']=False
                            db.execute('UPDATE protocol_policies SET config=?,updated=? WHERE user_id=?',(json.dumps(config),time.time(),uid))
                            audit(db,uid,uid,'single challenge authorization consumed')
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'followup' if followup else 'session',json.dumps({'session':session['id'],'pain':pain,'scale':'NRS 0-10','recall':'agora','effort':effort,'effortScale':'numeric-authorial-0-10' if isinstance(effort,(int,float)) else 'categorical-authorial-1','response':'missing' if skipped else 'answered','newSymptoms':body.get('newSymptoms','nao_sei'),'function':str(body.get('function',''))[:1000],'notes':str(body.get('notes',''))[:2000]}),time.time()))
                    audit(db,uid,uid,'followup' if followup else 'session completed')
                    return self.send(200,{'ok':True})
                if self.path == '/api/event' and self.command == 'POST':
                    note = str(body.get('notes','')).strip()
                    if not 3<=len(note)<=2000: raise ApiError(400,'Descreva o ocorrido em até 2000 caracteres.')
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(uid,'event',json.dumps({'notes':note}),time.time()))
                    db.execute("UPDATE users SET state='suspenso' WHERE id=?",(uid,)); audit(db,uid,uid,'event reported, suspended')
                    return self.send(200,{'ok':True})
                if self.path == '/api/patients' and self.command == 'GET':
                    if user['role']!='clinician': raise ApiError(403,'Acesso profissional necessário.')
                    patients=[]
                    for r in db.execute('SELECT u.id,u.name,u.state FROM users u JOIN assignments a ON a.user_id=u.id WHERE a.clinician=?',(uid,)):
                        p=dict(r); p['records']=[dict(x) for x in db.execute('SELECT kind,payload,created FROM records WHERE user_id=? ORDER BY created DESC',(r['id'],))]
                        policy=db.execute('SELECT config FROM protocol_policies WHERE user_id=?',(r['id'],)).fetchone()
                        p['policy']=json.loads(policy['config']) if policy else None
                        latest_review=max((x['created'] for x in p['records'] if x['kind']=='review'),default=0)
                        last_reply=max((x['created'] for x in p['records'] if x['kind']=='message' and json.loads(x['payload']).get('sender')=='clinician'),default=0)
                        p['pendingEvents']=sum(x['kind'] in ('event','pause') and x['created']>latest_review for x in p['records'])
                        p['pendingMessages']=sum(x['kind']=='message' and json.loads(x['payload']).get('sender')=='participant' and x['created']>last_reply for x in p['records'])
                        p['pendingFollowup']=db.execute('SELECT count(*) FROM sessions WHERE user_id=? AND completed IS NOT NULL AND followup IS NULL',(r['id'],)).fetchone()[0]
                        patients.append(p)
                    return self.send(200,patients)
                if self.path == '/api/review' and self.command == 'POST':
                    target=body.get('id'); state=body.get('state'); note=str(body.get('notes','')).strip(); plan=str(body.get('plan','')).strip()
                    if user['role']!='clinician' or not db.execute('SELECT 1 FROM assignments WHERE user_id=? AND clinician=?',(target,uid)).fetchone(): raise ApiError(403,'Participante não atribuído a você.')
                    if state not in ('ativo','suspenso','encaminhado') or len(note)<5 or len(note)>2000 or (state=='ativo' and not 5<=len(plan)<=4000): raise ApiError(400,'Informe decisão, justificativa e orientação individual para ativar.')
                    db.execute('UPDATE users SET state=? WHERE id=?',(state,target))
                    if state=='ativo': db.execute('INSERT INTO plans VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET content=excluded.content,clinician=excluded.clinician,updated=excluded.updated',(target,plan,uid,time.time()))
                    db.execute('INSERT INTO records(user_id,kind,payload,created) VALUES(?,?,?,?)',(target,'review',json.dumps({'state':state,'notes':note,'clinician':uid}),time.time()))
                    audit(db,uid,target,'clinical review: '+state)
                    return self.send(200,{'ok':True})
                raise ApiError(404,'Recurso não encontrado.')
        except ApiError as e: self.send(e.status,{'error':e.message})
        except (ValueError,TypeError,json.JSONDecodeError): self.send(400,{'error':'Dados inválidos.'})
        except Exception: self.send(500,{'error':'Não foi possível concluir. Tente novamente.'})

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8080); parser.add_argument('--clinician'); parser.add_argument('--admin'); parser.add_argument('--assign',nargs=2,metavar=('PARTICIPANT_EMAIL','CLINICIAN_EMAIL')); args=parser.parse_args(); initialize()
    if args.clinician or args.admin:
        import getpass
        pwd=getpass.getpass('Senha profissional (mínimo 12 caracteres): ')
        if len(pwd)<12: raise SystemExit('Senha insuficiente')
        with connect() as db: db.execute("INSERT INTO users(name,email,password,role,state) VALUES(?,?,?,?,'ativo')",('Administrador' if args.admin else 'Profissional',(args.admin or args.clinician).lower(),password(pwd),'admin' if args.admin else 'clinician'))
    elif args.assign:
        with connect() as db:
            p=db.execute("SELECT id FROM users WHERE email=? AND role='participant'",(args.assign[0].lower(),)).fetchone(); c=db.execute("SELECT id FROM users WHERE email=? AND role='clinician'",(args.assign[1].lower(),)).fetchone()
            if not p or not c: raise SystemExit('Contas não encontradas')
            db.execute('INSERT INTO assignments VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET clinician=excluded.clinician',(p['id'],c['id']))
            audit(db,c['id'],p['id'],'assignment')
    else:
        print(f'Aplicativo local: {ORIGIN}',flush=True)
        ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

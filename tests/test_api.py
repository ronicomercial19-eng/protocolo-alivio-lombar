import http.cookiejar, json, os, sqlite3, subprocess, sys, tempfile, time, unittest, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.db=Path(cls.tmp.name)/'test.sqlite3'; server.DB=cls.db; server.initialize()
        with server.connect() as db:
            db.execute("INSERT INTO users(name,email,password,role,state) VALUES(?,?,?,'clinician','ativo')",('Equipe','clinic@example.test',server.password('long-test-password')))
        with server.connect() as db:
            db.execute("INSERT INTO users(name,email,password,role,state) VALUES(?,?,?,'admin','ativo')",('Admin','admin@example.test',server.password('long-test-password')))
        env={**os.environ,'APP_DB':str(cls.db),'APP_ORIGIN':'http://127.0.0.1:8081'}
        cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port','8081'],env=env,stdout=subprocess.DEVNULL)
        for _ in range(40):
            try: urllib.request.urlopen('http://127.0.0.1:8081/');break
            except OSError: time.sleep(.1)
    @classmethod
    def tearDownClass(cls): cls.proc.terminate();cls.proc.wait();cls.tmp.cleanup()
    def client(self): return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(self,c,path,body=None,csrf='',origin='http://127.0.0.1:8081'):
        req=urllib.request.Request('http://127.0.0.1:8081/api/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','Origin':origin,'X-CSRF-Token':csrf})
        try:
            with c.open(req) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_end_to_end_and_authorization(self):
        a,b,c=self.client(),self.client(),self.client()
        for client,email in [(a,'a@example.test'),(b,'b@example.test')]:
            self.assertEqual(self.call(client,'register',{'name':'Teste','email':email,'password':'long-test-password','consent':True})[0],200)
        ua=self.call(a,'me')[1];ub=self.call(b,'me')[1]
        self.assertEqual(self.call(a,'triage/draft',{'duration':'3 meses','goal':'Subir escadas'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'me')[1]['state'],'triagem_pendente')
        self.assertEqual(self.call(a,'between',{'activity':'caminhada','notes':'Dia fictício'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'message',{'notes':'Mensagem fictícia','id':ub['id']},ua['csrf'])[0],403)
        self.assertEqual(self.call(a,'message',{'notes':'Mensagem fictícia'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'triage',{'duration':'3 meses','newSymptoms':'nao'},'wrong')[0],403)
        self.assertEqual(self.call(a,'triage',{'duration':'3 meses','newSymptoms':'nao'},ua['csrf'],'https://evil.test')[0],403)
        self.assertEqual(self.call(a,'triage',{'duration':'3 meses','newSymptoms':'nao'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],403)
        self.assertEqual(self.call(a,'patients')[0],403)
        self.assertEqual(self.call(c,'login',{'email':'clinic@example.test','password':'long-test-password'})[0],200)
        uc=self.call(c,'me')[1]
        self.assertEqual(self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisado','plan':'OrientaÃ§Ã£o individual de teste'},uc['csrf'])[0],403)
        with server.connect() as db: db.execute('INSERT INTO assignments VALUES(?,?)',(ua['id'],uc['id']))
        self.assertEqual(self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisado','plan':'OrientaÃ§Ã£o individual de teste'},uc['csrf'])[0],200)
        config={'module':1,'painProtection':6,'sleepProtection':1,'stressProtection':3,'painAdvance':1,'sleepAdvance':3,'stressAdvance':1,'allowAdvance':True,
                'preparation':[{'title':'Preparação','instruction':'Teste fictício','seconds':5}],
                'maintenance':[{'title':'Principal','instruction':'Teste fictício','seconds':5}],
                'protection':[{'title':'Proteção','instruction':'Teste fictício','seconds':5}],
                'challenge':[{'title':'Desafio','instruction':'Teste fictício','seconds':5}]}
        self.assertEqual(self.call(a,'policy',{'id':ua['id'],'config':config},ua['csrf'])[0],403)
        self.assertEqual(self.call(c,'policy',{'id':ua['id'],'config':config},uc['csrf'])[0],200)
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],409)
        self.assertEqual(self.call(a,'checkin',{'pain':False,'sleep':3,'stress':1},ua['csrf'])[0],400)
        self.assertEqual(self.call(a,'checkin',{'pain':0,'sleep':3,'stress':1},ua['csrf'])[0],200)
        lesson=self.call(a,'protocol')[1]['lesson']
        self.assertEqual(lesson['mode'],'advance');self.assertEqual(len(lesson['blocks']),3)
        self.assertEqual(self.call(a,'checkin',{'pain':7,'sleep':3,'stress':1},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'protocol')[1]['lesson']['mode'],'protection')
        self.assertEqual(self.call(a,'checkin',{'pain':3,'sleep':2,'stress':2},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'protocol')[1]['lesson']['mode'],'maintenance')
        self.assertEqual(self.call(c,'policy',{'id':ua['id'],'config':config},uc['csrf'])[0],200)
        self.assertFalse(self.call(a,'protocol')[1]['calibrated'])
        self.assertEqual(self.call(a,'checkin',{'pain':0,'sleep':3,'stress':1},ua['csrf'])[0],200)
        sid=self.call(a,'session/start',{},ua['csrf'])[1]['id']
        self.assertEqual(self.call(a,'checkin',{'pain':3,'sleep':2,'stress':2},ua['csrf'])[0],409)
        self.assertEqual(self.call(a,'session/complete',{'id':sid,'pain':3},ua['csrf'])[0],400)
        self.assertEqual(self.call(b,'session/complete',{'id':sid,'pain':3},ub['csrf'])[0],404)
        self.assertEqual(self.call(a,'session/complete',{'id':sid,'pain':11},ua['csrf'])[0],400)
        self.assertEqual(self.call(a,'session/complete',{'id':sid,'pain':3,'effort':'dificil'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'session/followup',{'id':sid,'pain':3},ua['csrf'])[0],409)
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],409)
        with server.connect() as db:db.execute('UPDATE sessions SET completed=? WHERE id=?',(time.time()-86401,sid))
        self.assertEqual(self.call(a,'session/followup',{'id':sid,'skipped':True},ua['csrf'])[0],200)
        missing=self.call(a,'me')[1]
        self.assertIsNone(missing['sessions'][0]['followup'])
        self.assertEqual(json.loads(missing['records'][0]['payload'])['response'],'missing')
        self.assertIsNone(json.loads(missing['records'][0]['payload'])['pain'])
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],409)
        self.assertEqual(self.call(a,'session/followup',{'id':sid,'pain':2},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'checkin',{'pain':0,'sleep':3,'stress':1},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'protocol')[1]['lesson']['mode'],'protection')
        self.assertEqual(self.call(a,'protocol')[1]['progress']['1'],1)
        self.assertEqual(len(self.call(c,'patients')[1]),1)
        self.assertEqual(self.call(b,'me')[1]['sessions'],[])
        self.assertEqual(self.call(a,'pause',{},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'me')[1]['state'],'suspenso')
        self.assertEqual(self.call(a,'event',{'notes':'Sintoma novo de teste'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],403)
        self.assertEqual(self.call(a,'logout',{},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'me')[0],401)


    def test_single_use_challenge_and_numeric_effort(self):
        a,c=self.client(),self.client()
        self.assertEqual(self.call(a,'register',{'name':'Teste desafio','email':'challenge@example.test','password':'long-test-password','consent':True})[0],200)
        ua=self.call(a,'me')[1]
        self.call(c,'login',{'email':'clinic@example.test','password':'long-test-password'})
        uc=self.call(c,'me')[1]
        with server.connect() as db:db.execute('INSERT INTO assignments VALUES(?,?)',(ua['id'],uc['id']))
        self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisão fictícia','plan':'Orientação fictícia'},uc['csrf'])
        step={'title':'Teste','instruction':'Somente teste','seconds':5}
        config={'module':1,'painProtection':6,'sleepProtection':1,'stressProtection':3,'painAdvance':1,'sleepAdvance':3,'stressAdvance':1,'allowAdvance':True,'preparation':[step],'maintenance':[step],'protection':[step],'challenge':[step]}
        self.call(c,'policy',{'id':ua['id'],'config':config},uc['csrf'])
        self.call(a,'checkin',{'pain':0,'sleep':3,'stress':1},ua['csrf'])
        sid=self.call(a,'session/start',{},ua['csrf'])[1]['id']
        self.assertEqual(self.call(a,'session/complete',{'id':sid,'pain':2,'effort':4,'newSymptoms':'nao'},ua['csrf'])[0],200)
        rows=self.call(c,'patients')[1]
        self.assertFalse(next(p for p in rows if p['id']==ua['id'])['policy']['allowAdvance'])
        payload=json.loads(self.call(a,'me')[1]['records'][0]['payload'])
        self.assertEqual(payload['effort'],4)
        self.assertEqual(payload['effortScale'],'numeric-authorial-0-10')
        self.assertFalse(self.call(a,'protocol')[1]['calibrated'])

    def test_admin_roles_assignment_and_backup(self):
        a,admin=self.client(),self.client()
        self.call(a,'register',{'name':'Gestão teste','email':'managed@example.test','password':'long-test-password','consent':True})
        ua=self.call(a,'me')[1]
        self.assertEqual(self.call(a,'admin/accounts')[0],403)
        self.call(admin,'login',{'email':'admin@example.test','password':'long-test-password'})
        op=self.call(admin,'me')[1]
        self.assertEqual(self.call(admin,'admin/role',{'id':ua['id'],'role':'clinician','password':'wrong'},op['csrf'])[0],403)
        self.assertEqual(self.call(admin,'admin/role',{'id':ua['id'],'role':'clinician','password':'long-test-password'},op['csrf'])[0],200)
        self.assertEqual(self.call(a,'me')[0],401)
        self.call(a,'register',{'name':'Paciente teste','email':'assigned@example.test','password':'long-test-password','consent':True})
        patient=self.call(a,'me')[1]
        self.assertEqual(self.call(admin,'admin/assign',{'id':patient['id'],'clinician':ua['id'],'password':'long-test-password'},op['csrf'])[0],200)
        self.assertEqual(self.call(a,'me')[1]['state'],'em_revisao')
        accounts=self.call(admin,'admin/accounts')[1]
        self.assertFalse(any('records' in row or 'password' in row for row in accounts))
        self.assertEqual(self.call(admin,'patients')[0],403)
        self.assertEqual(self.call(admin,'admin/role',{'id':ua['id'],'role':'participant','password':'long-test-password'},op['csrf'])[0],409)
        backup=Path(self.tmp.name)/'backup.sqlite3'
        result=subprocess.run([sys.executable,str(ROOT/'backup.py'),str(backup)],env={**os.environ,'APP_DB':str(self.db)},capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        db=sqlite3.connect(backup)
        try:self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        finally:db.close()

if __name__=='__main__':unittest.main()

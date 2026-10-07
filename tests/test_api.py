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
    def test_product_evaluation_and_operational_metrics(self):
        clinician,admin,participant=self.client(),self.client(),self.client()
        self.assertEqual(self.call(clinician,'login',{'email':'clinic@example.test','password':'long-test-password'})[0],200)
        self.assertEqual(self.call(admin,'login',{'email':'admin@example.test','password':'long-test-password'})[0],200)
        self.assertEqual(self.call(participant,'register',{'name':'Avaliação fictícia','email':'evaluation@example.test','password':'long-test-password','consent':True})[0],200)
        clinician_csrf=self.call(clinician,'me')[1]['csrf']
        participant_csrf=self.call(participant,'me')[1]['csrf']
        self.assertEqual(self.call(participant,'evaluation')[0],403)
        self.assertEqual(self.call(participant,'admin/metrics')[0],403)
        self.assertEqual(self.call(clinician,'evaluation',{'item':'safety','status':'approved','notes':'Revisão do fluxo fictício'},clinician_csrf)[0],200)
        self.assertEqual(self.call(clinician,'evaluation')[1][0]['status'],'approved')
        self.assertEqual(self.call(clinician,'evaluation',{'item':'unknown','status':'approved','notes':'Revisão do fluxo fictício'},clinician_csrf)[0],400)
        self.assertEqual(self.call(participant,'triage',{'duration':'3 meses','newSymptoms':'nao','neurologicConcern':'nao','seriousCondition':'nao'},participant_csrf)[0],200)
        metrics=self.call(admin,'admin/metrics')[1]
        self.assertGreaterEqual(metrics['participants'],1)
        self.assertGreaterEqual(metrics['states']['em_revisao'],1)
        self.assertGreaterEqual(metrics['funnel']['registered'],metrics['funnel']['triaged'])
        self.assertGreaterEqual(metrics['funnel']['triaged'],1)
        self.assertEqual(metrics['funnel']['answeredFollowup'],0)
    def test_educator_cannot_release_clinical_care(self):
        educator,patient,admin=self.client(),self.client(),self.client()
        self.assertEqual(self.call(educator,'register',{'name':'Educador fictício','email':'educator@example.test','password':'long-test-password','consent':True})[0],200)
        educator_id=self.call(educator,'me')[1]['id']
        self.assertEqual(self.call(patient,'register',{'name':'Paciente educador','email':'educator-patient@example.test','password':'long-test-password','consent':True})[0],200)
        patient_id=self.call(patient,'me')[1]['id']
        self.assertEqual(self.call(admin,'login',{'email':'admin@example.test','password':'long-test-password'})[0],200)
        csrf=self.call(admin,'me')[1]['csrf']
        self.assertEqual(self.call(admin,'admin/role',{'id':educator_id,'role':'educator','password':'long-test-password'},csrf)[0],200)
        self.assertEqual(self.call(admin,'admin/assign-educator',{'id':patient_id,'educator':educator_id,'password':'long-test-password'},csrf)[0],200)
        self.assertEqual(self.call(educator,'login',{'email':'educator@example.test','password':'long-test-password'})[0],200)
        educator_csrf=self.call(educator,'me')[1]['csrf']
        self.assertEqual(self.call(educator,'patients')[0],403)
        self.assertEqual(self.call(educator,'evaluation')[0],403)
        self.assertEqual(self.call(educator,'review',{'id':patient_id,'state':'ativo','notes':'Tentativa de liberação','plan':'Plano indevido'},educator_csrf)[0],403)
        self.assertEqual(self.call(educator,'educator/note',{'id':patient_id,'notes':'Observação de execução fictícia'},educator_csrf)[0],200)
        cases=self.call(educator,'educator/patients')[1]
        self.assertEqual(len(cases),1)
        self.assertFalse(any(r['kind']=='triage' for r in cases[0]['records']))
    def test_neurologic_concern_pauses_until_assessed(self):
        patient,admin,doctor=self.client(),self.client(),self.client()
        self.assertEqual(self.call(patient,'register',{'name':'Risco fictício','email':'risk@example.test','password':'long-test-password','consent':True})[0],200)
        me=self.call(patient,'me')[1]
        self.assertEqual(self.call(admin,'login',{'email':'admin@example.test','password':'long-test-password'})[0],200)
        admin_csrf=self.call(admin,'me')[1]['csrf']
        doctor_id=next(x['id'] for x in self.call(admin,'admin/accounts')[1] if x['email']=='clinic@example.test')
        self.assertEqual(self.call(admin,'admin/assign',{'id':me['id'],'clinician':doctor_id,'password':'long-test-password'},admin_csrf)[0],200)
        self.assertEqual(self.call(patient,'triage',{'duration':'3 meses','newSymptoms':'sim','neurologicConcern':'sim','seriousCondition':'nao'},me['csrf'])[0],200)
        self.assertEqual(self.call(patient,'me')[1]['state'],'suspenso')
        self.assertEqual(self.call(doctor,'login',{'email':'clinic@example.test','password':'long-test-password'})[0],200)
        doctor_csrf=self.call(doctor,'me')[1]['csrf']
        case=next(x for x in self.call(doctor,'patients')[1] if x['id']==me['id'])
        self.assertTrue(case['pendingRisk'])
        decision={'id':me['id'],'state':'ativo','notes':'Avaliação individual fictícia documentada','plan':'Orientação individual fictícia','reviewed':True}
        self.assertEqual(self.call(doctor,'review',decision,doctor_csrf)[0],400)
        decision['urgentAssessed']=True
        self.assertEqual(self.call(doctor,'review',decision,doctor_csrf)[0],200)
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
        self.assertEqual(self.call(a,'triage',{'duration':'3 meses','newSymptoms':'nao','neurologicConcern':'nao','seriousCondition':'nao'},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'session/start',{},ua['csrf'])[0],403)
        self.assertEqual(self.call(a,'patients')[0],403)
        self.assertEqual(self.call(c,'login',{'email':'clinic@example.test','password':'long-test-password'})[0],200)
        uc=self.call(c,'me')[1]
        self.assertEqual(self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisado','plan':'OrientaÃ§Ã£o individual de teste'},uc['csrf'])[0],403)
        with server.connect() as db: db.execute('INSERT INTO assignments VALUES(?,?)',(ua['id'],uc['id']))
        self.assertEqual(self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisado','plan':'OrientaÃ§Ã£o individual de teste','reviewed':True},uc['csrf'])[0],200)
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
        self.assertIsNotNone(missing['sessions'][0]['followup'])
        self.assertEqual(missing['state'],'em_revisao')
        self.assertEqual(json.loads(missing['records'][0]['payload'])['response'],'missing')
        self.assertIsNone(json.loads(missing['records'][0]['payload'])['pain'])
        self.assertEqual(self.call(a,'session/followup',{'id':sid,'pain':2},ua['csrf'])[0],200)
        self.assertEqual(self.call(a,'checkin',{'pain':0,'sleep':3,'stress':1},ua['csrf'])[0],403)
        self.assertEqual(self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Acompanhamento ausente revisado','plan':'Retomada orientada para teste','reviewed':True},uc['csrf'])[0],200)
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
        self.assertEqual(self.call(a,'triage',{'duration':'3 meses','newSymptoms':'nao','neurologicConcern':'nao','seriousCondition':'nao'},ua['csrf'])[0],200)
        self.call(c,'review',{'id':ua['id'],'state':'ativo','notes':'Revisão fictícia','plan':'Orientação fictícia','reviewed':True},uc['csrf'])
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
        self.assertEqual(self.call(admin,'admin/role',{'id':ua['id'],'role':'physician','password':'wrong'},op['csrf'])[0],403)
        self.assertEqual(self.call(admin,'admin/role',{'id':ua['id'],'role':'physician','password':'long-test-password'},op['csrf'])[0],200)
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

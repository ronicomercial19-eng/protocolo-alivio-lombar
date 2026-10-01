"""Create a separate fictional account to preview the complete journey locally."""
import json, secrets, server, time
server.initialize()
email='jornada@example.test'
pwd=secrets.token_urlsafe(18)
config={'module':1,'targetSessions':12,'painProtection':6,'sleepProtection':1,'stressProtection':3,'painAdvance':1,'sleepAdvance':3,'stressAdvance':1,'allowAdvance':True,
    'preparation':[{'title':'Seu momento de preparação','instruction':'Demonstração de interface. Aqui será exibida a preparação individual aprovada pela equipe, com vídeo, orientação e dose. Não execute exercícios a partir deste exemplo.','seconds':30}],
    'maintenance':[{'title':'Sua etapa principal','instruction':'Demonstração da versão de manutenção. O conteúdo final e a dose serão definidos pelo profissional responsável.','seconds':30}],
    'protection':[{'title':'Uma versão mais suave para hoje','instruction':'Demonstração da versão de proteção. A alternativa individual aprovada aparecerá aqui, sem exigir que você escolha entre treinos.','seconds':30}],
    'challenge':[{'title':'Um passo a mais, se você quiser','instruction':'Demonstração de desafio opcional previamente autorizado. Você pode pular esta etapa. Nenhum exercício está prescrito neste exemplo.','seconds':30}]}
with server.connect() as db:
    if db.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():
        raise SystemExit('Conta demo já existe; não alterada. Use a senha emitida na primeira execução.')
    clinician=db.execute("INSERT INTO users(name,email,password,role,state) VALUES(?,?,?,'clinician','ativo')",('Equipe fictícia','equipe-jornada@example.test',server.password(secrets.token_urlsafe(32)))).lastrowid
    uid=db.execute("INSERT INTO users(name,email,password,state) VALUES(?,?,?,'ativo')",('Jornada Demonstrativa',email,server.password(pwd))).lastrowid
    db.execute('INSERT INTO assignments VALUES(?,?)',(uid,clinician))
    db.execute('INSERT INTO plans VALUES(?,?,?,?)',(uid,'Conta fictícia para demonstração da jornada. Nenhuma prescrição real.',clinician,time.time()))
    db.execute('INSERT INTO protocol_policies VALUES(?,?,?,?)',(uid,json.dumps(config),clinician,time.time()))
    server.audit(db,clinician,uid,'fictional demo seeded')
print('Conta fictícia:',email)
print('Senha temporária local:',pwd)
print('Os limites desta conta são exemplos técnicos, sem uso clínico.')

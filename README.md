# Protocolo Alívio Lombar

Frontend de acompanhamento e backend persistente Python/SQLite, servido por Express para o ambiente Node do AI Studio.

## Executar

Node 22+ e Python 3.13+: `npm ci` e `npm run dev`. Acesse a porta 3000.

Versão compilada: `npm run build` e `npm start`.

[Configuração e jornada do piloto](docs/PILOTO.md): armazenamento persistente, origem HTTPS, equipe responsável e verificações antes de distribuir um link. O Dockerfile inclui ambos os runtimes; validar seu build no ambiente de hospedagem.

A pessoa cria sua conta e segue para a triagem. A equipe revisa antes de liberar aulas. Não existem credenciais administrativas padrão. No mesmo banco, `python server.py --admin EMAIL` cria o administrador.

## Testes

`npm test` verifica o fluxo pelo Express e persistência após reinício.

`python -m unittest discover -s tests -v` verifica API clínica, permissões, registros e backup.

Piloto com identidades fictícias. Cadastro funcionando não significa serviço clínico pronto para dados reais. Consentimento, privacidade, atendimento, conteúdo aprovado, recuperação de conta e infraestrutura dependem da configuração. Sink Score e parâmetros são autorais, sem validação clínica do produto. Vídeos definitivos não incluídos.

Não adicionar senhas, banco, backups, anexos ou dados pessoais ao GitHub.

# Configuração do piloto e cadastro

A versão Express anterior mantinha contas numa Map sem persistência, não emitia cookie e não implementava as APIs de triagem, protocolo e equipe. Rotas ausentes devolviam HTML. Agora o Express encaminha API e mídia ao backend completo Python/SQLite em loopback.

## Executar no AI Studio ou num serviço Node

É necessário Node 22+ e Python 3.13+. Execute `npm ci` e `npm run dev`; para versão compilada: `npm run build` e `npm start`. A porta padrão é 3000. O Dockerfile inclui os dois runtimes; o build Docker ainda precisa ser validado na hospedagem.

Importar ou sincronizar o repositório não confirma que Python está instalado. Se necessário, definir PYTHON_BIN com o caminho do interpretador no serviço. Sem backend, a aplicação responde indisponibilidade explícita; não simula cadastro bem-sucedido.

## Antes de distribuir um link

1. Definir APP_DB em volume persistente; arquivo num container efêmero não preserva contas após substituição da instância. Operar uma instância com SQLite. Não escalar réplicas independentes com bancos locais.
2. Definir PUBLIC_ORIGIN com a URL exata. Atrás de proxy HTTPS confiável, definir TRUST_PROXY=1. Não confiar em proxies arbitrários.
3. No mesmo banco, criar administrador: `python server.py --admin EMAIL`. A senha é pedida no terminal; não existem senhas administrativas padrão.
4. Criar a conta do profissional na interface e atribuir o papel em Gestão. Definir DEFAULT_CLINICIAN_EMAIL com essa conta. Isso atribui o participante à fila de revisão, sem liberar aula. Se o parâmetro estiver errado, o cadastro é recusado sem criar conta parcial. Sem esse parâmetro, atribuição manual e pendência visível ao participante.
5. A equipe cadastra conteúdo e limites individuais e registra a revisão. Verificar toda a jornada com uma conta fictícia nova e repetir o login depois de reiniciar o serviço.

## Jornada e dossiê V3

Cadastro e cookie → avaliação inicial em três passos → espera de revisão → decisão profissional e plano → calibração → aula individual → feedback → registro do dia seguinte.

Requisitos rechecados nas páginas 26–29 do dossiê e no roteiro de telas: ausência de sintomas não significa aptidão automática; avanço de módulo depende do profissional; desafio requer autorização prévia e escolha; respostas puladas são dados ausentes; adesão, resposta e eventos são separados; contato e pausa permanecem disponíveis. Sink Score e parâmetros são autorais, sem alegação de validação clínica. O original do dossiê não foi republicado.

## Testes

`npm test`: TypeScript e teste pelo Express de cadastro, sessão, triagem, atribuição à fila, bloqueio antes de revisão, origem e persistência após reinício.

`python -m unittest discover -s tests -v`: permissões, protocolo, gestão, registros e backup.

## Limites do piloto

Esta distribuição mantém o aviso de uso com dados fictícios. Antes de dados reais, definir responsável pelo serviço, informação de privacidade e consentimento, contato e urgência, conteúdo aprovado, recuperação de conta, infraestrutura e backups protegidos. O dossiê não equivale à aprovação clínica ou jurídica desses itens. Pagamentos e vídeos definitivos não estão integrados.

## Container para teste local

`docker build -t alivio-lombar .`

`docker run --rm -p 3000:3000 -v lombar-data:/app/data alivio-lombar`

O volume preserva o banco. Esses comandos não configuram HTTPS ou equipe automaticamente. Docker não foi executado nesta estação; TypeScript e testes do gateway foram executados.

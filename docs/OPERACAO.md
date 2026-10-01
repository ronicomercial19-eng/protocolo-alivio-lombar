# Operação do piloto

## Primeiro acesso

Requer Python 3.13+. Execute `python server.py`. O aplicativo abre em http://127.0.0.1:8080 e grava em `data/app.sqlite3`.

Crie um administrador pelo terminal do servidor:

```sh
python server.py --admin administrador@example.test
```

A senha é solicitada sem eco. Não há administrador padrão, senha pública ou promoção de papel pelo cadastro. Na interface, profissionais e participantes cadastram suas contas. O administrador entra em Gestão, promove uma conta separada a profissional e atribui os participantes. Alterações exigem confirmação da senha do administrador; mudar papel revoga sessões. A administração vê dados cadastrais e atribuição, sem acesso aos relatos clínicos.

## Preparar uma aula

O profissional entra em Equipe, abre um participante atribuído e “Preparar aulas e limites individuais”. Define módulo, metas de acompanhamento, limites autorais e etapas de preparação, principal, proteção e eventual desafio. Para cada etapa: nome, objetivo, versão, alternativa, orientação, vídeo local e tempo. Não há necessidade de editar JSON. Conteúdo e limites exigem decisão individual do responsável.

A equipe registra revisão com motivo e orientação, para ativar o programa. Nenhuma compra, check-in ou cadastro libera exercício por si só. Desafio requer autorização individual de uso único. Trocar o profissional responsável invalida a política anterior e devolve o participante à revisão.

## Acompanhamento

Equipe mostra eventos/pausas após a última revisão, mensagens após a última resposta profissional e registros do dia seguinte pendentes. Essa fila é operacional, não um classificador de urgência médica. Mensagens são armazenadas no painel local e não enviam notificações externas.

## Backup e restauração

```sh
python backup.py /caminho-seguro/backup.sqlite3
```

Usa o mecanismo online do SQLite e verifica integridade. Nunca substituir o banco ativo para fazer backup. O arquivo contém dados sensíveis e precisa de armazenamento protegido; o script não oferece criptografia em repouso.

Para ensaiar restauração, parar uma instância de teste, copiar o backup para um arquivo novo e configurar `APP_DB` para esse arquivo. Executar `PRAGMA integrity_check`, conferir contagens e fazer login na instância isolada. Não restaurar sobre produção sem plano operacional.

## Pendências externas antes de operação comercial

Hospedagem HTTPS e serviço de produção, recuperação/verificação de e-mail, MFA, provedor de pagamento, notificações, backups criptografados, revisão clínica/jurídica e conteúdo audiovisual definitivo. Esta entrega não provisiona recursos externos nem certifica segurança ou eficácia clínica. O servidor atual escuta apenas loopback e atende um piloto local. Não publicar esse servidor diretamente na internet.

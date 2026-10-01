# Protocolo Alívio Lombar

Aplicativo de acompanhamento de um programa de exercícios: frontend responsivo e backend Python/SQLite. Piloto local, com dados fictícios e revisão profissional. Resultados individuais variam.

## Funcionalidades

- Cadastro e autenticação por cookie HttpOnly, proteção de origem e CSRF.
- Avaliação inicial em três passos, com rascunho persistente.
- Jornada de quatro módulos e calibração de dor/sono/disposição.
- Aula individual em blocos, modo foco, temporizador e mídia local autorizada.
- Diário de dor, esforço e função; registros ausentes explicitados.
- Acompanhamento de 24h e suspensão por pausa/evento.
- Painel profissional, fila de revisões e mensagens, editor visual das aulas.
- Gestão de papéis e atribuição de participantes, com reautenticação.
- Backup consistente do SQLite e testes de integração.

## Executar

Python 3.13 ou superior, sem dependências externas.

```sh
python server.py
```

Abra http://127.0.0.1:8080. Para criar a conta administrativa:

```sh
python server.py --admin administrador@example.test
```

A senha é solicitada no terminal. Cadastre contas fictícias pela interface e use Gestão para definir profissionais e atribuições. Aulas e limites individuais são cadastrados pelo profissional no editor visual. Não existem senhas administrativas padrão.

Para ver uma jornada demonstrativa:

```sh
python seed_demo.py
```

O comando imprime uma senha aleatória local para uma conta fictícia. Os exemplos não prescrevem exercícios reais.

## Testes

```sh
python -m unittest discover -s tests -v
```

## Operação e limites

Consulte [Operação](docs/OPERACAO.md). O servidor escuta somente no computador local. Antes de produção, concluir hospedagem HTTPS, recuperação de conta, MFA profissional, integração de pagamentos/notificações, proteção de backups e revisão clínica/jurídica. SQLite, auditoria e controles implementados não constituem certificação de prontuário ou conformidade regulatória.

Sink Score utiliza uma política autoral individual; não há escore clínico validado. Módulos e desafios dependem de autorização profissional. Vídeos e exercícios definitivos não estão incluídos. O frontend usa Fraunces/Georgia e Inter/system-ui, com fallbacks locais.

Banco, backups, arquivos de mídia, anexos originais e planejamento comercial não fazem parte desta distribuição pública. Não inserir prontuários, credenciais, dados reais ou chaves no repositório.

## Lovable

O aplicativo atual usa JavaScript no frontend e Python no backend. Compatibilidade/importação deve ser verificada na conta escolhida; este repositório não representa uma conexão já ativa com Lovable. Uma migração de stack ou hospedagem depende dessa escolha.

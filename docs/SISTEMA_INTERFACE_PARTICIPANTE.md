# Sistema de interface — participante +alívio

Este documento descreve a interface implementada para o piloto. Sua finalidade é manter consistência entre telas e orientar a revisão com pessoas usuárias; não substitui teste de acessibilidade ou validação clínica.

## Princípios

- Uma tarefa principal por tela; informar o próximo passo e o estado do acompanhamento em linguagem direta.
- Apresentar pausas, riscos e pendências por texto, além de cor ou ícone. Não prometer alívio ou liberação automática.
- Usar controles HTML nativos, rótulos visíveis, foco aparente e áreas de toque de pelo menos 48 px nos componentes principais.
- Respeitar zoom, preferência de movimento reduzido e opção de fonte ampliada. Evitar prazos, progresso ou métricas que não existam nos dados.

## Fundamentos visuais

Os valores em `web/experience.css` são a fonte para a interface atual: fundo da página `#f4f6f1`, superfície `#ffffff`, texto `#182322`, texto secundário `#40564e`, verde principal `#245c46`, borda `#cdd8cf` e destaque verde claro `#b7ed43` com texto escuro. O tema escuro usa tokens alternativos. O destaque verde vivo não deve ser usado como texto pequeno em fundo branco.

Tipografia de sistema, tamanho base 16 px e altura de linha 1,6; títulos responsivos com `clamp`. O modo de fonte ampliada altera a base para 20 px. Espaçamento, cantos arredondados e largura máxima dos formulários seguem os componentes existentes em `style.css`, `brand.css` e `experience.css`; esses arquivos ainda não constituem uma biblioteca independente.

## Componentes e estados

- **Botão principal:** ação prioritária, rótulo com verbo e contraste suficiente; secundário para ações alternativas; perigo apenas para ações de interrupção.
- **Formulários:** pergunta ou rótulo visível associado ao controle; campos obrigatórios são verificados antes do envio. Dor e esforço usam opções individuais de 0 a 10 com descrição dos extremos.
- **Cartão de próximo passo:** estado real do usuário, ação relevante e identificação da equipe quando atribuída. Sem equipe, a pendência fica explícita.
- **Avisos:** mensagens de confirmação ou erro usam região de status; sinais neurológicos relatados mostram alerta de avaliação imediata. Mensagens internas não são canal de urgência.
- **Histórico:** filtros com estado selecionado anunciado, registros com data e gráfico com descrição textual de cada valor; resposta ausente não é zero.
- **Sessão guiada:** instrução textual, navegação entre etapas, pausa, possibilidade de sair e botão de ajuda. O conteúdo deve ser cadastrado por profissional; vídeos definitivos permanecem pendentes.
- **Estados vazios:** explicar o que ainda não existe e, quando possível, indicar o próximo passo. Uma sessão suspensa não oferece botão de retomada.

## Mapa do participante

Entrada → cadastro e consentimento do piloto → avaliação em três etapas → revisão profissional → início e protocolo → check-in → aula → resposta pós-sessão → acompanhamento de 24 horas. Em qualquer fase, ajuda e pausa ficam acessíveis. O retorno da equipe e histórico são acessíveis a partir do início.

## Verificação antes do uso real

Validar contraste nos dois temas, reflow em telas pequenas e zoom de 200%, navegação só por teclado, leitores de tela reais, compreensão com pessoas da faixa etária atendida, linguagem de segurança e conteúdo clínico. Definir recuperação de conta, suporte, privacidade e infraestrutura antes de usar dados reais. As regras numéricas do piloto são operacionais e precisam de revisão clínica; as quatro etapas históricas existentes ainda não representam a progressão solicitada de três níveis.

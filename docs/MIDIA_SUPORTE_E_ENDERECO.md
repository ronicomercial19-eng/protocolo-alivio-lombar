# Mídia, suporte e endereço de revisão

Estado em 07/10/2026. Os nove vídeos ainda não foram gravados. O quadro de nove aulas na interface médica é uma reserva de produção, não um currículo aprovado nem uma liberação de exercício.

## Depois deste piloto: preparar cada aula

Usar a [matriz das nove sessões](SESSOES_01_A_09.md) para escrever roteiro, objetivo, dose, demonstração, alternativa, condição de pausa e revisão. Registrar versão, data e responsáveis por cada aprovação. Não marcar como aprovada uma aula sem o conteúdo correspondente.

O editor de orientação individual já aceita um caminho de vídeo por etapa. O arquivo precisa ser colocado pela operação em `media/` no servidor e o campo deve apontar para `/media/nome-do-arquivo.mp4` ou `.webm`. O app ainda não oferece upload de vídeo. A pasta `media/` é ignorada pelo Git e não entra na imagem Docker atual; na hospedagem, será necessário montar armazenamento persistente nesse caminho. Antes de liberar, conferir áudio, imagem, legibilidade, alternativa textual, reprodução em celular e conexão lenta; manter o arquivo e sua versão aprovados juntos.

## Suporte

A mensagem no aplicativo é interna e não envia alerta externo. Ainda não há telefone, WhatsApp, e-mail, horário de atendimento, responsável nem prazo de resposta definidos. A interface do paciente informa essa limitação. Antes de dados reais, publicar um canal operado pela equipe, cobertura e procedimento de escalonamento. Em emergência no Brasil, o [SAMU atende pelo 192](https://www.gov.br/saude/pt-br/composicao/saes/samu-192); o app não substitui esse serviço.

## Endereço final

Em 07/10/2026, `https://alivia-lombar-amigo.lovable.app/` e `/avaliacao-medica` responderam HTTP 200. O conteúdo publicado é o projeto Lovable, separado da implementação deste repositório Git; a nova interface Git e o quadro das nove aulas não aparecem nesse endereço. Portanto, a disponibilidade da URL **não verifica** a jornada Git. Depois de escolher e implantar o destino deste repositório, executar nele o fluxo com contas fictícias dos quatro papéis, em celular, e conferir persistência após reinício.

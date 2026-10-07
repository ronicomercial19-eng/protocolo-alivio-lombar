# Plano de entrega — Protocolo Alívio Lombar

Estado em 06/10/2026. Cada caixa só deve ser marcada após verificação no ambiente em que o Dr. Augusto e os participantes acessarão o produto. Os limites de dor, sono, esforço e progressão são regras operacionais individuais; não constituem escore clinicamente validado.

## Fase 1 — Uma jornada funcional e persistente

- [x] Servidor Node encaminha API e mídia ao serviço Python/SQLite.
- [x] Cadastro, triagem, fila profissional e persistência após reinício passam no teste integrado.
- [x] Retirar da interface o login Google que não tinha verificação de token no servidor.
- [x] Registrar acompanhamento pulado como dado ausente e devolver o caso à revisão profissional.
- [ ] Testar a jornada completa no navegador móvel, com contas fictícias de paciente, profissional e administrador.
- [ ] Validar Docker e configuração do host onde o piloto será executado.

## Fase 2 — Decisão clínica auditável

- [ ] Pactuar com o Dr. Augusto os critérios de entrada, exclusão, pausa, encaminhamento e retorno.
- [x] Estruturar perguntas de segurança e exigir motivo registrado para ativação; preocupação neurológica relatada pausa o programa.
- [x] Separar permissões de médico e educação física; só o médico atribuído libera aulas e política individual.
- [x] Exibir histórico de decisões e pendências no caso profissional.
- [ ] Fechar com o médico a redação final da triagem e das regras de encaminhamento.
- [ ] Versionar formalmente as mudanças de limites individuais para comparação entre versões.
- [ ] Revisar com o médico o texto de urgência e o canal real de contato.

## Fase 3 — Experiência de avaliação do Dr. Augusto

- [x] Criar uma visão guiada no app: público, fluxo, segurança, revisão e limites da evidência.
- [x] Apresentar um caso fictício explicativo do fluxo, sem tratá-lo como resultado real.
- [ ] Ligar cada alegação científica à referência auditada, indicando o que o estudo sustenta e o que permanece autoral.
- [x] Registrar no app o parecer do médico por item: aprovado, ajustar ou pendente.

## Fase 4 — Conteúdo e piloto assistido

- [ ] Fechar com a equipe a sequência inicial de nove sessões, dose, alternativas e condições de progressão.
- [x] Criar matriz de produção para nove sessões, toda marcada como pendente de conteúdo e aprovação.
- [ ] Aprovar roteiros, gravar e carregar vídeos, verificar acesso em celular e conexão lenta.
- [ ] Executar o piloto com uma pessoa indicada pelo médico, após autorização e infraestrutura adequada.
- [ ] Revisar a experiência e a resposta após as duas primeiras sessões antes de ampliar convites.

## Fase 5 — Operação para centenas de participantes

- [ ] Definir capacidade diária de triagem e revisão; fila com responsável, prazo e escalonamento.
- [x] Mostrar métricas operacionais reais e simular o tempo da primeira revisão para cenários como 697 solicitações.
- [x] Permitir lotes de convites únicos quando o acesso por convite estiver ativado no servidor.
- [ ] Preparar consentimento e privacidade para dados reais, recuperação de conta, suporte e backups protegidos.
- [ ] Medir convite → cadastro → triagem → liberação → sessão → acompanhamento, sem chamar adesão de eficácia.
- [ ] Testar carga, disponibilidade, restauração de backup e alertas antes de abrir a oferta em escala.
- [ ] Ampliar em lotes, acompanhando abandonos, eventos, tempo de resposta e capacidade da equipe.

## Critério para apresentar um link como piloto funcional

O link deve permitir que uma conta fictícia percorra cadastro, triagem, atribuição, revisão, calibração, aula, registro de resposta e retorno de 24 horas; uma segunda conta profissional deve visualizar e decidir sobre o caso; o histórico deve permanecer após reinício. O teste deve ocorrer no endereço final, não apenas no computador de desenvolvimento.

## UI por persona — implementação no Git

- [x] Médico: guia visual com escopo, jornada, matriz de segurança, responsabilidades, limites da evidência e parecer persistente por item.
- [x] Entrada pública do app: apresentação das quatro responsabilidades, caminho do piloto e limites de uso antes do cadastro.
- [x] Médico: fila de casos atribuídos com pesquisa local, eventos e mensagens destacados.
- [x] Paciente: cadastro, triagem, aulas individualizadas, diário, registro imediato e de 24 horas, pausa, ajuda e indicação visual da etapa atual.
- [x] Educação física: casos atribuídos, plano vigente, registros e observações para o médico, com limite de atuação explícito.
- [x] Gestão: atribuição de responsáveis, papéis, métricas operacionais e simulação de capacidade.
- [ ] Validar em celular no endereço final com os quatro papéis e casos fictícios.
- [ ] Concluir e aprovar vídeos, dose, alternativas, critérios clínicos e canal real de suporte antes de pacientes reais.
- [ ] Auditar referências completas e vincular cada alegação do produto à evidência apropriada.

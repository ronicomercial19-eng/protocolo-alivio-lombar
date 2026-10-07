// Interface de revisão do produto. As decisões clínicas continuam nos fluxos existentes.
function landingHome(){
  return `<div class="review-landing"><section class="review-hero"><div><span class="eyebrow">Protocolo Alívio Lombar · piloto em preparação</span><h1>Uma jornada clara para cuidar da lombar, passo a passo.</h1><p>O participante relata seu momento, o médico decide sobre a orientação individual e a equipe acompanha a resposta. O conteúdo e os critérios finais ainda passam por revisão profissional.</p><div class="review-tags"><span>Triagem</span><span>Decisão médica</span><span>Sessões orientadas</span><span>Resposta em 24h</span></div><div class="review-landing-actions">${btn('Criar conta de teste','signup')}${btn('Entrar na minha área','login','secondary')}</div></div><aside class="review-warning"><strong>Antes de usar</strong><p>Este ambiente é um piloto técnico. Use dados fictícios. Uma conta criada não equivale a avaliação, prescrição ou autorização para fazer exercícios.</p><p>Oferta proposta: R$ 697 · contratação indisponível.</p></aside></section><section class="review-section"><div class="review-heading"><span class="eyebrow">Como funciona</span><h2>Uma experiência, quatro responsabilidades.</h2></div><div class="review-personas">${[['Paciente','Relata sintomas, recebe orientação liberada e registra a resposta.'],['Médico','Analisa critérios, decide e documenta a indicação individual.'],['Educação física','Observa a execução e propõe adaptações ao médico.'],['Gestão','Organiza convites, responsáveis e a capacidade de atendimento.']].map(([title,detail],i)=>`<article><span>0${i+1}</span><h3>${title}</h3><p>${detail}</p></article>`).join('')}</div></section><section class="review-note"><strong>Limite da proposta:</strong> referências científicas podem orientar componentes do cuidado. A sequência, os parâmetros e o produto completo não têm eficácia ou segurança clínica demonstrada nesta versão.</section></div>`;
}
function medicalGuide(){
  const latest=new Map();
  for(const item of evaluations)if(!latest.has(item.item))latest.set(item.item,item);
  const sections=[
    ['escopo','Escopo'],['jornada','Jornada'],['seguranca','Segurança'],
    ['personas','Personas'],['evidencias','Evidências'],['parecer','Parecer']
  ];
  const steps=[
    ['01','Convite','Acesso e identidade'],
    ['02','Triagem','Relato e sinais de alerta'],
    ['03','Revisão','Decisão médica justificada'],
    ['04','Sessão','Orientação individual'],
    ['05','Registro','Resposta imediata e em 24h'],
    ['06','Retorno','Nova revisão quando indicada']
  ];
  const personas=[
    ['Médico','Avalia escopo, critérios e conteúdo. Revisa o caso atribuído e registra uma decisão individual.'],
    ['Paciente','Preenche a triagem, acessa apenas aulas liberadas e relata sua resposta e eventos.'],
    ['Educação física','Consulta pessoas atribuídas, registra observações e sugere adaptações. Não libera clinicamente.'],
    ['Gestão','Atribui responsáveis e acompanha fila, contas e métricas operacionais; sem acesso administrativo aos relatos clínicos.']
  ];
  const safety=[
    ['Entrada','Adultos com dor lombar subaguda ou crônica inespecífica, após avaliação e prescrição profissional.','Público proposto; elegibilidade individual depende do médico.'],
    ['Triagem','Relato de sintomas, objetivos e preocupações; ausência de marcação não exclui doença.','Implementada, redação final pendente de revisão clínica.'],
    ['Pausa','Evento novo e resposta ausente suspendem a continuidade automática.','Regra operacional implementada; conduta clínica precisa ser pactuada.'],
    ['Encaminhamento','O médico registra decisão e motivo; o app não presta atendimento de urgência.','Canal externo e prazo de resposta ainda precisam ser definidos.'],
    ['Progressão','Política individual e limites editáveis; não há ponto de corte validado do produto.','Dose e nove sessões aguardam aprovação.']
  ];
  return `<div class="review-page">
    <section class="review-hero" id="escopo"><div><span class="eyebrow">Dossiê de avaliação · produto em revisão</span><h1>Dr., veja a jornada inteira antes de decidir.</h1><p>Uma visão do que a interface executa, de onde há decisão profissional e do que ainda precisa ser aprovado para um piloto com pessoas reais.</p><div class="review-tags"><span>Segurança</span><span>Critérios de entrada</span><span>Fluxo de dados</span><span>Experiência do paciente</span></div></div><aside class="review-warning"><strong>Estado atual</strong><p>O software registra uma jornada e decisões. Ele não comprova segurança, eficácia ou validação clínica deste infoproduto. Conteúdo e parâmetros ainda exigem revisão.</p></aside></section>
    <nav class="review-nav" aria-label="Seções da avaliação">${sections.map(([id,label])=>`<a href="#${id}">${label}</a>`).join('')}</nav>
    <section class="review-section" id="jornada"><div class="review-heading"><span class="eyebrow">01 · Percurso</span><h2>Do convite ao retorno</h2><p>Cada etapa separa o que a pessoa relata do que um profissional decide.</p></div><ol class="review-timeline">${steps.map(([n,title,detail])=>`<li><b>${n}</b><strong>${title}</strong><small>${detail}</small></li>`).join('')}</ol><div class="review-note"><strong>Caso explicativo, fictício:</strong> uma pessoa relata lombalgia há mais de três meses; o médico analisa a triagem, define a orientação individual, a pessoa registra a resposta à sessão e em 24 horas. Isso demonstra o fluxo, não um resultado clínico.</div></section>
    <section class="review-section" id="seguranca"><div class="review-heading"><span class="eyebrow">02 · Parâmetros</span><h2>O que acontece diante de cada risco</h2><p>Estas regras do sistema não substituem avaliação individual.</p></div><div class="review-matrix">${safety.map(([title,behavior,limit])=>`<article><h3>${title}</h3><p>${behavior}</p><small>${limit}</small></article>`).join('')}</div><div class="review-alert"><strong>Antes do piloto real:</strong> fechar critérios de exclusão, urgência, pausa, retomada e canal de contato; aprovar roteiros e doses das nove sessões.</div></section>
    <section class="review-section" id="personas"><div class="review-heading"><span class="eyebrow">03 · Responsabilidades</span><h2>Quatro visões, decisões diferentes</h2></div><div class="review-personas">${personas.map(([title,detail],i)=>`<article><span>0${i+1}</span><h3>${title}</h3><p>${detail}</p></article>`).join('')}</div><p class="muted">Os relatos clínicos ficam no servidor do aplicativo; o administrador vê métricas operacionais. O ambiente precisa de configuração, privacidade e suporte antes de receber dados reais.</p></section>
    <section class="review-section" id="evidencias"><div class="review-heading"><span class="eyebrow">04 · Literatura</span><h2>Evidência dos componentes não valida o pacote.</h2></div><div class="review-evidence"><div><h3>O que a literatura pode orientar</h3><p>Exercício, avaliação e medidas de dor têm literatura própria. Cada alegação deve ser confrontada com o artigo completo e com a população estudada.</p></div><div><h3>O que ainda é autoral</h3><p>Sequência de nove aulas, limites numéricos, progressão, interface e desfechos deste produto. Parecer profissional não transforma esses elementos em intervenção validada.</p></div></div><p class="muted">Fontes de escopo: <a href="https://www.nice.org.uk/guidance/ng59/chapter/recommendations" target="_blank" rel="noopener noreferrer">NICE NG59</a> · <a href="https://www.acponline.org/sites/default/files/acp-policy-library/guidelines/noninvasive_treatments_for_chronic_low_back_pain_2017.pdf" target="_blank" rel="noopener noreferrer">ACP 2017</a>. Auditoria artigo por artigo ainda pendente.</p></section>
    <section class="review-section" id="parecer"><div class="review-heading"><span class="eyebrow">05 · Sua análise</span><h2>Parecer por item</h2><p>Marque o estado e registre o ajuste necessário. “Aprovado” se refere somente ao item analisado, sem validar o produto inteiro.</p></div><div class="review-checklist">${evaluationItems.map(([id,title,description],i)=>{const e=latest.get(id);return `<details class="card patient-case"><summary><span class="review-num">0${i+1}</span><strong>${esc(title)}</strong><span class="review-status">${e?esc({approved:'Aprovado neste item',adjust:'Ajustar',pending:'Pendente'}[e.status]):'Sem parecer'}</span></summary><p>${esc(description)}</p>${e?`<p><strong>Último parecer:</strong> ${esc(e.notes)} <small>${date(e.created)}</small></p>`:''}<form id="evaluation-${id}" data-item="${id}"><label>Classificação<select name="status" required><option value="pending">Pendente</option><option value="adjust">Ajustar</option><option value="approved">Aprovado neste item</option></select></label><label>Motivo e condição para aprovação<textarea name="notes" required minlength="5" maxlength="2000"></textarea></label><button class="full">Registrar parecer</button></form></details>`}).join('')}</div></section>
  </div>`;
}

function bindReviewUI(){
  const main=app.querySelector('main');
  if(!main)return;
  if(page==='dashboard'&&me?.role==='participant'){
    const current={triagem_pendente:0,em_revisao:1,ativo:2,suspenso:1,encaminhado:1}[me.state]??0;
    const strip=document.createElement('section');
    strip.className='patient-journey';
    strip.setAttribute('aria-label','Etapas da jornada');
    strip.innerHTML='<strong>Sua jornada</strong><ol>'+['Sua avaliação','Revisão profissional','Aulas liberadas','Registros e retorno'].map((label,i)=>`<li class="${i<=current?'reached':''}" ${i===current?'aria-current="step"':''}><span>${i+1}</span>${label}</li>`).join('')+'</ol><p>O estado da conta mostra etapas do sistema. Somente uma decisão individual registrada pela equipe autoriza aulas.</p>';
    main.insertBefore(strip,main.firstChild);
  }
  if(page==='team'){
    const cases=[...main.querySelectorAll('.patient-case')];
    const bar=document.createElement('section');
    bar.className='review-filter card';
    bar.innerHTML='<div><strong>Fila atribuída a você</strong><p class="muted">Priorize eventos e mensagens. A pesquisa filtra apenas os casos carregados nesta página.</p></div><label>Buscar participante<input id="case-search" type="search" placeholder="Nome ou estado"></label><p id="case-count" role="status"></p>';
    const cards=main.querySelector('.cards');
    cards?.insertAdjacentElement('afterend',bar);
    const input=bar.querySelector('input'),count=bar.querySelector('#case-count');
    const filter=()=>{const q=input.value.trim().toLocaleLowerCase('pt-BR');let n=0;for(const item of cases){const visible=(item.querySelector('summary')?.textContent||'').toLocaleLowerCase('pt-BR').includes(q);item.hidden=!visible;if(visible)n++}count.textContent=`${n} de ${cases.length} casos exibidos`};
    input.addEventListener('input',filter);filter();
  }
  if(page==='educator'||page==='management'){
    const intro=document.createElement('aside');
    intro.className='review-role-note';
    intro.innerHTML=page==='educator'
      ?'<strong>Limite da sua atuação</strong><p>Registre a execução e proponha adaptações. A decisão de liberar, pausar ou retomar aulas fica com o médico responsável.</p>'
      :'<strong>Visão operacional</strong><p>As contagens ajudam a dimensionar a fila; não representam adesão clínica, melhora ou previsão de vendas.</p>';
    main.insertBefore(intro,main.firstChild);
  }
}

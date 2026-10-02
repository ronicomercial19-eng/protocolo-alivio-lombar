import { googleSignIn, logout, getAuthToken, initAuth } from '/auth.js';
async function openWorkspace(){if(me.role==='clinician'){patients=await api('patients');page='team'}else if(me.role==='admin'){adminAccounts=await api('admin/accounts');page='management'}else page='dashboard'}
let me=null, page='home', register=false, patients=[], timer=null, seconds=0;
const app=document.querySelector('#app');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=t=>new Date(t*1000).toLocaleString('pt-BR');
const states={triagem_pendente:'Triagem pendente',em_revisao:'Em revisão profissional',ativo:'Programa ativo',suspenso:'Programa suspenso',encaminhado:'Encaminhamento recomendado'};
function notice(s){const n=document.querySelector('#notice');n.textContent=s;n.style.display='block';setTimeout(()=>n.style.display='none',6000)}
async function api(path,body){const r=await fetch('/api/'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','X-CSRF-Token':me?.csrf||''}:{},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error);return data}
async function refresh(){me=await api('me');render()}
function btn(label,action,cls=''){return `<button type="button" class="${cls}" data-action="${action}">${label}</button>`}
function bindNotifications() {
  const btn = document.querySelector('#setup-notifications');
  if (btn) btn.onclick = async () => {
    if (!('Notification' in window)) return alert('Notificações não suportadas neste navegador.');
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      notice('Lembretes diários ativados!');
      // Simplificação: agendar notificação simulada para daqui a 1 minuto
      setTimeout(() => {
        new Notification('Protocolo Alívio Lombar', { body: 'Hora de realizar sua prática diária!' });
      }, 60000);
    } else {
      alert('Permissão de notificação negada.');
    }
  };
}

function render(){clearInterval(timer);timer=null;
app.innerHTML=`<a class="skip-link" href="#main-content">Pular para o conteúdo</a><div class="banner">Piloto local • conteúdo e fluxos sujeitos à revisão clínica • use dados fictícios</div><header><div class="logo">alívio<b>•</b></div><nav>${me?(me.role==='admin'?['management']:me.role==='clinician'?['team']:['dashboard','protocol','diary','help']).map(p=>btn({dashboard:'Meu cuidado',protocol:'Protocolo / Aulas',diary:'Diário',help:'Ajuda',team:'Equipe',management:'Gestão'}[p],p,page===p?'active':'')).join('')+btn('Sair','logout'):btn('Entrar','login','secondary')}</nav></header><main class="wrap" id="main-content" tabindex="-1">${!me?(page==='login'?auth():home()):({dashboard:careDashboard,triage:careTriage,diary:careHistory,help:careHelp,focus,team:staffTeam,management,protocol,lesson,lessonFocus,checkout:careCheckout,celebrate,between,review,pauseConfirm}[page]||dashboard)()}</main><footer>Protocolo Alívio Lombar · por Nine Living · Programa de exercícios com orientação profissional. Resultados individuais variam. Em caso de sintomas novos ou preocupantes, procure avaliação.</footer>`;
app.querySelectorAll('nav [data-action]').forEach(b=>{if(b.dataset.action===page)b.setAttribute('aria-current','page')});
app.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action));
app.querySelectorAll('form').forEach(f=>f.onsubmit=submit);
if(page==='login') bindAuth();
if(page==='dashboard') bindNotifications();
if(typeof bindProtocol==='function')bindProtocol();
if(typeof bindCare==='function')bindCare();bindStaff();
if(page==='focus'&&me){timer=setInterval(()=>{seconds++;const el=document.querySelector('#timer');if(el)el.textContent=`${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`},1000)}
}
function home(){return `<section class="hero"><div><span class="eyebrow">Cuidado que respeita seu ritmo</span><h1>Exercício guiado para sua lombar,<br>no seu ritmo.</h1><p>Programa para adultos com lombalgia crônica inespecífica, com orientação profissional, registro de resposta e progressão individualizada.</p>${btn('Começar meu acompanhamento →','signup')}<p class="muted">Oferta proposta: R$ 697 · contratação ainda indisponível</p></div><div class="hero-art"><div class="hero-brand">${logoMarkup}</div><p>Um passo de cada vez.</p></div></section><div class="cards">${[['01','Entender seu momento','Triagem e revisão profissional antes das sessões.'],['02','Mover com orientação','Uma orientação individual, com espaço para pausa e adaptação.'],['03','Acompanhar sua resposta','Seu diário ajuda a equipe a revisar o próximo passo.']].map(x=>`<article class="card"><span class="eyebrow">${x[0]}</span><h2>${x[1]}</h2><p>${x[2]}</p></article>`).join('')}</div>`}
function auth(){return `<div class="card form"><span class="eyebrow">Seu espaço de cuidado</span><h1>${register?'Vamos começar':'Bem-vindo de volta'}</h1>
<button class="gsi-material-button" id="google-signin">
  <div class="gsi-material-button-state"></div>
  <div class="gsi-material-button-content-wrapper">
    <div class="gsi-material-button-icon">
      <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" style="display: block;">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
        <path fill="none" d="M0 0h48v48H0z"></path>
      </svg>
    </div>
    <span class="gsi-material-button-contents">Sign in with Google</span>
  </div>
</button>
<p>ou use seu e-mail:</p>
<form id="auth">${register?'<label for="name">Como podemos chamar você?</label><input id="name" name="name" required minlength="2" maxlength="100" autocomplete="name">':''}<label for="email">E-mail</label><input id="email" name="email" type="email" required autocomplete="email"><label for="password">Senha</label><input id="password" name="password" type="password" required minlength="12" maxlength="256" autocomplete="${register?'new-password':'current-password'}">${register?'<label class="check"><input name="consent" type="checkbox" required>Concordo com o armazenamento local dos dados deste piloto para acompanhamento. Usarei apenas dados fictícios. Versão piloto 1.</label>':''}<button class="full">${register?'Criar minha conta':'Entrar'}</button></form><p>${btn(register?'Já tenho conta':'Criar uma conta','toggle','secondary')}</p></div>`}
function dashboard(){if (!me) return '';
const sessions=me.sessions||[];
const last=sessions[0];
const totalSessions = 12; // Exemplo de meta
const completed = sessions.filter(s=>s.completed).length;
const progress = Math.min((completed / totalSessions) * 100, 100);

return `<span class="eyebrow">Meu cuidado</span><div class="row"><h1>Olá, ${esc(me.name.split(' ')[0])}.</h1><span class="pill">${esc(states[me.state]||me.state)}</span></div>
<div class="card">
  <h2>Seu progresso</h2>
  <div style="background:#e0e6dd;height:20px;border-radius:10px;margin:10px 0;">
    <div style="background:#234f43;height:100%;width:${progress}%;border-radius:10px;"></div>
  </div>
  <p>${completed} de ${totalSessions} sessões concluídas</p>
  <button id="setup-notifications" class="secondary">Configurar lembrete diário</button>
</div>
<p>Seu próximo passo, no seu ritmo.</p><div class="cards"><div class="card"><span class="eyebrow">Sessões registradas</span><div class="metric">${completed}</div><span class="muted">Adesão, sem estimar eficácia</span></div><div class="card"><span class="eyebrow">Registro diário</span><div class="metric">${(me.records||[]).filter(r=>['session','followup'].includes(r.kind)).length}</div><span class="muted">Seu acompanhamento ao longo do tempo</span></div><div class="card"><span class="eyebrow">Acompanhamento</span><div class="metric">${last?.completed&&!last.followup?'Pendente':'Em dia'}</div><span class="muted">Revisão profissional de progressão</span></div></div><div class="grid"><article class="card highlight"><span class="eyebrow">Seu próximo passo</span><h2>${me.state==='ativo'?'Sua orientação individual':'Vamos cuidar da base'}</h2><p>${me.plan?esc(me.plan.content):'Preencha sua triagem. A equipe responsável precisa revisar suas respostas antes de orientar sessões.'}</p>${me.state==='ativo'?btn('Abrir minhas aulas','protocol','secondary'):btn('Ver triagem','triage','secondary')}</article><article class="card"><h2>Depois da sessão</h2><p>Registre sua resposta após 24 horas. Esse intervalo é uma regra operacional do programa.</p>${last?.completed&&!last.followup?`<p class="muted">Disponível em ${date(last.completed+86400)}</p>${btn('Abrir acompanhamento','diary','secondary')}`:'<p class="muted">Os registros aparecerão aqui.</p>'}</article></div>`}
function triage(){return `<div class="card form"><span class="eyebrow">Conhecer seu momento</span><h1>Triagem inicial</h1><p>Estas respostas serão revisadas por um profissional. Não constituem diagnóstico ou liberação automática.</p><form id="triage"><label for="duration">Há quanto tempo você sente desconforto?</label><select id="duration" name="duration" required><option value="">Selecione</option><option>Menos de 3 meses</option><option>3 meses ou mais</option><option>Não sei informar</option></select><label for="newSymptoms">Há sintomas novos ou mudança preocupante?</label><select id="newSymptoms" name="newSymptoms" required><option value="">Selecione</option><option value="sim">Sim</option><option value="nao">Não</option><option value="nao_sei">Não sei</option></select><label for="goal">Qual atividade você gostaria de retomar?</label><textarea id="goal" name="goal" maxlength="1000"></textarea><button class="full">Enviar para revisão</button></form></div>`}
function record(r){let p;try{p=JSON.parse(r.payload)}catch{p={}}return `<div class="record"><div class="row"><strong>${esc({triage:'Triagem',consent:'Consentimento',session:'Após a sessão',followup:'Acompanhamento de 24h',review:'Revisão profissional',event:'Relato de evento'}[r.kind]||r.kind)}</strong><small>${date(r.created)}</small></div><p>${p.pain!==undefined?'Dor no momento: '+esc(p.pain)+'/10. ':''}${esc(p.notes||p.goal||p.purpose||'Registro recebido.')}</p></div>`}
function diary(){const last=me.sessions[0];return `<span class="eyebrow">Sua trajetória</span><h1>Diário de cuidado</h1><div class="grid"><div class="card"><h2>Seus registros</h2>${me.records.length?me.records.map(record).join(''):'<p>Seu diário começa com a triagem.</p>'}</div><div class="card"><h2>Acompanhamento de 24h</h2>${last?.completed&&!last.followup?`<p>Disponível em ${date(last.completed+86400)}.</p>${Date.now()/1000>=last.completed+86400?responseForm('followup',last.id):'<p class="muted">Aguarde o horário. Você pode relatar um evento a qualquer momento em Ajuda.</p>'}`:'<p>Nenhum acompanhamento pendente.</p>'}</div></div>`}
function responseForm(id,sid){return `<form id="${id}" data-id="${sid}"><label for="pain">Dor agora (0 = nenhuma, 10 = máxima)</label><input name="pain" id="pain" type="number" min="0" max="10" step="1" required><label for="notes">Como você se sente?</label><textarea name="notes" id="notes" maxlength="2000"></textarea><button class="full">Salvar registro</button></form>`}
function focus(){const s=me.sessions[0];if(!s||s.completed)return dashboard();return `<div class="focus"><div class="row"><span class="eyebrow">Modo foco</span>${btn('Pausar e voltar','dashboard','secondary')}</div><h1>Um movimento de cada vez.</h1><p>Siga a orientação individual abaixo. O temporizador é apenas uma referência de tempo.</p><div class="focus-content">${esc(s.plan)}</div><div class="timer" id="timer">00:00</div><div class="card"><h2>Concluir e registrar</h2>${responseForm('complete',s.id)}</div><p>${btn('Interromper e relatar um evento','help','secondary')}</p></div>`}
function help(){return `<div class="card form"><span class="eyebrow">Você pode pausar</span><h1>Ajuda e segurança</h1><p>Se houver sintomas novos ou preocupantes, interrompa a atividade e procure avaliação. Este piloto não oferece atendimento de urgência ou mensagens em tempo real.</p><p>Em uma emergência no Brasil, ligue 192. Não aguarde resposta deste aplicativo.</p><h2>Relatar um evento</h2><p>O relato suspende novas sessões e fica disponível à equipe atribuída. O piloto não envia notificações externas.</p><form id="event"><label for="notes">O que aconteceu?</label><textarea id="notes" name="notes" required minlength="3" maxlength="2000"></textarea><button class="full danger">Registrar e suspender sessões</button></form></div>`}
function team(){return `<span class="eyebrow">Área profissional</span><h1>Revisões e acompanhamento</h1><p>Somente participantes atribuídos à sua conta.</p>${patients.length?patients.map(p=>`<div class="card"><div class="row"><h2>${esc(p.name)}</h2><span class="pill">${esc(states[p.state])}</span></div>${p.records.map(careRecord).join('')}<form id="reply-${p.id}" data-id="${p.id}"><label>Responder ao participante<textarea name="notes" required minlength="3" maxlength="2000"></textarea></label><button class="full">Enviar retorno</button></form>${policyEditor(p)}<form id="review-${p.id}" data-id="${p.id}"><label>Decisão<select name="state"><option value="suspenso">Manter suspenso</option><option value="ativo">Ativar com orientação individual</option><option value="encaminhado">Encaminhar para avaliação</option></select></label><label>Justificativa<textarea name="notes" required minlength="5" maxlength="2000"></textarea></label><label>Orientação individual e dose<textarea name="plan" maxlength="4000"></textarea></label><button class="full">Registrar decisão</button></form></div>`).join(''):'<div class="card"><p>Nenhum participante atribuído. A atribuição é feita pelo operador no servidor.</p></div>'}`}
async function action(a){try{if(await staffAction(a))return;if(await careAction(a))return;if(typeof protocolAction==='function'&&await protocolAction(a))return;if(a==='logout'){await api('logout',{});await logout();me=null;journey=null;patients=[];adminAccounts=[];policyDrafts={};assessmentDraft={};page='home'}else if(a==='signup'||a==='login'){register=a==='signup';page='login'}else if(a==='toggle'){register=!register}else if(a==='start'){if(!me.sessions[0]||me.sessions[0].completed){await api('session/start',{});me=await api('me')}seconds=0;page='focus'}else{page=a;if(a==='team')patients=await api('patients')}render()}catch(e){notice(e.message)}}

function bindAuth(){
  const btn = document.querySelector('#google-signin');
  if(btn) btn.onclick = async () => {
    try {
      const user = await googleSignIn();
      await api('login-google', { email: user.email, name: user.displayName });
      me=await api('me');
      await openWorkspace();
      render();
    } catch(e) { notice(e.message); }
  }
}

async function submit(e){e.preventDefault();const f=e.target;const b=e.submitter||f.querySelector('button:not([type=button])');if(b)b.disabled=true;try{const d=Object.fromEntries(new FormData(f));if(await staffSubmit(f,d))return;if(await careSubmit(f,d))return;if(typeof protocolSubmit==='function'&&await protocolSubmit(f,d)){return;}if(f.id==='auth'){if(register)d.consent=f.elements.consent.checked;await api(register?'register':'login',d);me=await api('me');await openWorkspace()}else if(f.id==='triage'){await api('triage',d);page='dashboard';notice('Triagem enviada. Aguarde revisão profissional.')}else if(['complete','followup'].includes(f.id)){d.id=Number(f.dataset.id);d.pain=Number(d.pain);await api('session/'+f.id,d);page='diary';notice('Registro salvo.')}else if(f.id==='event'){await api('event',d);page='dashboard';notice('Evento registrado. Sessões suspensas.')}else if(f.id.startsWith('review-')){d.id=Number(f.dataset.id);await api('review',d);patients=await api('patients');notice('Decisão registrada.')}await refresh()}catch(err){notice(err.message);if(b)b.disabled=false}}
api('me').then(async u=>{me=u;await openWorkspace();render()}).catch(()=>render());

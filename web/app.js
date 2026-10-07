async function openWorkspace(){if(['physician','clinician'].includes(me.role)){patients=await api('patients');evaluations=await api('evaluation');page='team'}else if(me.role==='educator'){educatorCases=await api('educator/patients');page='educator'}else if(me.role==='admin'){adminAccounts=await api('admin/accounts');adminMetrics=await api('admin/metrics');page='management'}else page='dashboard'}
let me=null, page='home', register=false, patients=[], timer=null, seconds=0;
const app=document.querySelector('#app');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=t=>new Date(t*1000).toLocaleString('pt-BR');
const states={triagem_pendente:'Triagem pendente',em_revisao:'Em revisão profissional',ativo:'Programa ativo',suspenso:'Programa suspenso',encaminhado:'Encaminhamento recomendado'};
function notice(s){const n=document.querySelector('#notice');n.textContent=s;n.style.display='block';setTimeout(()=>n.style.display='none',6000)}
async function api(path, body) {
  const headers = body ? { 'Content-Type': 'application/json', 'X-CSRF-Token': me?.csrf || '' } : {};
  
  const r = await fetch('/api/' + path, {
    method: body ? 'POST' : 'GET',
    headers,
    credentials: 'same-origin',
    body: body ? JSON.stringify(body) : undefined
  });
  
  const data = await r.json();
  if (!r.ok) throw Error(data.error);
  return data;
}
async function refresh(){me=await api('me');render()}
function btn(label,action,cls=''){return `<button type="button" class="${cls}" data-action="${action}">${label}</button>`}

function render(){clearInterval(timer);timer=null;
app.innerHTML=`<a class="skip-link" href="#main-content">Pular para o conteúdo</a><div class="banner">Piloto local • conteúdo e fluxos sujeitos à revisão clínica • use dados fictícios</div><header><div class="logo">alívio<b>•</b></div><nav>${me?(me.role==='admin'?['management']:['physician','clinician'].includes(me.role)?['team','evaluation']:me.role==='educator'?['educator']:['dashboard','protocol','diary','help']).map(p=>btn({dashboard:'Meu cuidado',protocol:'Protocolo / Aulas',diary:'Diário',help:'Ajuda',team:'Equipe médica',evaluation:'Avaliação do produto',educator:'Educação física',management:'Gestão'}[p],p,page===p?'active':'')).join('')+btn('Sair','logout'):btn('Entrar','login','secondary')}</nav></header><main class="wrap" id="main-content" tabindex="-1">${me?.role==='participant'?careSafetyBanner():''}${!me?(page==='login'?auth():landingHome()):({dashboard:careDashboard,triage:careTriage,diary:careHistory,help:careHelp,focus,team:staffTeam,evaluation:medicalGuide,educator:educatorWorkspace,management,protocol,lesson,lessonFocus,checkout:careCheckout,celebrate,between,review,pauseConfirm}[page]||dashboard)()}</main><footer>Protocolo Alívio Lombar · por Nine Living · Programa de exercícios com orientação profissional. Resultados individuais variam. Em caso de sintomas novos ou preocupantes, procure avaliação.</footer>`;
app.querySelectorAll('nav [data-action]').forEach(b=>{if(b.dataset.action===page)b.setAttribute('aria-current','page')});
app.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action));
app.querySelectorAll('form').forEach(f=>f.onsubmit=submit);
if(typeof bindProtocol==='function')bindProtocol();
if(typeof bindCare==='function')bindCare();bindStaff();bindMedicalReview();bindCapacityPlanner();bindRoleControls();bindReviewUI();
if(page==='focus'&&me){timer=setInterval(()=>{seconds++;const el=document.querySelector('#timer');if(el)el.textContent=`${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`},1000)}
}
function home(){return `<section class="hero"><div><span class="eyebrow">Cuidado que respeita seu ritmo</span><h1>Exercício guiado para sua lombar,<br>no seu ritmo.</h1><p>Programa para adultos com lombalgia crônica inespecífica, com orientação profissional, registro de resposta e progressão individualizada.</p>${btn('Começar meu acompanhamento →','signup')}<p class="muted">Oferta proposta: R$ 697 · contratação ainda indisponível</p></div><div class="hero-art"><div class="hero-brand">${logoMarkup}</div><p>Um passo de cada vez.</p></div></section><div class="cards">${[['01','Entender seu momento','Triagem e revisão profissional antes das sessões.'],['02','Mover com orientação','Uma orientação individual, com espaço para pausa e adaptação.'],['03','Acompanhar sua resposta','Seu diário ajuda a equipe a revisar o próximo passo.']].map(x=>`<article class="card"><span class="eyebrow">${x[0]}</span><h2>${x[1]}</h2><p>${x[2]}</p></article>`).join('')}</div>`}
function auth(){return `<div class="card form"><span class="eyebrow">Seu espaço de cuidado</span><h1>${register?'Vamos começar':'Bem-vindo de volta'}</h1>
<form id="auth">${register?'<label for="name">Como podemos chamar você?</label><input id="name" name="name" required minlength="2" maxlength="100" autocomplete="name">':''}<label for="email">E-mail</label><input id="email" name="email" type="email" required autocomplete="email"><label for="password">Senha</label><input id="password" name="password" type="password" required minlength="12" maxlength="256" autocomplete="${register?'new-password':'current-password'}">${register?'<label for="inviteCode">Código de convite, se fornecido pela equipe</label><input id="inviteCode" name="inviteCode" autocomplete="off" maxlength="100"><label class="check"><input name="consent" type="checkbox" required>Concordo com o armazenamento local dos dados deste piloto para acompanhamento. Usarei apenas dados fictícios. Versão piloto 1.</label>':''}<button class="full">${register?'Criar minha conta':'Entrar'}</button></form><p>${btn(register?'Já tenho conta':'Criar uma conta','toggle','secondary')}</p></div>`}
function dashboard(){return careDashboard()}
function focus(){return careDashboard()}
async function action(a){try{if(await medicalAction(a))return;if(await educatorAction(a))return;if(await staffAction(a))return;if(await careAction(a))return;if(typeof protocolAction==='function'&&await protocolAction(a))return;if(a==='logout'){await api('logout',{});me=null;journey=null;patients=[];adminAccounts=[];policyDrafts={};assessmentDraft={};page='home'}else if(a==='signup'||a==='login'){register=a==='signup';page='login'}else if(a==='toggle'){register=!register}else if(a==='start'){if(!me.sessions[0]||me.sessions[0].completed){await api('session/start',{});me=await api('me')}seconds=0;page='focus'}else{page=a;if(a==='team')patients=await api('patients')}render()}catch(e){notice(e.message)}}

async function submit(e){e.preventDefault();const f=e.target;const b=e.submitter||f.querySelector('button:not([type=button])');if(b)b.disabled=true;try{const d=Object.fromEntries(new FormData(f));if(await medicalSubmit(f,d))return;if(await educatorSubmit(f,d))return;if(await staffSubmit(f,d))return;if(await careSubmit(f,d))return;if(typeof protocolSubmit==='function'&&await protocolSubmit(f,d)){return;}if(f.id==='auth'){if(register)d.consent=f.elements.consent.checked;await api(register?'register':'login',d);me=await api('me');await openWorkspace()}else if(f.id==='triage'){await api('triage',d);page='dashboard';notice('Triagem enviada. Aguarde revisão profissional.')}else if(['complete','followup'].includes(f.id)){d.id=Number(f.dataset.id);d.pain=Number(d.pain);await api('session/'+f.id,d);page='diary';notice('Registro salvo.')}else if(f.id==='event'){await api('event',d);page='dashboard';notice('Evento registrado. Sessões suspensas.')}else if(f.id.startsWith('review-')){d.id=Number(f.dataset.id);d.reviewed=f.elements.reviewed.checked;d.urgentAssessed=f.elements.urgentAssessed?.checked||false;await api('review',d);patients=await api('patients');notice('Decisão registrada.')}await refresh()}catch(err){notice(err.message);if(b)b.disabled=false}}
api('me').then(async user => { me=user; await openWorkspace(); render(); }).catch(() => render());

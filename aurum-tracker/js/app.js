var SEED_CLIENTS=null,SEED_CONTRACT=null;
let clients=[],editingId=null,deletingId=null;

function uid(){return Date.now().toString(36)+Math.random().toString(36).slice(2)}
function getComp(c,p){const x=COMP[c];if(!x)return null;const y=x[p];if(!y)return null;return y[getContractLevel()]??null}
function getContractLevel(){return parseInt(localStorage.getItem('cye_contract')||SEED_CONTRACT||'90')}
function saveContractLevel(){localStorage.setItem('cye_contract',document.getElementById('contract-level').value)}
function loadClients(){const r=localStorage.getItem('cye_clients');if(r){try{return JSON.parse(r)}catch(e){}}if(SEED_CLIENTS){try{return JSON.parse(SEED_CLIENTS)}catch(e){}}return []}
function saveData(){
  localStorage.setItem('cye_clients',JSON.stringify(clients));
  const s=document.getElementById('save-status');
  s.innerHTML='<span class="save-dot"></span> Saved '+new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  setTimeout(()=>{s.innerHTML='<span class="save-dot"></span> Auto-saved'},3000);
}

function switchTab(id,el){
  document.querySelectorAll('.tab-page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  if(el)el.classList.add('active');
  const titles={clients:'Clients',goals:'My Goals',leads:'Lead Spend',carriers:'Carriers %'};
  document.getElementById('page-title').textContent=titles[id]||'';
  document.getElementById('add-btn').style.display=id==='clients'?'':'none';
  // only show sidebar search on clients tab
  document.getElementById('sidebar-search-wrap').style.display=id==='clients'?'':'none';
  if(id==='goals')renderGoals();
  if(id==='leads')renderLeads();
  if(id==='carriers'){document.getElementById('contract-level').value=getContractLevel();renderCarriers()}
}

function monthsElapsed(soldDate){
  if(!soldDate)return 0;
  const sold=new Date(soldDate+'T00:00:00');
  const now=new Date();
  return Math.floor((now-sold)/(1000*60*60*24*30.44));
}
function monthsRemaining(soldDate,totalMonths){
  if(!soldDate||!totalMonths)return null;
  const clear=new Date(soldDate+'T00:00:00');
  clear.setMonth(clear.getMonth()+parseInt(totalMonths));
  return Math.ceil((clear-new Date())/(1000*60*60*24*30.44));
}
function fmtDate(d){if(!d)return '—';return new Date(d+'T00:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}
function fmtPhone(p){if(!p)return '—';const d=p.replace(/\D/g,'');return d.length===10?'('+d.slice(0,3)+') '+d.slice(3,6)+'-'+d.slice(6):p}
function initials(f,l){return((f||'')[0]||'').toUpperCase()+((l||'')[0]||'').toUpperCase()||'??'}

function toggleExpand(id){
  const detail=document.getElementById('detail-'+id);
  const row=document.getElementById('row-'+id);
  const isOpen=detail.classList.contains('open');
  document.querySelectorAll('.client-detail').forEach(d=>d.classList.remove('open'));
  document.querySelectorAll('.client-row').forEach(r=>r.classList.remove('expanded'));
  if(!isOpen){detail.classList.add('open');row.classList.add('expanded')}
}

function renderStats(){
  const active=clients.filter(c=>(monthsRemaining(c.sold,c.months)||0)>0).length;
  const premium=clients.reduce((s,c)=>s+(parseFloat(c.premium)||0),0);
  const target=clients.reduce((s,c)=>s+(parseFloat(c.targetpremium)||0),0);
  const takehome=clients.reduce((s,c)=>s+(parseFloat(c.takehome)||0),0);
  document.getElementById('stats-row').innerHTML=
    '<div class="stat"><div class="stat-label">Total clients</div><div class="stat-val teal">'+clients.length+'</div></div>'+
    '<div class="stat"><div class="stat-label">Advancement active</div><div class="stat-val red">'+active+'</div></div>'+
    '<div class="stat"><div class="stat-label">Annual premium</div><div class="stat-val">$'+Math.round(premium).toLocaleString()+'</div></div>'+
    '<div class="stat"><div class="stat-label">Target premium</div><div class="stat-val gold">$'+Math.round(target).toLocaleString()+'</div></div>'+
    '<div class="stat"><div class="stat-label">Total take home</div><div class="stat-val green">$'+Math.round(takehome).toLocaleString()+'</div></div>';
}

function render(){
  renderStats();
  let search=document.getElementById('search').value.toLowerCase();
  const fs=document.getElementById('filter-status').value;
  const sort=document.getElementById('filter-sort').value;
  let list=clients.slice();
  if(search)list=list.filter(c=>(c.first+' '+c.last).toLowerCase().includes(search)||(c.email||'').toLowerCase().includes(search)||(c.carrierSel||'').toLowerCase().includes(search));
  if(fs==='active')list=list.filter(c=>(monthsRemaining(c.sold,c.months)||0)>0);
  if(fs==='clear')list=list.filter(c=>{const m=monthsRemaining(c.sold,c.months);return m!==null&&m<=0});
  if(sort==='date-desc')list.sort((a,b)=>new Date(b.sold||0)-new Date(a.sold||0));
  if(sort==='date-asc')list.sort((a,b)=>new Date(a.sold||0)-new Date(b.sold||0));
  if(sort==='name')list.sort((a,b)=>(a.first+a.last).localeCompare(b.first+b.last));
  if(sort==='takehome')list.sort((a,b)=>(parseFloat(b.takehome)||0)-(parseFloat(a.takehome)||0));

  const body=document.getElementById('client-list-body');
  const empty=document.getElementById('empty');
  if(!list.length){body.innerHTML='';empty.style.display='block';return}
  empty.style.display='none';

  body.innerHTML=list.map(c=>{
    const mr=monthsRemaining(c.sold,c.months);
    const total=parseInt(c.months)||1;
    const elapsed=monthsElapsed(c.sold);
    const paidMonths=Math.min(elapsed,total);
    const pct=Math.min(Math.round((paidMonths/total)*100),100);
    const isDone=mr!==null&&mr<=0;
    const carrier=c.carrierSel==='Other'?'Other':((c.carrierSel||'')+(c.productSel&&c.productSel!=='—'?' — '+c.productSel:''));
    const th=parseFloat(c.takehome)||0;
    const tp=parseFloat(c.targetpremium)||0;
    const ap=parseFloat(c.premium)||0;

    // determine bar class
    let fillClass=pct>=100?'done':pct>=60?'active':pct>=30?'mid':'early';

    // mini bar for row
    const miniBar=mr!==null
      ?`<div class="adv-mini"><div class="adv-mini-bar"><div class="adv-mini-fill ${fillClass}" style="width:${pct}%"></div></div><span class="adv-mini-label">${isDone?'✓ Clear':Math.max(mr,0)+' mo left'}</span></div>`
      :'<span style="color:var(--text3);font-size:12px">—</span>';

    // month dots for expanded view
    let dotsHtml='';
    if(total>0){
      for(let m=1;m<=total;m++){
        const isPaid=m<=paidMonths;
        const dotClass=isPaid?(isDone?'paid done-dot':'paid'):'';
        dotsHtml+=`<div class="month-dot ${dotClass}" title="Month ${m}">${m}</div>`;
      }
    }

    // status pct class
    const pctClass=pct>=100?'done':pct>=60?'':pct>=30?'mid':'';

    const detailHtml=`<div class="client-detail" id="detail-${c.id}">
      <div class="status-section">
        <div class="status-header">
          <span class="status-title">Advancement Status</span>
          <span class="status-pct ${pctClass}">${pct}%</span>
        </div>
        <div class="status-bar-track">
          <div class="status-bar-fill ${fillClass}" style="width:${pct}%"></div>
        </div>
        <div class="month-dots">${dotsHtml}</div>
        <div class="status-footer">
          <span class="status-mo-label">${paidMonths} of ${total} months paid</span>
          ${isDone?'<span class="status-clear-badge">✓ Fully Vested</span>':'<span class="status-active-badge">Active</span>'}
        </div>
      </div>
      <div class="detail-grid">
        <div class="detail-item"><div class="detail-label">Phone</div><div class="detail-val mono">${fmtPhone(c.phone)}</div></div>
        <div class="detail-item"><div class="detail-label">Email</div><div class="detail-val" style="font-size:13px">${c.email||'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Carrier / Product</div><div class="detail-val">${carrier||'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Annual Premium</div><div class="detail-val mono">$${ap?ap.toLocaleString():'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Target Premium</div><div class="detail-val gold mono">${tp?'$'+tp.toLocaleString():'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Commission %</div><div class="detail-val teal mono">${c.commissionpct?c.commissionpct+'%':'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Take Home</div><div class="detail-val green mono" style="font-size:20px;font-weight:800">${th?'$'+Math.round(th).toLocaleString():'—'}</div></div>
        <div class="detail-item"><div class="detail-label">Window</div><div class="detail-val mono">${c.months?c.months+' months':'—'}</div></div>
      </div>
      <div class="detail-actions">
        <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openModal('${c.id}')">✏ Edit</button>
        <button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteClient('${c.id}')">🗑 Delete</button>
      </div>
    </div>`;

    return `<div class="client-row-wrap">
      <div class="client-row" id="row-${c.id}" onclick="toggleExpand('${c.id}')">
        <div class="client-name-col">
          <div class="client-avatar">${initials(c.first,c.last)}</div>
          <div>
            <div class="client-name">${c.first} ${c.last}</div>
            <div class="client-product">${carrier||'No carrier set'}</div>
          </div>
          <span class="expand-chevron">▾</span>
        </div>
        <div class="client-date-col">${fmtDate(c.sold)}</div>
        <div class="adv-col">${miniBar}</div>
      </div>
      ${detailHtml}
    </div>`;
  }).join('');
}

// ── GOALS SYSTEM ──
let goals=[];
let editingGoalId=null;
let selectedEmoji='🏎';

function loadGoals(){const r=localStorage.getItem('cye_goals');if(r){try{return JSON.parse(r)}catch(e){}}return []}
function saveGoals(){
  localStorage.setItem('cye_goals',JSON.stringify(goals));
  const s=document.getElementById('save-status');
  s.innerHTML='<span class="save-dot"></span> Saved '+new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  setTimeout(()=>{s.innerHTML='<span class="save-dot"></span> Auto-saved'},3000);
}

function selectEmoji(el,emoji){
  document.querySelectorAll('.emoji-opt').forEach(e=>e.classList.remove('selected'));
  el.classList.add('selected');
  selectedEmoji=emoji;
}

function updateGoalPreview(){
  const target=parseFloat(document.getElementById('g-target').value)||0;
  const earned=clients.reduce((s,c)=>s+(parseFloat(c.takehome)||0),0);
  const pct=target>0?Math.min(Math.round((earned/target)*100),100):0;
  document.getElementById('g-preview-pct').textContent=pct+'%';
  document.getElementById('g-preview-sub').textContent=target>0?'Take home $'+Math.round(earned).toLocaleString()+' of $'+target.toLocaleString():'Enter a target amount';
}

function openGoalModal(id){
  editingGoalId=id||null;
  selectedEmoji='🏎';
  document.querySelectorAll('.emoji-opt').forEach(e=>e.classList.remove('selected'));
  if(id){
    const g=goals.find(x=>x.id===id);if(!g)return;
    document.getElementById('goal-modal-title').textContent='Edit Goal';
    document.getElementById('g-title').value=g.title||'';
    document.getElementById('g-target').value=g.target||'';
    selectedEmoji=g.emoji||'🎯';
    // highlight correct emoji
    document.querySelectorAll('.emoji-opt').forEach(e=>{if(e.textContent===selectedEmoji)e.classList.add('selected')});
  } else {
    document.getElementById('goal-modal-title').textContent='Add Goal';
    document.getElementById('g-title').value='';
    document.getElementById('g-target').value='';
    document.querySelector('.emoji-opt').classList.add('selected');
    selectedEmoji='🏎';
  }
  updateGoalPreview();
  document.getElementById('goal-overlay').classList.add('open');
}

function closeGoalModal(){document.getElementById('goal-overlay').classList.remove('open');editingGoalId=null}

function saveGoal(){
  const title=(document.getElementById('g-title').value||'').trim();
  const target=parseFloat(document.getElementById('g-target').value)||0;
  if(!title){alert('Please enter a goal name.');return}
  if(!target){alert('Please enter a target amount.');return}
  const data={id:editingGoalId||uid(),emoji:selectedEmoji,title,target};
  if(editingGoalId)goals=goals.map(g=>g.id===editingGoalId?data:g);
  else goals.unshift(data);
  saveGoals();closeGoalModal();renderGoals();
}

function deleteGoal(id){
  if(!confirm('Delete this goal?'))return;
  goals=goals.filter(g=>g.id!==id);
  saveGoals();renderGoals();
}

function renderGoals(){
  const list=document.getElementById('goals-list');
  const empty=document.getElementById('goals-empty');
  if(!goals.length){list.innerHTML='';empty.style.display='block';return}
  empty.style.display='none';

  // total take home is the shared "earned" value across all goals
  const totalTakehome=clients.reduce((s,c)=>s+(parseFloat(c.takehome)||0),0);

  list.innerHTML=goals.map(g=>{
    const target=parseFloat(g.target)||0;
    const earned=totalTakehome;
    const pct=target>0?Math.min(Math.round((earned/target)*100),100):0;
    const isDone=pct>=100;
    const remaining=Math.max(target-earned,0);

    // bar color based on progress
    let barColor,barShadow,pctColor;
    if(isDone){
      barColor='linear-gradient(90deg,#00a854,var(--green))';
      barShadow='0 0 20px rgba(0,230,118,0.4)';
      pctColor='var(--green)';
    } else if(pct>=60){
      barColor='linear-gradient(90deg,#007a70,var(--teal),var(--teal2))';
      barShadow='0 0 20px rgba(0,201,184,0.4)';
      pctColor='var(--teal)';
    } else if(pct>=30){
      barColor='linear-gradient(90deg,#c0700a,#f39c12)';
      barShadow='0 0 16px rgba(243,156,18,0.3)';
      pctColor='#f39c12';
    } else {
      barColor='linear-gradient(90deg,#9b2335,var(--red))';
      barShadow='0 0 16px rgba(255,71,87,0.3)';
      pctColor='var(--red)';
    }

    // milestones
    const milestones=[25,50,75,100].map(m=>{
      const reached=pct>=m;
      return `<div class="goal-milestone${reached?' reached':''}">
        <div style="font-size:16px">${reached?'✅':'⬜'}</div>
        <div class="goal-milestone-pct">${m}%</div>
        <div class="goal-milestone-label">$${(target*m/100).toLocaleString()}</div>
      </div>`;
    }).join('');

    return `<div class="goal-card">
      <div class="goal-top">
        <div class="goal-icon-title">
          <div class="goal-emoji" style="background:rgba(0,201,184,0.08);border-color:var(--teal-border)">${g.emoji}</div>
          <div>
            <div class="goal-title">${g.title}</div>
            <div class="goal-subtitle">Target — $${target.toLocaleString()}</div>
          </div>
        </div>
        <div class="goal-actions">
          <button class="btn btn-ghost btn-sm btn-icon" onclick="openGoalModal('${g.id}')" title="Edit">✏</button>
          <button class="btn btn-danger btn-sm btn-icon" onclick="deleteGoal('${g.id}')" title="Delete">🗑</button>
        </div>
      </div>

      <div class="goal-pct-row">
        <div class="goal-pct" style="color:${pctColor}">${pct}%</div>
        <div class="goal-pct-label">of goal reached</div>
      </div>

      <div class="goal-bar-track">
        <div class="goal-bar-fill" style="width:${pct}%;background:${barColor};box-shadow:${barShadow}"></div>
      </div>

      <div class="goal-3stats">
        <div class="goal-stat">
          <div class="goal-stat-label">Take Home</div>
          <div class="goal-stat-val" style="color:${pctColor}">$${Math.round(earned).toLocaleString()}</div>
        </div>
        <div class="goal-stat">
          <div class="goal-stat-label">Goal</div>
          <div class="goal-stat-val" style="color:var(--gold)">$${target.toLocaleString()}</div>
        </div>
        <div class="goal-stat">
          <div class="goal-stat-label">Remaining</div>
          <div class="goal-stat-val" style="color:var(--green)">${isDone?'Done 🎉':'$'+Math.round(remaining).toLocaleString()}</div>
        </div>
      </div>

      <div class="goal-milestones">${milestones}</div>
    </div>`;
  }).join('');
}

function renderCarriers(){
  const lvl=getContractLevel();let html='';
  Object.keys(COMP).forEach((carrier,i)=>{
    const products=COMP[carrier];const id='carr-'+i;let rows='';
    Object.keys(products).forEach(product=>{
      const rates=products[product];const pct=rates[lvl];
      if(pct===null||pct===undefined)return;
      const col=pct>=100?'var(--green)':pct>=75?'#f39c12':'var(--red)';
      rows+=`<div class="carrier-product-row"><span style="color:var(--text2)">${product}</span><span style="font-size:20px;font-weight:800;color:${col};font-family:'DM Mono',monospace">${pct}%</span></div>`;
    });
    if(!rows)return;
    html+=`<div class="carrier-card"><div class="carrier-card-header" onclick="toggleCarrier('${id}')"><span class="carrier-card-title">${carrier}</span><span id="chev-${id}" style="color:var(--text3);font-size:16px;transition:transform .2s;display:inline-block">▾</span></div><div class="carrier-card-body" id="${id}"><div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Your rate @ FFL level ${lvl}</div>${rows}</div></div>`;
  });
  document.getElementById('carriers-content').innerHTML=html||'<p style="color:var(--text3);padding:20px;font-size:13px">No data.</p>';
}

function toggleCarrier(id){
  const b=document.getElementById(id);const c=document.getElementById('chev-'+id);
  const open=b.style.display!=='none'&&b.style.display!=='';
  b.style.display=open?'none':'block';c.style.transform=open?'':'rotate(180deg)';
}

function calcTakehome(){
  const ap=parseFloat(document.getElementById('f-premium').value)||0;
  const rate=parseFloat(document.getElementById('f-commissionpct').value)||0;
  const th=ap*(rate/100);
  document.getElementById('f-takehome-preview').textContent=th>0?'$'+Math.round(th).toLocaleString():'$0';
  document.getElementById('f-takehome-breakdown').textContent=th>0?'AP $'+ap.toLocaleString()+' × '+rate+'%':'Enter annual premium and commission % above';
}
function updateProductDropdown(){
  const carrier=document.getElementById('f-carrier-sel').value;
  const sel=document.getElementById('f-product-sel');
  sel.innerHTML='<option value="">Select product...</option>';
  (PRODUCTS_BY_CARRIER[carrier]||[]).forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;sel.appendChild(o)});
  document.getElementById('f-commissionpct').value='';
  document.getElementById('comm-auto-badge').style.display='none';
  calcTakehome();
}
function autoFillCommission(){
  const carrier=document.getElementById('f-carrier-sel').value;
  const product=document.getElementById('f-product-sel').value;
  const badge=document.getElementById('comm-auto-badge');
  if(carrier&&product&&product!=='—'){
    const auto=getComp(carrier,product);
    if(auto!==null&&auto!==undefined){document.getElementById('f-commissionpct').value=auto;badge.style.display='inline';calcTakehome();return}
  }
  badge.style.display='none';calcTakehome();
}
function openModal(id){
  editingId=id||null;
  // populate lead source dropdown from saved companies
  const lsEl=document.getElementById('f-leadsource');
  lsEl.innerHTML='<option value="">No lead source</option>';
  leadCompanies.forEach(lc=>{const o=document.createElement('option');o.value=lc.id;o.textContent=lc.name;lsEl.appendChild(o)});
  if(id){
    const c=clients.find(x=>x.id===id);if(!c)return;
    document.getElementById('modal-title-text').textContent='Edit client';
    ['first','last','phone','email','sold','months','premium','commissionpct','targetpremium'].forEach(f=>{const el=document.getElementById('f-'+f);if(el)el.value=c[f]||''});
    document.getElementById('f-carrier-sel').value=c.carrierSel||'';
    updateProductDropdown();
    document.getElementById('f-product-sel').value=c.productSel||'';
    document.getElementById('f-commissionpct').value=c.commissionpct||'';
    document.getElementById('f-leadsource').value=c.leadsource||'';
    document.getElementById('comm-auto-badge').style.display='none';
  }else{
    document.getElementById('modal-title-text').textContent='Add client';
    ['first','last','phone','email','sold','months','premium','commissionpct','targetpremium'].forEach(f=>{const el=document.getElementById('f-'+f);if(el)el.value=''});
    document.getElementById('f-carrier-sel').value='';
    document.getElementById('f-product-sel').innerHTML='<option value="">Select product...</option>';
    document.getElementById('f-leadsource').value='';
    document.getElementById('comm-auto-badge').style.display='none';
  }
  document.getElementById('f-takehome-preview').textContent='$0';
  document.getElementById('f-takehome-breakdown').textContent='Enter annual premium and commission % above';
  calcTakehome();
  document.getElementById('modal-overlay').classList.add('open');
}
function closeModal(){document.getElementById('modal-overlay').classList.remove('open');editingId=null}
function deleteClient(id){deletingId=id;document.getElementById('confirm-overlay').classList.add('open')}
function closeConfirm(){document.getElementById('confirm-overlay').classList.remove('open');deletingId=null}
function confirmDelete(){clients=clients.filter(c=>c.id!==deletingId);saveData();closeConfirm();render()}
function saveClient(){
  const g=f=>(document.getElementById('f-'+f).value||'').trim();
  const first=g('first'),last=g('last');
  if(!first||!last){alert('Please enter a first and last name.');return}
  const ap=parseFloat(g('premium'))||0,rate=parseFloat(g('commissionpct'))||0;
  const data={id:editingId||uid(),first,last,phone:g('phone'),email:g('email'),carrierSel:document.getElementById('f-carrier-sel').value,productSel:document.getElementById('f-product-sel').value,sold:g('sold'),months:g('months'),premium:g('premium'),targetpremium:g('targetpremium'),commissionpct:g('commissionpct'),takehome:ap*(rate/100),leadsource:document.getElementById('f-leadsource').value,createdAt:editingId?(clients.find(c=>c.id===editingId)||{}).createdAt:new Date().toISOString()};
  if(editingId)clients=clients.map(c=>c.id===editingId?data:c);
  else clients.unshift(data);
  saveData();closeModal();render();
}
function exportCSV(){
  if(!clients.length){alert('No clients to export.');return}
  const h=['First','Last','Phone','Email','Carrier','Product','Sold','Months','Annual Premium','Target Premium','Commission %','Take Home'];
  const rows=clients.map(c=>[c.first,c.last,c.phone,c.email,c.carrierSel,c.productSel,c.sold,c.months,c.premium,c.targetpremium||0,c.commissionpct,Math.round(c.takehome||0)].map(v=>'"'+(v||'').toString().replace(/"/g,'""')+'"').join(','));
  const csv=[h.join(',')].concat(rows).join('\n');
  const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='clients-'+new Date().toISOString().slice(0,10)+'.csv';a.click();
}
function downloadHTML(){
  const html=document.documentElement.outerHTML;
  const d=html.replace('var SEED_CLIENTS=null','var SEED_CLIENTS='+JSON.stringify(JSON.stringify(clients))).replace('var SEED_CONTRACT=null','var SEED_CONTRACT="'+getContractLevel()+'"');
  const blob=new Blob([d],{type:'text/html'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='aurum-tracker-'+new Date().toISOString().slice(0,10)+'.html';a.click();URL.revokeObjectURL(a.href);
}
// ── LEAD SPEND SYSTEM ──
let leadCompanies=[];
let editingLeadId=null;

function loadLeadCompanies(){const r=localStorage.getItem('cye_leads');if(r){try{return JSON.parse(r)}catch(e){}}return []}
function saveLeadData(){
  localStorage.setItem('cye_leads',JSON.stringify(leadCompanies));
  const s=document.getElementById('save-status');
  s.innerHTML='<span class="save-dot"></span> Saved '+new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  setTimeout(()=>{s.innerHTML='<span class="save-dot"></span> Auto-saved'},3000);
}

function updateLeadPreview(){
  const spent=parseFloat(document.getElementById('l-spent').value)||0;
  const count=parseFloat(document.getElementById('l-count').value)||0;
  const cpl=spent>0&&count>0?(spent/count).toFixed(2):null;
  document.getElementById('l-preview-cpl').textContent=cpl?'$'+cpl:'—';
  document.getElementById('l-preview-sub').textContent=cpl?spent.toLocaleString('en-US',{style:'currency',currency:'USD'})+' ÷ '+count+' leads':'Enter amount and lead count above';
}

function openLeadModal(id){
  editingLeadId=id||null;
  if(id){
    const lc=leadCompanies.find(x=>x.id===id);if(!lc)return;
    document.getElementById('lead-modal-title').textContent='Edit Lead Company';
    document.getElementById('l-name').value=lc.name||'';
    document.getElementById('l-spent').value=lc.spent||'';
    document.getElementById('l-count').value=lc.count||'';
    document.getElementById('l-date').value=lc.date||'';
    document.getElementById('l-notes').value=lc.notes||'';
  } else {
    document.getElementById('lead-modal-title').textContent='Add Lead Company';
    document.getElementById('l-name').value='';
    document.getElementById('l-spent').value='';
    document.getElementById('l-count').value='';
    document.getElementById('l-date').value='';
    document.getElementById('l-notes').value='';
  }
  updateLeadPreview();
  document.getElementById('lead-overlay').classList.add('open');
}
function closeLeadModal(){document.getElementById('lead-overlay').classList.remove('open');editingLeadId=null}

function saveLeadCompany(){
  const name=(document.getElementById('l-name').value||'').trim();
  if(!name){alert('Please enter a company name.');return}
  const spent=parseFloat(document.getElementById('l-spent').value)||0;
  const count=parseInt(document.getElementById('l-count').value)||0;
  const data={
    id:editingLeadId||uid(),
    name,spent,count,
    date:document.getElementById('l-date').value||'',
    notes:(document.getElementById('l-notes').value||'').trim()
  };
  if(editingLeadId)leadCompanies=leadCompanies.map(lc=>lc.id===editingLeadId?data:lc);
  else leadCompanies.unshift(data);
  saveLeadData();closeLeadModal();renderLeads();
}

function deleteLeadCompany(id){
  if(!confirm('Delete this lead company? Clients tagged to it will be untagged.'))return;
  // untag clients linked to this company
  clients=clients.map(c=>c.leadsource===id?{...c,leadsource:''}:c);
  saveData();
  leadCompanies=leadCompanies.filter(lc=>lc.id!==id);
  saveLeadData();renderLeads();
}

function toggleLcBody(id){
  const body=document.getElementById('lcb-'+id);
  const chev=document.getElementById('lcc-'+id);
  const open=body.style.display==='block';
  body.style.display=open?'none':'block';
  chev.style.transform=open?'':'rotate(180deg)';
}

function renderLeads(){
  const list=document.getElementById('lead-companies-list');
  const empty=document.getElementById('leads-empty');
  const roiRow=document.getElementById('leads-roi-row');

  if(!leadCompanies.length){list.innerHTML='';roiRow.innerHTML='';empty.style.display='block';return}
  empty.style.display='none';

  // overall summary stats
  const totalSpent=leadCompanies.reduce((s,lc)=>s+lc.spent,0);
  const totalLeads=leadCompanies.reduce((s,lc)=>s+lc.count,0);
  const totalRevenueFromLeads=clients.filter(c=>c.leadsource).reduce((s,c)=>s+(parseFloat(c.takehome)||0),0);
  const totalROI=totalSpent>0?((totalRevenueFromLeads-totalSpent)/totalSpent*100):0;
  const overallCPL=totalLeads>0?(totalSpent/totalLeads):0;

  roiRow.innerHTML=
    `<div class="stat"><div class="stat-label">Total lead spend</div><div class="stat-val red">$${Math.round(totalSpent).toLocaleString()}</div></div>`+
    `<div class="stat"><div class="stat-label">Total leads bought</div><div class="stat-val">${totalLeads}</div></div>`+
    `<div class="stat"><div class="stat-label">Avg cost per lead</div><div class="stat-val teal">$${overallCPL>0?overallCPL.toFixed(2):'—'}</div></div>`+
    `<div class="stat"><div class="stat-label">Revenue from leads</div><div class="stat-val green">$${Math.round(totalRevenueFromLeads).toLocaleString()}</div></div>`+
    `<div class="stat"><div class="stat-label">Overall ROI</div><div class="stat-val" style="color:${totalROI>=0?'var(--green)':'var(--red)'}">${totalROI>=0?'+':''}${Math.round(totalROI)}%</div></div>`;

  list.innerHTML=leadCompanies.map(lc=>{
    // clients tagged to this company
    const tagged=clients.filter(c=>c.leadsource===lc.id);
    const revenueFromThis=tagged.reduce((s,c)=>s+(parseFloat(c.takehome)||0),0);
    const roi=lc.spent>0?((revenueFromThis-lc.spent)/lc.spent*100):0;
    const cpl=lc.count>0?(lc.spent/lc.count):0;
    const convRate=lc.count>0?(tagged.length/lc.count*100):0;
    const isDone=roi>0;
    const isZero=lc.spent===0;

    // ROI bar — capped at 200% for display
    const barPct=Math.min(Math.max(roi,0),200)/200*100;
    const barColor=roi>=100?'linear-gradient(90deg,#00a854,var(--green))':roi>=0?'linear-gradient(90deg,#007a70,var(--teal))':'linear-gradient(90deg,#9b2335,var(--red))';

    const clientRows=tagged.length
      ?tagged.map(c=>{
        const carrier=c.carrierSel==='Other'?'Other':((c.carrierSel||'')+(c.productSel&&c.productSel!=='—'?' — '+c.productSel:''));
        return `<div class="lc-client-row">
          <div>
            <div class="lc-client-name">${c.first} ${c.last}</div>
            <div class="lc-client-product">${carrier||'No carrier'}</div>
          </div>
          <div class="lc-client-th">+$${Math.round(parseFloat(c.takehome)||0).toLocaleString()}</div>
        </div>`;
      }).join('')
      :`<div class="lc-no-clients">No clients tagged to this source yet. Tag clients when adding or editing them.</div>`;

    const roiBadgeClass=isZero?'zero':isDone?'pos':'neg';
    const roiBadgeText=isZero?'No spend':isDone?'+'+Math.round(roi)+'% ROI':Math.round(roi)+'% ROI';

    return `<div class="lc-card">
      <div class="lc-header" onclick="toggleLcBody('${lc.id}')">
        <div class="lc-header-left">
          <div class="lc-icon">💸</div>
          <div>
            <div class="lc-name">${lc.name}</div>
            <div class="lc-meta">${lc.count} leads · $${lc.spent.toLocaleString()} spent${lc.date?' · '+new Date(lc.date+'T00:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}):''}</div>
          </div>
        </div>
        <div class="lc-header-right">
          <span class="lc-roi-badge ${roiBadgeClass}">${roiBadgeText}</span>
          <span id="lcc-${lc.id}" style="color:var(--text3);font-size:16px;transition:transform .2s;display:inline-block">▾</span>
        </div>
      </div>
      <div class="lc-body" id="lcb-${lc.id}">
        <div class="lc-stats">
          <div class="lc-stat"><div class="lc-stat-label">Amount spent</div><div class="lc-stat-val" style="color:var(--red)">$${lc.spent.toLocaleString()}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Leads bought</div><div class="lc-stat-val">${lc.count}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Cost per lead</div><div class="lc-stat-val" style="color:var(--teal)">${cpl>0?'$'+cpl.toFixed(2):'—'}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Clients closed</div><div class="lc-stat-val" style="color:var(--gold)">${tagged.length}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Conv. rate</div><div class="lc-stat-val" style="color:var(--teal)">${lc.count>0?convRate.toFixed(1)+'%':'—'}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Revenue</div><div class="lc-stat-val" style="color:var(--green)">$${Math.round(revenueFromThis).toLocaleString()}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">Net profit</div><div class="lc-stat-val" style="color:${revenueFromThis-lc.spent>=0?'var(--green)':'var(--red)'}">$${Math.round(revenueFromThis-lc.spent).toLocaleString()}</div></div>
          <div class="lc-stat"><div class="lc-stat-label">ROI</div><div class="lc-stat-val" style="color:${roi>=0?'var(--green)':'var(--red)'}">${isZero?'—':(roi>=0?'+':'')+Math.round(roi)+'%'}</div></div>
        </div>
        ${lc.notes?`<div style="font-size:12px;color:var(--text3);background:var(--bg3);border-radius:8px;padding:10px 14px;margin-bottom:14px">📝 ${lc.notes}</div>`:''}
        <div class="lc-roi-bar-wrap">
          <div class="lc-roi-bar-label">
            <span>ROI progress</span>
            <span style="color:${roi>=0?'var(--green)':'var(--red)'}">${isZero?'No spend yet':(roi>=0?'+':'')+Math.round(roi)+'% return on spend'}</span>
          </div>
          <div class="lc-roi-bar-track">
            <div class="lc-roi-bar-fill" style="width:${barPct}%;background:${barColor};box-shadow:0 0 10px rgba(0,201,184,0.3)"></div>
          </div>
        </div>
        <div class="lc-clients-section">
          <div class="lc-clients-title">Clients from this source (${tagged.length})</div>
          ${clientRows}
        </div>
        <div class="lc-actions">
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openLeadModal('${lc.id}')">✏ Edit</button>
          <button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteLeadCompany('${lc.id}')">🗑 Delete</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

clients=loadClients();
goals=loadGoals();
leadCompanies=loadLeadCompanies();
document.getElementById('contract-level').value=getContractLevel();
render();

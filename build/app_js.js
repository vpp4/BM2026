const D=DATA, DAYS=D.days, CATS=D.cats, TAGS=D.tags;
const DN=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const LS=k=>{try{return JSON.parse(localStorage.getItem(k))}catch(e){return null}};
const SV=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};

let home = LS('home') || [40.772262,-119.204136];
let favs = new Set(LS('favs')||[]);
const st = {q:'', tags:new Set(), day:-1, star:false, favOnly:false, now:false,
            ver:false, guest:false, noWoo:false, music:false, mode:'walk', t0:0, t1:1440, walk:99, limit:200};

// flatten to occurrences once
const OCC=[];
D.ev.forEach((e,i)=>e.o.forEach(o=>OCC.push({e,i,d:o[0],s:o[1],x:o[2]})));
const hav=(a,b)=>{const R=6371e3,r=Math.PI/180,p1=a[0]*r,p2=b[0]*r,
 dp=p2-p1,dl=(b[1]-a[1])*r,h=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;
 return 2*R*Math.asin(Math.sqrt(h))};
// 80 m/min on foot. 200 m/min (12 km/h) on an e-bike — deliberately below a
// bike's flat-ground speed: playa dust is soft, and you brake for crowds,
// art cars and whiteouts.
const SPEED={walk:80, bike:200};
function metresOf(e){ if(!e.p) return null;
 if(e._m!==undefined && e._h===home) return e._m;
 e._h=home; e._m=hav(home,e.p); return e._m }
const mins=(m,mode)=>m===null?null:Math.round(m/SPEED[mode]);
const pad=n=>String(n).padStart(2,'0');
const hm=m=>pad(Math.floor(m/60)%24)+':'+pad(m%60);
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function nowRef(){ const n=new Date(); const d=DAYS.indexOf(n.toISOString().slice(0,10));
 return {d, m:n.getHours()*60+n.getMinutes()} }

function match(o){
 const e=o.e;
 if(st.music ? !e.m : !!e.m) return false;
 if(st.star && !e.s) return false;
 if(st.ver && !e.v) return false;
 if(st.guest && !e.u) return false;
 if(st.noWoo && e.w) return false;
 if(st.favOnly && !favs.has(e.t)) return false;
 if(st.day>=0 && o.d!==st.day) return false;
 if(o.s<st.t0 || o.s>st.t1) return false;
 if(st.walk<99){ const t=mins(metresOf(e),st.mode); if(t!==null && t>st.walk) return false }
 if(st.tags.size && !e.g.some(g=>st.tags.has(g))) return false;
 if(st.now){ const n=nowRef(); if(n.d<0) return false;
   if(o.d!==n.d || o.x<n.m || o.s>n.m+180) return false }
 if(st.q){ const q=st.q.toLowerCase();
   if(!((e.t+' '+e.d+' '+(e.h||'')+' '+(e.l||'')).toLowerCase().includes(q))) return false }
 return true;
}

function render(){
 const hits=OCC.filter(match).sort((a,b)=>a.d-b.d||a.s-b.s);
 document.getElementById('cnt').textContent = hits.length+' found';
 const box=document.getElementById('out');
 if(!hits.length){ box.innerHTML='<p class="empty">Nothing matches. Loosen a filter.</p>'; return }
 const show=hits.slice(0,st.limit); let h='',lastDay=-1;
 for(const o of show){
  const e=o.e;
  if(o.d!==lastDay){ lastDay=o.d;
   const dt=new Date(DAYS[o.d]+'T12:00:00');
   h+='<li class="dayhd">'+DN[dt.getDay()]+' &middot; '+DAYS[o.d]+'</li>' }
  const m=metresOf(e), tw=mins(m,'walk'), tb=mins(m,'bike');
  h+='<li class="ev">'+
   '<div class="wh"><b>'+hm(o.s)+'</b><span>'+hm(o.x)+'</span></div><div>'+
   '<p class="tt">'+esc(e.t)+'</p>'+
   (e.d?'<p class="dd">'+esc(e.d)+'</p>':'')+
   '<p class="mt"><span class="cat">'+esc(CATS[e.c])+'</span>'+
   (e.l?'<span class="lo">'+esc(e.l)+'</span>':'')+
   (m!==null?'<span class="wk">'+tw+'&thinsp;min walk <span class="sep">/</span> '
     +tb+'&thinsp;min bike</span>':'<span class="wk">distance n/a</span>')+
   (e.v?'<span class="one vf">verified</span>':'')+
   (e.u?'<span class="one ug">guest?</span>':'')+
   (e.w?'<span class="one wo">woo</span>':'')+
   (e.o.length===1?'<span class="one">only showing</span>':'')+
   (e.h?'<span class="ho">'+esc(e.h)+'</span>':'')+
   '</p></div>'+
   '<button class="fav'+(favs.has(e.t)?' on':'')+'" data-t="'+esc(e.t)+
   '" aria-label="Save '+esc(e.t)+'">'+(favs.has(e.t)?'★':'☆')+'</button></li>';
 }
 box.innerHTML=h+(hits.length>st.limit
  ? '<button class="more" id="more">Show '+Math.min(200,hits.length-st.limit)+' more of '+hits.length+'</button>':'');
 const m=document.getElementById('more');
 if(m) m.onclick=()=>{st.limit+=200;render()};
 box.querySelectorAll('.fav').forEach(b=>b.onclick=()=>{
   const t=b.dataset.t; favs.has(t)?favs.delete(t):favs.add(t);
   SV('favs',[...favs]); render() });
}
const reset=()=>{st.limit=200;badge();render()};

// ---- controls
const $=id=>document.getElementById(id);
$('q').addEventListener('input',e=>{st.q=e.target.value.trim();reset()});

document.querySelectorAll('[data-tag]').forEach(b=>b.onclick=()=>{
 const i=+b.dataset.tag; st.tags.has(i)?st.tags.delete(i):st.tags.add(i);
 b.classList.toggle('on'); reset()});

document.querySelectorAll('[data-day]').forEach(b=>b.onclick=()=>{
 const d=+b.dataset.day; st.day = st.day===d?-1:d;
 document.querySelectorAll('[data-day]').forEach(x=>x.classList.toggle('on',+x.dataset.day===st.day));
 reset()});

// Events / Sets is a mode, not a filter — it never counts toward the filter badge
function mode(music){
 st.music=music;
 $('mEv').classList.toggle('on',!music); $('mEv').setAttribute('aria-pressed',!music);
 $('mMu').classList.toggle('on',music);  $('mMu').setAttribute('aria-pressed',music);
 reset()}
$('mEv').onclick=()=>mode(false); $('mMu').onclick=()=>mode(true);

const TOGS=[['bStar','star'],['bFav','favOnly'],['bNow','now'],
            ['bVer','ver'],['bGuest','guest'],['bWoo','noWoo']];
TOGS.forEach(([id,key])=>$(id).onclick=()=>{
 const on=!st[key]; st[key]=on; $(id).classList.toggle('on',on);
 if(key==='now' && on){ st.day=-1;
   document.querySelectorAll('[data-day]').forEach(x=>x.classList.remove('on')) }
 reset()});

$('bAdv').onclick=()=>{
 const open=$('adv').classList.toggle('open');
 $('bAdv').setAttribute('aria-expanded',open); sizeHead()};

const t0=$('t0'),t1=$('t1'),wk=$('wk'),hi=$('hm');
function times(){
 let a=+t0.value,b=+t1.value;
 if(a>=b){ if(this===t1) a=b-1; else b=a+1; t0.value=a; t1.value=b }  // keep the pair ordered
 st.t0=a*60; st.t1=b*60;
 $('tv').textContent=pad(a)+':00–'+pad(b)+':00'; reset()}
t0.oninput=t1.oninput=times;
function walkLabel(){ $('wv').textContent =
 st.walk>=99 ? 'anywhere' : st.walk+' min '+(st.mode==='bike'?'ride':'walk') }
wk.oninput=()=>{st.walk = +wk.value >= +wk.max ? 99 : +wk.value; walkLabel(); reset()};
$('mWalk').onclick=()=>setMode('walk'); $('mBike').onclick=()=>setMode('bike');
// An e-bike collapses BRC: the furthest thing in the dataset is a 37-min walk
// but a 15-min ride. A 5-99 min slider would pass everything in bike mode, so
// the range tightens to stay useful.
const RANGE={walk:{min:5,max:99,step:5}, bike:{min:2,max:20,step:2}};
function setMode(m){ st.mode=m;
 const r=RANGE[m], was=+wk.value, wasAny=was>=+wk.max;
 wk.min=r.min; wk.max=r.max; wk.step=r.step;
 wk.value = wasAny ? r.max : Math.min(Math.max(was,r.min), r.max);
 st.walk = +wk.value >= r.max ? 99 : +wk.value;
 $('mWalk').classList.toggle('on',m==='walk'); $('mBike').classList.toggle('on',m==='bike');
 $('mWalk').setAttribute('aria-pressed',m==='walk');
 $('mBike').setAttribute('aria-pressed',m==='bike');
 SV('mode',m); walkLabel(); reset() }
setMode(LS('mode')||'walk');
// address picker — nobody knows their lat/lng, everybody knows "4:00 & E"
const GEO=D.geo, hc=$('hc'), hs=$('hs');
const CLOCKS=[]; for(let m=120;m<=600;m+=15) CLOCKS.push(m);
const cLabel=m=>Math.floor(m/60)+':'+pad(m%60);
hc.innerHTML=CLOCKS.map(m=>`<option value="${m}">${cLabel(m)}</option>`).join('');
hs.innerHTML=GEO.streets.filter(s=>GEO.table[s])
 .map(s=>`<option value="${s}">${s==='ESPLANADE'?'Esplanade':s}</option>`).join('');
function applyHome(save){
 const p=(GEO.table[hs.value]||{})[hc.value];
 if(!p) return;
 home=p; if(save){SV('home',p); SV('addr',[hc.value,hs.value])}
 D.ev.forEach(e=>delete e._h); reset();
}
const savedAddr=LS('addr');
if(savedAddr){ hc.value=savedAddr[0]; hs.value=savedAddr[1] }
else{ // start on whatever address is closest to the built-in default
 let bd=1e9;
 for(const s in GEO.table) for(const m in GEO.table[s]){
   const d=hav(home,GEO.table[s][m]); if(d<bd){bd=d;hc.value=m;hs.value=s}}
}
hc.onchange=hs.onchange=()=>applyHome(true);

function badge(){
 const n = st.tags.size + TOGS.filter(([,k])=>st[k]).length
         + (st.walk<99?1:0) + ((st.t0>0||st.t1<1440)?1:0);
 const el=$('fc'); el.textContent=n; el.hidden=!n}

$('clr').onclick=()=>{
 st.tags.clear(); TOGS.forEach(([id,k])=>{st[k]=false;$(id).classList.remove('on')});
 document.querySelectorAll('[data-tag]').forEach(b=>b.classList.remove('on'));
 t0.value=0; t1.value=24; wk.value=99; times(); wk.oninput()};

function sizeHead(){ document.documentElement.style.setProperty('--hh',
 document.querySelector('.bar').offsetHeight+'px') }
addEventListener('resize',sizeHead);
sizeHead(); times(); render();

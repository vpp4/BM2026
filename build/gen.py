# -*- coding: utf-8 -*-
import os
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(ROOT, 'data')
OUT   = os.path.join(ROOT, 'out')
BUILD = os.path.dirname(os.path.abspath(__file__))
DB    = os.path.join(ROOT, 'brc2026.db')
def dpath(n): return os.path.join(DATA, n)
def bpath(n): return os.path.join(BUILD, n)
def opath(n): return os.path.join(OUT, n)
import json, html, collections
S=json.load(open(bpath('schedule.json')))
THEMES=['Philosophy','Science','AI & society','Death & grief','Storytelling',
        'Lecture','Culture & land','Climate & tech','Conversation craft','Games for the brain']
HUE={'Philosophy':228,'Science':190,'AI & society':266,'Death & grief':348,'Storytelling':32,
     'Lecture':158,'Culture & land':96,'Climate & tech':205,'Conversation craft':310,'Games for the brain':50}
DAYNAME={'2026-08-30':'Gate Sunday','2026-08-31':'Monday','2026-09-01':'Tuesday','2026-09-02':'Wednesday',
         '2026-09-03':'Thursday','2026-09-04':'Friday','2026-09-05':'Saturday — Burn Night','2026-09-06':'Temple Sunday'}
def esc(s): return html.escape(s or '')
def hm(h): return f'{int(h):02d}:{int(round((h%1)*60)):02d}'

days=collections.OrderedDict()
for e in S: days.setdefault(e['day'],[]).append(e)
for d in days: days[d].sort(key=lambda x:(x['sh'],-x['dur']))

rows=[]
for d,evs in days.items():
    # free-window + density bar over 05:00-23:00
    seg=[]
    prev_end=5.0
    for e in evs:
        s=max(5.0,e['sh']); en=min(23.0,e['sh']+e['dur'])
        seg.append((s,en))
    busy=[]
    for s,en in sorted(seg):
        if busy and s<=busy[-1][1]: busy[-1]=(busy[-1][0],max(busy[-1][1],en))
        else: busy.append((s,en))
    gaps=[]
    cur=5.0
    for s,en in busy:
        if s-cur>=1.0: gaps.append((cur,s))
        cur=max(cur,en)
    if 23.0-cur>=1.0: gaps.append((cur,23.0))
    bar=''.join(f'<span class="blk" style="left:{(s-5)/18*100:.2f}%;width:{(en-s)/18*100:.2f}%"></span>' for s,en in busy)
    ticks=''.join(f'<span class="tk" style="left:{(h-5)/18*100:.2f}%"><i></i>{h}</span>' for h in (6,9,12,15,18,21))

    cards=[]
    running_end=0
    for e in evs:
        clash = e['sh'] < running_end - 0.01
        running_end=max(running_end,e['sh']+e['dur'])
        walk = f'{e["walk"]} min walk' if e['walk'] is not None else 'walk n/a'
        oneshot = '<span class="flag oneshot" title="This is the only time it runs all week">only showing</span>' if e['n_occ']==1 else ''
        clashf  = '<span class="flag clash" title="Starts before the previous listing ends">overlaps</span>' if clash else ''
        cards.append(f'''<li class="ev" data-theme-name="{esc(e['theme'])}" data-walk="{e['walk'] if e['walk'] is not None else 99}" data-clash="{1 if clash else 0}">
 <div class="when"><b>{esc(e['start'])}</b><span>{esc(e['end'])}</span></div>
 <div class="body">
  <p class="ttl">{esc(e['title'])}</p>
  <p class="dsc">{esc(e['desc'])}</p>
  <p class="meta"><span class="chip" style="--h:{HUE[e['theme']]}">{esc(e['theme'])}</span>
   <span class="loc">{esc(e['loc']) or 'location TBD'}</span>
   <span class="walk">{walk}</span>
   {oneshot}{clashf}
   <span class="host">{esc(e['host']) or 'Burning Man org'}</span></p>
 </div></li>''')
    gaptxt = ' · '.join(f'{hm(a)}–{hm(b)}' for a,b in gaps) or 'no gap over an hour'
    rows.append(f'''<section class="day" id="d{d}">
 <header class="dayhead">
  <h2>{DAYNAME[d]}</h2><p class="dt">{d} · {len(evs)} picks</p>
  <div class="bar">{bar}{ticks}</div>
  <p class="gaps"><span>open</span> {esc(gaptxt)}</p>
 </header>
 <ol class="evs">{''.join(cards)}</ol>
</section>''')

nav=''.join(f'<a href="#d{d}">{DAYNAME[d].split(" ")[0][:3]}<b>{len(v)}</b></a>' for d,v in days.items())
chips=''.join(f'<button class="fchip on" data-t="{esc(t)}" style="--h:{HUE[t]}">{esc(t)}<b>{sum(1 for e in S if e["theme"]==t)}</b></button>' for t in THEMES)

CSS = '''
:root{
 --ground:#E6E6E1; --surface:#F4F4F0; --raise:#FBFBF8;
 --ink:#16181B; --ink2:#3D4247; --muted:#6C7176; --line:#D2D2CA; --line2:#BFBFB5;
 --accent:#1E42C0; --accent-ink:#fff; --chipL:92%; --chipS:38%; --chipT:26%;
 --barfill:#1E42C0; --bartrack:#D2D2CA;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
 --ground:#0F1115; --surface:#171A1F; --raise:#1E2229;
 --ink:#E9EBED; --ink2:#BEC4CA; --muted:#8D949B; --line:#282D34; --line2:#3A414A;
 --accent:#7C99FF; --accent-ink:#0F1115; --chipL:22%; --chipS:42%; --chipT:78%;
 --barfill:#7C99FF; --bartrack:#282D34; }}
:root[data-theme="dark"]{
 --ground:#0F1115; --surface:#171A1F; --raise:#1E2229;
 --ink:#E9EBED; --ink2:#BEC4CA; --muted:#8D949B; --line:#282D34; --line2:#3A414A;
 --accent:#7C99FF; --accent-ink:#0F1115; --chipL:22%; --chipS:42%; --chipT:78%;
 --barfill:#7C99FF; --bartrack:#282D34; }

*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font-family:Charter,"Iowan Old Style",Palatino,Georgia,serif;
 font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
.cond{font-family:"Avenir Next Condensed","HelveticaNeue-CondensedBold","Arial Narrow",system-ui,sans-serif}
.mono{font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px 80px}

header.top{padding:52px 0 26px;border-bottom:2px solid var(--ink)}
h1{font-family:"Avenir Next Condensed","HelveticaNeue-CondensedBold","Arial Narrow",system-ui,sans-serif;
 font-weight:700;font-size:clamp(38px,7vw,68px);line-height:.94;letter-spacing:-.015em;
 margin:0 0 10px;text-wrap:balance;text-transform:uppercase}
h1 em{font-style:normal;color:var(--accent);display:block}
.sub{margin:0;max-width:64ch;color:var(--ink2);font-size:17px}
.facts{display:flex;flex-wrap:wrap;gap:0;margin:24px 0 0;border-top:1px solid var(--line)}
.facts div{flex:1 1 130px;padding:12px 16px 12px 0;border-right:1px solid var(--line)}
.facts div:last-child{border-right:0}
.facts b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}
.facts span{font-size:11px;letter-spacing:.11em;text-transform:uppercase;color:var(--muted)}

.controls{position:sticky;top:0;z-index:20;background:var(--ground);
 border-bottom:1px solid var(--line);padding:12px 0 12px;margin-bottom:8px}
.navdays{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.navdays a{text-decoration:none;color:var(--ink2);border:1px solid var(--line2);
 padding:4px 9px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;
 display:flex;gap:6px;align-items:baseline;border-radius:2px}
.navdays a:hover,.navdays a:focus-visible{border-color:var(--accent);color:var(--accent)}
.navdays a b{font-variant-numeric:tabular-nums;font-size:11px;color:var(--muted)}
.filters{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.fchip{cursor:pointer;font:inherit;font-size:12px;padding:4px 10px;border-radius:2px;
 border:1px solid hsl(var(--h) var(--chipS) 62% / .5);
 background:transparent;color:var(--muted);display:flex;gap:6px;align-items:baseline}
.fchip.on{background:hsl(var(--h) var(--chipS) var(--chipL));color:hsl(var(--h) 55% var(--chipT));
 border-color:hsl(var(--h) var(--chipS) 60% / .55);font-weight:600}
.fchip b{font-size:10px;font-variant-numeric:tabular-nums;opacity:.7;font-weight:500}
.fchip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.walkctl{display:flex;gap:9px;align-items:center;font-size:12px;color:var(--muted);
 margin-left:auto;text-transform:uppercase;letter-spacing:.07em}
.walkctl input{width:130px;accent-color:var(--accent)}
.walkctl output{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600}

.day{margin-top:38px;scroll-margin-top:130px}
.dayhead{border-top:2px solid var(--ink);padding-top:12px}
.dayhead h2{font-family:"Avenir Next Condensed","HelveticaNeue-CondensedBold","Arial Narrow",system-ui,sans-serif;
 text-transform:uppercase;font-size:30px;letter-spacing:-.005em;margin:0;font-weight:700}
.dt{margin:2px 0 14px;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
 font-variant-numeric:tabular-nums}
.bar{position:relative;height:22px;background:var(--bartrack);border-radius:1px;margin-bottom:26px}
.blk{position:absolute;top:0;height:10px;background:var(--barfill);opacity:.85;border-radius:1px}
.tk{position:absolute;top:12px;font-size:10px;color:var(--muted);transform:translateX(-50%);
 font-family:"SF Mono",ui-monospace,Menlo,monospace}
.tk i{display:block;width:1px;height:4px;background:var(--line2);margin:0 auto 1px}
.gaps{margin:-16px 0 18px;font-size:12.5px;color:var(--ink2);font-family:"SF Mono",ui-monospace,Menlo,monospace}
.gaps span{text-transform:uppercase;letter-spacing:.11em;font-size:10px;color:var(--muted);
 font-family:inherit;margin-right:8px}

.evs{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px;background:var(--line)}
.ev{display:grid;grid-template-columns:74px 1fr;gap:18px;background:var(--surface);padding:14px 16px 15px}
.ev:hover{background:var(--raise)}
.when{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;
 text-align:right;padding-top:2px}
.when b{display:block;font-size:15px;font-weight:600;letter-spacing:-.02em}
.when span{display:block;font-size:11.5px;color:var(--muted)}
.ttl{margin:0 0 3px;font-size:17.5px;font-weight:600;line-height:1.28;text-wrap:balance}
.dsc{margin:0 0 8px;color:var(--ink2);font-size:14.5px;line-height:1.5;max-width:66ch}
.meta{margin:0;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:11.5px;
 color:var(--muted);text-transform:uppercase;letter-spacing:.06em;
 font-family:"Avenir Next Condensed","Arial Narrow",system-ui,sans-serif}
.chip{background:hsl(var(--h) var(--chipS) var(--chipL));color:hsl(var(--h) 55% var(--chipT));
 padding:2px 7px;border-radius:2px;font-weight:600;letter-spacing:.07em}
.loc{color:var(--ink2);font-weight:600}
.walk{font-family:"SF Mono",ui-monospace,Menlo,monospace;text-transform:none;letter-spacing:0}
.host{opacity:.75;text-transform:none;letter-spacing:0;font-style:italic;
 font-family:Charter,Palatino,Georgia,serif}
.flag{padding:2px 7px;border-radius:2px;font-weight:600;letter-spacing:.07em}
.oneshot{border:1px solid var(--accent);color:var(--accent)}
.clash{border:1px dashed var(--line2);color:var(--muted)}
.ev[hidden]{display:none}
.day.empty{display:none}
footer{margin-top:56px;border-top:1px solid var(--line);padding-top:18px;
 font-size:13px;color:var(--muted);max-width:70ch}
footer code{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:12px;
 background:var(--surface);padding:1px 5px;border-radius:2px;color:var(--ink2)}
@media (max-width:620px){ .ev{grid-template-columns:58px 1fr;gap:12px} .walkctl{margin-left:0;width:100%} }
@media (prefers-reduced-motion:reduce){ *{transition:none!important;animation:none!important} }
'''

JS = '''
const chips=[...document.querySelectorAll('.fchip')], slider=document.getElementById('wk'),
      out=document.getElementById('wkv'), evs=[...document.querySelectorAll('.ev')];
function apply(){
  const on=new Set(chips.filter(c=>c.classList.contains('on')).map(c=>c.dataset.t));
  const max=+slider.value; out.textContent = max>=35?'any':max+' min';
  evs.forEach(e=>{
    const w=+e.dataset.walk;
    e.hidden = !on.has(e.dataset.themeName) || (max<35 && w!==99 && w>max);
  });
  document.querySelectorAll('.day').forEach(d=>{
    d.classList.toggle('empty', ![...d.querySelectorAll('.ev')].some(e=>!e.hidden));
  });
}
chips.forEach(c=>c.addEventListener('click',()=>{c.classList.toggle('on');apply()}));
slider.addEventListener('input',apply); apply();
'''

doc=f'''<title>Axis Mundi Salon</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
 <h1>Axis Mundi<em>Salon</em></h1>
 <p class="sub">Every talk, lecture, death café, science hour and real conversation at Burning Man 2026 —
 filtered to the {len(S)} sessions that land between 5am and 11pm, measured on foot from 4:00 &amp; E.
 Pulled from the Dust dataset, which the app itself can't filter this way.</p>
 <div class="facts">
  <div><b>{len(S)}</b><span>sessions</span></div>
  <div><b>{len(set(e['title'] for e in S))}</b><span>distinct events</span></div>
  <div><b>3,408</b><span>screened from</span></div>
  <div><b>{sum(1 for e in S if e['n_occ']==1)}</b><span>one showing only</span></div>
  <div><b>{sorted(e['walk'] for e in S if e['walk'] is not None)[len(([e for e in S if e['walk'] is not None]))//2]}<small style="font-size:14px"> min</small></b><span>median walk</span></div>
 </div>
</header>

<div class="controls">
 <nav class="navdays">{nav}</nav>
 <div class="filters">{chips}
  <label class="walkctl">walk under <input id="wk" type="range" min="5" max="35" step="5" value="35"><output id="wkv">any</output></label>
 </div>
</div>

{''.join(rows)}

<footer>
<p><b>How to read it.</b> The bar under each day covers 5am–11pm; filled blocks are hours with something on,
and the <em>open</em> line lists every gap over an hour — that's your bike time, meal time, and Temple time.
<b>Only showing</b> means the event runs exactly once all week. <b>Overlaps</b> means it starts before the
previous listing ends, so you're choosing between them, not stacking them.</p>
<p>Walk times assume 80 m/min from the centroid of 4:00 &amp; E. Seventeen sessions have no GPS in the
source data (Center Camp stages, Temple grounds, open-playa coordinates) and show <code>walk n/a</code>.
Times are the official ones and will drift on playa — treat them as intentions, not guarantees.</p>
</footer>
</div>
<script>{JS}</script>'''
open(opath('salon.html'),'w',encoding='utf-8').write(doc)
print('wrote out/salon.html', len(doc),'bytes')

# -*- coding: utf-8 -*-
"""Inline payload.json + app_css.css + app_js.js into the single-file offline app."""
import os, json, datetime
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.dirname(os.path.abspath(__file__))
OUT   = os.path.join(ROOT, 'out')
b = lambda n: os.path.join(BUILD, n)

data = open(b('payload.json'), encoding='utf-8').read()
css  = open(b('app_css.css'),  encoding='utf-8').read()
js   = open(b('app_js.js'),    encoding='utf-8').read()
d    = json.loads(data)

DN = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
def label(iso):
    wd = datetime.date(*map(int, iso.split('-'))).weekday()   # Mon=0..Sun=6
    return DN[(wd + 1) % 7]
daybtn = ''.join(f'<button class="dp" data-day="{i}" aria-label="{label(x)} {x[8:]}">'
                 f'<b>{label(x)[0]}</b><i>{int(x[8:])}</i></button>'
                 for i, x in enumerate(d['days']))
tagbtn = ''.join(f'<button class="tb" data-tag="{i}">{t}</button>'
                 for i, t in enumerate(d['tags']))

HEAD = '''<title>Playa Brain</title>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<style>__CSS__</style>
<div class="wrap">
<div class="bar">
 <div class="row1">
  <h1>Playa<b>Brain</b></h1>
  <input id="q" type="search" placeholder="Search talks, camps, DJs&hellip;" autocomplete="off">
  <span class="cnt" id="cnt">&mdash;</span>
 </div>
 <div class="row2">
  <div class="seg" role="group" aria-label="What to show">
   <button class="sg on" id="mEv" aria-pressed="true">Events</button>
   <button class="sg" id="mMu" aria-pressed="false">&#9834; Sets</button>
  </div>
  <div class="days">__DAYS__</div>
  <button class="fbtn" id="bAdv" aria-expanded="false">Filters<span class="fc" id="fc" hidden></span></button>
 </div>
 <div class="sheet" id="adv">
  <section><h3>Interests</h3><div class="chips">__TAGS__</div></section>
  <section><h3>Show only</h3><div class="chips">
   <button class="tb star" id="bStar">&#9733; my picks</button>
   <button class="tb" id="bFav">saved</button>
   <button class="tb" id="bNow">on now</button>
   <button class="tb ver" id="bVer" title="A real, checkable person or institution">verified</button>
   <button class="tb gst" id="bGuest" title="Promises expertise but names nobody">guest?</button>
  </div></section>
  <section><h3>Hide</h3><div class="chips">
   <button class="tb nw" id="bWoo" title="Hide pseudo-science">pseudo-science</button>
  </div></section>
  <section class="ctl">
   <label>Hours<span class="v" id="tv"></span>
    <span class="rng"><input id="t0" type="range" min="0" max="23" value="0"><input id="t1" type="range" min="1" max="24" value="24"></span></label>
   <label>Walk under<span class="v" id="wv">any</span>
    <span class="rng"><input id="wk" type="range" min="5" max="99" step="5" value="99"></span></label>
   <label>Home GPS<input id="hm" type="text" spellcheck="false"></label>
  </section>
  <button class="clr" id="clr">Clear all filters</button>
 </div>
</div>
<ol id="out"></ol>
</div>
<script>const DATA=__DATA__;
__JS__
</script>'''

doc = (HEAD.replace('__CSS__', css).replace('__DAYS__', daybtn)
           .replace('__TAGS__', tagbtn).replace('__DATA__', data).replace('__JS__', js))
p = os.path.join(OUT, 'playabrain.html')
open(p, 'w', encoding='utf-8').write(doc)
print(f'wrote out/playabrain.html  {len(doc.encode())/1024:.0f} KB')

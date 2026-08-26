# -*- coding: utf-8 -*-
"""Probe the official Burning Man API and report what it adds over Dust.

    cp .env.example .env   # then paste your key in; .env is gitignored
    python3 build/bmapi.py            # compare 2026 against data/ we already have
    python3 build/bmapi.py --pull     # also write data/bm_api_*.json

Answers the question that decides whether a full re-pull is worth it: are the
official descriptions longer than the ~190 chars Dust ships? Every text-derived
tag in this repo (meals, showers, beauty, deep-talk, named speakers) is capped
by that limit.
"""
import os, sys, json, urllib.request, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
def load_env():
    """Read KEY=VALUE from .env at the repo root. No dependency, and the file
    is gitignored — this repo is public."""
    p = os.path.join(ROOT, '.env')
    if not os.path.exists(p): return
    mode = os.stat(p).st_mode
    if mode & 0o077:
        print(f'warning: .env is readable by others; run  chmod 600 {p}')
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()
KEY  = os.environ.get('BM_API_KEY')
BASE = 'https://api.burningman.org/api'
YEAR = int(os.environ.get('BM_YEAR', '2026'))

if not KEY:
    sys.exit('No BM_API_KEY. Either:\n'
             '  cp .env.example .env  &&  edit it\n'
             '  export BM_API_KEY=...')

def get(path, **q):
    q = {k: v for k, v in q.items() if v is not None}
    url = f'{BASE}/{path}?' + '&'.join(f'{k}={v}' for k, v in q.items())
    req = urllib.request.Request(url, headers={'X-API-Key': KEY,
                                               'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def lens(rows, field):
    v = [len(r.get(field) or '') for r in rows if r.get(field)]
    return (len(v), round(st.median(v)), max(v)) if v else (0, 0, 0)

print(f'--- official API, year {YEAR} ---')
ev = get('event', year=YEAR)
ca = get('camp',  year=YEAR)
ar = get('art',   year=YEAR)
try:
    mv = get('mv', year=YEAR)
except Exception as e:
    mv = []; print(f'  mv unavailable: {e}')
print(f'  events {len(ev)}   camps {len(ca)}   art {len(ar)}   mutant vehicles {len(mv)}')

print('\n--- THE question: description length ---')
for f in ('description', 'print_description'):
    n, med, mx = lens(ev, f)
    print(f'  event.{f:18} n={n:<5} median={med:<5} max={mx}')
try:
    dust = json.load(open(os.path.join(DATA, 'bm_events.json')))
    n, med, mx = lens(dust, 'description')
    print(f'  dust .description         n={n:<5} median={med:<5} max={mx}')
    best = max(('description', 'print_description'),
               key=lambda f: lens(ev, f)[1])
    gain = lens(ev, best)[1] / max(med, 1)
    print(f'\n  => official "{best}" is {gain:.1f}x Dust\'s median.')
    print('     Worth re-pulling.' if gain > 1.3 else '     Not worth re-pulling.')
except FileNotFoundError:
    pass

print('\n--- fields Dust drops ---')
for label, rows, fields in (('camp', ca, ('contact_email', 'location')),
                            ('event', ev, ('url', 'print_description', 'slug'))):
    for f in fields:
        got = sum(1 for r in rows if r.get(f))
        print(f'  {label}.{f:20} present on {got}/{len(rows)}')
if ca and isinstance(ca[0].get('location'), dict):
    print(f'  camp.location keys: {", ".join(ca[0]["location"].keys())}')

if '--pull' in sys.argv:
    for nm, rows in (('events', ev), ('camps', ca), ('art', ar), ('mv', mv)):
        p = os.path.join(DATA, f'bm_api_{nm}.json')
        json.dump(rows, open(p, 'w'), ensure_ascii=False)
        print(f'wrote data/bm_api_{nm}.json  {os.path.getsize(p)/1024:.0f} KB')

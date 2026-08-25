# -*- coding: utf-8 -*-
"""Re-pull the Burning Man dataset from the Dust API into data/."""
import os, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data'); os.makedirs(DATA, exist_ok=True)
DS   = os.environ.get('DUST_DATASET', 'ttitd-2026')       # Burning Man; see festivals.json for regionals
BASE = 'https://api.dust.events'
def get(url, dest):
    with urllib.request.urlopen(url, timeout=120) as r: body = r.read()
    open(dest, 'wb').write(body); print(f'{os.path.basename(dest):24} {len(body)/1024:>7.0f} KB')
for n in ('events', 'camps', 'art'):
    get(f'{BASE}/static/{DS}/{n}.json', os.path.join(DATA, f'bm_{n}.json'))
# RSL = the DJ lineup. Production ships an empty [] until the lineup is locked,
# so prefer the -dev feed and fall back to production if it ever overtakes it.
try:
    get(f'{BASE}/static/{DS}/rsl-dev.json', os.path.join(DATA, 'bm_rsl.json'))
except Exception as e:
    print('rsl-dev unavailable, falling back:', e)
    get(f'{BASE}/static/{DS}/rsl.json', os.path.join(DATA, 'bm_rsl.json'))
get(f'{BASE}/data/festivals.json',        os.path.join(DATA, 'festivals.json'))
get(f'{BASE}/static/datasets/datasets.json', os.path.join(DATA, 'ds2.json'))

# -*- coding: utf-8 -*-
"""Build an address -> GPS table for BRC, so the apps can ask for '4:00 & E'
instead of raw coordinates.

Two sources, in order of preference:
  1. the real camps at that address (median error 46 m, leave-one-out)
  2. a polar model fitted to all 1,042 addressed camps, for gaps (60 m)
"""
import os, sqlite3, math, json, statistics as st
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(ROOT, 'brc2026.db')); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute(
    "SELECT street,clock_min,lat,lng FROM camps WHERE street IS NOT NULL AND lat IS NOT NULL")]

def hav(a, b):
    R = 6371e3; p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
def bearing(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0]); dl = math.radians(b[1] - a[1])
    return (math.degrees(math.atan2(math.sin(dl)*math.cos(p2),
        math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl))) + 360) % 360

# --- fit the centre by minimising per-street radius spread
def spread(man):
    per = {}
    for r in rows: per.setdefault(r['street'], []).append(hav(man, (r['lat'], r['lng'])))
    return sum(st.pstdev(v) for v in per.values() if len(v) > 3)
man, best = (40.7864, -119.2035), None; best = spread(man); step = 0.0006
for _ in range(7):
    moved = True
    while moved:
        moved = False
        for d in ((step,0), (-step,0), (0,step), (0,-step)):
            c = (man[0]+d[0], man[1]+d[1]); s = spread(c)
            if s < best: man, best, moved = c, s, True
    step /= 3

rad, ang = {}, []
for r in rows:
    rad.setdefault(r['street'], []).append(hav(man, (r['lat'], r['lng'])))
    ang.append((r['clock_min'], bearing(man, (r['lat'], r['lng']))))
rad = {k: st.median(v) for k, v in rad.items() if len(v) > 3}

# The outermost streets (J: 15 camps, K: 9) are too thinly sampled for a stable
# median, and BRC's outer ring is partial — so their fitted radii can come out
# inverted. Radius must increase as you move outward; enforce that, using the
# median spacing of the well-sampled streets to repair any violation.
ORDER = [s for s in ['ESPLANADE','A','B','C','D','E','F','G','H','I','J','K','L'] if s in rad]
steps = [rad[b]-rad[a] for a, b in zip(ORDER, ORDER[1:]) if rad[b] > rad[a]]
step  = st.median(steps) if steps else 85.0
for a, b in zip(ORDER, ORDER[1:]):
    if rad[b] <= rad[a]:
        print(f'  repaired {b}: {rad[b]:.0f} -> {rad[a]+step:.0f} m (was inside {a})')
        rad[b] = rad[a] + step
ref = [((b - c*0.5) + 360) % 360 for c, b in ang]
B0 = math.degrees(math.atan2(sum(math.sin(math.radians(x)) for x in ref),
                             sum(math.cos(math.radians(x)) for x in ref))) % 360

def project(street, cm):
    r = rad.get(street)
    if not r: return None
    R = 6371e3; d = r/R; brg = math.radians(B0 + cm*0.5)
    p1, l1 = math.radians(man[0]), math.radians(man[1])
    p2 = math.asin(math.sin(p1)*math.cos(d) + math.cos(p1)*math.sin(d)*math.cos(brg))
    l2 = l1 + math.atan2(math.sin(brg)*math.sin(d)*math.cos(p1),
                         math.cos(d) - math.sin(p1)*math.sin(p2))
    return (math.degrees(p2), math.degrees(l2))

idx = {}
for r in rows: idx.setdefault(r['street'], []).append((r['clock_min'], r['lat'], r['lng']))
def lookup(street, cm):
    c = idx.get(street)
    if not c: return None
    near = [x for x in c if abs(x[0] - cm) <= 8]
    if not near: return None
    return (sum(x[1] for x in near)/len(near), sum(x[2] for x in near)/len(near))

STREETS = ['ESPLANADE','A','B','C','D','E','F','G','H','I','J','K','L']
table, exact = {}, 0
for s in STREETS:
    col = {}
    for cm in range(120, 601, 15):           # 2:00 -> 10:00 every 15 minutes
        p = lookup(s, cm)
        if p: exact += 1
        else: p = project(s, cm)
        if p: col[str(cm)] = [round(p[0], 5), round(p[1], 5)]
    if col: table[s] = col

LAND = {'The Man': [round(man[0],5), round(man[1],5)]}
for nm, q in (('Center Camp','Center Camp'),):
    r = con.execute("SELECT AVG(lat),AVG(lng) FROM camps WHERE location LIKE ?", (f'%{q}%',)).fetchone()
    if r and r[0]: LAND[nm] = [round(r[0],5), round(r[1],5)]

out = {'streets': STREETS, 'table': table, 'landmarks': LAND}
json.dump(out, open(os.path.join(BUILD,'geo.json'),'w'), separators=(',',':'))
n = sum(len(v) for v in table.values())
print(f'man     {man[0]:.5f}, {man[1]:.5f}')
print(f'bearing {B0:.2f} deg + 0.5 deg/min')
print(f'table   {n} addresses ({exact} from real camps, {n-exact} projected)')
print(f'size    {os.path.getsize(os.path.join(BUILD,"geo.json"))/1024:.1f} KB')

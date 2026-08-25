import os
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(ROOT, 'data')
OUT   = os.path.join(ROOT, 'out')
BUILD = os.path.dirname(os.path.abspath(__file__))
DB    = os.path.join(ROOT, 'brc2026.db')
def dpath(n): return os.path.join(DATA, n)
def bpath(n): return os.path.join(BUILD, n)
def opath(n): return os.path.join(OUT, n)
import sqlite3, math, re, json
HOME = (40.772262, -119.204136)   # centroid, 4:00 & E
def hav(a,b):
    R=6371000.0; p1,p2=math.radians(a[0]),math.radians(b[0])
    dp,dl=p2-p1,math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

con=sqlite3.connect(DB); con.row_factory=sqlite3.Row

# broad net for "deep talk & ideas"
STRONG = r'''philosoph|salon|lecture|symposium|panel discussion|debate|discourse|dialogue|
socratic|existential|consciousness|epistem|metaphys|ontolog|death cafe|grief|mortality|dying|
bereave|neuroscien|cosmolog|astrophys|quantum|anthropolog|sociolog|psycholog|ethic|moral|
storytelling|story slam|memoir|oral history|book club|reading group|q&a|ask me anything|
fireside chat|think tank|intellectual|academic|seminar|colloqui|essay|discussion group|
deep conversation|meaningful conversation|conversation about|talk about|speaker series|ted ?talk|
futurism|sensemaking|first principles|critical thinking|logic|rhetoric|mytholog|theolog|
spiritual inquiry|inquiry|contemplat|wisdom|meaning of life|purpose|identity|politics|economic|
history of|science of|psychedelic (science|integration|research)|artificial intelligence|
\bai\b|technology and|ethics of|climate|sustainab|activism|justice|decolon|gender|sexuality studies|
mens? (group|circle)|womens? circle|sharing circle|listening|authentic relating|circling|
nonviolent communication|nvc|vulnerab|human condition|why we|what is|how to think'''
STRONG = re.compile('|'.join(x.strip() for x in STRONG.split('|')), re.I|re.X)

# things that mean "this is a party/food/sex thing that merely used a keyword"
NOISE = re.compile(r'\b(dj|beats|bass|dance ?floor|open bar|bloody mary|mimosa|pancake|'
                   r'grilled cheese|bacon|snow ?cone|margarita)\b', re.I)

rows = con.execute('''
SELECT e.*, (SELECT GROUP_CONCAT(o.dow||' '||substr(o.start,12,5)||'-'||substr(o.end,12,5),' | ')
             FROM occ o WHERE o.event_uid=e.uid
               AND CAST(substr(o.start,12,2) AS INT) BETWEEN 5 AND 22) AS times,
       (SELECT COUNT(*) FROM occ o WHERE o.event_uid=e.uid
          AND CAST(substr(o.start,12,2) AS INT) BETWEEN 5 AND 22) AS n_wake
FROM events e''').fetchall()

out=[]
for r in rows:
    if not r['n_wake']: continue                       # nothing in 05:00-22:59
    blob = ' '.join(filter(None,[r['title'], r['description']]))
    hits = set(m.group(0).lower() for m in STRONG.finditer(blob))
    if not hits: continue
    body = (r['description'] or '')
    if NOISE.search(blob) and len(hits) < 2: continue
    d = hav(HOME,(r['lat'],r['lng'])) if r['lat'] else None
    out.append({'uid':r['uid'],'title':r['title'],'type':r['event_type'],
                'host':r['host_name'],'loc':r['location'],
                'walk_min': round(d/80.0,1) if d else None,   # 80 m/min walking
                'times':r['times'],'n_occ':r['n_occurrences'],
                'hits':sorted(hits)[:6],'desc':body})
out.sort(key=lambda x:(x['walk_min'] is None, x['walk_min'] or 0))
json.dump(out, open(bpath('candidates.json'),'w'), indent=1)
print(f'candidates: {len(out)} of {len(rows)} events')
from collections import Counter
print(Counter(c['type'] for c in out).most_common())

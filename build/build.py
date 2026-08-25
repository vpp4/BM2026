import os
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(ROOT, 'data')
OUT   = os.path.join(ROOT, 'out')
BUILD = os.path.dirname(os.path.abspath(__file__))
DB    = os.path.join(ROOT, 'brc2026.db')
def dpath(n): return os.path.join(DATA, n)
def bpath(n): return os.path.join(BUILD, n)
def opath(n): return os.path.join(OUT, n)
import json, sqlite3, re, math

def load(n): return json.load(open(dpath(n)))

events, camps, art = load('bm_events.json'), load('bm_camps.json'), load('bm_art.json')

# The Man, BRC 2026 (derived below from camp GPS centroid fallback)
MAN = (40.786400, -119.203500)

def hav(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

# location_string looks like "A & 4:45", "Esplanade & 7:30", or plaza/landmark text
A = re.compile(r'^\s*(.+?)\s*&\s*(\d{1,2}):(\d{2})\s*$')   # "E & 4:00"
B = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*&\s*(.+?)\s*$')     # "4:00 & E"
def parse_loc(s):
    s = s or ''
    m = B.match(s)
    if m: return (m.group(3).strip().upper(), int(m.group(1)) % 12 * 60 + int(m.group(2)))
    m = A.match(s)
    if m: return (m.group(1).strip().upper(), int(m.group(2)) % 12 * 60 + int(m.group(3)))
    return (None, None)

campmap = {c['uid']: c for c in camps}
artmap  = {a['uid']: a for a in art}

con = sqlite3.connect(DB)
con.executescript('''
DROP TABLE IF EXISTS occ; DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS camps; DROP TABLE IF EXISTS art;
DROP TABLE IF EXISTS ev_fts;
DROP INDEX IF EXISTS i1; DROP INDEX IF EXISTS i2;
DROP INDEX IF EXISTS i3; DROP INDEX IF EXISTS i4;
CREATE TABLE events(
  uid TEXT PRIMARY KEY, title TEXT, description TEXT, event_type TEXT,
  host_uid TEXT, host_name TEXT, host_kind TEXT, host_desc TEXT, host_url TEXT,
  location TEXT, street TEXT, clock_min INTEGER, lat REAL, lng REAL,
  dist_from_man_m REAL, contact TEXT, n_occurrences INTEGER, total_hours REAL);
CREATE TABLE occ(
  id INTEGER PRIMARY KEY, event_uid TEXT, start TEXT, end TEXT,
  day TEXT, dow TEXT, start_hour REAL, end_hour REAL, duration_h REAL, overnight INTEGER);
CREATE TABLE camps(uid TEXT PRIMARY KEY, name TEXT, description TEXT, url TEXT,
  hometown TEXT, location TEXT, street TEXT, clock_min INTEGER, lat REAL, lng REAL,
  dist_from_man_m REAL, landmark TEXT, facing TEXT, accepting_campers INTEGER, n_events INTEGER);
CREATE TABLE art(uid TEXT PRIMARY KEY, name TEXT, artist TEXT, description TEXT,
  category TEXT, art_type TEXT, tags TEXT, hometown TEXT, location TEXT,
  lat REAL, lng REAL, dist_from_man_m REAL, url TEXT, needs_volunteers INTEGER);
''')

DOW = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
def hourf(t):  # "2026-08-31T18:00:00" -> 18.0
    return int(t[11:13]) + int(t[14:16])/60.0

for c in camps:
    st, cm = parse_loc(c.get('location_string'))
    g = c.get('gps') or {}
    lat, lng = g.get('lat'), g.get('long')
    con.execute('INSERT OR REPLACE INTO camps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)', (
        c['uid'], c.get('name'), c.get('description'), c.get('url'), c.get('hometown'),
        c.get('location_string'), st, cm, lat, lng,
        hav(MAN, (lat, lng)) if lat else None,
        c.get('landmark'), c.get('facing'), 1 if c.get('accepting_campers') else 0))

for a in art:
    g = a.get('location') or {}
    lat, lng = g.get('gps_latitude'), g.get('gps_longitude')
    con.execute('INSERT OR REPLACE INTO art VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
        a['uid'], a.get('name'), a.get('artist'), a.get('description'),
        a.get('category'), a.get('art_type'),
        ','.join(a.get('tags') or []) if isinstance(a.get('tags'), list) else a.get('tags'),
        a.get('hometown'), a.get('location_string'), lat, lng,
        hav(MAN, (lat, lng)) if lat else None,
        a.get('url'), 1 if a.get('needs_volunteers') else 0))

oid = 0
for e in events:
    host_uid = e.get('hosted_by_camp') or e.get('located_at_art')
    kind = name = desc = url = loc = st = None
    cm = lat = lng = dist = None
    if e.get('hosted_by_camp') and e['hosted_by_camp'] in campmap:
        c = campmap[e['hosted_by_camp']]; kind = 'camp'
        name, desc, url = c.get('name'), c.get('description'), c.get('url')
        loc, (st, cm) = c.get('location_string'), parse_loc(c.get('location_string'))
        g = c.get('gps') or {}; lat, lng = g.get('lat'), g.get('long')
    elif e.get('located_at_art') and e['located_at_art'] in artmap:
        a = artmap[e['located_at_art']]; kind = 'art'
        name, desc, url = a.get('name'), a.get('description'), a.get('url')
        loc = a.get('location_string')
        g = a.get('location') or {}
        lat, lng = g.get('gps_latitude'), g.get('gps_longitude')
    if e.get('other_location'): loc = loc or e['other_location']
    if lat: dist = hav(MAN, (lat, lng))

    occs = e.get('occurrence_set') or []
    tot = 0.0
    for o in occs:
        s, en = o.get('start_time'), o.get('end_time')
        if not s or not en: continue
        sh, eh = hourf(s), hourf(en)
        dur = (eh - sh) % 24 or 24.0
        if s[:10] != en[:10] and eh <= sh: dur = (24 - sh) + eh
        tot += dur
        oid += 1
        con.execute('INSERT INTO occ VALUES(?,?,?,?,?,?,?,?,?,?)', (
            oid, e['uid'], s, en, s[:10], DOW[__import__('datetime').date(
                int(s[:4]), int(s[5:7]), int(s[8:10])).weekday()],
            sh, eh, round(dur, 2), 1 if s[:10] != en[:10] else 0))

    con.execute('INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
        e['uid'], e.get('title'), e.get('description'),
        (e.get('event_type') or {}).get('label'),
        host_uid, name, kind, desc, url, loc, st, cm, lat, lng, dist,
        e.get('contact'), len(occs), round(tot, 2)))

con.execute('UPDATE camps SET n_events=(SELECT COUNT(*) FROM events WHERE events.host_uid=camps.uid)')
con.executescript('''
CREATE INDEX i1 ON occ(day); CREATE INDEX i2 ON occ(start_hour);
CREATE INDEX i3 ON occ(event_uid); CREATE INDEX i4 ON events(event_type);
CREATE VIRTUAL TABLE ev_fts USING fts5(uid UNINDEXED, title, description, host_name, host_desc);
''')
con.execute('INSERT INTO ev_fts SELECT uid,title,description,host_name,host_desc FROM events')
con.commit()
for t in ('events','occ','camps','art'):
    print(t, con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0])

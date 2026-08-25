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
import json, re, sqlite3, datetime

ev=json.load(open(dpath('bm_events.json'))); ca=json.load(open(dpath('bm_camps.json'))); ar=json.load(open(dpath('bm_art.json')))
try: rsl=json.load(open(dpath('bm_rsl.json')))
except Exception: rsl=[]
campmap={c['uid']:c for c in ca}; artmap={a['uid']:a for a in ar}
picks={x['title'] for x in json.load(open(bpath('schedule.json')))}

CATS=['Class/Workshop','Music/Party','Other','Beverages','Food','Arts & Crafts','Mature Audiences','Kids Activities','DJ set']
DAYS=['2026-08-30','2026-08-31','2026-09-01','2026-09-02','2026-09-03','2026-09-04','2026-09-05','2026-09-06','2026-09-07']

# automatic interest tags across ALL 3408 events
TAGS=[
 ('Talks & ideas', r'philosoph|salon|lecture|symposium|panel|debate|discourse|dialogue|socratic|discussion|'
                   r'\btalks?\b|speaker|q&a|ask me anything|fireside|seminar|forum|roundtable|epistem|existential|'
                   r'consciousness|ethic|meaning of|why we|what is|conversation'),
 ('Science & nerd', r'science|scientist|neuroscien|quantum|physics|astronom|geolog|biolog|chemis|math|research|'
                    r'professor|\bphd\b|data|engineer|robot|climate|ecolog|evolution|space|telescope|census|nerd'),
 ('AI',            r'\bai\b|\ba\.i\.|artificial intelligence|machine learning|\bllm\b|chatgpt|agi|algorithm'),
 ('Death & grief', r'death|dying|grief|griev|mortality|bereave|loss of|funeral|memorial|temple burn|empty chair'),
 ('Storytelling',  r'storytell|story slam|\bstories\b|open mic|poetry|poem|spoken word|memoir|narrative|improv'),
 ('Music & party', r'\bdj\b|dance|beats|bass|techno|house music|live set|concert|band|karaoke|jam|sound camp|rave|disco'),
 ('Food & drink',  r'coffee|tea\b|breakfast|pancake|bacon|dinner|lunch|snack|cocktail|whiskey|beer|wine|margarita|'
                   r'smoothie|grilled|pizza|taco|bar\b|booze|mimosa|kombucha|ice cream|popsicle'),
 ('Body & moving', r'yoga|dance class|acro|stretch|massage|breathwork|somatic|qigong|tai chi|martial|pilates|'
                   r'aerial|pole|hoop|flow art|run\b|workout|sound bath|meditat'),
 ('Sex & intimacy',r'sex|erotic|intimacy|tantra|tantric|bdsm|kink|shibari|cuddle|nude|naked|orgasm|consent|'
                   r'polyamor|non-monogam|play party|strap|seduc'),
 ('Craft & making',r'workshop.*make|build|craft|sew|knit|weld|repair|fix|solder|paint|draw|print|jewelry|'
                   r'leather|woodwork|blacksmith|3d print|costume|hat\b|tie.?dye'),
 ('Games & puzzle',r'trivia|game|puzzle|chess|crossword|bingo|tournament|cards|poker|scavenger|contest|competition'),
 ('Healing & woo', r'heal|reiki|tarot|astrolog|oracle|chakra|shaman|energy work|aura|crystal|psychic|ceremon|ritual'),
 ('Queer & id',    r'queer|\blgbt|trans\b|transgender|nonbinary|non-binary|genderqueer|two spirit|gay|lesbian|'
                   r'\bbi\b|drag|pride|\bpoc\b|people of color|indigenous|disabilit|neurodiver|sober|recovery'),
 ('Kids & family', r'kids|children|family|teen|youth|parent'),
]
TAGS=[(n,re.compile(p,re.I)) for n,p in TAGS]

# --- provenance flags -------------------------------------------------------
# v = a real, checkable person or institution stands behind it (hand-verified)
VERIFIED = {
 "Therapy in Psychedelic Treatments",        # Rick Doblin, founder of MAPS
 "Opening Fire Ritual",                      # Crimson Rose, Burning Man co-founder
 "Two Spirit Wisdom",                        # Dean Barlese, Northern Paiute elder
 "You're on Paiute Land. Meet an Elder.",    # Dean Barlese
 "The Wisdom of Elephants",                  # Philip Price, conservationist
 "Geology of the Black Rock Desert",         # UC Davis geologist
 "Geology of the West with Astro Dave",
 "Experience a Playa Deep Time Bike Tour",
 "Ask an Astronomer-Black Rock Observatory", # Black Rock Observatory
 "Tortoise Talk",                            # Mojave Desert tortoise biologists
 "The quantum amplituhedron w/ Stan",        # real object in particle physics
 "The Neuroscience of Psychedelics + Q&A",
 "Stabilizing the Climate: Sunshades",
 "The Emerging Clean Tech Revolution",
 "Unearthing Data Centers",
 "Sustainable Food Systems",
 "DataBash: BRC Census & Researchers",       # the actual BRC Census
 "DataBash: Get Nerdy with Burning Nerds!",
 "Phage Talks",
 "Director of Event Operations Interview",   # BRC staff
 "Meet the Man Base Build Krewe Talk, Q&A",
 "Art Speaks: Artist Storytelling",          # official Burning Man artist-talk series
 "TEDX Black Rock City - Reunion Talks",
}
# u = promises expertise but names nobody — worth checking when late announcements land
UNNAMED = re.compile(r'special guest|guest speaker|surprise guest|renowned|world.?class|acclaimed|'
 r'leaders? in|leading|pioneer|expert(s)? (in|on|from)|serial founder|founders? (of|building)|'
 r'lightning talk|speaker series|keynote|panel(ist)?s?\b|award.?winning|internationally|'
 r'to be announced|\btba\b|neuroscientist|policy expert|conservationist|scientists?\b|researchers?\b', re.I)
# w = pseudo-science markers
WOO = re.compile(r'quantum (magic|consciousness|breakthrough|healing)|manifest(ing|ation)?\b|telepath|'
 r'reality transurfing|pranic|akashic|starseed|light language|energy (healing|awakening|work)|'
 r'chakra|\baura\b|psychic|sacred geometry|vibrational frequency|law of attraction|ascension|'
 r'channel(ing|ed)|infinite intelligence|swami|attuned water|life force energy|'
 r'nobel peace prize nominee|crystal healing|third eye', re.I)



def r5(x): return round(x,5) if x is not None else None

out=[]
for e in ev:
    kind=name=loc=None; lat=lng=None
    if e.get('hosted_by_camp') in campmap:
        c=campmap[e['hosted_by_camp']]; kind=0; name=c.get('name'); loc=c.get('location_string')
        g=c.get('gps') or {}; lat,lng=g.get('lat'),g.get('long')
    elif e.get('located_at_art') in artmap:
        a=artmap[e['located_at_art']]; kind=1; name=a.get('name'); loc=a.get('location_string')
        g=a.get('location') or {}; lat,lng=g.get('gps_latitude'),g.get('gps_longitude')
    if not loc and e.get('other_location'): loc=e['other_location']

    occ=[]
    for o in (e.get('occurrence_set') or []):
        s,en=o.get('start_time'),o.get('end_time')
        if not s or not en or s[:10] not in DAYS: continue
        sm=int(s[11:13])*60+int(s[14:16]); em=int(en[11:13])*60+int(en[14:16])
        if en[:10]!=s[:10]: em+=1440*(DAYS.index(en[:10])-DAYS.index(s[:10])) if en[:10] in DAYS else 1440
        occ.append([DAYS.index(s[:10]),sm,em])
    if not occ: continue

    blob=' '.join(filter(None,[e.get('title'),e.get('description')]))
    tg=[i for i,(n,rx) in enumerate(TAGS) if rx.search(blob)]
    rec={'t':e.get('title'),'d':e.get('description') or '','c':CATS.index(e['event_type']['label']),
         'o':occ,'g':tg}
    if name: rec['h']=name
    if loc:  rec['l']=loc
    if lat:  rec['p']=[r5(lat),r5(lng)]
    if kind==1: rec['a']=1
    if e.get('title') in picks: rec['s']=1
    lab=e['event_type']['label']
    woo = bool(WOO.search(blob))
    if e.get('title') in VERIFIED: rec['v']=1
    if woo: rec['w']=1
    elif UNNAMED.search(blob) and lab in ('Class/Workshop','Other'): rec['u']=1
    out.append(rec)


# ---------------------------------------------------------------- DJ lineup --
# The only genre signal available is the venue: RSL carries artist + time but no
# genre, so the camp's own description is what classifies the room.
MEL = re.compile(r'deep house|organic house|afro ?house|melodic|downtempo|down.?tempo|ambient|'
 r'chill|sunrise|sunset|jazz|soul|funk|nu.?disco|world music|minimal|progressive|balearic|'
 r'lounge|acoustic|piano|strings|groov', re.I)
BASS = re.compile(r'dubstep|riddim|hardstyle|psytrance|drum ?(and|n|&) ?bass|\bdnb\b|'
 r'bass music|heavy bass|\brave\b|hard techno|gabber|\bedm\b|banger|filthy|headbang', re.I)
# artists whose names I can actually vouch for in this genre space
KNOWN_MEL = re.compile(r'Tycho|Parra for Cuva|Seth Schwarz|Xinobi|Igor Marijuan|Museus|H[aä]ana|'
 r'Rodriguez Jr|Moldover|Bedouin|Acid Pauli|Nicola Cruz|Lee Burridge|Bonobo|Monolink|'
 r'Ben B[oö]hmer|Lane 8|Christian L[oö]ffler|Nils Frahm|Jan Blomqvist|Be Svendsen|Satori', re.I)

MEL_TAG, BASS_TAG = len(TAGS), len(TAGS)+1
campdesc = {c['uid']: (c.get('description') or '') for c in ca}
campgps  = {c['uid']: c.get('gps') for c in ca}
campname = {}
for c in ca:
    if c.get('name'): campname[c['name']] = c

n_music = 0
for x in rsl:
    venue = x.get('camp') or x.get('artCar') or ''
    cid   = x.get('campId')
    desc  = campdesc.get(cid) or (campname.get(venue, {}).get('description') or '')
    g     = campgps.get(cid) or (campname.get(venue, {}).get('gps') or {})
    lat, lng = (g or {}).get('lat'), (g or {}).get('long')
    vibe  = MEL.search(desc) and not BASS.search(desc)
    heavy = bool(BASS.search(desc))
    for o in (x.get('occurrences') or []):
        who = (o.get('who') or '').strip()
        st, en = o.get('startTime') or '', o.get('endTime') or ''
        if not who or not st or st[:10] not in DAYS: continue
        di = DAYS.index(st[:10])
        sm = int(st[11:13])*60 + int(st[14:16])
        if en:
            em = int(en[11:13])*60 + int(en[14:16])
            if en[:10] != st[:10]: em += 1440
        else:
            em = sm + 60
        tags = []
        known = bool(KNOWN_MEL.search(who))
        if vibe or known: tags.append(MEL_TAG)
        if heavy and not known: tags.append(BASS_TAG)
        rec = {'t': who, 'd': f'DJ set at {venue}' if venue else 'DJ set',
               'c': CATS.index('DJ set'), 'o': [[di, sm, em]], 'g': tags, 'm': 1}
        if venue: rec['h'] = venue
        if x.get('location'): rec['l'] = x['location']
        if lat: rec['p'] = [r5(lat), r5(lng)]
        if known: rec['v'] = 1
        out.append(rec); n_music += 1

geo=json.load(open(bpath('geo.json')))
data={'geo':geo,'days':DAYS,'cats':CATS,'tags':[n for n,_ in TAGS]+['Melodic & organic','Bass & rave'],'ev':out}

raw=json.dumps(data,separators=(',',':'),ensure_ascii=False)
open(bpath('payload.json'),'w',encoding='utf-8').write(raw)
import gzip,base64
gz=gzip.compress(raw.encode(),9)
print(f"records kept    : {len(out)}  (events {len(out)-n_music}, DJ sets {n_music})")
print(f"  verified real   : {sum(1 for r in out if r.get('v'))}")
print(f"  unnamed guest?  : {sum(1 for r in out if r.get('u'))}")
print(f"  woo-flagged     : {sum(1 for r in out if r.get('w'))}")
print(f"payload minified : {len(raw.encode())/1024:.0f} KB")
print(f"payload gzipped  : {len(gz)/1024:.0f} KB")
print(f"gzip+base64      : {len(base64.b64encode(gz))/1024:.0f} KB")
from collections import Counter
c=Counter(t for r in out for t in r['g'])
print('\ntag coverage:'); [print(f"   {data['tags'][i]:16} {n}") for i,n in c.most_common()]
print(f"   {'(untagged)':16} {sum(1 for r in out if not r['g'])}")

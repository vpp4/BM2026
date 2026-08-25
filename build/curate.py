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
import sqlite3, math, json
HOME=(40.772262,-119.204136)
def hav(a,b):
    R=6371000.0;p1,p2=math.radians(a[0]),math.radians(b[0])
    dp,dl=p2-p1,math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

PICKS = {
 # title : theme
 'Street Epistemology':'Philosophy','Consequences of a Gnostic Neuron':'Philosophy',
 'Gnostic Neuron':'Philosophy','Conundrum Clinic: Principles Collide':'Philosophy',
 'Parley! (Guided Conversations)':'Philosophy','Beyond Small Talk':'Philosophy',
 'No Small Talk':'Philosophy','Deep Talk: Strip Your Soul Bare':'Philosophy',
 'Radical Connection Circle':'Philosophy','The Human Design':'Philosophy',
 'Consciousness, Love & Happiness':'Philosophy','You belong here':'Philosophy',
 'Mother Nature is Pregnant. We are her it':'Philosophy',
 'Wizard Talks':'Lecture','Phage Talks':'Lecture','Disorient Talks':'Lecture',
 'TEDX Black Rock City - Reunion Talks':'Lecture','Drunk History Talks':'Lecture',
 'Tent Talks with Catfish':'Lecture','LongeviTEA talks':'Lecture',
 'Ask an Astronomer-Black Rock Observatory':'Science','Tortoise Talk':'Science',
 'The quantum amplituhedron w/ Stan':'Science','Quantum Tangerines':'Science',
 'Science Open Mic':'Science','Cinnamon rolls and math':'Science',
 'Geology of the Black Rock Desert':'Science','Geological perspective on climate change':'Science',
 'Experience a Playa Deep Time Bike Tour':'Science',
 'The Black Rock Desert:Our Inspiring Home':'Science',
 'Your Very Smart and Very Dumb Brain 101':'Science',
 'The Festival Effect: Brain & Belonging':'Science',
 'The Neuroscience of Psychedelics + Q&A':'Science',
 'The Neuroscience of Changing the World':'Science',
 'The Science of Human Flourishing':'Science','The Science behind human flourishing':'Science',
 'Precision Health Promotion':'Science','Academics Anonymous Support Circle':'Science',
 'DataBash: BRC Census & Researchers':'Science','DataBash: Get Nerdy with Burning Nerds!':'Science',
 "MDMA Therapy: What's Next?":'Science','Psychedelics & Medicine':'Science',
 'Psychedelic States':'Science','Psychedelics: Trust, Policy & Future':'Science',
 'Ego Death, Harm Reduction, & Connection':'Science',
 'AI & The Culture':'AI & society','The (AI)xis Mundi: What is Intelligence?':'AI & society',
 'Cooperation as Operating System of Life':'AI & society','AI Art: Mentor, Mirror, or Monster?':'AI & society',
 'What Are Burners Creating with AI?':'AI & society','Is a Flourishing World Possible with AI?':'AI & society',
 'Neuroscience, Creativity and AI':'AI & society','AI, Art, and the Future':'AI & society',
 'Culture & AI: A Matrilineal Case Study':'AI & society','Radical Humanity in the Age of AI':'AI & society',
 'The Last Human Advantage':'AI & society','AI, Tech & Society Panel':'AI & society',
 'Shifting States':'AI & society','From Scarcity to Abundance':'AI & society',
 'Beyond Hierarchy: A New OS for Humanity':'AI & society','AI Office Hours-Bring Your Weird Problem':'AI & society',
 'Unearthing Data Centers':'AI & society','No Datacenters in BRC Rally':'AI & society',
 'Death Cafe':'Death & grief','Death Cafe: A Grief Gathering':'Death & grief',
 'What the Dying Teach the Living':'Death & grief','How to Die Before You Die':'Death & grief',
 'Grief Circles at Center Camp':'Death & grief','The Empty Chair':'Death & grief',
 'What to leave at the Temple on Playa':'Death & grief','Microdosing Death':'Death & grief',
 'Catheric Writing Workshop':'Death & grief',
 'Art Speaks: Artist Storytelling':'Storytelling','Stories Under The Dome':'Storytelling',
 'Storytelling Hour':'Storytelling','Storytelling: A Radical Gift of Hope':'Storytelling',
 'An Immersive Storytelling Experience':'Storytelling','Paranormal Storytelling Happy Hour':'Storytelling',
 'Strictly Clownfidential Storytelling':'Storytelling','Storytelling Trading Booth':'Storytelling',
 'Poetry Pavilion':'Storytelling','The Three Lives Project':'Storytelling',
 'Meet the Man Base Build Krewe Talk, Q&A':'Storytelling',
 'Creating Community (Speaker Series)':'Culture & land',
 "You're on Paiute Land. Meet an Elder.":'Culture & land','Two Spirit Wisdom':'Culture & land',
 'The Wisdom of Elephants':'Culture & land','Indigenous-led Rights of Nature':'Culture & land',
 'History of LNT & Its Relationship to BM':'Culture & land','Incubating a Better World':'Culture & land',
 'Participation Changes Everything':'Culture & land','Mythological You!':'Culture & land',
 'Jazz History Workshop':'Culture & land','Jazz History Workshop 2':'Culture & land',
 'Talk Series: About Sustainability':'Climate & tech','Sustainable Food Systems':'Climate & tech',
 'Stabilizing the Climate: Sunshades':'Climate & tech','The Emerging Clean Tech Revolution':'Climate & tech',
 "What's All This Plastic?!?":'Climate & tech',
 'Update on BRC Sustainability Roadmap':'Climate & tech','Solar Maxing':'Climate & tech',
 'Navigating conflict with grace':'Conversation craft','Healing Relationships - Beginning Anew':'Conversation craft',
 'Circling: Real Connection Lab':'Conversation craft','Authentic Relating Workshop':'Conversation craft',
 'The Language of Connection':'Conversation craft',
 'Cryptic Crossword Meetup':'Games for the brain','Chess Simultan':'Games for the brain',
 'Actually Fun Trivia':'Games for the brain','Puzzle Therapy':'Games for the brain',
 'Word Game Meetups and Tournaments':'Games for the brain','QLC Counseling':'Games for the brain',
}

con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
rows=con.execute('''SELECT e.uid,e.title,e.description,e.event_type,e.host_name,e.location,
 e.lat,e.lng,e.n_occurrences,o.day,o.dow,o.start,o.end,o.start_hour,o.duration_h
 FROM events e JOIN occ o ON o.event_uid=e.uid''').fetchall()

out=[]; seen=set(); matched=set()
for r in rows:
    t=r['title']
    if t not in PICKS: continue
    matched.add(t)
    if not (5 <= r['start_hour'] < 23): continue          # your 5am-11pm window
    k=(t,r['start'])
    if k in seen: continue
    seen.add(k)
    d=hav(HOME,(r['lat'],r['lng'])) if r['lat'] else None
    out.append({'title':t,'theme':PICKS[t],'desc':r['description'],'type':r['event_type'],
      'host':r['host_name'],'loc':r['location'],'day':r['day'],'dow':r['dow'],
      'start':r['start'][11:16],'end':r['end'][11:16],'sh':r['start_hour'],
      'dur':r['duration_h'],'walk':round(d/80.0) if d else None,'n_occ':r['n_occurrences']})

missing=[t for t in PICKS if t not in matched]
out.sort(key=lambda x:(x['day'],x['sh']))
json.dump(out,open(bpath('schedule.json'),'w'),indent=1)
print(f'picked titles: {len(PICKS)-len(missing)}/{len(PICKS)}   sessions in your hours: {len(out)}')
if missing: print('NOT FOUND (title mismatch):'); [print('   ',m) for m in missing]

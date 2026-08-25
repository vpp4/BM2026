# Burning Man 2026 — "Axis Mundi" event data

Everything needed to re-cut the event picks or rebuild the offline app, with no
network access required (the raw API pulls are already in `data/`).

Source: the [Dust](https://github.com/damiant/dust) app's public API. No auth.
  https://api.dust.events/static/ttitd-2026/{events,camps,art}.json   Burning Man
  https://api.dust.events/data/festivals.json                         60+ regional burns

## Layout

    data/               raw API pulls, untouched — the provenance snapshot
    build/              the pipeline + its intermediates
    out/                the two finished pages
    brc2026.db          SQLite: events, occ, camps, art, ev_fts (gitignored)

`data/` is committed on purpose — api.dust.events will not serve 2026 forever —
with one exception: `bm_rsl.json`, the DJ lineup, is gitignored because it is
pre-release (production still returns `[]`). Run `fetch.py` to pull it.

`out/` is committed — the built pages are the point of the repo. Download
`out/playabrain.html` and open it in any browser; that single file is the whole
tool, offline, no clone or Python required.

## Pipeline

Each step reads the previous one's output. Run from anywhere; paths self-resolve.

    python3 build/fetch.py       # OPTIONAL: re-pull from the API into data/
                                 #   (also grabs the DJ lineup; prefers rsl-dev.json,
                                 #    since production still serves an empty [])
    python3 build/build.py       # data/*.json      -> brc2026.db          (idempotent)
    python3 build/shortlist.py   # brc2026.db       -> build/candidates.json
    python3 build/curate.py      # brc2026.db       -> build/schedule.json
    python3 build/gen.py         # schedule.json    -> out/salon.html
    python3 build/payload.py     # data + schedule  -> build/payload.json
    python3 build/assemble.py    # payload+css+js   -> out/playabrain.html

`fetch.py` honours `DUST_DATASET` if you want a regional instead:
`DUST_DATASET=soak-2026 python3 build/fetch.py` — check `data/festivals.json` for ids.

## The two outputs

**out/playabrain.html** (741 KB) — offline search over all 3,408 events. Single file,
no server, no network. Tags, time-of-day, walk distance from an editable home GPS,
"on now" against the device clock, favourites in localStorage.
AirDrop to phone, save to Files, open in Safari.

**out/salon.html** (123 KB) — the curated deep-talk itinerary: 164 sessions, 05:00–23:00,
day by day, with free-window bars and overlap flags.

## Where the judgement calls live

- `build/curate.py` — `PICKS`, the 112 hand-picked titles and their themes. Edit here
  to re-cut the itinerary for different interests.
- `build/payload.py` — `TAGS`, the 14 keyword-derived interest tags applied to all 3,408
  events. Rough by design; the full-text search is what actually covers the long tail.
- `build/shortlist.py` — `HOME`, and the first-pass keyword net. **Its recall is poor
  on its own** — it returned 155 candidates and missed many good ones. `build/missed.txt`
  is the 1,517 events it rejected, kept precisely so the second pass stays possible.

## Gotchas found in the source data

- Addresses come in both orders: `E & 4:00` *and* `4:00 & E`. `parse_loc()` handles both.
- 142 camps use plaza/portal addresses that don't parse into street+clock. They still
  carry GPS, so distances are fine.
- Camp records include a `border` polygon that is 57% of the camps file and useless
  here — dropped in `payload.py`.
- 17 curated sessions have no GPS at all (Center Camp stages, Temple grounds, open-playa
  coordinates) and show `walk n/a`.
- Art `location` is sometimes `null` (unplaced pieces, mutant vehicles); only 330 of 823
  have GPS.

Distances assume 80 m/min walking from the centroid of 4:00 & E
(40.772262, -119.204136). Change `HOME` in `curate.py`, or just edit it live in the app.

## Music

`data/bm_rsl.json` is the RSL feed — 400 parties, 1,604 DJ slots with artist,
time, and venue. It carries **no genre field**, so `payload.py` classifies each
set by its *venue*: the camp's own description decides whether a room is
`Melodic & organic` or `Bass & rave`. That puts you in the right room, not in
front of the right DJ — and the bass tag badly undercounts, because camps
advertise as "electrifying beats", never as rave camps. Use melodic as an
include, not bass as an exclude.

The ~30 artists in `KNOWN_MEL` are ones whose genre I could actually vouch for;
they get the same green `verified` badge the real thinkers use.

**This lineup is pre-release and will change.** Re-run `fetch.py` before travel.

## Amenity tags (meals / showers / beauty)

None of these exist in Dust. There is no amenity field, no category, and no map
layer — `map-2026.geojson` carries only `OBJECTID`/`FID`, and 235 source files
in damiant/dust never mention showers. They exist solely in the prose camps
wrote about themselves, so `payload.py` reads the **host camp's** description,
not just the event text.

- **Real meals** — Dust's Food+Beverages holds 560 events; 125 are edible. Eight
  actual meals are filed under Beverages (Bloody Mary Breakfast, Champagne &
  Donuts), so both categories are read rather than trusting the camp's filing.
- **Showers & steam** — mostly steam, sauna and foam; greywater rules make real
  showers rare as a gift. `SHOWER_NOT` excludes camps describing *member*
  infrastructure: Wrongtown and Stag Camp both say "camp showers" and mean
  their own crew, not you.
- **Beauty & grooming** — a deliberately wide net (massage, salon, nails, paint,
  glitter, costume). 373 events; treat it as a browse aid, not a shortlist.

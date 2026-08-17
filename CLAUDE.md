# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of standalone static HTML pages served from the repo root. There is no build step, no
`package.json`, no bundler, no test suite, and no lint config. Every page is a single self-contained
file with inline CSS and inline JS; third-party libraries come from CDNs at runtime.

The repo name says "qr-generate", but it now hosts two unrelated things:

1. **QR / deep-link tooling** — `index.html`, `generator.html`, `qr_simple.html`
2. **"An Nhiên" meditation app** — `boong.html` plus `assets/` and `scripts/` (the bulk of recent work;
   commits are named `boong<N>`)

`aupc_thumoi/` holds separate one-off invitation-card pages.

## Commands

```bash
# Local dev — must be served over HTTP, not opened as file://
# (boong.html fetch()es assets/*.json and assets/mo_click.m4a)
python3 -m http.server 8000

# Regenerate the meditation music catalogs (run from the repo ROOT — the scripts
# write to relative paths 'assets/...'). No dependencies beyond node/python3 stdlib.
node scripts/build_chant_catalog.mjs                    # -> assets/chant_catalog.json
python3 scripts/generate_meditation_playlists.py        # -> assets/meditation_job_playlists_150.json
python3 scripts/generate_meditation_collections_150.py  # -> assets/meditation_job_collections_150.json

# Deploy to Firebase Hosting (project: an-nhien-boong)
firebase deploy --only hosting
```

Pushing to `main` also triggers `.github/workflows/static.yml`, which uploads the **entire repository**
to GitHub Pages. Both deploy targets are live simultaneously and serve from the repo root.

## Deployment gotchas

- `index.html` is **not** a landing page — it is the QR redirect shim. It reads `?android=`, `?ios=`,
  `?fallback=` and immediately `window.location.href`s based on user-agent sniffing. `generator.html`
  hardcodes `https://bdangvnt.github.io/qr-generate/` as the base URL it builds those links against, so
  changing the Pages URL means editing that constant.
- `firebase.json` sets `"public": "./"` and rewrites `**` to `/index.html`. Firebase serves matching
  static files first, so direct paths like `/boong.html` still work — but any unmatched path lands on
  the redirect shim, not a 404.
- The repo root contains large binaries and Vietnamese filenames with spaces and diacritics
  (e.g. `0 - Mẫu thiệp.png`). Everything at root ships to both hosts.

## boong.html architecture

~2600 lines, one file. Understanding these pieces avoids most surprises:

**Two separate script blocks.** A `type="module"` block imports Firebase v12 ESM from `gstatic.com` and
initializes app + analytics only (no auth, no Firestore). Everything else lives in a classic `<script>`
where all state and functions are **module-free globals** — the HTML uses inline `onclick="playChuong(event)"`,
so those functions must stay on `window`. Do not convert this block to a module.

**Audio is three independent systems.** Keep them straight:
- *Chuông* (bell) — fully synthesized in Web Audio: additive sine partials with per-mode decay plus a
  short white-noise strike transient (`playChuongSound`). Two timbres selected by the `bellType` global
  (`'near'` / `'far'`), driven by the `#bell-far` / `#bell-near` buttons.
- *Mõ* (wooden fish) — a decoded sample (`assets/mo_click.m4a`) fired through `moGain`, whose gain is
  `MO_GAIN = 24.0`. The sample is quiet; that multiplier is deliberate.
- *Background music* — a plain `<audio id="chant-audio">` element, **not** routed through the AudioContext,
  so it has its own volume slider (`#music-volume`) independent of `masterGain` (`#volume-slider`).

`initAudio()` is lazy and every play path awaits `audioCtx.resume()` — required for mobile autoplay policy.

**Auto rhythm** is a `setTimeout` schedule, not audio-clock scheduled: `RHYTHM_PATTERN` gives offsets in ms
from cycle start, replayed every `AUTO_RHYTHM_CYCLE` (23s). All pending ids live in `autoTimeouts` and are
cleared by `stopAutoMode()`.

**Playlist pipeline.** `loadChantCatalog()` reads localStorage cache → falls back to fetching
`assets/meditation_job_playlists_150.json` → normalizes and caches. There is no live archive.org call at
runtime; scraping happens offline in `scripts/`. Tracks then flow through `applyTrackFilters()`
(duration cap `SHORT_TRACK_SECONDS`, Vietnamese-first ordering, instrumental/vocal heuristics) and either
`buildCuratedMode()` (keyword buckets in `CURATED_BUCKETS`) or profile scoring
(`computeTrackScore` + `scoreWithProfile`, weighted by age/occupation/intent from onboarding).

The playlist-mode `<select>` has three families of options: `profile`, curated moods
(`focus`/`relax`/`uplift`, each with a `youth-` variant), and per-occupation modes
(`lap_trinh_vien`, `ke_toan`, `phap_che`, `kinh_doanh`, `sang_tao`) that come straight from the
`CATEGORY_KEYWORDS` keys in the Python generators. Adding an occupation means editing both sides.

**localStorage keys** (all versioned in the name):
`boong-user-profile-v1`, `boong-music-preferences-v1`, `boong-music-panel-ui-v1`, `boong-chant-catalog-v2`.
The catalog cache has a 24h TTL — when the shape of `assets/meditation_job_playlists_150.json` changes,
bump `TRACK_CACHE_KEY` or returning users keep the stale cached tracks for a day.

## Conventions

- All user-facing copy is Vietnamese. Keep new UI text Vietnamese and match the existing tone.
- Some strings are intentionally unaccented ASCII (`'Chi lay bai <= 20 phut'`) and the track-classification
  regexes match **both** accented and unaccented Vietnamese (`khong loi` / `không lời`). Preserve both forms
  when editing those patterns.
- `qr_simple_bk.html` is a superseded backup of `qr_simple.html` (the current one adds the center-logo
  feature). Edit `qr_simple.html`.
- Both QR pages use the CDN `qrcode-generator` 1.4.4 UMD build and draw modules manually onto a canvas at
  error-correction level `'H'` — level H is what makes the center logo overlay tolerable.

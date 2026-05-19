# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run / develop

```bash
pip install -r backend/requirements.txt
python backend/app.py        # serves API + frontend on http://localhost:5000
```

Flask runs in `debug=True`, so editing `backend/app.py` auto-reloads. Frontend assets are static — just refresh the browser. There is no build step, no bundler, no test suite.

`backend/app.py` is started from the repo root (it resolves `data.json` / `routes.json` via `os.path.dirname(__file__)/..`). Running it from another cwd still works, but launching the module a different way (e.g. `flask run`) won't pick up the `.env` load at the top of the file.

## Architecture

The app is a single-page Leaflet map plus a Flask API. There is no database — both JSON files are read once at startup into module-level globals (`STATIONS`, `ROUTES`) and every request reads from those in memory.

**Data files (repo root, not in `backend/`)**
- `data.json` — wraps a stringified JSON array under a `data` key: `{"data": "[{stationid, stationname, latitude, longitude}, ...]"}`. ~888 stops, the master station list.
- `routes.json` — array of route objects: `{route_id, name, description, color, schedule: {time_range, frequency, length_km, num_buses}, stops: [{stationid, name, lat, lng}, ...]}`. ~52 routes. The `stops` arrays here are the source of truth for what's reachable — `/api/suggest` and `/api/plan` only consider stops that appear on some route.

**Backend (`backend/app.py`)** — one file, all endpoints:
- `GET /` and `/<path>` serve `frontend/` as static files (Flask `static_folder='../frontend'`).
- `GET /api/routes` — summary list (no stop arrays).
- `GET /api/routes/<id>?now=HH:MM` — full route with `arrival` injected on every stop by `estimate_arrival_times`.
- `GET /api/search?q=...` — fuzzy match `q` against route_id / name / description / stop names; strips a leading "route" / "route no" so "route 4C" matches "4C".
- `GET /api/suggest?q=...` — autocomplete for stop names (min 2 chars, top 15).
- `GET /api/plan?from=...&to=...&now=HH:MM` — finds routes where `from` appears before `to` in the stop list and returns the next bus at the `from` stop (top 5, soonest first).

**Timing model (the non-obvious bit).** All arrival estimates flow through `get_stop_offsets()`: it spreads `length_km` evenly across stops, divides by a hard-coded **40 km/h** average speed, adds a 0.5 min boarding penalty per segment, and floors each segment at 1 min. If `length_km` is missing it falls back to cycle-time estimation from `frequency` × `num_buses`. `estimate_arrival_times()` then picks the next departure from stop 0 ≥ `now` and tracks that *single* bus across all stops, so arrival times are monotonically increasing by construction. `/api/plan` reuses the same `get_stop_offsets()` and walks departures forward to find the next one whose arrival at the `from` stop is ≥ `now`. If you change the speed/penalty constants, both endpoints shift together — that's intentional.

**Frontend (`frontend/`)** — vanilla JS, no framework, no modules. `app.js` is one file with module-level `map`, `allRoutes`, `currentLayers`. Three UI regions in `index.html`:
- left `#sidebar` — trip planner (from/to inputs with autocomplete, "Find Buses" button, results list).
- center `#map` — Leaflet, draws stops as `circleMarker`s coloured per route; highlight markers (from/to) are orange `#FF9500` and larger.
- right `#right-panel` — collapsible route browser / search / per-route detail view.

Clicking a plan result calls `selectRoute(routeId, fromStopName, toStopName)`, which fetches the route with `now`, draws it, opens the right panel, and passes the from/to names down so both the map markers and the stop list get highlighted. The `highlight-stop` CSS class on the detail list is what visually marks the matched stops.

## Mobile viewport

`style.css` has a `@media (max-width: 834px)` block at the bottom that stacks sidebar / map / right-panel vertically and turns `#panel-toggle` into a bottom-sheet handle. This is the existing breakpoint — extend it rather than starting from scratch. Body styles set `text-transform: uppercase` and use the `LamboType` display font; preserve both when touching mobile styles. The trip planner panel grows to fill all available height (`flex: 1` on `#plan-results`) — on a small screen that competes with the map for vertical space, so any redesign needs to bound it.

## Conventions worth knowing

- All UI text is uppercase via CSS (`text-transform: uppercase` on `body`). Don't add manual uppercase in JS strings.
- Frontend is ES5-style (`var`, `function()`, no arrow functions or `const`/`let`). Match the surrounding style when editing `app.js`.
- Times are always `HH:MM` 24-hour strings on the wire; the client builds `now` from `new Date()` and sends it with every timed request so server clock skew doesn't matter.
- `routes.json` `stops[].name` is the *display* name and the join key used by `/api/plan` matching — it doesn't always equal `data.json`'s `stationname`. Match against `routes.json` names for anything user-facing.

## Other docs in the repo

- `README.md` — public-facing overview.
- `explanation.md`, `design.md` — longer writeups of the timing algorithm and UI design. `code_explained.md` and `noob.md` exist locally but are gitignored.

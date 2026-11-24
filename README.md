# Group 1 Pickleball Tournament Report

Tournament Report website for SW2928 Individual and Dual Sports, Group 1, 2FSM-4 (UST).

- Facts: `data/site.json` (event, members, committees), `data/results.json` (scores), `data/gallery.json` (photos, videos, scans)
- Page text: `content/*.html`
- Style: `src/style.css` (tokens described in `DESIGN.md`), `src/site.js`
- Build: `python3 build.py` writes the finished site to `docs/`. Standings and placings are computed from the scores, so change a score only in `data/results.json`.
- Hosting: GitHub Pages, serving the `docs/` folder of the `main` branch.

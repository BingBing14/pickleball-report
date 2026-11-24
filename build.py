#!/usr/bin/env python3
"""Build the static site into docs/.

All facts live in data/*.json; page text lives in content/*.html.
Standings and placings are computed here from data/results.json, so a score
correction is made in one place and every page agrees.

Usage: python3 build.py
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
esc = html.escape


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


SITE = load("site.json")
RES = load("results.json")
GAL = load("gallery.json")
TEAMS = RES["teams"]
MATCHES = RES["matches"]
TARGET = RES["point_target"]
CAP = RES["time_cap_minutes"]


# ---------- results logic ----------

def team_name(tid):
    return " / ".join(TEAMS[tid]["players"])


def winner_loser(m):
    a, b = m["score"]
    if a == b:
        sys.exit(f"{m['id']}: a tie score is not allowed")
    return (m["home"], m["away"]) if a > b else (m["away"], m["home"])


def hit_time_cap(m):
    return max(m["score"]) < TARGET


def standings(pool):
    rows = {t: {"team": t, "w": 0, "l": 0, "pf": 0, "pa": 0} for t, v in TEAMS.items() if v["pool"] == pool}
    games = [m for m in MATCHES if m["stage"] == f"Pool {pool}"]
    for m in games:
        (h, a), (sh, sa) = (m["home"], m["away"]), m["score"]
        rows[h]["pf"] += sh; rows[h]["pa"] += sa
        rows[a]["pf"] += sa; rows[a]["pa"] += sh
        w, l = winner_loser(m)
        rows[w]["w"] += 1; rows[l]["l"] += 1
    for r in rows.values():
        r["diff"] = r["pf"] - r["pa"]

    def h2h(t1, t2):
        for m in games:
            if {m["home"], m["away"]} == {t1, t2}:
                return winner_loser(m)[0]
        return None

    order = sorted(rows.values(), key=lambda r: (-r["w"], -r["diff"], r["pa"]))
    # Head-to-head only decides a two-way tie on wins (the brief's order: wins, H2H, diff, PA, coin flip).
    for i in range(len(order) - 1):
        same = [r for r in order if r["w"] == order[i]["w"]]
        if len(same) == 2 and order[i] in same and order[i + 1] in same:
            win = h2h(order[i]["team"], order[i + 1]["team"])
            if win == order[i + 1]["team"]:
                order[i], order[i + 1] = order[i + 1], order[i]
    for i, r in enumerate(order):
        r["rank"] = i + 1
        nxt = order[i + 1] if i + 1 < len(order) else None
        if nxt and (r["w"], r["diff"], r["pa"]) == (nxt["w"], nxt["diff"], nxt["pa"]) and not h2h(r["team"], nxt["team"]):
            sys.exit(f"Pool {pool}: {r['team']} and {nxt['team']} are fully tied; a coin flip result must be recorded")
    return order


STAND = {p: standings(p) for p in ("A", "B")}


def check_medal_round():
    final = next(m for m in MATCHES if m["stage"] == "Final")
    third = next(m for m in MATCHES if m["stage"] == "3rd place")
    want_final = {STAND["A"][0]["team"], STAND["B"][0]["team"]}
    want_third = {STAND["A"][1]["team"], STAND["B"][1]["team"]}
    if {final["home"], final["away"]} != want_final:
        sys.exit(f"Final teams {final['home']}/{final['away']} do not match pool winners {want_final}")
    if {third["home"], third["away"]} != want_third:
        sys.exit(f"3rd-place teams do not match pool runners-up {want_third}")
    return final, third


FINAL, THIRD = check_medal_round()


def placings():
    f_w, f_l = winner_loser(FINAL)
    t_w, t_l = winner_loser(THIRD)
    thirds = sorted([STAND["A"][2], STAND["B"][2]], key=lambda r: (-r["w"], -r["diff"], r["pa"]))
    return [f_w, f_l, t_w, t_l, thirds[0]["team"], thirds[1]["team"]]


PLACES = placings()


# ---------- HTML pieces ----------

def name(key):
    return SITE["members"][key]


def chip(text, cls=""):
    return f'<span class="chip {cls}">{esc(text)}</span>'


def scoreboard(m):
    w, _ = winner_loser(m)
    rows = []
    for tid, pts in ((m["home"], m["score"][0]), (m["away"], m["score"][1])):
        won = tid == w
        rows.append(
            f'<div class="sb-row{" sb-win" if won else ""}">'
            f'<span class="sb-team"><span class="sb-id">{tid}</span>{esc(team_name(tid))}</span>'
            f'<span class="sb-pts">{pts}</span>'
            f'{"<span class=\"sr-only\"> (winner)</span>" if won else ""}</div>'
        )
    cap = chip(f"Ended at {CAP}-min cap", "chip-ink") if hit_time_cap(m) else chip(f"First to {TARGET}", "chip-ink")
    note = f'<p class="sb-note">{esc(m["note"])}</p>' if m.get("note") else ""
    return (
        f'<article class="scoreboard" aria-label="{m["id"]}, {esc(m["stage"])}">'
        f'<header class="sb-head"><span>{m["id"]} · {esc(m["stage"])}</span>'
        f'<span>Round {m["round"]} · Court {m["court"]}</span></header>'
        + "".join(rows)
        + f'<footer class="sb-foot">{cap}</footer>{note}</article>'
    )


def scoreboards(stage_filter=None):
    ms = [m for m in MATCHES if stage_filter is None or stage_filter(m)]
    return '<div class="sb-grid">' + "".join(scoreboard(m) for m in ms) + "</div>"


def standings_table(pool):
    head = ("<tr><th scope=\"col\">Rank</th><th scope=\"col\">Team</th><th scope=\"col\" class=\"num\">W–L</th>"
            "<th scope=\"col\" class=\"num\">Points for</th><th scope=\"col\" class=\"num\">Points against</th>"
            "<th scope=\"col\" class=\"num\">Diff</th></tr>")
    body = ""
    for r in STAND[pool]:
        d = f'+{r["diff"]}' if r["diff"] > 0 else str(r["diff"]).replace("-", "−")
        body += (f'<tr><td class="num">{r["rank"]}</td><th scope="row"><span class="tid">{r["team"]}</span> '
                 f'{esc(team_name(r["team"]))}</th><td class="num">{r["w"]}–{r["l"]}</td>'
                 f'<td class="num">{r["pf"]}</td><td class="num">{r["pa"]}</td><td class="num">{d}</td></tr>')
    return (f'<div class="table-wrap"><table><caption>Pool {pool} standings (Court {1 if pool == "A" else 2})</caption>'
            f"<thead>{head}</thead><tbody>{body}</tbody></table></div>")


def placings_block():
    labels = ["Champions", "Runners-up", "Third place", "Fourth place", "Fifth place", "Sixth place"]
    medals = ["gold", "silver", "bronze", "", "", ""]
    items = ""
    for i, tid in enumerate(PLACES):
        items += (f'<li class="place place-{i + 1}"><span class="place-num {medals[i]}">{i + 1}</span>'
                  f'<span class="place-body"><span class="place-label">{labels[i]}</span>'
                  f'<span class="place-team">{esc(team_name(tid))}</span><span class="place-id">Team {tid}</span></span></li>')
    return f'<ol class="placings">{items}</ol>'


def champion_card():
    w, l = winner_loser(FINAL)
    return (f'<div class="champion"><p class="label">Champions</p><p class="champion-team">{esc(team_name(w))}</p>'
            f'<p class="champion-meta">Won the Final {max(FINAL["score"])}–{min(FINAL["score"])} against {esc(team_name(l))}</p>'
            f'<a class="btn btn-light" href="results.html">See all results</a></div>')


def teams_table():
    rows = "".join(
        f'<tr><th scope="row"><span class="tid">{t}</span></th><td>Pool {v["pool"]}</td><td>{esc(" / ".join(v["players"]))}</td></tr>'
        for t, v in TEAMS.items())
    return ('<div class="table-wrap"><table><caption>Teams (drawn at random)</caption><thead><tr><th scope="col">Team</th>'
            f'<th scope="col">Pool</th><th scope="col">Players</th></tr></thead><tbody>{rows}</tbody></table></div>')


def schedule_table(with_results=True):
    rows = ""
    for m in MATCHES:
        res = ""
        if with_results:
            w, l = winner_loser(m)
            res = f'<td>{w} won {max(m["score"])}–{min(m["score"])}{" (time cap)" if hit_time_cap(m) else ""}</td>'
        rows += (f'<tr><td class="num">{m["round"]}</td><td class="num">{m["court"]}</td><th scope="row">{m["id"]}</th>'
                 f'<td>{esc(m["stage"])}</td><td>{m["home"]} vs {m["away"]}</td>{res}</tr>')
    rh = '<th scope="col">Result</th>' if with_results else ""
    return ('<div class="table-wrap"><table><caption>Match schedule, in order of play</caption><thead><tr>'
            '<th scope="col" class="num">Round</th><th scope="col" class="num">Court</th><th scope="col">Match</th>'
            f'<th scope="col">Stage</th><th scope="col">Teams</th>{rh}</tr></thead><tbody>{rows}</tbody></table></div>')


def bracket():
    def mini(pool):
        lis = "".join(f'<li><span class="tid">{r["team"]}</span> {esc(team_name(r["team"]))}'
                      f'<span class="br-rec">{r["w"]}–{r["l"]}</span></li>' for r in STAND[pool])
        return (f'<div class="br-box"><p class="br-title">Pool {pool} · Court {1 if pool == "A" else 2}</p>'
                f'<ol class="br-pool">{lis}</ol></div>')

    def game(m, title):
        w, _ = winner_loser(m)
        lines = "".join(
            f'<li class="{"br-win" if t == w else ""}"><span class="tid">{t}</span> {esc(team_name(t))}<span class="br-pts">{p}</span></li>'
            for t, p in ((m["home"], m["score"][0]), (m["away"], m["score"][1])))
        return f'<div class="br-box br-game"><p class="br-title">{title} · Court {m["court"]}</p><ul>{lines}</ul></div>'

    return ('<div class="bracket" role="group" aria-label="Tournament bracket">'
            f'<div class="br-col"><p class="br-step">Pool play · Rounds 1–3</p>{mini("A")}{mini("B")}</div>'
            '<div class="br-arrow" aria-hidden="true"></div>'
            f'<div class="br-col"><p class="br-step">Medal round · Round 4</p>'
            f'{game(FINAL, "Final: A1st vs B1st")}{game(THIRD, "3rd place: A2nd vs B2nd")}</div></div>')


def committees_block():
    out = ""
    for c in SITE["committees"]:
        people = "".join(
            f'<li>{esc(name(k))}{" <span class=\"chip\">Group leader</span>" if k == SITE["leader"] else ""}</li>'
            for k in c["members"])
        duties = "".join(f"<li>{esc(d)}</li>" for d in c["duties"])
        out += (f'<article class="card committee"><header><h3>{esc(c["name"])}</h3>'
                f'<p class="card-meta">{esc(c["title"])} · {len(c["members"])} member{"s" if len(c["members"]) > 1 else ""}</p></header>'
                f'<ul class="people">{people}</ul><p class="label">Responsibilities</p><ul class="duties">{duties}</ul></article>')
    return f'<div class="card-grid">{out}</div>'


def members_table():
    owner = {}
    for c in SITE["committees"]:
        for k in c["members"]:
            owner[k] = c["name"]
    def surname_sort(kv):
        full = kv[1]
        return full[full.index("Dela Paz"):] if "Dela Paz" in full else full.split()[-1]
    rows = sorted(SITE["members"].items(), key=surname_sort)
    body = "".join(f'<tr><th scope="row">{esc(full)}</th><td>{esc(owner.get(k, ""))}</td></tr>' for k, full in rows)
    return ('<div class="table-wrap"><table><caption>All 15 members and their committee</caption><thead><tr>'
            f'<th scope="col">Member</th><th scope="col">Committee</th></tr></thead><tbody>{body}</tbody></table></div>')


def gallery_block():
    if not GAL["groups"]:
        return '<p class="notice">Photos from the tournament are being added to this page.</p>'
    out = ""
    for g in GAL["groups"]:
        figs = "".join(
            f'<figure class="g-item"><a href="assets/photos/{esc(p["file"])}" class="g-link" data-caption="{esc(p["caption"])}">'
            f'<img src="assets/photos/{esc(p["file"])}" alt="{esc(p["alt"])}" loading="lazy" width="{p.get("w", 1200)}" height="{p.get("h", 800)}"></a>'
            f'<figcaption>{esc(p["caption"])}</figcaption></figure>' for p in g["photos"])
        out += f'<section class="g-group"><h2>{esc(g["title"])}</h2><div class="g-grid">{figs}</div></section>'
    return out


def videos_block():
    if not GAL["videos"]:
        return ""
    items = "".join(
        f'<figure class="video"><div class="video-frame"><iframe src="https://drive.google.com/file/d/{esc(v["id"])}/preview" '
        f'title="{esc(v["title"])}" loading="lazy" allow="autoplay; fullscreen" allowfullscreen></iframe></div>'
        f'<figcaption>{esc(v["title"])} · <a href="https://drive.google.com/file/d/{esc(v["id"])}/view" target="_blank" rel="noopener">Open on Drive</a></figcaption></figure>'
        for v in GAL["videos"])
    return f'<section class="g-group"><h2>Videos</h2><div class="video-grid">{items}</div></section>'


def appendix_scans():
    if not GAL["appendix_scans"]:
        return '<p class="notice">Photos of the handwritten score sheets and standings sheet are being added here.</p>'
    return '<div class="g-grid">' + "".join(
        f'<figure class="g-item"><a href="assets/photos/{esc(p["file"])}" class="g-link" data-caption="{esc(p["caption"])}">'
        f'<img src="assets/photos/{esc(p["file"])}" alt="{esc(p["alt"])}" loading="lazy"></a>'
        f'<figcaption>{esc(p["caption"])}</figcaption></figure>' for p in GAL["appendix_scans"]) + "</div>"


def facts():
    n_cap = sum(hit_time_cap(m) for m in MATCHES)
    items = [
        ("Date", SITE["date"]), ("Venue", SITE["venue"]), ("Time", f'{SITE["start"]} to {SITE["end"]}'),
        ("Courts", f'{SITE["courts"]}, doubles'), ("Teams", f"{len(TEAMS)} pairs, 12 players from Group 2"),
        ("Matches", f"{len(MATCHES)} ({n_cap} ended at the {CAP}-minute cap)"),
        ("Organized by", f'{SITE["group"]}, {SITE["section"]} (team color {SITE["team_color"]})'),
        ("Course", f'{SITE["course"]}, {SITE["program"]}'),
    ]
    return '<dl class="facts">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in items) + "</dl>"


TOKENS = {
    "facts": facts, "champion": champion_card, "placings": placings_block, "teams": teams_table,
    "bracket": bracket, "schedule": schedule_table, "schedule_plain": lambda: schedule_table(False),
    "standings_A": lambda: standings_table("A"), "standings_B": lambda: standings_table("B"),
    "scoreboards": scoreboards,
    "scoreboards_pool": lambda: scoreboards(lambda m: m["stage"].startswith("Pool")),
    "scoreboards_medal": lambda: scoreboards(lambda m: not m["stage"].startswith("Pool")),
    "committees": committees_block, "members": members_table, "gallery": gallery_block,
    "videos": videos_block, "appendix_scans": appendix_scans,
    "n_cap": lambda: str(sum(hit_time_cap(m) for m in MATCHES)),
    "toc": lambda: '<ul class="toc">' + "".join(
        f'<li><a href="{p["file"]}"><span class="nav-num">{p["num"]:02d}</span><span>{esc(p["name"])}</span></a></li>'
        for p in SITE["pages"][1:]) + "</ul>",
    "final_summary": lambda: (lambda w, l: f'{esc(team_name(w))} ({w}) won the tournament, beating {esc(team_name(l))} ({l}) '
                              f'{max(FINAL["score"])}–{min(FINAL["score"])} in the Final.')(*winner_loser(FINAL)),
    "director": lambda: esc(name("Arellano")), "leader": lambda: esc(name(SITE["leader"])),
}


def fill(text):
    def rep(mo):
        key = mo.group(1)
        if key.startswith("site."):
            return esc(str(SITE[key[5:]]))
        if key not in TOKENS:
            sys.exit(f"Unknown token {{{{{key}}}}}")
        return TOKENS[key]()
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", rep, text)


# ---------- page template ----------

ICON_MENU = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
ICON_UP = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def nav_links(cur, cls):
    out = ""
    for p in SITE["pages"]:
        here = ' aria-current="page"' if p["file"] == cur else ""
        out += f'<li><a href="{p["file"]}"{here}><span class="nav-num">{p["num"]:02d}</span><span class="nav-txt">{esc(p["short"] if cls == "nav-row" else p["name"])}</span></a></li>'
    return f'<ul class="{cls}">{out}</ul>'


def render(page, body, lead):
    pages = SITE["pages"]
    i = pages.index(page)
    prev_p = pages[i - 1] if i > 0 else None
    next_p = pages[i + 1] if i + 1 < len(pages) else None
    is_home = page["file"] == "index.html"
    title = f'{page["name"]} · {SITE["title"]}'

    def pn(p, kind):
        if not p:
            return "<span></span>"
        return (f'<a class="pn pn-{kind}" href="{p["file"]}" rel="{kind}"><span class="label">{"Previous" if kind == "prev" else "Next"} · '
                f'Section {p["num"]:02d}</span><span class="pn-name">{esc(p["name"])}</span></a>')

    head_block = "" if is_home else (
        f'<header class="page-head"><div class="wrap"><p class="label">Section {page["num"]:02d} of 12</p>'
        f'<h1>{esc(page["name"])}</h1>{f"<p class=\"lead\">{lead}</p>" if lead else ""}</div></header>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(SITE['title'])}: {esc(page['name'])}. {esc(SITE['group'])}, {esc(SITE['section'])}, {esc(SITE['course'])}, University of Santo Tomas.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header" id="top">
  <div class="wrap header-bar">
    <a class="mark" href="index.html"><span class="mark-ball" aria-hidden="true"></span><span><strong>{esc(SITE['short_title'])}</strong><span class="mark-sub">Tournament Report · {esc(SITE['section'])}</span></span></a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu">{ICON_MENU}<span>Sections</span></button>
  </div>
  <nav class="wrap nav-desktop" aria-label="Report sections">{nav_links(page['file'], 'nav-row')}</nav>
  <nav class="menu" id="menu" aria-label="All report sections" hidden>
    <div class="wrap"><p class="label">All 12 sections</p>{nav_links(page['file'], 'nav-list')}</div>
  </nav>
</header>
<main id="main">
{head_block}
{body}
<nav class="wrap prevnext" aria-label="Previous and next section">{pn(prev_p, 'prev')}{pn(next_p, 'next')}</nav>
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <p><strong>{esc(SITE['title'])}</strong></p>
      <p>{esc(SITE['group'])}, {esc(SITE['section'])} · {esc(SITE['course'])}</p>
      <p>{esc(SITE['program'])}, {esc(SITE['school'])}</p>
      <p>Instructor: {esc(SITE['instructor'])}</p>
    </div>
    <div class="footer-side">
      <p>Tournament held {esc(SITE['date'])}</p>
      <a href="#top" class="totop-link">Back to top</a>
    </div>
  </div>
</footer>
<a href="#top" class="totop" aria-label="Back to top" hidden>{ICON_UP}</a>
<script src="site.js" defer></script>
</body>
</html>
"""


def parse_fragment(path):
    raw = path.read_text(encoding="utf-8")
    lead = ""
    if raw.startswith("lead:"):
        first, raw = raw.split("\n", 1)
        lead = first[5:].strip()
    return raw, lead


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "assets").mkdir()
    problems = []
    for page in SITE["pages"]:
        src = ROOT / "content" / page["file"]
        body, lead = parse_fragment(src)
        page_html = render(page, fill(body), fill(lead))
        page_html = re.sub(r"<!--.*?-->\s*", "", page_html, flags=re.S)  # group notes stay in the source only
        visible = re.sub(r"<[^>]+>", " ", page_html)
        for bad in ("CONFIRM", "TODO", "lorem", "{{"):
            if bad.lower() in visible.lower():
                problems.append(f"{page['file']}: contains '{bad}'")
        (OUT / page["file"]).write_text(page_html, encoding="utf-8")
    for f in ("style.css", "site.js"):
        shutil.copy(ROOT / "src" / f, OUT / f)
    shutil.copy(ROOT / "src" / "icon.svg", OUT / "assets" / "icon.svg")
    if (ROOT / "assets" / "photos").exists():
        shutil.copytree(ROOT / "assets" / "photos", OUT / "assets" / "photos")
    (OUT / ".nojekyll").write_text("")
    for p in STAND:
        print(f"Pool {p}: " + ", ".join(f"{r['rank']}. {r['team']} {r['w']}-{r['l']} ({r['diff']:+d})" for r in STAND[p]))
    print("Placings: " + ", ".join(f"{i + 1}. {t}" for i, t in enumerate(PLACES)))
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"Built {len(SITE['pages'])} pages into docs/")


if __name__ == "__main__":
    main()

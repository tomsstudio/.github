#!/usr/bin/env python3
"""Regenerate the org profile's commit graph from real commit data.

Expects commits.tsv (one ISO date per line) in <scratch-dir>.
Stdlib only - no dependencies, deliberately.

    python3 tools/gen-commit-graph.py . profile/assets
"""
import collections, datetime as dt, pathlib, sys

SCRATCH = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
BODY = 'Helvetica, Arial, sans-serif'

counts = collections.Counter()
for line in (SCRATCH / "commits.tsv").read_text().splitlines():
    if line.strip(): counts[dt.date.fromisoformat(line.split("\t")[0])] += 1

END = dt.date.today()                                   # anchor to today, not last commit
END += dt.timedelta(days=6 - END.weekday())             # pad forward to Sunday
WEEKS = 32; START = END - dt.timedelta(weeks=WEEKS - 1, days=6)  # a Monday

LIGHT = dict(ink="#334641", mute="#7d8f8a", ramp=["#ece4da", "#bac7be", "#7c9e95", "#3e756c", "#004c43"])
DARK = dict(ink="#d8e0dc", mute="#7d8f8a", ramp=["#1e2724", "#00423a", "#2a6b60", "#5e9187", "#a8c4bd"])

def level(n):
    if n == 0: return 0
    if n <= 2: return 1
    if n <= 5: return 2
    if n <= 10: return 3
    return 4

def heatmap(p):
    CELL, GAP, STEP = 14, 3, 17
    x0, y0 = 42, 30
    W, H = 600, 185
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="Commit activity over the last {WEEKS} weeks">']

    seen = set()
    for wk in range(WEEKS):
        d0 = START + dt.timedelta(weeks=wk)
        for off in range(7):
            d = d0 + dt.timedelta(days=off)
            if d.day <= 7:
                m = d.strftime("%b")
                if m not in seen:
                    seen.add(m)
                    s.append(f'<text x="{x0 + wk*STEP}" y="{y0-10}" font-family="{BODY}" '
                             f'font-size="10.5" fill="{p["mute"]}">{m}</text>')
                break
    for i, lab in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        s.append(f'<text x="{x0-8}" y="{y0 + i*STEP + CELL-3}" text-anchor="end" '
                 f'font-family="{BODY}" font-size="9.5" fill="{p["mute"]}">{lab}</text>')

    total = 0
    for wk in range(WEEKS):
        for dow in range(7):
            day = START + dt.timedelta(weeks=wk, days=dow)
            if day > END: continue
            n = counts.get(day, 0); total += n
            s.append(f'<rect x="{x0 + wk*STEP}" y="{y0 + dow*STEP}" width="{CELL}" height="{CELL}" '
                     f'fill="{p["ramp"][level(n)]}"/>')

    by = y0 + 7*STEP + 22
    s.append(f'<text x="{x0}" y="{by}" font-family="{BODY}" font-size="11.5" fill="{p["ink"]}">'
             f'<tspan font-weight="bold">{total}</tspan> commits in the last {WEEKS} weeks</text>')
    lx = W - 8 - (5*14 + 34)
    s.append(f'<text x="{lx-5}" y="{by}" text-anchor="end" font-family="{BODY}" font-size="10" fill="{p["mute"]}">Less</text>')
    for i, c in enumerate(p["ramp"]):
        s.append(f'<rect x="{lx + i*14}" y="{by-10}" width="10" height="10" fill="{c}"/>')
    s.append(f'<text x="{lx + 5*14 + 1}" y="{by}" font-family="{BODY}" font-size="10" fill="{p["mute"]}">More</text>')
    s.append("</svg>")
    return "\n".join(s), total

for name, p in (("light", LIGHT), ("dark", DARK)):
    hm, total = heatmap(p)
    (OUT / f"commits-{name}.svg").write_text(hm)
print(f"total commits rendered: {total}")

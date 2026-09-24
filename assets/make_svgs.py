"""Builds the animated terminal header in a dark and a light version.

Edit LINES below and run `python assets/make_svgs.py` from the repo root.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent

FONT = ("ui-monospace,'SF Mono','JetBrains Mono','Cascadia Mono',Consolas,"
        "Menlo,'DejaVu Sans Mono',monospace")

THEMES = {
    "dark": dict(
        win="#1a1512", win_line="#3a2e27", bar="#211a16", dots="#3f322b",
        shadow=0.5, title="#7d6e62",
        fg="#ecdfd0", dim="#86776a", prompt="#f2a65e", fn="#f2a65e",
        str="#e8c291", arg="#c7a489", ok="#a9d38b", warn="#f2a65e",
    ),
    "light": dict(
        win="#fffcf8", win_line="#e7d9c9", bar="#f7efe5", dots="#e6d8c8",
        shadow=0.12, title="#a08f80",
        fg="#2e2622", dim="#9b8b7d", prompt="#b8561c", fn="#b8561c",
        str="#8d5a26", arg="#8a7565", ok="#3f7b35", warn="#b8561c",
    ),
}

# Each line is one of:
#   ("cmd", text)                      typed after the prompt
#   ("out", [(text, class), ...])      printed at once
#   ("step", call_tokens, date, status)
#   ("metric", name, value, note)
#   ("", None)                         blank
#   ("final", None)                    prompt with a blinking cursor
S = lambda s: (f'"{s}"', "str")
LINES = [
    ("cmd", "whoami"),
    ("out", [("subodh singh", "fg b"), (" · ai engineer · india", "fg")]),
    ("out", [("i build ai agents, and the tools that check what they actually do", "dim")]),
    ("", None),
    ("cmd", "regshield replay career.trace"),
    ("step", [("intern", "fn"), ("(", "fg"), S("ati motors"), (", ", "fg"), ("role=", "arg"),
              S("data engineer"), (")", "fg")], "2024.01", "ok"),
    ("step", [("graduate", "fn"), ("(", "fg"), S("iiit vadodara"), (", ", "fg"),
              S("b.tech cse"), (")", "fg")], "2024", "ok"),
    ("step", [("work", "fn"), ("(", "fg"), S("clarice systems"), (", ", "fg"), ("client=", "arg"),
              S("drdo"), (")", "fg")], "2024-26", "ok"),
    ("step", [("ship", "fn"), ("(", "fg"), S("regshield"), (", ", "fg"), S("researchagent"),
              (", ", "fg"), S("datalens"), (")", "fg")], "2026", "ok"),
    ("step", [("learn", "fn"), ("(", "fg"), S("llm inference"), (")", "fg")], "now", "running"),
    ("", None),
    ("out", [("PASSED", "ok b"), ("  career  subodh singh  (composite 0.98)", "fg")]),
    ("metric", "tool_selection", "1.00", "python, langgraph, fastapi, react"),
    ("metric", "call_ordering", "1.00", "internship, degree, job. in that order"),
    ("metric", "step_efficiency", "0.90", "took a 12 s query to under 3 s. next: 1"),
    ("metric", "reasoning_faithfulness", "1.00", "every project below links to its code"),
    ("", None),
    ("final", None),
]

FS, CW, LH = 13.5, 8.1, 20          # font size, cell width, line height
WX, WY, WW = 8, 4, 760             # terminal window
BAR = 34
TX = WX + 28                         # text left edge
BASE0 = WY + BAR + 30                # baseline of first line
WH = BAR + 30 + (len(LINES) - 1) * LH + 22
W, H = WX * 2 + WW, WY + WH + 18


def seg(text, cls, col, y):
    """Place text on the cell grid. Runs of 2+ spaces are split so every
    column lines up no matter which monospace font the viewer has."""
    out = []
    for m in re.finditer(r"\S+(?: \S+)*", text):
        x = TX + (col + m.start()) * CW
        n = len(m.group())
        out.append(f'<text x="{x:.1f}" y="{y}" textLength="{n * CW:.1f}" '
                   f'lengthAdjust="spacing" class="{cls}">{escape(m.group())}</text>')
    return out


def tokens(toks, col, y):
    out = []
    for text, cls in toks:
        out += seg(text, cls, col, y)
        col += len(text)
    return out


def shown(at, parts):
    return f'<g class="a" style="animation-delay:{at:.2f}s">{"".join(parts)}</g>'


def terminal(t):
    keys, body = [], []
    time, typed, step = 0.5, 0, 0
    for i, line in enumerate(LINES):
        y = BASE0 + i * LH
        kind = line[0]
        if kind == "":
            continue
        after_blank = LINES[i - 1][0] == ""
        if kind in ("cmd", "final"):
            parts = seg("~", "prompt", 0, y) + seg("$", "prompt", 2, y)
            cx = TX + 4 * CW
            cursor = (f'x="{cx:.1f}" y="{y - FS * 0.82:.1f}" width="{CW:.1f}" '
                      f'height="{FS * 1.08:.1f}" fill="{t["prompt"]}"')
            if kind == "final":
                time += 0.35
                body.append(shown(time, parts + [f'<rect class="blink" {cursor}/>']))
                continue
            cmd = line[1]
            n = len(cmd)
            if typed:
                time += 0.45
            show, start = time, time + 0.3
            dur = n * (0.06 if n < 10 else 0.042)
            done = start + dur + 0.2
            typed += 1
            keys.append(f"@keyframes ty{typed}{{to{{transform:translateX({n * CW:.1f}px)}}}}")
            parts += seg(cmd, "fg", 4, y)
            # a cover slides right in steps, uncovering one character at a
            # time; the cursor rides on its left edge
            parts.append(
                f'<g style="animation:ty{typed} {dur:.2f}s steps({n},end) {start:.2f}s forwards">'
                f'<rect class="cover" x="{cx - 1:.1f}" y="{y - FS:.1f}" width="{n * CW + CW + 4:.1f}" '
                f'height="{LH}" fill="{t["win"]}"/>'
                f'<rect class="cur" style="animation-delay:{done:.2f}s" {cursor}/></g>')
            body.append(shown(show, parts))
            time = done
        elif kind == "out":
            time += 0.45 if after_blank else 0.12
            body.append(shown(time, tokens(line[1], 0, y)))
        elif kind == "step":
            _, call, date, status = line
            step += 1
            time += 0.34
            body.append(shown(time, seg(f"step {step}", "dim", 2, y) + tokens(call, 10, y)
                              + seg(date, "dim", 59, y)))
            cls = "ok" if status == "ok" else "warn pulse"
            body.append(shown(time + 0.2, seg(status, cls, 68, y)))
        elif kind == "metric":
            _, name, val, note = line
            time += 0.1
            body.append(shown(time, seg(name, "fg", 2, y) + seg(val, "ok", 26, y)
                              + seg(note, "dim", 32, y)))
    return keys, body


def style(t, keys):
    return f"""<style>
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
.fg{{fill:{t['fg']}}}.dim{{fill:{t['dim']}}}.prompt{{fill:{t['prompt']}}}.fn{{fill:{t['fn']}}}
.str{{fill:{t['str']}}}.arg{{fill:{t['arg']}}}.ok{{fill:{t['ok']}}}.warn{{fill:{t['warn']}}}.b{{font-weight:700}}
.a{{opacity:0;animation:show .01s linear forwards}}
.cur{{animation:hide .01s linear forwards}}
.blink{{animation:blink 1.1s step-end infinite}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes show{{to{{opacity:1}}}}
@keyframes hide{{to{{opacity:0}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes pulse{{50%{{opacity:.35}}}}
{chr(10).join(keys)}
@media (prefers-reduced-motion:reduce){{.a{{animation:none;opacity:1}}.cover,.cur{{display:none}}
.blink,.pulse{{animation:none}}}}
</style>"""


def header(t):
    keys, body = terminal(t)
    r = 10.5
    win = [
        f'<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="125%">'
        f'<feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000" '
        f'flood-opacity="{t["shadow"]}"/></filter></defs>',
        f'<rect filter="url(#sh)" x="{WX}" y="{WY}" width="{WW}" height="{WH}" rx="11" '
        f'fill="{t["win"]}" stroke="{t["win_line"]}"/>',
        f'<path d="M{WX + 0.5},{WY + BAR} V{WY + 0.5 + r} a{r},{r} 0 0 1 {r},-{r} '
        f'H{WX + WW - 0.5 - r} a{r},{r} 0 0 1 {r},{r} V{WY + BAR} Z" fill="{t["bar"]}"/>',
        f'<line x1="{WX}" y1="{WY + BAR}" x2="{WX + WW}" y2="{WY + BAR}" stroke="{t["win_line"]}"/>',
    ]
    win += [f'<circle cx="{WX + 20 + k * 17}" cy="{WY + BAR / 2}" r="5.5" fill="{t["dots"]}"/>'
            for k in range(3)]
    win.append(f'<text x="{WX + WW / 2}" y="{WY + BAR / 2 + 4}" text-anchor="middle" '
               f'style="font-size:12px;fill:{t["title"]}">subodh@senpai: ~</text>')
    return "\n".join(
        [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="Terminal replaying Subodh Singh\'s career as an agent trace">',
         style(t, keys)] + win + body + ["</svg>"])


if __name__ == "__main__":
    for name, t in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(header(t), encoding="utf-8")
        print("wrote", f"header-{name}.svg")

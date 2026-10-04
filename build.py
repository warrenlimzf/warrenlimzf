"""Generates the terminal-style SVG cards for the GitHub profile README.

Run `python3 build.py`; it writes a dark and a light version of every card into assets/.
SVG only (no JS, no web fonts) because GitHub serves README images through its image
proxy, which strips scripts and blocks external requests. Animation is SMIL, and every
static attribute holds the readable state, so a renderer that ignores animation (GitHub
mobile, link previews) still shows the whole card.

The look follows the "hacker" profiles Warren picked: a dark terminal, a neofetch panel
with an ASCII portrait made from his headshot (ascii.py), and block-letter name art.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from ascii import portrait

OUT = Path(__file__).parent / "assets"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": dict(
        bg="#0D1117", panel="#010409", bar="#161B22", line="#30363D", text="#E6EDF3",
        muted="#7D8590", key="#79C0FF", green="#3FB950", glow="#39D353", dim="#0E4429",
        yellow="#E3B341", pink="#F778BA", purple="#BC8CFF", orange="#FFA657", ascii="#56D364",
    ),
    "light": dict(
        bg="#FFFFFF", panel="#F6F8FA", bar="#EAEEF2", line="#D0D7DE", text="#1F2328",
        muted="#656D76", key="#0969DA", green="#1A7F37", glow="#2DA44E", dim="#ACEEBB",
        yellow="#9A6700", pink="#BF3989", purple="#8250DF", orange="#BC4C00", ascii="#1A7F37",
    ),
}


def window(t, w, h, title, uid):
    """Terminal window chrome shared by every card."""
    dots = "".join(f'<circle cx="{26 + k * 20}" cy="21" r="6" fill="{c}"/>'
                   for k, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]))
    return f"""
  <defs>
    <clipPath id="win{uid}"><rect width="{w}" height="{h}" rx="12"/></clipPath>
    <linearGradient id="scan{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['glow']}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{t['glow']}" stop-opacity="0.07"/>
      <stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#win{uid})">
    <rect width="{w}" height="{h}" fill="{t['panel']}"/>
    <rect width="{w}" height="42" fill="{t['bar']}"/>
    <line x1="0" x2="{w}" y1="42" y2="42" stroke="{t['line']}"/>
    {dots}
    <text x="{w / 2}" y="26" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{t['muted']}">{escape(title)}</text>
    <rect x="0" y="-120" width="{w}" height="120" fill="url(#scan{uid})">
      <animate attributeName="y" values="-120;{h}" dur="6s" repeatCount="indefinite"/>
    </rect>
  </g>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{t['line']}"/>"""


def prompt(t, x, y, cmd, size=14):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" xml:space="preserve">'
            f'<tspan fill="{t["green"]}">warren@github</tspan><tspan fill="{t["muted"]}">:</tspan>'
            f'<tspan fill="{t["key"]}">~</tspan><tspan fill="{t["muted"]}">$ </tspan>'
            f'<tspan fill="{t["text"]}">{escape(cmd)}</tspan></text>')


def cursor(t, x, y, h=17):
    return (f'<rect x="{x}" y="{y - h + 3}" width="9" height="{h}" fill="{t["glow"]}">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')


# ---------------------------------------------------------------- header
# "ANSI Shadow" letters; the solid cells are drawn as squares so they line up in any font
LETTERS = {
    "W": ["█   █", "█   █", "█ █ █", "█████", " █ █ "],
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "L": ["█    ", "█    ", "█    ", "█    ", "█████"],
    "I": ["███", " █ ", " █ ", " █ ", "███"],
    "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    " ": ["  ", "  ", "  ", "  ", "  "],
}

PHRASES = [
    "finance student who builds his own research tools",
    "buy-side equity research: Salesforce, ServiceNow, Copart",
    "Eurasia AM Challenge 2026 champion, +97.1% vs +90.5%",
    "valuation for what to own, the chart for when",
]
CHAR_W = 8.43     # 14px system mono, average advance
SLOT, TYPE_T, HOLD_T = 6.5, 2.0, 6.0


def typing(t, x, y, uid):
    """Cycles the phrases. The clock is shifted so t=0 (and any renderer that ignores
    animation) shows the first phrase fully typed, never a blank line."""
    total = SLOT * len(PHRASES)
    step = 0.05

    def width(i, now):
        local = (now + TYPE_T) % total - i * SLOT
        n = len(PHRASES[i])
        if 0 <= local < TYPE_T:
            return int(local / TYPE_T * n) * CHAR_W
        return n * CHAR_W if TYPE_T <= local < HOLD_T else 0

    def frames(fn):
        out, last = [], None
        for k in range(int(total / step)):
            v = fn(k * step)
            if v != last:
                out.append((k * step, v))
                last = v
        return out

    def animate(attr, fr, fmt):
        kt = ";".join(f"{f[0] / total:.4f}" for f in fr)
        vals = ";".join(fmt(f[1]) for f in fr)
        return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{total}s" '
                f'repeatCount="indefinite" keyTimes="{kt}" values="{vals}"/>')

    defs, texts = [], []
    for i, p in enumerate(PHRASES):
        fr = frames(lambda now, i=i: width(i, now))
        defs.append(f'<clipPath id="tc{uid}{i}"><rect x="{x}" y="{y - 16}" height="22" width="{width(i, 0):.1f}">'
                    f'{animate("width", fr, lambda v: f"{v:.1f}")}</rect></clipPath>')
        texts.append(f'<text x="{x}" y="{y}" clip-path="url(#tc{uid}{i})" font-family="{MONO}" font-size="14" '
                     f'fill="{t["text"]}">{escape(p)}</text>')
    cur = lambda now: max(width(i, now) for i in range(len(PHRASES)))
    cur_el = (f'<rect y="{y - 13}" width="9" height="17" fill="{t["glow"]}" x="{x + cur(0) + 2:.1f}">'
              f'{animate("x", frames(cur), lambda v: f"{x + v + 2:.1f}")}'
              f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    return "".join(defs), "".join(texts) + cur_el


def header(t, uid):
    W, H = 1000, 300
    cell, gap = 13, 1.5
    word = "WARREN LIM"
    cols = sum(len(LETTERS[c][0]) + 1 for c in word) - 1
    x0 = (W - cols * cell) / 2
    y0 = 100
    shadow, solid = [], []
    cx = x0
    for c in word:
        rows = LETTERS[c]
        for r, row in enumerate(rows):
            for k, ch in enumerate(row):
                if ch == "█":
                    x, y = cx + k * cell, y0 + r * cell
                    shadow.append(f'<rect x="{x + 4:.1f}" y="{y + 4:.1f}" width="{cell - gap}" height="{cell - gap}"/>')
                    solid.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell - gap}" height="{cell - gap}"/>')
        cx += (len(rows[0]) + 1) * cell
    art_w = cols * cell
    tdefs, ttext = typing(t, 64, 254, uid)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Warren Lim, finance student who builds his own research tools">
  <title>Warren Lim</title>{window(t, W, H, 'warren@github: ~ — zsh', uid)}
  <defs>
    {tdefs}
    <linearGradient id="nm{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['glow']}"/><stop offset="0.5" stop-color="{t['key']}"/><stop offset="1" stop-color="{t['glow']}"/>
    </linearGradient>
    <linearGradient id="sh{uid}" gradientUnits="userSpaceOnUse" x1="{x0 - 200:.0f}" y1="0" x2="{x0:.0f}" y2="0">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.55"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;{art_w + 400:.0f} 0" dur="5s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  {prompt(t, 28, 74, 'figlet "warren lim" | lolcat')}
  <g fill="{t['dim']}">{''.join(shadow)}</g>
  <g fill="url(#nm{uid})">{''.join(solid)}</g>
  <g fill="url(#sh{uid})">{''.join(solid)}</g>
  {prompt(t, 28, 226, 'echo $WHOAMI')}
  <text x="44" y="254" font-family="{MONO}" font-size="14" fill="{t['green']}">&gt;</text>
  {ttext}
</svg>"""


# ---------------------------------------------------------------- neofetch
# every figure is from Personal/Career/Job Application Profile.md
FETCH = [
    ("head", "warren@limzf"),
    ("rule", ""),
    ("kv", "Degree", "NTU, Business (Banking & Finance)"),
    ("kv", "Exchange", "SMU, fall 2026"),
    ("kv", "Location", "Singapore"),
    ("kv", "Focus", "Buy-side equity research"),
    ("kv", "Studying", "FMVA, CFA Level I in November"),
    ("gap",),
    ("sec", "Track record"),
    ("kv", "EAMC 2026", "Champion, Eurasia AM Challenge"),
    ("kv", "Return", "+97.1% vs +90.5% benchmark"),
    ("kv", "Sharpe", "0.94 vs 0.86"),
    ("kv", "Whitman", "factsheets: 3 min -> 20 s"),
    ("kv", "Pinnacle", "Salesforce, ServiceNow, Copart"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "Code", "Python, TypeScript, Excel VBA"),
    ("kv", "Data", "Bloomberg, Capital IQ, FRED"),
    ("kv", "Builds", "Claude Code, Next.js, Vercel"),
    ("gap",),
    ("sec", "Contact"),
    ("kv", "Web", "warrenlimzf.com"),
    ("kv", "LinkedIn", "in/warrenlimzf"),
]


def neofetch(t, uid):
    W = 1000
    COLS = 72
    rows = portrait(cols=COLS, aspect=0.553, invert=t["bg"] == "#FFFFFF")
    fs, cw, lh = 8.6, 5.2, 9.4
    px, py = 34, 92
    art_h = len(rows) * lh
    lines = []
    for i, r in enumerate(rows):
        r = r.ljust(COLS)
        lines.append(f'<text x="{px}" y="{py + i * lh:.1f}" textLength="{COLS * cw:.1f}" lengthAdjust="spacing" '
                     f'xml:space="preserve">{escape(r)}</text>')
    # right column
    rx, ry, step = 474, 96, 20.5
    out, y = [], ry
    for item in FETCH:
        kind = item[0]
        if kind == "head":
            out.append(f'<text x="{rx}" y="{y}" font-size="15" font-weight="700"><tspan fill="{t["green"]}">warren</tspan>'
                       f'<tspan fill="{t["text"]}">@</tspan><tspan fill="{t["green"]}">limzf</tspan></text>')
        elif kind == "rule":
            out.append(f'<text x="{rx}" y="{y - 4}" font-size="14" fill="{t["muted"]}">{"-" * 12}</text>')
            y -= 6
        elif kind == "gap":
            y -= 9
        elif kind == "sec":
            out.append(f'<text x="{rx}" y="{y}" font-size="13.5" font-weight="700" fill="{t["yellow"]}">-- {escape(item[1])} '
                       f'<tspan fill="{t["line"]}">{"-" * (34 - len(item[1]))}</tspan></text>')
        else:
            k, v = item[1], item[2]
            dots = "." * (11 - len(k))
            out.append(f'<text x="{rx}" y="{y}" font-size="13.5" xml:space="preserve"><tspan fill="{t["key"]}" font-weight="700">{escape(k)}</tspan>'
                       f'<tspan fill="{t["line"]}"> {dots} </tspan><tspan fill="{t["text"]}">{escape(v)}</tspan></text>')
        y += step
    blocks = "".join(f'<rect x="{rx + k * 26}" y="{y - 4}" width="24" height="14" fill="{c}"/>'
                     for k, c in enumerate([t["line"], "#F85149", t["green"], t["yellow"], t["key"], t["purple"], "#39C5CF", t["text"]]))
    H = int(max(py + art_h, y + 10) + 48)
    end_y = H - 22
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="neofetch: ASCII portrait of Warren beside his degree, track record, stack and contact">
  <title>neofetch</title>{window(t, W, H, 'warren@github: ~ — neofetch', uid)}
  <defs>
    <linearGradient id="pg{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['ascii']}"/><stop offset="1" stop-color="{t['key']}"/>
    </linearGradient>
  </defs>
  {prompt(t, 28, 70, 'neofetch')}
  <rect x="{px - 12}" y="{py - 16}" width="{COLS * cw + 24:.0f}" height="{art_h + 14:.0f}" rx="8" fill="{t['bg']}" stroke="{t['line']}"/>
  <g font-family="{MONO}" font-size="{fs}" fill="url(#pg{uid})">{''.join(lines)}
    <animate attributeName="opacity" values="1;0.82;1;1;0.9;1" keyTimes="0;0.04;0.08;0.6;0.62;1" dur="7s" repeatCount="indefinite"/>
  </g>
  <g font-family="{MONO}">{''.join(out)}{blocks}</g>
  {prompt(t, 28, end_y, '')}
  {cursor(t, 28 + 17 * CHAR_W, end_y)}
</svg>"""


# ---------------------------------------------------------------- projects
PROJECTS = [
    ("macro-research", "Next.js", "key", "US macro indicators on live FRED charts, plus company research"),
    ("market-dashboard", "TypeScript", "key", "a US market report every trading day: the tape and the movers"),
    ("trading-journal", "TypeScript", "key", "every trade logged and reviewed, embedded in my site"),
    ("vcp-strategy-desk", "Python", "yellow", "swing-trading rulebook on a pre-registered out-of-sample test"),
    ("bank-nav-automation", "Python", "yellow", "LGT, BoS and UBS statements into Excel, each figure screenshotted"),
    ("web-design-skill", "Claude Code", "orange", "a Claude Code skill that keeps my sites from looking machine-made"),
]


def projects(t, uid):
    W = 1000
    top, step = 104, 27
    H = top + step * len(PROJECTS) + 74
    rows = []
    for i, (name, lang, col, desc) in enumerate(PROJECTS):
        y = top + i * step
        perm = "drwxr-xr-x" if i < 4 else "drwxr-xr-x"
        pub = i == 4
        rows.append(f'<text x="28" y="{y}" font-size="13" xml:space="preserve">'
                    f'<tspan fill="{t["muted"]}">{perm}  </tspan>'
                    f'<tspan fill="{t[col]}">{escape(lang.ljust(11))}</tspan>'
                    f'<tspan fill="{t["key"]}" font-weight="700">  {escape(name.ljust(20))}</tspan>'
                    f'<tspan fill="{t["text"]}">{escape(desc)}</tspan>'
                    f'{"<tspan fill=" + chr(34) + t["green"] + chr(34) + "> [public]</tspan>" if pub else ""}</text>')
    end_y = top + step * len(PROJECTS) + 20
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Six projects Warren has built">
  <title>ls ~/projects</title>{window(t, W, H, 'warren@github: ~/projects', uid)}
  {prompt(t, 28, 74, 'ls -la ~/projects  # most repos are private; the live work is on warrenlimzf.com')}
  <g font-family="{MONO}">{''.join(rows)}</g>
  {prompt(t, 28, end_y, '')}
  {cursor(t, 28 + 17 * CHAR_W, end_y)}
</svg>"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        uid = name[0]
        (OUT / f"header-{name}.svg").write_text(header(t, uid))
        (OUT / f"neofetch-{name}.svg").write_text(neofetch(t, uid))
        (OUT / f"projects-{name}.svg").write_text(projects(t, uid))
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))

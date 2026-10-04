"""Generates the animated SVG cards for the GitHub profile README.

Run `python3 build.py`; it writes light + dark versions of every card into assets/.
SVGs only (no JS, no web fonts) because GitHub serves README images through its
image proxy, which strips scripts and blocks external requests.
"""
import random
import re
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "assets"

THEMES = {
    "light": dict(
        bg1="#FBF8F1", bg2="#F0E8D8", ink="#14213D", muted="#5B6478",
        accent="#A8843F", soft="#E9DCBF", glass="#FFFFFF", glass_op=0.58,
        stroke="#14213D", stroke_op=0.10, blob1="#E8D3A6", blob2="#C9D5EC",
        down="#8E97AA", term="#FFFFFF", term_op=0.70,
    ),
    "dark": dict(
        bg1="#0A1222", bg2="#121D35", ink="#F3EDE0", muted="#9AA3B5",
        accent="#D9BE84", soft="#3A3322", glass="#FFFFFF", glass_op=0.05,
        stroke="#F3EDE0", stroke_op=0.12, blob1="#4A3B1F", blob2="#1F3260",
        down="#5F6982", term="#060B16", term_op=0.55,
    ),
}

SERIF = "Georgia, 'Times New Roman', serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# numerals take the mono face, words take the serif (house type rule)
NUM = re.compile(r"(\+?\d[\d.,]*(?:\s?(?:%|min|s\b))?\+?)")


def rich(text, mono_fill=None):
    out = []
    for part in NUM.split(text):
        if not part:
            continue
        if NUM.fullmatch(part):
            fill = f' fill="{mono_fill}"' if mono_fill else ""
            out.append(f'<tspan font-family="{MONO}" font-size="0.92em"{fill}>{escape(part)}</tspan>')
        else:
            out.append(escape(part))
    return "".join(out)


def backdrop(t, w, h, uid):
    return f"""
  <defs>
    <linearGradient id="bg{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg1']}"/><stop offset="1" stop-color="{t['bg2']}"/>
    </linearGradient>
    <filter id="blur{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>
    <clipPath id="frame{uid}"><rect width="{w}" height="{h}" rx="22"/></clipPath>
  </defs>
  <g clip-path="url(#frame{uid})">
    <rect width="{w}" height="{h}" fill="url(#bg{uid})"/>
    <g filter="url(#blur{uid})" opacity="0.9">
      <circle cx="{w*0.78:.0f}" cy="{h*0.25:.0f}" r="170" fill="{t['blob1']}">
        <animateTransform attributeName="transform" type="translate" values="0 0;-60 40;0 0" dur="18s" repeatCount="indefinite"/>
      </circle>
      <circle cx="{w*0.18:.0f}" cy="{h*0.85:.0f}" r="190" fill="{t['blob2']}">
        <animateTransform attributeName="transform" type="translate" values="0 0;70 -30;0 0" dur="22s" repeatCount="indefinite"/>
      </circle>
    </g>
  </g>
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="22" fill="none" stroke="{t['stroke']}" stroke-opacity="{t['stroke_op']}"/>"""


def glass(t, x, y, w, h, rx=16):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{t["glass"]}" '
            f'fill-opacity="{t["glass_op"]}" stroke="{t["stroke"]}" stroke-opacity="{t["stroke_op"]}"/>')


# ---------------------------------------------------------------- hero
PHRASES = [
    "Equity research: Salesforce, ServiceNow, Copart",
    "Business analysis turned into a buy or avoid",
    "Research tools built with Claude Code",
    "Valuation for what, the chart for when",
]
CHAR_W = 7.6      # Georgia 19px, measured average advance
SLOT = 5.0        # seconds per phrase
TYPE_T = 2.2      # seconds to type a phrase
HOLD_T = 4.4      # phrase disappears at this point in its slot


def typing(t, x, y):
    """Cycles the phrases. The clock is shifted so t=0 (and any renderer that
    ignores animation) shows the first phrase fully typed, never a blank line."""
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
        defs.append(f'<clipPath id="tc{i}"><rect x="{x}" y="{y - 22}" height="30" width="{width(i, 0):.1f}">'
                    f'{animate("width", fr, lambda v: f"{v:.1f}")}</rect></clipPath>')
        texts.append(f'<text x="{x}" y="{y}" clip-path="url(#tc{i})" font-family="{SERIF}" font-size="19" '
                     f'fill="{t["ink"]}">{escape(p)}</text>')
    cur = lambda now: max(width(i, now) for i in range(len(PHRASES)))
    cursor = (f'<rect y="{y - 17}" width="2" height="22" fill="{t["accent"]}" x="{x + cur(0) + 3:.1f}">'
              f'{animate("x", frames(cur), lambda v: f"{x + v + 3:.1f}")}'
              f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    return "".join(defs), "".join(texts) + cursor


def candles(n=24, seed=7):
    random.seed(seed)
    px, out = 100.0, []
    for _ in range(n):
        o = px
        c = o + random.gauss(1.1, 3.2)
        hi = max(o, c) + abs(random.gauss(0, 1.8))
        lo = min(o, c) - abs(random.gauss(0, 1.8))
        out.append((o, hi, lo, c))
        px = c
    return out


def ascii_chart(t, x0, y0, cols=24, rows=15, dx=14, dy=15.5):
    data = candles(cols)
    lo = min(d[2] for d in data)
    hi = max(d[1] for d in data)
    row = lambda v: round((hi - v) / (hi - lo) * (rows - 1))
    parts = []
    for i, (o, h, l, c) in enumerate(data):
        up = c >= o
        top_b, bot_b = row(max(o, c)), row(min(o, c))
        chars = []
        for r in range(row(h), row(l) + 1):
            ch = ("█" if up else "▒") if top_b <= r <= bot_b else "│"
            chars.append(f'<tspan x="{x0 + i * dx}" y="{y0 + r * dy:.1f}">{ch}</tspan>')
        fill = t["accent"] if up else t["down"]
        last = i == cols - 1
        anim = (f'<animate attributeName="opacity" values="1;0.3;1" dur="1.6s" begin="{0.25 + i * 0.09:.2f}s" repeatCount="indefinite"/>'
                if last else "")
        parts.append(
            f'<text font-family="{MONO}" font-size="14" fill="{fill}">{"".join(chars)}{anim}</text>')
    last_close_y = y0 + row(data[-1][3]) * dy - 5
    w = cols * dx
    parts.append(f'<line x1="{x0 - 4}" x2="{x0 + w}" y1="{last_close_y:.1f}" y2="{last_close_y:.1f}" stroke="{t["accent"]}" '
                 f'stroke-opacity="0.55" stroke-dasharray="3 4"><animate attributeName="stroke-dashoffset" values="0;-14" dur="1.2s" repeatCount="indefinite"/></line>')
    base = y0 + (rows - 1) * dy + 12
    parts.append(f'<line x1="{x0 - 4}" x2="{x0 + w}" y1="{base:.1f}" y2="{base:.1f}" stroke="{t["muted"]}" stroke-opacity="0.45"/>')
    return "".join(parts)


TAPE = ("EQUITY RESEARCH  ·  REVERSE DCF  ·  CATALYSTS AND RISKS  ·  BLOOMBERG  ·  CAPITAL IQ  ·  "
        "EXCEL VBA  ·  POWER AUTOMATE  ·  CLAUDE CODE  ·  FMVA  ·  CFA LEVEL I CANDIDATE  ·  ")


def hero(t, uid):
    W, H = 1000, 470
    tdefs, tbody = typing(t, 92, 268)
    tape_w = len(TAPE) * 7.3
    chips = [
        ("Champion", "Eurasia Asset Management Challenge 2026"),
        ("Intern", "Pinnacle Capital Asia, investment research"),
        ("Studying", "FMVA, sitting CFA Level I in November"),
    ]
    chip_svg = []
    for i, (k, v) in enumerate(chips):
        y = 322 + i * 24
        chip_svg.append(
            f'<g>'
            f'<circle cx="70" cy="{y - 5}" r="3" fill="{t["accent"]}"/>'
            f'<text x="84" y="{y}" font-family="{SERIF}" font-size="14.5" fill="{t["muted"]}">'
            f'<tspan fill="{t["ink"]}" font-weight="bold">{k}</tspan>  {escape(v)}</text></g>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Warren Lim, finance student at NTU who builds research tools">
  <title>Warren Lim</title>{backdrop(t, W, H, uid)}
  <defs>{tdefs}<clipPath id="tape{uid}"><rect x="25" y="404" width="950" height="40"/></clipPath></defs>
  {glass(t, 24, 24, 952, 422, 18)}
  <text x="66" y="84" font-family="{SERIF}" font-size="12.5" letter-spacing="2.4" fill="{t['muted']}">NTU SINGAPORE  ·  BANKING &amp; FINANCE  ·  CLASS OF <tspan font-family="{MONO}">2027</tspan></text>
  <text x="64" y="150" font-family="{SERIF}" font-size="58" fill="{t['ink']}">Warren Lim</text>
  <text x="66" y="186" font-family="{SERIF}" font-size="20" font-style="italic" fill="{t['muted']}">a finance student who builds his own research tools</text>
  <rect x="66" y="212" width="44" height="2" fill="{t['accent']}"/>
  <text x="66" y="268" font-family="{SERIF}" font-size="21" fill="{t['accent']}">›</text>
  {tbody}
  {''.join(chip_svg)}
  <text x="586" y="84" font-family="{SERIF}" font-size="13" fill="{t['muted']}">EAMC <tspan font-family="{MONO}">2026</tspan>  ·  <tspan font-family="{MONO}">50</tspan>-stock portfolio, cumulative return</text>
  <text x="586" y="110" font-family="{MONO}" font-size="20" fill="{t['accent']}">+97.1%<tspan font-size="13" fill="{t['muted']}">  vs benchmark +90.5%</tspan></text>
  {ascii_chart(t, 592, 146)}
  <line x1="25" x2="975" y1="404" y2="404" stroke="{t['stroke']}" stroke-opacity="{t['stroke_op']}"/>
  <g clip-path="url(#tape{uid})">
    <text y="429" font-family="{SERIF}" font-size="12" letter-spacing="1.6" fill="{t['muted']}">
      <tspan x="40">{escape(TAPE * 2)}</tspan>
      <animateTransform attributeName="transform" type="translate" values="0 0;-{tape_w:.0f} 0" dur="40s" repeatCount="indefinite"/>
    </text>
  </g>
</svg>"""


# ---------------------------------------------------------------- terminal
TERM = [
    ("cmd", "whoami"),
    ("out", "Warren Lim, Bachelor of Business (Banking & Finance) at NTU, on exchange at SMU this fall"),
    ("cmd", "cat focus.txt"),
    ("out", "Buy-side equity research. A good company is not always a good stock at today's price."),
    ("cmd", "ls track-record/"),
    ("out", "Eurasia AM Challenge 2026: champion, 97.1% vs 90.5% cumulative, Sharpe 0.94 vs 0.86"),
    ("out", "Whitman Independent Advisors: factsheet processing cut from 3 min to 20 s"),
    ("out", "Pinnacle Capital Asia: research on Salesforce, ServiceNow and Copart"),
    ("cmd", "claude --build"),
    ("out", "30+ repos so far: research sites, trading tools, dashboards, automations"),
]


def terminal(t, uid):
    W = 1000
    top, step = 96, 27
    H = top + step * len(TERM) + 46
    body, defs, clock = [], [], 0.4
    for i, (kind, text) in enumerate(TERM):
        y = top + i * step
        if kind == "cmd":
            w = len(text) * 8.6 + 30
            defs.append(f'<clipPath id="cc{uid}{i}"><rect x="56" y="{y - 18}" height="26" width="{w:.0f}">'
                        f'</rect></clipPath>')
            body.append(f'<g clip-path="url(#cc{uid}{i})"><text x="56" y="{y}" font-family="{MONO}" font-size="14.5" fill="{t["accent"]}">$ '
                        f'<tspan fill="{t["ink"]}">{escape(text)}</tspan></text></g>')
            clock += 0.9
        else:
            body.append(f'<text x="78" y="{y}" font-family="{SERIF}" font-size="15.5" fill="{t["muted"]}">'
                        f'{rich(text, t["ink"])}</text>')
            clock += 0.35
    end_y = top + len(TERM) * step
    body.append(f'<text x="56" y="{end_y}" font-family="{MONO}" font-size="14.5" fill="{t["accent"]}">$ '
                f'<tspan fill="{t["ink"]}">▍</tspan>'
                f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" begin="{clock + 0.1:.2f}s" repeatCount="indefinite"/></text>')
    dots = "".join(f'<circle cx="{52 + k * 18}" cy="47" r="5.5" fill="{c}" fill-opacity="0.85"/>'
                   for k, c in enumerate(["#E5806B", "#E6BE5A", "#7DBE7A"]))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="About Warren in a terminal window">
  <title>whoami</title>{backdrop(t, W, H, uid)}
  <defs>{''.join(defs)}</defs>
  <rect x="24" y="24" width="952" height="{H - 48}" rx="16" fill="{t['term']}" fill-opacity="{t['term_op']}" stroke="{t['stroke']}" stroke-opacity="{t['stroke_op']}"/>
  <line x1="24" x2="976" y1="70" y2="70" stroke="{t['stroke']}" stroke-opacity="{t['stroke_op']}"/>
  {dots}
  <text x="500" y="52" text-anchor="middle" font-family="{SERIF}" font-size="13" fill="{t['muted']}">~/warren</text>
  {''.join(body)}
</svg>"""


# ---------------------------------------------------------------- projects
PROJECTS = [
    ("Macro research site", ["US macro indicators with live FRED", "charts, plus company research"], "NEXT.JS · RESEARCH"),
    ("Market dashboard", ["A US market report for each trading", "day, with the tape and the movers"], "TYPESCRIPT · DATA"),
    ("Trading journal", ["Every trade logged and reviewed,", "embedded in my personal site"], "TYPESCRIPT · REVIEW"),
    ("VCP strategy desk", ["Swing-trading rulebook tested on a", "pre-registered out-of-sample run"], "PYTHON · BACKTESTING"),
    ("Bank NAV automation", ["Reads LGT, BoS and UBS statements", "into Excel, each figure screenshotted"], "PYTHON · OCR · OPEN SOURCE"),
    ("Web design skill", ["A Claude Code skill that keeps my", "sites from looking machine-made"], "CLAUDE CODE · DESIGN"),
]


def projects(t, uid):
    W, cw, ch, gap, x0, y0 = 1000, 296, 168, 20, 42, 112
    H = y0 + 2 * ch + gap + 40
    cards = []
    for i, (title, lines, tags) in enumerate(PROJECTS):
        cx = x0 + (i % 3) * (cw + gap)
        cy = y0 + (i // 3) * (ch + gap)
        b = 0.2 + i * 0.12
        desc = "".join(f'<tspan x="{cx + 22}" dy="{0 if k == 0 else 20}">{escape(l)}</tspan>' for k, l in enumerate(lines))
        cards.append(f"""<g>
    <animateTransform attributeName="transform" type="translate" values="0 10;0 0" begin="{b:.2f}s" dur="0.5s" fill="freeze"/>
    {glass(t, cx, cy, cw, ch, 14)}
    <text x="{cx + 22}" y="{cy + 34}" font-family="{MONO}" font-size="12.5" fill="{t['accent']}">0{i + 1}</text>
    <text x="{cx + 22}" y="{cy + 66}" font-family="{SERIF}" font-size="20" fill="{t['ink']}">{escape(title)}</text>
    <text x="{cx + 22}" y="{cy + 96}" font-family="{SERIF}" font-size="14.5" fill="{t['muted']}">{desc}</text>
    <line x1="{cx + 22}" x2="{cx + cw - 22}" y1="{cy + ch - 40}" y2="{cy + ch - 40}" stroke="{t['stroke']}" stroke-opacity="{t['stroke_op']}"/>
    <text x="{cx + 22}" y="{cy + ch - 18}" font-family="{SERIF}" font-size="11" letter-spacing="1.6" fill="{t['accent']}">{escape(tags)}</text>
  </g>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Six projects Warren has built">
  <title>Things I have built</title>{backdrop(t, W, H, uid)}
  <text x="44" y="66" font-family="{SERIF}" font-size="28" fill="{t['ink']}">Things I have built</text>
  <text x="44" y="92" font-family="{SERIF}" font-size="14.5" font-style="italic" fill="{t['muted']}">Most of these repos are private. The live work sits on warrenlimzf.com.</text>
  {''.join(cards)}
</svg>"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        uid = name[0]
        (OUT / f"hero-{name}.svg").write_text(hero(t, uid))
        (OUT / f"terminal-{name}.svg").write_text(terminal(t, uid))
        (OUT / f"projects-{name}.svg").write_text(projects(t, uid))
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))

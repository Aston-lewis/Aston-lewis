kk#!/usr/bin/env python3
"""
Generate assets/terminal.svg: an animated terminal (SMIL, no JavaScript)
for Aston's GitHub profile README.

Usage:
    python gen_terminal.py terminal.svg banner.txt
"""

import sys
from html import escape

OUT = sys.argv[1] if len(sys.argv) > 1 else "terminal.svg"
BANNER = sys.argv[2] if len(sys.argv) > 2 else "banner.txt"

T = 20.0
W, LH, FS = 880, 19, 13.5
X0, Y0 = 26, 70

# ============================================================
# YOUR PROFILE DETAILS
# ============================================================

USERNAME = "Aston-lewis"
NAME = "Aston Valerine Lewis"
EDUCATION = "Computer Engineering · AIML @ SJEC"

SYSTEM = "Omarchy (Arch Linux) x86_64"
WM = "Hyprland"
TERMINAL = "Ghostty · tmux"
EDITOR = "VS Code"
SHELL = "bash"

LANGUAGES = "Python · C++ · C · Java"
FOCUS = "AI · Machine Learning · Computer Vision"
PROJECTS = "Wildfire Detection · Lunar Boulder Detection"
OTHER_PROJECTS = "Local LLMs · RAG · AI Applications"
PROBLEM_SOLVING = "DSA · LeetCode"

C = {
    "bg": "#0d1117",
    "bar": "#161b22",
    "border": "#30363d",
    "text": "#c9d1d9",
    "dim": "#8b949e",
    "green": "#7ee787",
    "blue": "#79c0ff",
    "gold": "#e3b341",
    "arch": "#1793d1",
    "red": "#ff7b72",
    "purple": "#d2a8ff",
}

parts = []


def show(t, end=0.975, attr="opacity"):
    """Show an element at time t and keep it visible until the cycle ends."""
    return (
        f'<animate attributeName="{attr}" values="0;1;0" '
        f'keyTimes="0;{t / T:.4f};{end}" '
        f'dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>'
    )


def letter(ch, t):
    """Reveal one character at a specific time."""
    ch = escape(ch) if ch != " " else "&#160;"

    return (
        f'<tspan fill-opacity="0">{ch}'
        f'{show(t, attr="fill-opacity")}</tspan>'
    )


def text(x, y, content, t, fill=None, extra=""):
    """Add an animated line of terminal text."""
    fill_attr = f' fill="{fill}"' if fill else ""

    parts.append(
        f'<text x="{x}" y="{y}" opacity="0"{fill_attr} {extra}>'
        f'{content}{show(t)}</text>'
    )


def prompt(line, t, cmd, step=0.075):
    """Display a terminal prompt and type its command character by character."""
    y = Y0 + line * LH

    p = (
        f'<tspan fill="{C["green"]}" font-weight="700">'
        f'{escape(USERNAME)}@github</tspan>'
        f'<tspan fill="{C["text"]}">:</tspan>'
        f'<tspan fill="{C["blue"]}" font-weight="700">~</tspan>'
        f'<tspan fill="{C["text"]}">$ </tspan>'
    )

    letters = "".join(
        letter(ch, t + 0.25 + i * step)
        for i, ch in enumerate(cmd)
    )

    parts.append(
        f'<text x="{X0}" y="{y}" opacity="0">'
        f'{p}<tspan fill="{C["text"]}">{letters}</tspan>'
        f'{show(t)}</text>'
    )

    return t + 0.25 + len(cmd) * step


# ============================================================
# WHOAMI + BANNER
# ============================================================

line = 0
t = prompt(line, 0.5, "whoami")

try:
    with open(BANNER, encoding="utf-8") as f:
        banner = [
            row.rstrip()
            for row in f.read().splitlines()
            if row.strip()
        ]
except FileNotFoundError:
    banner = [
        "    _    _                 _",
        "   / \\  | |__   ___  _ __ | |",
        "  / _ \\ | '_ \\ / _ \\| '_ \\| |",
        " / ___ \\| |_) | (_) | | | | |",
        "/_/   \\_\\_.__/ \\___/|_| |_|_|",
    ]

t += 0.3

# Animated banner shine
BLH = 15.5
by = Y0 + (line + 1) * LH

for i, row in enumerate(banner):
    text(
        X0,
        by + i * BLH,
        escape(row),
        t + i * 0.07,
        "url(#shine)",
        'filter="url(#glow)" xml:space="preserve"',
    )

line += -(-int(len(banner) * BLH) // LH)
t += len(banner) * 0.07 + 0.25

line += 1

# Name and education
text(
    X0,
    Y0 + line * LH,
    (
        f'<tspan fill="{C["text"]}" font-weight="700">'
        f'{escape(NAME)}</tspan>'
        f'<tspan fill="{C["dim"]}">'
        f'  ·  {escape(EDUCATION)}</tspan>'
    ),
    t,
)

line += 1

text(
    X0,
    Y0 + line * LH,
    (
        f'<tspan fill="{C["dim"]}">'
        f'AI · Machine Learning · Computer Vision · DSA'
        f'</tspan>'
    ),
    t + 0.15,
)


# ============================================================
# FASTFETCH
# ============================================================

line += 2
t = prompt(line, t + 0.6, "fastfetch")
t += 0.35

first = line + 1

# Arch-style terminal logo
logo = [
    "        /\\",
    "       /  \\",
    "      /\\   \\",
    "     /      \\",
    "    /   ,,   \\",
    "   /   |  |  -\\",
    "  /_-''    ''-_\\",
]

for i, row in enumerate(logo):
    text(
        X0,
        Y0 + (first + 1 + i) * LH,
        escape(row),
        t + i * 0.05,
        C["arch"],
        'font-weight="700" xml:space="preserve"',
    )

IX = X0 + 175

info = [
    (USERNAME, ""),
    ("───────────────", None),
    ("OS", SYSTEM),
    ("WM", WM),
    ("Terminal", TERMINAL),
    ("Editor", EDITOR),
    ("Shell", SHELL),
    ("Focus", FOCUS),
    ("Languages", LANGUAGES),
    ("Projects", PROJECTS),
    ("Also", OTHER_PROJECTS),
    ("Problem Solving", PROBLEM_SOLVING),
]

for i, (key, value) in enumerate(info):
    y = Y0 + (first + i) * LH

    if i == 0:
        content = (
            f'<tspan fill="{C["green"]}" font-weight="700">'
            f'{escape(key)}</tspan>'
            f'<tspan fill="{C["text"]}">@github</tspan>'
        )

    elif value is None:
        content = f'<tspan fill="{C["dim"]}">{escape(key)}</tspan>'

    else:
        content = (
            f'<tspan fill="{C["gold"]}" font-weight="700">'
            f'{escape(key)}</tspan>'
            f'<tspan x="{IX + 112}" fill="{C["text"]}">'
            f'{escape(value)}</tspan>'
        )

    text(IX, y, content, t + 0.3 + i * 0.12)


# Color palette row
line = first + len(info)

palette = [
    "#484f58",
    C["red"],
    C["green"],
    C["gold"],
    C["blue"],
    C["purple"],
    "#39c5cf",
    "#f0f6fc",
]

blocks = "".join(
    f'<rect x="{IX + j * 22}" '
    f'y="{Y0 + line * LH - 11}" '
    f'width="18" height="12" rx="2" fill="{color}"/>'
    for j, color in enumerate(palette)
)

parts.append(
    f'<g opacity="0">{blocks}'
    f'{show(t + 0.3 + len(info) * 0.12)}</g>'
)

t += 0.3 + len(info) * 0.12 + 0.5


# ============================================================
# PROJECTS / PLAYGROUND
# ============================================================

line += 2
t = prompt(line, t, "cat playground.txt")

line += 1

text(
    X0,
    Y0 + line * LH,
    (
        f'<tspan fill="{C["purple"]}">'
        f'"Building AI that can see, learn, and solve problems."'
        f'</tspan>'
    ),
    t + 0.35,
)

t += 1.0

line += 1

text(
    X0,
    Y0 + line * LH,
    (
        f'<tspan fill="{C["dim"]}">'
        f'Wildfire Detection · Lunar Boulder Detection · Local LLMs'
        f'</tspan>'
    ),
    t,
)

t += 0.8


# ============================================================
# PASSWORD ANIMATION
# ============================================================

line += 2
t = prompt(line, t, "sudo make me-a-sandwich")

line += 1
y = Y0 + line * LH

stars = "".join(
    letter("*", t + 0.6 + i * 0.09)
    for i in range(8)
)

text(
    X0,
    y,
    (
        f'<tspan fill="{C["dim"]}">'
        f'[sudo] password for aston: {stars}'
        f'</tspan>'
    ),
    t + 0.3,
)

t += 0.6 + 8 * 0.09 + 0.4

line += 1

text(
    X0,
    Y0 + line * LH,
    f'<tspan fill="{C["green"]}">okay.</tspan>',
    t,
)

t += 0.6


# ============================================================
# FINAL PROMPT + BLINKING CURSOR
# ============================================================

line += 2
y = Y0 + line * LH

p = (
    f'<tspan fill="{C["green"]}" font-weight="700">'
    f'{escape(USERNAME)}@github</tspan>'
    f'<tspan fill="{C["text"]}">:</tspan>'
    f'<tspan fill="{C["blue"]}" font-weight="700">~</tspan>'
    f'<tspan fill="{C["text"]}">$ </tspan>'
)

cursor = (
    f'<tspan fill="{C["text"]}">█'
    f'<animate attributeName="fill-opacity" '
    f'values="1;0" dur="1s" repeatCount="indefinite" '
    f'calcMode="discrete"/></tspan>'
)

parts.append(
    f'<text x="{X0}" y="{y}" opacity="0">'
    f'{p}{cursor}{show(t)}</text>'
)

assert t < T * 0.95, (
    f"Animation ({t:.1f}s) does not fit in cycle ({T}s)"
)

H = Y0 + line * LH + 34


# ============================================================
# SVG OUTPUT
# ============================================================

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{W}" height="{H}"
viewBox="0 0 {W} {H}"
role="img"
aria-labelledby="title desc">

<title id="title">{escape(NAME)} — animated terminal</title>

<desc id="desc">
Animated terminal showing Aston's profile, AIML education,
Omarchy, Hyprland, Ghostty, VS Code, AI and machine learning projects.
</desc>

<defs>
  <linearGradient id="shine"
    gradientUnits="userSpaceOnUse"
    x1="0" y1="0" x2="520" y2="0">

    <stop offset="0" stop-color="#c8a56a"/>
    <stop offset="0.42" stop-color="#e3b341"/>
    <stop offset="0.5" stop-color="#fff4d6"/>
    <stop offset="0.58" stop-color="#e3b341"/>
    <stop offset="1" stop-color="#c8a56a"/>

    <animateTransform
      attributeName="gradientTransform"
      type="translate"
      values="-520 0;520 0"
      dur="3.5s"
      repeatCount="indefinite"/>
  </linearGradient>

  <filter id="glow"
    x="-5%" y="-30%" width="110%" height="160%">

    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge>
      <feMergeNode in="b"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <pattern id="scan"
    width="4" height="4"
    patternUnits="userSpaceOnUse">

    <rect width="4" height="2"
      fill="#ffffff" opacity="0.025"/>
  </pattern>
</defs>

<rect width="{W}" height="{H}"
  rx="12" fill="{C['bg']}" stroke="{C['border']}"/>

<path
  d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v24H0z"
  fill="{C['bar']}"/>

<line x1="0" y1="36" x2="{W}" y2="36"
  stroke="{C['border']}"/>

<circle cx="22" cy="18" r="6" fill="#ff5f57"/>
<circle cx="42" cy="18" r="6" fill="#febc2e"/>
<circle cx="62" cy="18" r="6" fill="#28c840"/>

<text
  x="{W / 2}"
  y="23"
  text-anchor="middle"
  fill="{C['dim']}"
  font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
  font-size="12.5">

  {escape(USERNAME)}@github: ~ — {escape(TERMINAL)}
</text>

<g
  font-family="'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
  font-size="{FS}"
  fill="{C['text']}">

{chr(10).join(parts)}

</g>

<rect
  x="1"
  y="37"
  width="{W - 2}"
  height="{H - 38}"
  fill="url(#scan)"
  pointer-events="none"/>

</svg>
'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"{OUT}: {W}x{H}, cycle {T}s, animation {t:.1f}s")

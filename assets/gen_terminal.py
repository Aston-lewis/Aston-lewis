"""Genera assets/terminal.svg: una terminal animada (SMIL, sin JavaScript) para
el README del perfil. GitHub muestra las animaciones SVG dentro de <img>.

Uso: python gen_terminal.py <ruta-salida.svg> <banner.txt>
"""
import sys
from html import escape

OUT, BANNER = sys.argv[1], sys.argv[2]

T = 20.0  # duración del ciclo completo (s); luego vuelve a empezar
W, LH, FS = 880, 19, 13.5
X0, Y0 = 26, 70

C = {
    'bg': '#0d1117', 'bar': '#161b22', 'border': '#30363d', 'text': '#c9d1d9',
    'dim': '#8b949e', 'green': '#7ee787', 'blue': '#79c0ff', 'gold': '#e3b341',
    'arch': '#1793d1', 'red': '#ff7b72', 'purple': '#d2a8ff',
}

parts = []


def show(t, end=0.975, attr='opacity'):
    """Aparece en el segundo `t` y se queda hasta el final del ciclo."""
    return (f'<animate attributeName="{attr}" values="0;1;0" keyTimes="0;{t / T:.4f};{end}" '
            f'dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>')


def letter(ch, t):
    """Letra que aparece en `t` (fill-opacity: funciona en <tspan>, opacity no)."""
    ch = escape(ch) if ch != ' ' else '&#160;'
    return f'<tspan fill-opacity="0">{ch}{show(t, attr="fill-opacity")}</tspan>'


def text(x, y, content, t, fill=None, extra=''):
    fill_attr = f' fill="{fill}"' if fill else ''
    parts.append(f'<text x="{x}" y="{y}" opacity="0"{fill_attr} {extra}>{content}{show(t)}</text>')


def prompt(line, t, cmd, step=0.075):
    """Prompt que aparece en `t` y luego "teclea" `cmd` letra por letra."""
    y = Y0 + line * LH
    p = (f'<tspan fill="{C["green"]}" font-weight="700">pablo@slylem0</tspan>'
         f'<tspan fill="{C["text"]}">:</tspan><tspan fill="{C["blue"]}" font-weight="700">~</tspan>'
         f'<tspan fill="{C["text"]}">$ </tspan>')
    # Prompt y letras en el mismo <text>: las letras siguen al prompt sin
    # depender del ancho de la fuente.
    letters = ''.join(letter(ch, t + 0.25 + i * step) for i, ch in enumerate(cmd))
    parts.append(f'<text x="{X0}" y="{y}" opacity="0">{p}<tspan fill="{C["text"]}">{letters}</tspan>'
                 f'{show(t)}</text>')
    return t + 0.25 + len(cmd) * step


line = 0
t = prompt(line, 0.5, 'whoami')

# Banner ANSI Shadow con brillo que recorre las letras.
banner = [l.rstrip() for l in open(BANNER, encoding='utf-8').read().splitlines() if l.strip()]
t += 0.3
# Las letras de bloque necesitan un interlineado igual a la altura de la
# fuente (con el de 19 px quedaban rayas entre filas).
BLH = 15.5
by = Y0 + (line + 1) * LH
for i, row in enumerate(banner):
    text(X0, by + i * BLH, escape(row), t + i * 0.07, 'url(#shine)',
         'filter="url(#glow)" xml:space="preserve"')
line += -(-int(len(banner) * BLH) // LH)  # filas de 19 px que ocupa el banner
t += len(banner) * 0.07 + 0.25
line += 1
text(X0, Y0 + line * LH,
     f'<tspan fill="{C["text"]}" font-weight="700">Pablo Nicolás Marín</tspan>'
     f'<tspan fill="{C["dim"]}">  ·  Systems Engineering @ Universidad del Valle, Colombia</tspan>', t)
line += 1
text(X0, Y0 + line * LH,
     f'<tspan fill="{C["dim"]}">cloud · linux · algorithms · math &amp; logic · a little bit of quantum</tspan>',
     t + 0.15)

# fastfetch con el logo de Arch.
line += 2
t = prompt(line, t + 0.6, 'fastfetch')
logo = [
    '        /\\',
    '       /  \\',
    '      /\\   \\',
    '     /      \\',
    '    /   ,,   \\',
    '   /   |  |  -\\',
    '  /_-\'\'    \'\'-_\\',
]
info = [
    ('pablo', '@slylem0'),
    ('───────────────', None),
    ('OS', 'Omarchy (Arch Linux) x86_64'),
    ('WM', 'Hyprland'),
    ('Terminal', 'Ghostty · tmux'),
    ('Editor', 'Neovim (LazyVim)'),
    ('Shell', 'bash + starship'),
    ('Cloud', 'AWS · Lambda · DynamoDB · Bedrock · CDK'),
    ('Langs', 'TypeScript · Python · C++ · Java · Go'),
    ('Club', 'AWS Student Builder Group @ Univalle'),
]
t += 0.35
first = line + 1
for i, row in enumerate(logo):
    text(X0, Y0 + (first + 1 + i) * LH, escape(row), t + i * 0.05, C['arch'],
         'font-weight="700" xml:space="preserve"')
IX = X0 + 175
for i, (k, v) in enumerate(info):
    y = Y0 + (first + i) * LH
    if i == 0:
        content = (f'<tspan fill="{C["green"]}" font-weight="700">{k}</tspan>'
                   f'<tspan fill="{C["text"]}">{v}</tspan>')
    elif v is None:
        content = f'<tspan fill="{C["dim"]}">{k}</tspan>'
    else:
        content = (f'<tspan fill="{C["gold"]}" font-weight="700">{k}</tspan>'
                   f'<tspan x="{IX + 78}" fill="{C["text"]}">{escape(v)}</tspan>')
    text(IX, y, content, t + 0.3 + i * 0.12)
line = first + len(info)
palette = ['#484f58', C['red'], C['green'], C['gold'], C['blue'], C['purple'], '#39c5cf', '#f0f6fc']
blocks = ''.join(f'<rect x="{IX + j * 22}" y="{Y0 + line * LH - 11}" width="18" height="12" rx="2" fill="{c}"/>'
                 for j, c in enumerate(palette))
parts.append(f'<g opacity="0">{blocks}{show(t + 0.3 + len(info) * 0.12)}</g>')
t += 0.3 + len(info) * 0.12 + 0.5

# Lema.
line += 2
t = prompt(line, t, 'cat playground.txt')
line += 1
text(X0, Y0 + line * LH,
     f'<tspan fill="{C["purple"]}">"Math, Logic &amp; Cybersecurity are my playgrounds"</tspan>', t + 0.35)
t += 0.9

# xkcd 149.
line += 2
t = prompt(line, t, 'sudo make me-a-sandwich')
line += 1
y = Y0 + line * LH
stars = ''.join(letter('*', t + 0.6 + i * 0.09) for i in range(8))
text(X0, y, f'<tspan fill="{C["dim"]}">[sudo] password for pablo: {stars}</tspan>', t + 0.3)
t += 0.6 + 8 * 0.09 + 0.4
line += 1
text(X0, Y0 + line * LH, f'<tspan fill="{C["green"]}">okay.</tspan>', t)
t += 0.6

# Prompt final con cursor parpadeante (un bloque █ dentro del mismo <text>).
line += 2
y = Y0 + line * LH
p = (f'<tspan fill="{C["green"]}" font-weight="700">pablo@slylem0</tspan>'
     f'<tspan fill="{C["text"]}">:</tspan><tspan fill="{C["blue"]}" font-weight="700">~</tspan>'
     f'<tspan fill="{C["text"]}">$ </tspan>')
cursor = (f'<tspan fill="{C["text"]}">█<animate attributeName="fill-opacity" values="1;0" '
          f'dur="1s" repeatCount="indefinite" calcMode="discrete"/></tspan>')
parts.append(f'<text x="{X0}" y="{y}" opacity="0">{p}{cursor}{show(t)}</text>')

assert t < T * 0.95, f'la animación ({t:.1f}s) no cabe en el ciclo ({T}s)'
H = Y0 + line * LH + 34

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">Pablo Nicolás Marín (Slylem0) terminal</title>
<desc id="desc">Animated terminal: whoami prints the SLYLEM0 banner, fastfetch shows Omarchy, Hyprland, Neovim and an AWS, TypeScript, Python, C++, Java and Go stack, then "Math, Logic and Cybersecurity are my playgrounds".</desc>
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="520" y2="0">
    <stop offset="0" stop-color="#c8a56a"/>
    <stop offset="0.42" stop-color="#e3b341"/>
    <stop offset="0.5" stop-color="#fff4d6"/>
    <stop offset="0.58" stop-color="#e3b341"/>
    <stop offset="1" stop-color="#c8a56a"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-520 0;520 0" dur="3.5s" repeatCount="indefinite"/>
  </linearGradient>
  <filter id="glow" x="-5%" y="-30%" width="110%" height="160%">
    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="2" fill="#ffffff" opacity="0.025"/>
  </pattern>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{C['bg']}" stroke="{C['border']}"/>
<path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v24H0z" fill="{C['bar']}"/>
<line x1="0" y1="36" x2="{W}" y2="36" stroke="{C['border']}"/>
<circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/><circle cx="62" cy="18" r="6" fill="#28c840"/>
<text x="{W / 2}" y="23" text-anchor="middle" fill="{C['dim']}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12.5">pablo@slylem0: ~ — ghostty</text>
<g font-family="'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace" font-size="{FS}" fill="{C['text']}">
{chr(10).join(parts)}
</g>
<rect x="1" y="37" width="{W - 2}" height="{H - 38}" fill="url(#scan)" pointer-events="none"/>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print(f'{OUT}: {W}x{H}, ciclo {T}s, animación {t:.1f}s')

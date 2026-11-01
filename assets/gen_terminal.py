#!/usr/bin/env python3

"""
Animated terminal SVG generator for a GitHub profile README.

Usage:
    python gen_terminal.py terminal.svg banner.txt

If banner.txt is omitted, the default banner is used.
"""

import html
import sys
from pathlib import Path


# ============================================================
# CUSTOMIZE YOUR PROFILE DETAILS HERE
# ============================================================

USERNAME = "Aston-lewis"
NAME = "Aston Valerine Lewis"
EDUCATION = "AIML @ SJEC"

# Your terminal setup
TERMINAL = "Ghostty"
MULTIPLEXER = "tmux"

# Your system and tools
OS = "Omarchy (Arch Linux)"
WM = "Hyprland"
EDITOR = "VS Code"
SHELL = "bash"

# Your interests / skills
INTERESTS = "AI · Machine Learning"
LANGUAGES = "Python · C++ · C"
FOCUS = "Computer Vision · ML"

# Password prompt label
PASSWORD_LABEL = "password for aston"


# ============================================================
# SVG / ANIMATION SETTINGS
# ============================================================

WIDTH = 880
HEIGHT = 655

# Total animation duration
CYCLE = 20

# Main terminal colors
BACKGROUND = "#0d1117"
TERMINAL_BG = "#161b22"
BORDER = "#30363d"
TEXT_COLOR = "#c9d1d9"
MUTED_COLOR = "#8b949e"
GREEN = "#3fb950"
BLUE = "#58a6ff"
YELLOW = "#d29922"
RED = "#f85149"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def esc(value):
    """Escape text so it can safely be inserted into SVG."""
    return html.escape(str(value), quote=True)


def show(content, start, duration=1.0):
    """Show an SVG element during a specific time interval."""
    end = start + duration

    return f"""
    <g opacity="0">
        {content}
        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="{start}s"
            dur="{duration}s"
            repeatCount="indefinite"
        />
    </g>
    """


def letter(char, start, duration=0.04):
    """Create a single animated character."""
    return f"""
    <tspan opacity="0">
        {esc(char)}
        <animate
            attributeName="opacity"
            from="0"
            to="1"
            begin="{start}s"
            dur="0.01s"
            fill="freeze"
            repeatCount="indefinite"
        />
    </tspan>
    """


def text_line(value, x, y, color=TEXT_COLOR, size=14, weight="normal"):
    """Create a regular SVG text line."""
    return f"""
    <text
        x="{x}"
        y="{y}"
        fill="{color}"
        font-family="monospace"
        font-size="{size}"
        font-weight="{weight}"
    >{esc(value)}</text>
    """


def prompt(command, start, y, username=USERNAME):
    """Create a terminal prompt with a command."""
    prompt_text = f"{username}@github:~$ {command}"

    return f"""
    <text
        x="32"
        y="{y}"
        fill="{GREEN}"
        font-family="monospace"
        font-size="14"
        opacity="0"
    >{esc(prompt_text)}
        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="{start}s"
            dur="2.5s"
            repeatCount="indefinite"
        />
    </text>
    """


def animated_text(value, x, y, start, color=TEXT_COLOR, size=14, speed=0.035):
    """Create text that appears one character at a time."""
    elements = []

    for index, char in enumerate(value):
        char_start = start + index * speed

        elements.append(
            f"""
            <text
                x="{x + index * 8.4}"
                y="{y}"
                fill="{color}"
                font-family="monospace"
                font-size="{size}"
                opacity="0"
            >{esc(char)}
                <animate
                    attributeName="opacity"
                    values="0;1;1;0"
                    keyTimes="0;0.001;0.999;1"
                    begin="{char_start}s"
                    dur="3s"
                    repeatCount="indefinite"
                />
            </text>
            """
        )

    return "\n".join(elements)


# ============================================================
# FASTFETCH-STYLE OUTPUT
# ============================================================

def fastfetch_output(start=4.0):
    """Create the profile's fastfetch-style terminal output."""

    lines = [
        ("Name", NAME, GREEN),
        ("Education", EDUCATION, BLUE),
        ("OS", OS, YELLOW),
        ("WM", WM, BLUE),
        ("Terminal", f"{TERMINAL} + {MULTIPLEXER}", GREEN),
        ("Editor", EDITOR, YELLOW),
        ("Shell", SHELL, BLUE),
        ("Interests", INTERESTS, GREEN),
        ("Languages", LANGUAGES, YELLOW),
        ("Focus", FOCUS, BLUE),
    ]

    output = []

    # Fastfetch-style logo
    logo = [
        "        /\\",
        "       /  \\",
        "      /\\   \\",
        "     /      \\",
        "    /   ,,   \\",
        "   /   |  |   \\",
        "  /_-''    ''-_\\",
    ]

    logo_x = 38
    logo_y = 210

    for i, line in enumerate(logo):
        output.append(
            text_line(
                line,
                logo_x,
                logo_y + i * 17,
                color=BLUE,
                size=13,
                weight="bold",
            )
        )

    # Profile information
    info_x = 260
    info_y = 210

    for i, (label, value, color) in enumerate(lines):
        y = info_y + i * 24

        output.append(
            text_line(
                f"{label}:",
                info_x,
                y,
                color=color,
                size=14,
                weight="bold",
            )
        )

        output.append(
            text_line(
                value,
                info_x + 105,
                y,
                color=TEXT_COLOR,
                size=14,
            )
        )

    # Make all output appear after the command
    combined = "\n".join(output)

    return f"""
    <g opacity="0">
        {combined}
        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="{start}s"
            dur="12s"
            repeatCount="indefinite"
        />
    </g>
    """


# ============================================================
# BANNER
# ============================================================

def load_banner(filename=None):
    """Load a banner from a text file, or use a default banner."""

    if filename:
        banner_path = Path(filename)

        if banner_path.exists():
            return banner_path.read_text(encoding="utf-8").rstrip()

    return r"""
     _              _                   _
    / \   ___  ___ | |_ ___  _ __      | | _____      ___ __
   / _ \ / __|/ _ \| __/ _ \| '_ \  _  | |/ _ \ \ /\ / / '_ \
  / ___ \\__ \ (_) | || (_) | | | || |_| |  __/\ V  V /| | | |
 /_/   \_\___/\___/ \__\___/|_| |_| \___/ \___| \_/\_/ |_| |_|
"""


def banner_svg(banner, start=0.7):
    """Render a banner with a subtle shine animation."""

    lines = banner.splitlines()
    output = []

    for i, line in enumerate(lines):
        output.append(
            text_line(
                line,
                32,
                105 + i * 17,
                color=GREEN,
                size=12,
                weight="bold",
            )
        )

    content = "\n".join(output)

    return f"""
    <g opacity="0">
        {content}
        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="{start}s"
            dur="19s"
            repeatCount="indefinite"
        />
    </g>
    """


# ============================================================
# TERMINAL ANIMATION
# ============================================================

def build_terminal(banner):
    """Build the complete animated SVG terminal."""

    elements = []

    # --------------------------------------------------------
    # Terminal window frame
    # --------------------------------------------------------

    elements.append(f"""
    <rect
        width="{WIDTH}"
        height="{HEIGHT}"
        rx="14"
        fill="{TERMINAL_BG}"
        stroke="{BORDER}"
        stroke-width="1.5"
    />
    """)

    # Title bar
    elements.append(f"""
    <rect
        x="0"
        y="0"
        width="{WIDTH}"
        height="42"
        rx="14"
        fill="#21262d"
    />

    <rect
        x="0"
        y="28"
        width="{WIDTH}"
        height="14"
        fill="#21262d"
    />
    """)

    # Window control buttons
    for i, color in enumerate([RED, YELLOW, GREEN]):
        elements.append(f"""
        <circle
            cx="{22 + i * 20}"
            cy="21"
            r="6"
            fill="{color}"
        />
        """)

    # Window title
    elements.append(
        text_line(
            f"{USERNAME}@github — {TERMINAL}",
            320,
            26,
            color=MUTED_COLOR,
            size=13,
        )
    )

    # --------------------------------------------------------
    # Intro prompt
    # --------------------------------------------------------

    elements.append(prompt("neofetch", 0.2, 75))

    # Banner
    elements.append(banner_svg(banner, start=0.8))

    # --------------------------------------------------------
    # Fastfetch output
    # --------------------------------------------------------

    elements.append(fastfetch_output(start=4.0))

    # --------------------------------------------------------
    # Password prompt
    # --------------------------------------------------------

    password_y = 500

    password_content = f"""
    <text
        x="32"
        y="{password_y}"
        fill="{GREEN}"
        font-family="monospace"
        font-size="14"
    >{esc(USERNAME)}@github:~$ sudo unlock
    </text>

    <text
        x="32"
        y="{password_y + 25}"
        fill="{TEXT_COLOR}"
        font-family="monospace"
        font-size="14"
    >[sudo] {esc(PASSWORD_LABEL)}:
    </text>

    <text
        x="32"
        y="{password_y + 50}"
        fill="{GREEN}"
        font-family="monospace"
        font-size="14"
    >Welcome back, {esc(USERNAME)}!
    </text>
    """

    elements.append(f"""
    <g opacity="0">
        {password_content}
        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="15s"
            dur="4s"
            repeatCount="indefinite"
        />
    </g>
    """)

    # --------------------------------------------------------
    # Final prompt + blinking cursor
    # --------------------------------------------------------

    final_y = 600

    elements.append(f"""
    <g opacity="0">
        <text
            x="32"
            y="{final_y}"
            fill="{GREEN}"
            font-family="monospace"
            font-size="14"
        >{esc(USERNAME)}@github:~$</text>

        <rect
            x="205"
            y="{final_y - 14}"
            width="9"
            height="17"
            fill="{GREEN}"
        >
            <animate
                attributeName="opacity"
                values="1;0;1"
                dur="1s"
                repeatCount="indefinite"
            />
        </rect>

        <animate
            attributeName="opacity"
            values="0;1;1;0"
            keyTimes="0;0.001;0.999;1"
            begin="18s"
            dur="2s"
            repeatCount="indefinite"
        />
    </g>
    """)

    # --------------------------------------------------------
    # SVG wrapper
    # --------------------------------------------------------

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-labelledby="title description"
>
    <title id="title">{esc(NAME)} — Animated Terminal</title>
    <desc id="description">
        Animated terminal showing {esc(NAME)}, {esc(EDUCATION)},
        and a fastfetch-style system summary.
    </desc>

    <rect
        width="{WIDTH}"
        height="{HEIGHT}"
        rx="14"
        fill="{BACKGROUND}"
    />

    {"".join(elements)}
</svg>
"""


# ============================================================
# MAIN
# ============================================================

def main():
    """Generate the SVG file."""

    output_file = sys.argv[1] if len(sys.argv) > 1 else "terminal.svg"
    banner_file = sys.argv[2] if len(sys.argv) > 2 else None

    banner = load_banner(banner_file)
    svg = build_terminal(banner)

    Path(output_file).write_text(svg, encoding="utf-8")

    print(f"Generated: {output_file}")
    print(f"Dimensions: {WIDTH}x{HEIGHT}")
    print(f"Animation cycle: {CYCLE}s")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_terminal.py - animated Linux terminal SVG generator (single file, stdlib only).

    python gen_terminal.py                 # writes terminal.svg
    python gen_terminal.py -o assets/t.svg # custom output path
    python gen_terminal.py --static        # no animation (final frame only)
    python gen_terminal.py --speed 1.5     # 1.5x faster typing/output
    python gen_terminal.py --width 820     # display width in px (height follows)

Everything - logo, info, commands, colours, timing, rendering - lives in this
file. To change the logo, edit ONLY the DISTRO_ASCII variable below.

Embed in your README with:
    ![terminal](terminal.svg)
"""

from __future__ import annotations

import argparse
import copy
import random
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional, Sequence, Union
from xml.sax.saxutils import escape, quoteattr

# =============================================================================
# 1. USER CONFIGURATION  (edit freely)
# =============================================================================

USERNAME = "aston"
HOSTNAME = "omarchy"
CWD = "~"
OUTPUT_FILE = "terminal.svg"
WINDOW_TITLE = None  # None -> "<user>@<host>: <cwd>"

# -----------------------------------------------------------------------------
# >>> LOGO: paste your distro's ASCII / Braille / Unicode logo between the
# >>> triple quotes. Indentation, spaces and line breaks are preserved.
# >>> It is a raw string (r"""), so backslashes can be pasted as-is.
# >>> Leading/trailing blank lines are ignored. (Sample below is a placeholder.)
# -----------------------------------------------------------------------------
DISTRO_ASCII = r"""
                   o+
                  ooo
                 +oooo
                +oooooo
                +oooooo+
              /:-:++oooo+
             /++++/+++++++
            /++++++++++++++
           ooosssso++osssssso
          ossssso-````/ossssss
         sssssso.      :sssssss
        sssssss/        osssso++
       ssssssss/        +ssssooo/
     ossssso+/:-        -:/+osssso
    sso+:-`                 `.-/+os
   +:.                           `-/      `
"""

# Logo colour(s): a single colour, or a list that is spread over the logo in
# vertical bands (e.g. ["#89b4fa", "#74c7ec", "#94e2d5"]). Names from PALETTE
# ("blue", "cyan", ...) or any hex colour work.
LOGO_COLORS = ["#89b4fa"]
LOGO_GAP = 3  # blank columns between logo and info

# Right-hand column of the fastfetch output: (label, value). Use ("", "") or
# (None, None) for a blank spacer line. " · " separators are dimmed automatically.
INFO = [
    ("Name", "Aston Valerine Lewis"),
    ("Education", "AIML @ SJEC"),
    ("OS", "Omarchy (Arch Linux)"),
    ("WM", "Hyprland"),
    ("Terminal", "Ghostty + tmux"),
    ("Editor", "VS Code"),
    ("Shell", "bash"),
    ("Interests", "AI · Machine Learning"),
    ("Languages", "Python · C++ · C"),
    ("Focus", "Computer Vision · ML"),
]
SHOW_TITLE = True      # "user@host" + separator line above the info
SHOW_PALETTE = True    # row of colour swatches below the info
TITLE_COLOR = "blue"
KEY_COLOR = "blue"
VALIGN = "center"      # "center" or "top": alignment of the shorter column


@dataclass
class Command:
    """One shell command and what it prints.

    output may be:
      None             -> prints nothing
      "@fastfetch"     -> the two-column fastfetch block (logo + INFO)
      "text\\nmore"    -> plain multi-line text
      [line, ...]      -> list of lines; a line is a str or a list of
                          segments, a segment being "text" or
                          (text, colour) or (text, colour, bold)
    The command "clear" starts a fresh screen.
    """
    text: str
    output: Union[None, str, Sequence] = None
    line_delay: Optional[float] = None    # seconds between output lines
    pause: Optional[float] = None         # idle time at the prompt before typing
    typing_speed: Optional[float] = None  # seconds per character


def dirs(*names: str, color: str = "blue") -> list:
    """Helper for `ls`-style output: names joined by two spaces, coloured."""
    line: list = []
    for i, name in enumerate(names):
        if i:
            line.append("  ")
        line.append((name, color, True))
    return [line]


# Sample content (placeholders - replace with your own). Add, remove or reorder.
COMMANDS = [
    Command("whoami", [[("aston", "fg")]]),
    Command("fastfetch", "@fastfetch", line_delay=0.05),
    Command("ls projects/", dirs(
        "face-detector", "digit-classifier", "image-segmentation",
        "ml-notebooks", "dotfiles")),
    Command("ls skills/", dirs(
        "python", "cpp", "c", "opencv", "pytorch", "numpy", "scikit-learn")),
    Command('echo "Welcome to my GitHub!"', [[("Welcome to my GitHub!", "yellow", True)]]),
]

# --- colours (Catppuccin Mocha inspired) ---
THEME = {
    "bg": "#1e1e2e",
    "fg": "#cdd6f4",
    "titlebar": "#181825",
    "border": "#45475a",
    "title": "#a6adc8",
    "muted": "#6c7086",
    "cursor": "#f5e0dc",
    "shadow": "#000000",
    "btn_close": "#ff5f56",
    "btn_min": "#ffbd2e",
    "btn_max": "#27c93f",
}
PALETTE = {
    "black": "#45475a", "red": "#f38ba8", "green": "#a6e3a1", "yellow": "#f9e2af",
    "blue": "#89b4fa", "magenta": "#cba6f7", "cyan": "#94e2d5", "white": "#bac2de",
}

# --- geometry ---
FONT_FAMILY = ("'JetBrains Mono','Fira Code','Cascadia Mono','DejaVu Sans Mono',"
               "'SF Mono',Menlo,Consolas,'Noto Sans Mono','Liberation Mono',monospace")
FONT_SIZE = 14.0
CHAR_RATIO = 0.6        # monospace advance width / font size (grid is enforced)
LINE_HEIGHT = 1.5       # multiple of FONT_SIZE
PAD_X = 22
PAD_Y = 18
TITLEBAR_H = 38
MARGIN = 26             # outer space (room for the shadow)
CORNER_RADIUS = 12
TERM_COLS = None        # None -> auto-fit content
TERM_ROWS = None        # None -> auto-fit tallest screen
MAX_AUTO_ROWS = 50      # auto mode: start a new screen when more rows are needed
MIN_COLS = 64
DISPLAY_WIDTH = None    # px width attribute of the <svg>; None -> natural size

# --- timing (seconds) ---
TYPING_SPEED = 0.07
TYPING_JITTER = 0.45    # 0..1 random variation of each keystroke
START_DELAY = 0.9       # empty terminal before the first prompt appears
COMMAND_PAUSE = 1.0     # idle at a fresh prompt before typing starts
POST_TYPE_DELAY = 0.4   # pause between last keystroke and "Enter"
OUTPUT_DELAY = 0.12     # Enter -> first output line
LINE_DELAY = 0.05       # between output lines
PROMPT_DELAY = 0.2      # last output line -> next prompt
PAGE_FADE = 0.4         # fade-out time when a screen is cleared / loop restarts
END_HOLD = 5.0          # final prompt idles this long before the loop restarts
CURSOR_BLINK = 0.5      # half period of cursor blink
SEED = 7                # RNG seed for typing jitter (deterministic output)


# =============================================================================
# 2. SETTINGS, ERRORS, TEXT UTILITIES
# =============================================================================

class ConfigError(Exception):
    """Raised for invalid user configuration (reported without a traceback)."""


@dataclass
class Settings:
    """Snapshot of the module-level config (so the CLI can override safely)."""
    username: str
    hostname: str
    cwd: str
    output_file: str
    window_title: Optional[str]
    distro_ascii: str
    logo_colors: Union[str, list]
    logo_gap: int
    info: list
    show_title: bool
    show_palette: bool
    title_color: str
    key_color: str
    valign: str
    commands: list
    theme: dict
    palette: dict
    font_family: str
    font_size: float
    char_ratio: float
    line_height: float
    pad_x: float
    pad_y: float
    titlebar_h: float
    margin: float
    corner_radius: float
    term_cols: Optional[int]
    term_rows: Optional[int]
    max_auto_rows: int
    min_cols: int
    display_width: Optional[float]
    typing_speed: float
    typing_jitter: float
    start_delay: float
    command_pause: float
    post_type_delay: float
    output_delay: float
    line_delay: float
    prompt_delay: float
    page_fade: float
    end_hold: float
    cursor_blink: float
    seed: int

    @classmethod
    def from_module(cls) -> "Settings":
        g = globals()
        return cls(**{f.name: copy.deepcopy(g[f.name.upper()]) for f in fields(cls)})

    # -- helpers -------------------------------------------------------------
    def color(self, name: str) -> str:
        """Resolve a theme/palette name or literal colour to a CSS colour."""
        if name in self.theme:
            return self.theme[name]
        if name in self.palette:
            return self.palette[name]
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", name) or re.fullmatch(r"[A-Za-z]+", name) \
                or re.fullmatch(r"rgba?\([0-9., %]+\)", name):
            return name
        raise ConfigError(f"Unknown colour {name!r}: use a THEME/PALETTE name, a hex "
                          f"colour like '#89b4fa', or a CSS colour name.")

    @property
    def cw(self) -> float:
        return self.font_size * self.char_ratio

    @property
    def lh(self) -> float:
        return self.font_size * self.line_height

    @property
    def row_limit(self) -> int:
        return self.term_rows or self.max_auto_rows

    def validate(self) -> None:
        if not isinstance(self.commands, (list, tuple)) or not self.commands:
            raise ConfigError("COMMANDS must be a non-empty list of Command(...) objects.")
        for i, c in enumerate(self.commands):
            if not isinstance(c, Command):
                raise ConfigError(f"COMMANDS[{i}] is not a Command(...) object.")
            if not isinstance(c.text, str):
                raise ConfigError(f"COMMANDS[{i}].text must be a string.")
        for name in ("typing_speed", "font_size", "char_ratio", "line_height", "cursor_blink"):
            if getattr(self, name) <= 0:
                raise ConfigError(f"{name.upper()} must be greater than 0.")
        for name in ("start_delay", "command_pause", "post_type_delay", "output_delay",
                     "line_delay", "prompt_delay", "page_fade", "end_hold"):
            if getattr(self, name) < 0:
                raise ConfigError(f"{name.upper()} must not be negative.")
        if not 0 <= self.typing_jitter < 1:
            raise ConfigError("TYPING_JITTER must be in the range [0, 1).")
        if self.valign not in ("center", "top"):
            raise ConfigError('VALIGN must be "center" or "top".')
        if self.term_rows is not None and self.term_rows < 2:
            raise ConfigError("TERM_ROWS must be at least 2.")
        if not isinstance(self.info, (list, tuple)):
            raise ConfigError("INFO must be a list of (label, value) pairs.")
        for i, item in enumerate(self.info):
            if not (isinstance(item, (tuple, list)) and len(item) == 2):
                raise ConfigError(f"INFO[{i}] must be a (label, value) pair.")
        for key in ("bg", "fg", "titlebar", "border", "title", "muted", "cursor", "shadow",
                    "btn_close", "btn_min", "btn_max"):
            if key not in self.theme:
                raise ConfigError(f"THEME is missing the key {key!r}.")
        for key in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            if key not in self.palette:
                raise ConfigError(f"PALETTE is missing the key {key!r}.")
        colors = self.logo_colors if isinstance(self.logo_colors, (list, tuple)) else [self.logo_colors]
        if not colors:
            raise ConfigError("LOGO_COLORS must contain at least one colour.")
        for c in list(colors) + [self.title_color, self.key_color]:
            self.color(c)


_XML_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def sanitize(text: str) -> str:
    """Remove characters that are illegal in XML and expand tabs."""
    return _XML_BAD.sub("", text.replace("\r", "").expandtabs(4))


def cell_width(ch: str) -> int:
    """Terminal cell width of one character (0 combining, 2 wide, else 1)."""
    if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def cell_len(text: str) -> int:
    return sum(cell_width(c) for c in text)


# =============================================================================
# 3. CONTENT MODEL  (prompt, fastfetch, generic output -> rows of cells)
# =============================================================================

@dataclass(frozen=True)
class Segment:
    text: str
    color: str = "fg"
    bold: bool = False
    bg: Optional[str] = None


Cells = list  # list[tuple[int, Segment]]  (column, segment)


def prepare_logo(raw: str) -> list:
    """Split DISTRO_ASCII into [(indent, text)], preserving indentation."""
    lines = [sanitize(l).rstrip(" ") for l in raw.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    out = []
    for l in lines:
        stripped = l.lstrip(" ")
        out.append((len(l) - len(stripped), stripped))
    return out


class ContentBuilder:
    """Turns settings into rows of positioned, coloured segments."""

    def __init__(self, s: Settings):
        self.s = s
        self.prompt_text = f"{s.username}@{s.hostname}:{s.cwd}$ "
        self.prompt_cols = cell_len(self.prompt_text)

    # -- prompt --------------------------------------------------------------
    def prompt_cells(self) -> Cells:
        s = self.s
        parts = [
            (f"{s.username}@{s.hostname}", "green", True),
            (":", "fg", False),
            (s.cwd, "blue", True),
            ("$", "fg", False),
        ]
        return self._sequence([Segment(sanitize(t), c, b) for t, c, b in parts])

    @staticmethod
    def _sequence(segs: Sequence[Segment], col: int = 0) -> Cells:
        cells = []
        for seg in segs:
            cells.append((col, seg))
            col += cell_len(seg.text)
        return cells

    # -- generic output ------------------------------------------------------
    def output_rows(self, spec) -> list:
        if spec is None:
            return []
        if isinstance(spec, str):
            if spec.strip() == "@fastfetch":
                return self.fastfetch_rows()
            spec = spec.split("\n")
        if not isinstance(spec, (list, tuple)):
            raise ConfigError("Command output must be None, a string or a list of lines.")
        return [self._line(line) for line in spec]

    def _line(self, line) -> Cells:
        if isinstance(line, str):
            return self._sequence([Segment(sanitize(line))])
        if not isinstance(line, (list, tuple)):
            raise ConfigError(f"Output line {line!r} must be a str or a list of segments.")
        segs = []
        for item in line:
            if isinstance(item, str):
                segs.append(Segment(sanitize(item)))
            elif isinstance(item, (list, tuple)) and 1 <= len(item) <= 3 and isinstance(item[0], str):
                text = sanitize(item[0])
                color = item[1] if len(item) > 1 else "fg"
                bold = bool(item[2]) if len(item) > 2 else False
                segs.append(Segment(text, color, bold))
            else:
                raise ConfigError(f"Bad output segment {item!r}: use 'text', (text, colour) "
                                  f"or (text, colour, bold).")
        return self._sequence(segs)

    # -- fastfetch -----------------------------------------------------------
    def logo_color(self, i: int, n: int) -> str:
        colors = self.s.logo_colors
        if isinstance(colors, str):
            return colors
        return colors[min(len(colors) - 1, i * len(colors) // max(n, 1))]

    def info_rows(self) -> list:
        s = self.s
        rows: list = []
        if s.show_title:
            title = f"{s.username}@{s.hostname}"
            rows.append(self._sequence([
                Segment(sanitize(s.username), s.title_color, True),
                Segment("@", "fg"),
                Segment(sanitize(s.hostname), s.title_color, True)]))
            rows.append([(0, Segment("-" * cell_len(title), "muted"))])
        entries = [(k, v) for k, v in s.info]
        labels = [cell_len(str(k)) + 1 for k, v in entries if k]
        value_col = (max(labels) + 2) if labels else 0
        for key, value in entries:
            if not key and not value:
                rows.append([])
                continue
            cells: Cells = [(0, Segment(sanitize(f"{key}:"), s.key_color, True))]
            col = value_col
            for part in re.split("(·)", sanitize(str(value))):
                if not part:
                    continue
                seg = Segment(part, "muted" if part == "·" else "fg")
                cells.append((col, seg))
                col += cell_len(part)
            rows.append(cells)
        if s.show_palette:
            rows.append([])
            names = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
            rows.append([(i * 3, Segment("   ", "fg", False, n)) for i, n in enumerate(names)])
        return rows

    def fastfetch_rows(self) -> list:
        s = self.s
        logo = prepare_logo(s.distro_ascii)
        info = self.info_rows()
        logo_w = max((ind + cell_len(t) for ind, t in logo), default=0)
        gap = s.logo_gap if logo else 0
        n = max(len(logo), len(info))

        def offset(count: int) -> int:
            return (n - count) // 2 if s.valign == "center" else 0

        lo, io = offset(len(logo)), offset(len(info))
        rows = []
        for i in range(n):
            cells: Cells = []
            li = i - lo
            if 0 <= li < len(logo) and logo[li][1]:
                indent, text = logo[li]
                cells.append((indent, Segment(text, self.logo_color(li, len(logo)))))
            ii = i - io
            if 0 <= ii < len(info):
                cells += [(logo_w + gap + c, seg) for c, seg in info[ii]]
            rows.append(cells)
        return rows


# =============================================================================
# 4. ANIMATION TIMELINE  (what appears when, in absolute seconds)
# =============================================================================

@dataclass
class RowItem:
    row: int
    cells: Cells
    t_on: float


@dataclass
class TypedItem:
    row: int
    col: int
    text: str
    times: list           # time each character appears
    cum: list             # cumulative cell width after each character


@dataclass
class CursorItem:
    row: int
    col: int
    t_on: float
    t_off: float
    times: list = field(default_factory=list)
    cum: list = field(default_factory=list)


@dataclass
class Page:
    """One 'screen' of the terminal; cleared (faded) when the next begins."""
    start: float
    end: float = 0.0
    rows: list = field(default_factory=list)
    typed: list = field(default_factory=list)
    cursors: list = field(default_factory=list)
    rows_used: int = 0


@dataclass
class Timeline:
    pages: list
    total: float


PAGE_FADE_IN = 0.15
PAGE_END_HOLD = 0.5   # keep the last output visible briefly before clearing
PAGE_GAP = 0.15       # blank time between a fade-out and the next screen


class TimelineBuilder:
    def __init__(self, s: Settings, content: ContentBuilder):
        self.s = s
        self.content = content

    def build(self) -> Timeline:
        s, content = self.s, self.content
        limit = s.row_limit
        rng = random.Random(s.seed)
        prompt = content.prompt_cells()
        pcols = content.prompt_cols

        page = Page(start=0.0)
        pages = [page]
        row = 0
        t = s.start_delay  # moment the next prompt appears

        def new_page(end_time: float) -> tuple:
            nonlocal page, row
            page.end = end_time
            page.rows_used = row
            start = end_time + s.page_fade + PAGE_GAP
            page = Page(start=start)
            pages.append(page)
            row = 0
            return start + PAGE_FADE_IN

        for cmd in s.commands:
            out = content.output_rows(cmd.output)
            need = 1 + len(out)
            if s.term_rows and need > s.term_rows:
                raise ConfigError(
                    f"Command {cmd.text!r} needs {need} rows but TERM_ROWS is {s.term_rows}. "
                    f"Increase TERM_ROWS or set it to None.")
            if row > 0 and row + need > limit:
                t = new_page(t + PAGE_END_HOLD)

            page.rows.append(RowItem(row, prompt, t))
            speed = cmd.typing_speed if cmd.typing_speed is not None else s.typing_speed
            ts = t + (cmd.pause if cmd.pause is not None else s.command_pause)
            text = sanitize(cmd.text)
            times, cum, tc, width = [], [], ts, 0
            for ch in text:
                times.append(tc)
                width += cell_width(ch)
                cum.append(width)
                tc += speed * (1 + rng.uniform(-s.typing_jitter, s.typing_jitter))
            t_enter = tc + s.post_type_delay
            if text:
                page.typed.append(TypedItem(row, pcols, text, times, cum))
            page.cursors.append(CursorItem(row, pcols, t, t_enter, times, cum))

            if text.strip() == "clear":
                t = new_page(t_enter + 0.1)
                continue

            t_out = t_enter + s.output_delay
            ld = cmd.line_delay if cmd.line_delay is not None else s.line_delay
            for k, cells in enumerate(out):
                page.rows.append(RowItem(row + 1 + k, cells, t_out + k * ld))
            row += need
            t = t_out + len(out) * ld + s.prompt_delay

        # final idle prompt with a blinking cursor
        if row > 0 and row + 1 > limit:
            t = new_page(t + PAGE_END_HOLD)
        page.rows.append(RowItem(row, prompt, t))
        page.rows_used = row + 1
        page.end = t + s.end_hold
        total = page.end + s.page_fade
        page.cursors.append(CursorItem(row, pcols, t, total))
        return Timeline(pages, total)


# =============================================================================
# 5. SVG EXPORT  (window chrome, text, SMIL animation)
# =============================================================================

def fmt(x: float, nd: int = 2) -> str:
    s = f"{x:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def normalize_frames(frames: list, total: float) -> list:
    """Sort/clean (time, value) keyframes: start at 0, end at `total`, strictly rising."""
    out: list = []
    for t, v in sorted(frames, key=lambda f: f[0]):
        t = min(max(t, 0.0), total)
        if out and t - out[-1][0] < 1e-4:
            out[-1] = (out[-1][0], v)  # later keyframe at (almost) same time wins
        else:
            out.append((t, v))
    if not out:
        return [(0.0, 0), (total, 0)]
    if out[0][0] > 0:
        out.insert(0, (0.0, out[0][1]))
    out[0] = (0.0, out[0][1])
    if out[-1][0] < total - 1e-4:
        out.append((total, out[-1][1]))
    else:
        out[-1] = (total, out[-1][1])
    return out


def animate(attr: str, frames: list, total: float, calc: str = "discrete") -> str:
    frames = normalize_frames(frames, total)
    key_times = ";".join(fmt(t / total, 5) for t, _ in frames)
    values = ";".join(fmt(v) if isinstance(v, (int, float)) else str(v) for _, v in frames)
    return (f'<animate attributeName="{attr}" calcMode="{calc}" keyTimes="{key_times}" '
            f'values="{values}" dur="{total:.3f}s" repeatCount="indefinite"/>')


class StyleRegistry:
    """Collects fill colours into compact CSS classes."""

    def __init__(self, s: Settings):
        self.s = s
        self.classes: dict = {}

    def cls(self, color: str, bold: bool) -> str:
        css = self.s.color(color)
        name = self.classes.setdefault(css, f"c{len(self.classes)}")
        return f"{name} b" if bold else name

    def css(self) -> str:
        s = self.s
        rules = [
            f"text{{font-family:{s.font_family};font-size:{fmt(s.font_size)}px;"
            f"white-space:pre;text-rendering:geometricPrecision}}",
            ".b{font-weight:700}",
            ".ui{font-family:system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}",
        ]
        rules += [f".{n}{{fill:{c}}}" for c, n in self.classes.items()]
        return "".join(rules)


@dataclass
class Geometry:
    cols: int
    rows: int
    win_w: float
    win_h: float
    svg_w: float
    svg_h: float


class TerminalRenderer:
    """Renders a Timeline into a standalone SVG document string."""

    def __init__(self, s: Settings, timeline: Timeline):
        self.s = s
        self.tl = timeline
        self.styles = StyleRegistry(s)
        self.geo = self._geometry()
        self._clip_id = 0

    # -- layout --------------------------------------------------------------
    def _geometry(self) -> Geometry:
        s = self.s
        content_cols = 0
        for page in self.tl.pages:
            for r in page.rows:
                for col, seg in r.cells:
                    content_cols = max(content_cols, col + cell_len(seg.text))
            for ty in page.typed:
                content_cols = max(content_cols, ty.col + cell_len(ty.text))
            for c in page.cursors:
                content_cols = max(content_cols, c.col + 1)
        cols = s.term_cols or max(s.min_cols, content_cols + 1)
        rows = s.term_rows or max(p.rows_used for p in self.tl.pages)
        win_w = cols * s.cw + 2 * s.pad_x
        win_h = s.titlebar_h + rows * s.lh + 2 * s.pad_y
        return Geometry(cols, rows, win_w, win_h, win_w + 2 * s.margin, win_h + 2 * s.margin)

    # -- primitives ----------------------------------------------------------
    def _cell(self, col: int, row: int, seg: Segment) -> str:
        s = self.s
        text = seg.text
        lead = len(text) - len(text.lstrip(" "))
        body = text.strip(" ")
        x = (col + cell_len(text[:lead])) * s.cw
        top = row * s.lh
        out = ""
        if seg.bg:
            out += (f'<rect x="{fmt(col * s.cw)}" y="{fmt(top)}" width="{fmt(cell_len(text) * s.cw)}" '
                    f'height="{fmt(s.lh)}" fill="{s.color(seg.bg)}"/>')
        if body:
            y = top + s.lh / 2 + s.font_size * 0.35
            out += (f'<text x="{fmt(x)}" y="{fmt(y)}" class="{self.styles.cls(seg.color, seg.bold)}" '
                    f'textLength="{fmt(cell_len(body) * s.cw)}" lengthAdjust="spacing">'
                    f'{escape(body)}</text>')
        return out

    def _cursor_rect(self, col: int, row: int) -> tuple:
        s = self.s
        h = s.font_size * 1.25
        y = row * s.lh + (s.lh - h) / 2
        return col * s.cw, y, h

    # -- cursor / page keyframes --------------------------------------------
    def _cursor_frames(self, c: CursorItem) -> list:
        blink = self.s.cursor_blink
        frames: list = [(0.0, 0)]

        def span(a: float, b: float) -> None:
            t, on = a, True
            while t < b - 1e-6:
                frames.append((t, 1 if on else 0))
                t += blink
                on = not on

        if c.times:
            span(c.t_on, c.times[0])
            frames.append((c.times[0], 1))   # solid while typing
            span(c.times[-1], c.t_off)
        else:
            span(c.t_on, c.t_off)
        frames.append((c.t_off, 0))
        return frames

    def _page_frames(self, page: Page) -> list:
        s = self.s
        frames: list = [(0.0, 1)] if page.start <= 0 else [
            (0.0, 0), (page.start, 0), (page.start + PAGE_FADE_IN, 1)]
        frames += [(page.end, 1), (page.end + s.page_fade, 0)]
        return frames

    # -- page ----------------------------------------------------------------
    def _page(self, page: Page, static: bool, show_cursor: bool) -> str:
        s, total = self.s, self.tl.total
        parts: list = []

        for r in sorted(page.rows, key=lambda r: (r.t_on, r.row)):
            body = "".join(self._cell(c, r.row, seg) for c, seg in r.cells)
            if not body:
                continue
            if static:
                parts.append(f"<g>{body}</g>")
            else:
                parts.append(f'<g opacity="0">{animate("opacity", [(0, 0), (r.t_on, 1)], total)}{body}</g>')

        for ty in page.typed:
            y = ty.row * s.lh + s.lh / 2 + s.font_size * 0.35
            n = cell_len(ty.text)
            seg_cls = self.styles.cls("fg", False)
            text_attrs = (f'x="{fmt(ty.col * s.cw)}" y="{fmt(y)}" class="{seg_cls}" '
                          f'textLength="{fmt(n * s.cw)}" lengthAdjust="spacing"')
            if static:
                parts.append(f"<text {text_attrs}>{escape(ty.text)}</text>")
                continue
            self._clip_id += 1
            cid = f"k{self._clip_id}"
            frames = [(0.0, 0)] + [(t, w * s.cw) for t, w in zip(ty.times, ty.cum)]
            parts.append(
                f'<clipPath id="{cid}"><rect x="{fmt(ty.col * s.cw)}" y="{fmt(ty.row * s.lh)}" '
                f'width="0" height="{fmt(s.lh)}">{animate("width", frames, total)}</rect></clipPath>'
                f'<text clip-path="url(#{cid})" {text_attrs}>{escape(ty.text)}</text>')

        for c in page.cursors:
            x, y, h = self._cursor_rect(c.col, c.row)
            fill = s.color("cursor")
            if static:
                if show_cursor and c.t_off >= total - 1e-6:
                    parts.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(s.cw)}" '
                                 f'height="{fmt(h)}" fill="{fill}"/>')
                continue
            anims = animate("opacity", self._cursor_frames(c), total)
            if c.times:
                frames = [(0.0, x)] + [(t, x + w * s.cw) for t, w in zip(c.times, c.cum)]
                anims += animate("x", frames, total)
            parts.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(s.cw)}" height="{fmt(h)}" '
                         f'fill="{fill}" opacity="0">{anims}</rect>')

        inner = "".join(parts)
        if static:
            return f"<g>{inner}</g>"
        first = page.start <= 0
        return (f'<g opacity="{1 if first else 0}">'
                f'{animate("opacity", self._page_frames(page), total, "linear")}{inner}</g>')

    # -- window chrome -------------------------------------------------------
    def _chrome(self) -> tuple:
        s, g = self.s, self.geo
        m, r = s.margin, s.corner_radius
        theme = s.color
        defs = (
            f'<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
            f'<feGaussianBlur stdDeviation="{fmt(m * 0.4)}"/></filter>'
            f'<clipPath id="win"><rect x="{fmt(m)}" y="{fmt(m)}" width="{fmt(g.win_w)}" '
            f'height="{fmt(g.win_h)}" rx="{fmt(r)}"/></clipPath>'
            f'<clipPath id="view"><rect x="{fmt(-s.pad_x / 2)}" y="{fmt(-s.pad_y / 2)}" '
            f'width="{fmt(g.cols * s.cw + s.pad_x)}" height="{fmt(g.rows * s.lh + s.pad_y)}"/></clipPath>')
        title = escape(sanitize(s.window_title or f"{s.username}@{s.hostname}: {s.cwd}"))
        by = m + s.titlebar_h / 2
        buttons = "".join(
            f'<circle cx="{fmt(m + 22 + i * 20)}" cy="{fmt(by)}" r="6" fill="{theme(k)}"/>'
            for i, k in enumerate(("btn_close", "btn_min", "btn_max")))
        chrome = (
            f'<rect x="{fmt(m)}" y="{fmt(m + m * 0.35)}" width="{fmt(g.win_w)}" height="{fmt(g.win_h)}" '
            f'rx="{fmt(r)}" fill="{theme("shadow")}" opacity="0.55" filter="url(#shadow)"/>'
            f'<g clip-path="url(#win)">'
            f'<rect x="{fmt(m)}" y="{fmt(m)}" width="{fmt(g.win_w)}" height="{fmt(g.win_h)}" fill="{theme("bg")}"/>'
            f'<rect x="{fmt(m)}" y="{fmt(m)}" width="{fmt(g.win_w)}" height="{fmt(s.titlebar_h)}" fill="{theme("titlebar")}"/>'
            f'<rect x="{fmt(m)}" y="{fmt(m + s.titlebar_h - 1)}" width="{fmt(g.win_w)}" height="1" fill="{theme("border")}" opacity="0.6"/>'
            f'</g>'
            f'<rect x="{fmt(m + 0.5)}" y="{fmt(m + 0.5)}" width="{fmt(g.win_w - 1)}" height="{fmt(g.win_h - 1)}" '
            f'rx="{fmt(r)}" fill="none" stroke="{theme("border")}" stroke-width="1"/>'
            f'{buttons}'
            f'<text x="{fmt(m + g.win_w / 2)}" y="{fmt(by + 4)}" text-anchor="middle" class="ui" '
            f'style="font-size:12.5px;white-space:normal" fill="{theme("title")}">{title}</text>')
        return defs, chrome

    # -- document ------------------------------------------------------------
    def render(self, static: bool = False) -> str:
        s, g = self.s, self.geo
        if static:
            best = max(self.tl.pages, key=lambda p: (p.rows_used, p.start))
            pages = [(best, best is self.tl.pages[-1])]
        else:
            pages = [(p, True) for p in self.tl.pages]
        body = "".join(self._page(p, static, cur) for p, cur in pages)
        defs, chrome = self._chrome()

        disp_w = s.display_width or g.svg_w
        disp_h = disp_w * g.svg_h / g.svg_w
        label = escape(f"Animated terminal: {s.username}@{s.hostname} running fastfetch")
        ox = s.margin + s.pad_x
        oy = s.margin + s.titlebar_h + s.pad_y
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" '
            f'viewBox="0 0 {fmt(g.svg_w)} {fmt(g.svg_h)}" width="{fmt(disp_w)}" height="{fmt(disp_h)}" '
            f'role="img" aria-label={quoteattr(label)}>\n'
            f'<title>{label}</title>\n'
            f'<style>{self.styles.css()}</style>\n'
            f'<defs>{defs}</defs>\n'
            f'{chrome}\n'
            f'<g transform="translate({fmt(ox)} {fmt(oy)})" clip-path="url(#view)">{body}</g>\n'
            '</svg>\n')


# NOTE: styles are collected while rendering, so the <style> block must be
# produced after the body. render() above builds `body` first for this reason.


# =============================================================================
# 6. COMMAND-LINE INTERFACE
# =============================================================================

def write_svg(path: Path, svg: str) -> None:
    ET.fromstring(svg.encode("utf-8"))  # sanity check: must be well-formed XML
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def generate(s: Settings, static: bool = False) -> tuple:
    s.validate()
    content = ContentBuilder(s)
    timeline = TimelineBuilder(s, content).build()
    renderer = TerminalRenderer(s, timeline)
    return renderer.render(static=static), timeline, renderer.geo


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="gen_terminal.py",
        description="Generate an animated terminal SVG (edit the config at the top of this file).")
    p.add_argument("-o", "--output", help=f"output file (default: {OUTPUT_FILE})")
    p.add_argument("--static", action="store_true", help="render a static frame, no animation")
    p.add_argument("--speed", type=float, default=1.0, help="typing/output speed multiplier (default 1.0)")
    p.add_argument("--seed", type=int, help="override typing-jitter seed")
    p.add_argument("--width", type=float, help="display width in px (aspect ratio is kept)")
    p.add_argument("-q", "--quiet", action="store_true", help="suppress the summary")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.speed <= 0:
            raise ConfigError("--speed must be greater than 0.")
        s = Settings.from_module()
        if args.speed != 1.0:
            s.typing_speed /= args.speed
            s.line_delay /= args.speed
            s.command_pause /= args.speed
        if args.seed is not None:
            s.seed = args.seed
        if args.width:
            s.display_width = args.width
        out = Path(args.output or s.output_file)
        svg, timeline, geo = generate(s, static=args.static)
        write_svg(out, svg)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except ET.ParseError as exc:
        print(f"Internal error: generated SVG is not well-formed XML ({exc}).", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"Could not write output: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        kb = out.stat().st_size / 1024
        mode = "static" if args.static else f"animated, {timeline.total:.1f}s loop"
        print(f"Wrote {out} ({kb:.1f} KiB, {geo.cols}x{geo.rows} cells, "
              f"{len(timeline.pages)} screen(s), {mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Curses-based TUI for FAKE_DATA log generation.

Provides an interactive 3-section interface (Sources, Scenarios, Config)
for selecting generators, scenarios, and configuration before running
main_generate.py's orchestrator.

Usage:
    python3 fake_data/tui_generate.py
"""

import curses
import sys
from pathlib import Path

# Bootstrap: ensure fake_data package is importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fake_data.main_generate import discover_generators
from fake_data.config import (
    discover_scenarios,
    DEFAULT_START_DATE,
    DEFAULT_DAYS,
    DEFAULT_SCALE,
)

# =============================================================================
# CONSTANTS
# =============================================================================

MIN_COLS = 80
MIN_ROWS = 20

# Section indices
SEC_SOURCES = 0
SEC_SCENARIOS = 1
SEC_CONFIG = 2

# Color pair IDs
CP_NORMAL = 1
CP_HIGHLIGHT = 2
CP_SELECTED = 3
CP_DEPENDENCY = 4
CP_DIMMED = 5
CP_HEADER = 6
CP_STATUS = 7

# Box-drawing characters
# Use single-line Unicode (widely supported) with ASCII fallback
try:
    # Test if terminal can handle Unicode box-drawing
    "\u250c".encode(sys.stdout.encoding or "utf-8")
    BOX_TL = "\u250c"  # ┌
    BOX_TR = "\u2510"  # ┐
    BOX_BL = "\u2514"  # └
    BOX_BR = "\u2518"  # ┘
    BOX_H = "\u2500"   # ─
    BOX_V = "\u2502"   # │
    BOX_TJ = "\u252c"  # ┬
    BOX_BJ = "\u2534"  # ┴
except (UnicodeEncodeError, LookupError):
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    BOX_H = "-"
    BOX_V = "|"
    BOX_TJ = "+"
    BOX_BJ = "+"


# =============================================================================
# HELPER: safe addstr
# =============================================================================

def safe_addstr(win, y, x, text, attr=0):
    """Write text to window, silently ignoring out-of-bounds errors."""
    try:
        max_y, max_x = win.getmaxyx()
        if y < 0 or y >= max_y or x < 0 or x >= max_x:
            return
        available = max_x - x
        if available <= 0:
            return
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass


# =============================================================================
# TUI STATE
# =============================================================================

class TUIState:
    """Holds all mutable state for the TUI."""

    def __init__(self):
        # Discovery results
        self.generators = {}       # source_id -> module
        self.gen_order = []        # list of source_ids (display order)
        self.gen_deps = {}         # source_id -> list of depends_on ids
        self.scenarios = {}        # scenario_id -> {"meta": ..., "instance": ...}
        self.scen_order = []       # list of scenario_ids (display order)

        # Selection state — sources
        self.src_all = True
        self.src_selected = set()  # manually selected
        self.src_dep = set()       # auto-included dependencies

        # Selection state — scenarios
        self.scen_mode = "all"     # "all", "none", or "custom"
        self.scen_selected = set()

        # Config values
        self.cfg_start_date = DEFAULT_START_DATE
        self.cfg_days = DEFAULT_DAYS
        self.cfg_scale = DEFAULT_SCALE
        # cfg_show_files removed — --show-files is a standalone command, not a generation flag
        self.cfg_quiet = False

        # Navigation
        self.section = SEC_SOURCES
        self.cursor = [0, 0, 0]  # cursor row per section

        # Edit mode
        self.editing = False
        self.edit_field = ""
        self.edit_value = ""
        self.edit_cursor = 0

    def discover(self):
        """Run discovery for generators and scenarios."""
        self.generators = discover_generators()
        self.gen_order = sorted(self.generators.keys())

        # Build dependency map
        for sid, mod in self.generators.items():
            deps = mod.SOURCE_META.get("depends_on", [])
            self.gen_deps[sid] = [d for d in deps if d in self.generators]

        # Start with all selected
        self.src_all = True
        self.src_selected = set(self.gen_order)
        self._recompute_deps()

        # Discover scenarios
        self.scenarios = discover_scenarios()
        self.scen_order = sorted(self.scenarios.keys())
        self.scen_mode = "all"
        self.scen_selected = set(self.scen_order)

    def _recompute_deps(self):
        """Recompute which sources are auto-included as dependencies."""
        needed = set()
        for sid in self.src_selected:
            for dep in self.gen_deps.get(sid, []):
                if dep not in self.src_selected:
                    needed.add(dep)
        # Transitive deps
        changed = True
        while changed:
            changed = False
            for dep in list(needed):
                for ddep in self.gen_deps.get(dep, []):
                    if ddep not in self.src_selected and ddep not in needed:
                        needed.add(ddep)
                        changed = True
        self.src_dep = needed

    def toggle_source(self, idx):
        """Toggle source at index in gen_order list."""
        if idx == 0:
            # "all" toggle
            if self.src_all:
                self.src_all = False
                self.src_selected.clear()
                self.src_dep.clear()
            else:
                self.src_all = True
                self.src_selected = set(self.gen_order)
                self._recompute_deps()
            return

        real_idx = idx - 1
        if real_idx < 0 or real_idx >= len(self.gen_order):
            return
        sid = self.gen_order[real_idx]

        # Cannot deselect a dependency while dependent is selected
        if sid in self.src_dep:
            return

        if sid in self.src_selected:
            self.src_selected.discard(sid)
        else:
            self.src_selected.add(sid)

        self.src_all = (self.src_selected == set(self.gen_order))
        self._recompute_deps()

    def toggle_scenario(self, idx):
        """Toggle scenario at index in display list."""
        if idx == 0:
            # "all" toggle
            if self.scen_mode == "all":
                self.scen_mode = "none"
                self.scen_selected.clear()
            else:
                self.scen_mode = "all"
                self.scen_selected = set(self.scen_order)
            return
        if idx == 1:
            # "none" toggle
            self.scen_mode = "none"
            self.scen_selected.clear()
            return

        real_idx = idx - 2
        if real_idx < 0 or real_idx >= len(self.scen_order):
            return
        sid = self.scen_order[real_idx]

        if sid in self.scen_selected:
            self.scen_selected.discard(sid)
        else:
            self.scen_selected.add(sid)

        if len(self.scen_selected) == len(self.scen_order) and self.scen_order:
            self.scen_mode = "all"
        elif len(self.scen_selected) == 0:
            self.scen_mode = "none"
        else:
            self.scen_mode = "custom"

    def source_row_count(self):
        """Number of rows in sources section (all + generators)."""
        return 1 + len(self.gen_order)

    def scenario_row_count(self):
        """Number of rows in scenarios section (all + none + scenarios)."""
        return 2 + len(self.scen_order)

    def config_row_count(self):
        """Number of rows in config section."""
        return 4  # start_date, days, scale, quiet

    def section_row_count(self, sec):
        if sec == SEC_SOURCES:
            return self.source_row_count()
        elif sec == SEC_SCENARIOS:
            return self.scenario_row_count()
        else:
            return self.config_row_count()

    def config_fields(self):
        """Return list of (label, value, field_name, editable_type)."""
        return [
            ("Start Date", self.cfg_start_date, "cfg_start_date", "text"),
            ("Days", str(self.cfg_days), "cfg_days", "int"),
            ("Scale", str(self.cfg_scale), "cfg_scale", "float"),
            ("Quiet", self.cfg_quiet, "cfg_quiet", "bool"),
        ]

    def active_sources(self):
        """Return set of all active source_ids (selected + deps)."""
        if self.src_all:
            return set(self.gen_order)
        return self.src_selected | self.src_dep

    def active_scenarios_str(self):
        """Return scenario string for command line."""
        if self.scen_mode == "all":
            return "all"
        if self.scen_mode == "none" or not self.scen_selected:
            return "none"
        return ",".join(sorted(self.scen_selected))

    def sources_str(self):
        """Return sources string for command line."""
        active = self.active_sources()
        if active == set(self.gen_order) and self.gen_order:
            return "all"
        if not active:
            return "none"
        return ",".join(sorted(active))

    def build_command_preview(self):
        """Build the command string preview."""
        parts = ["python3 fake_data/main_generate.py"]
        parts.append(f"--sources={self.sources_str()}")
        parts.append(f"--days={self.cfg_days}")
        parts.append(f"--start-date={self.cfg_start_date}")
        parts.append(f"--scale={self.cfg_scale}")
        parts.append(f"--scenarios={self.active_scenarios_str()}")
        if self.cfg_quiet:
            parts.append("--quiet")
        return " ".join(parts)

    def build_argv(self):
        """Build sys.argv list for main_generate.main()."""
        argv = ["main_generate.py"]
        argv.append(f"--sources={self.sources_str()}")
        argv.append(f"--days={self.cfg_days}")
        argv.append(f"--start-date={self.cfg_start_date}")
        argv.append(f"--scale={self.cfg_scale}")
        argv.append(f"--scenarios={self.active_scenarios_str()}")
        if self.cfg_quiet:
            argv.append("--quiet")
        return argv


# =============================================================================
# DRAWING
# =============================================================================

def init_colors():
    """Initialize color pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(CP_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(CP_SELECTED, curses.COLOR_GREEN, -1)
    curses.init_pair(CP_DEPENDENCY, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_DIMMED, 8, -1)  # dark gray (color 8 = bright black)
    curses.init_pair(CP_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_STATUS, curses.COLOR_BLACK, curses.COLOR_WHITE)


def draw_box(stdscr, y, x, h, w):
    """Draw a double-line box at (y, x) with height h and width w."""
    # Top border
    safe_addstr(stdscr, y, x, BOX_TL)
    for cx in range(x + 1, x + w - 1):
        safe_addstr(stdscr, y, cx, BOX_H)
    safe_addstr(stdscr, y, x + w - 1, BOX_TR)

    # Side borders
    for ry in range(y + 1, y + h - 1):
        safe_addstr(stdscr, ry, x, BOX_V)
        safe_addstr(stdscr, ry, x + w - 1, BOX_V)

    # Bottom border
    safe_addstr(stdscr, y + h - 1, x, BOX_BL)
    for cx in range(x + 1, x + w - 1):
        safe_addstr(stdscr, y + h - 1, cx, BOX_H)
    safe_addstr(stdscr, y + h - 1, x + w - 1, BOX_BR)


def draw_three_panel_box(stdscr, y, x, h, w1, w2, w3):
    """Draw a three-panel double-line box."""
    total_w = w1 + w2 + w3 + 2  # +2 for inner dividers sharing border

    # Top border
    safe_addstr(stdscr, y, x, BOX_TL)
    for cx in range(x + 1, x + w1):
        safe_addstr(stdscr, y, cx, BOX_H)
    safe_addstr(stdscr, y, x + w1, BOX_TJ)
    for cx in range(x + w1 + 1, x + w1 + w2 + 1):
        safe_addstr(stdscr, y, cx, BOX_H)
    safe_addstr(stdscr, y, x + w1 + w2 + 1, BOX_TJ)
    for cx in range(x + w1 + w2 + 2, x + total_w - 1):
        safe_addstr(stdscr, y, cx, BOX_H)
    safe_addstr(stdscr, y, x + total_w - 1, BOX_TR)

    # Sides + dividers
    for ry in range(y + 1, y + h - 1):
        safe_addstr(stdscr, ry, x, BOX_V)
        safe_addstr(stdscr, ry, x + w1, BOX_V)
        safe_addstr(stdscr, ry, x + w1 + w2 + 1, BOX_V)
        safe_addstr(stdscr, ry, x + total_w - 1, BOX_V)

    # Bottom border
    safe_addstr(stdscr, y + h - 1, x, BOX_BL)
    for cx in range(x + 1, x + w1):
        safe_addstr(stdscr, y + h - 1, cx, BOX_H)
    safe_addstr(stdscr, y + h - 1, x + w1, BOX_BJ)
    for cx in range(x + w1 + 1, x + w1 + w2 + 1):
        safe_addstr(stdscr, y + h - 1, cx, BOX_H)
    safe_addstr(stdscr, y + h - 1, x + w1 + w2 + 1, BOX_BJ)
    for cx in range(x + w1 + w2 + 2, x + total_w - 1):
        safe_addstr(stdscr, y + h - 1, cx, BOX_H)
    safe_addstr(stdscr, y + h - 1, x + total_w - 1, BOX_BR)


def draw_sources(stdscr, state, box_y, box_x, inner_w, inner_h):
    """Draw the SOURCES section content."""
    is_active = (state.section == SEC_SOURCES)
    header_attr = curses.color_pair(CP_HEADER) | curses.A_BOLD
    safe_addstr(stdscr, box_y, box_x, " SOURCES ", header_attr)

    y = box_y + 1
    # "all" toggle
    marker = "[x]" if state.src_all else "[ ]"
    row_attr = curses.color_pair(CP_NORMAL)
    if is_active and state.cursor[SEC_SOURCES] == 0:
        row_attr = curses.color_pair(CP_HIGHLIGHT)
    elif state.src_all:
        row_attr = curses.color_pair(CP_SELECTED)
    text = f" {marker} all"
    safe_addstr(stdscr, y, box_x, text.ljust(inner_w), row_attr)
    y += 1

    # Generator rows
    for i, sid in enumerate(state.gen_order):
        if y - box_y >= inner_h:
            break
        is_dep = sid in state.src_dep
        is_sel = sid in state.src_selected

        if is_dep:
            marker = "[+]"
        elif is_sel or state.src_all:
            marker = "[x]"
        else:
            marker = "[ ]"

        suffix = " (dep)" if is_dep else ""
        label = f" {marker} {sid}{suffix}"

        row_attr = curses.color_pair(CP_NORMAL)
        if is_active and state.cursor[SEC_SOURCES] == i + 1:
            row_attr = curses.color_pair(CP_HIGHLIGHT)
        elif is_dep:
            row_attr = curses.color_pair(CP_DEPENDENCY)
        elif is_sel or state.src_all:
            row_attr = curses.color_pair(CP_SELECTED)

        safe_addstr(stdscr, y, box_x, label.ljust(inner_w), row_attr)
        y += 1


def draw_scenarios(stdscr, state, box_y, box_x, inner_w, inner_h):
    """Draw the SCENARIOS section content."""
    is_active = (state.section == SEC_SCENARIOS)
    header_attr = curses.color_pair(CP_HEADER) | curses.A_BOLD
    safe_addstr(stdscr, box_y, box_x, " SCENARIOS ", header_attr)

    y = box_y + 1
    # "all" toggle
    marker = "[x]" if state.scen_mode == "all" else "[ ]"
    row_attr = curses.color_pair(CP_NORMAL)
    if is_active and state.cursor[SEC_SCENARIOS] == 0:
        row_attr = curses.color_pair(CP_HIGHLIGHT)
    elif state.scen_mode == "all":
        row_attr = curses.color_pair(CP_SELECTED)
    safe_addstr(stdscr, y, box_x, f" {marker} all".ljust(inner_w), row_attr)
    y += 1

    # "none" toggle
    marker = "[x]" if state.scen_mode == "none" else "[ ]"
    row_attr = curses.color_pair(CP_NORMAL)
    if is_active and state.cursor[SEC_SCENARIOS] == 1:
        row_attr = curses.color_pair(CP_HIGHLIGHT)
    elif state.scen_mode == "none":
        row_attr = curses.color_pair(CP_SELECTED)
    safe_addstr(stdscr, y, box_x, f" {marker} none".ljust(inner_w), row_attr)
    y += 1

    # Scenario rows
    for i, sid in enumerate(state.scen_order):
        if y - box_y >= inner_h:
            break
        meta = state.scenarios[sid]["meta"]
        is_sel = sid in state.scen_selected

        # Day range display
        start_d = meta.get("start_day", 0)
        end_d = meta.get("end_day", 0)
        day_range = f"D{start_d}-{end_d}"

        # Check if scenario is beyond configured days
        is_skipped = start_d >= state.cfg_days

        marker = "[x]" if is_sel else "[ ]"
        suffix = f" ({day_range})"
        if is_skipped:
            suffix += " (skip)"
        label = f" {marker} {sid}{suffix}"

        row_attr = curses.color_pair(CP_NORMAL)
        if is_active and state.cursor[SEC_SCENARIOS] == i + 2:
            row_attr = curses.color_pair(CP_HIGHLIGHT)
        elif is_skipped:
            row_attr = curses.color_pair(CP_DIMMED)
        elif is_sel:
            row_attr = curses.color_pair(CP_SELECTED)

        safe_addstr(stdscr, y, box_x, label.ljust(inner_w), row_attr)
        y += 1


def draw_config(stdscr, state, box_y, box_x, inner_w, inner_h):
    """Draw the CONFIG section content."""
    is_active = (state.section == SEC_CONFIG)
    header_attr = curses.color_pair(CP_HEADER) | curses.A_BOLD
    safe_addstr(stdscr, box_y, box_x, " CONFIG ", header_attr)

    y = box_y + 1
    fields = state.config_fields()

    for i, (label, value, field_name, ftype) in enumerate(fields):
        if y - box_y >= inner_h:
            break

        row_attr = curses.color_pair(CP_NORMAL)
        if is_active and state.cursor[SEC_CONFIG] == i:
            row_attr = curses.color_pair(CP_HIGHLIGHT)

        if state.editing and state.edit_field == field_name:
            # Show editing state
            text = f" {label}: {state.edit_value}_"
            safe_addstr(stdscr, y, box_x, text.ljust(inner_w), row_attr | curses.A_BOLD)
        elif ftype == "bool":
            marker = "[x]" if value else "[ ]"
            text = f" {marker} {label}"
            safe_addstr(stdscr, y, box_x, text.ljust(inner_w), row_attr)
        else:
            text = f" {label}: {value}"
            safe_addstr(stdscr, y, box_x, text.ljust(inner_w), row_attr)

        y += 1


def draw_status_bar(stdscr, state, max_y, max_x):
    """Draw the status bar at the bottom of the screen."""
    active_src = state.active_sources()
    src_count = len(active_src)
    scen_count = len(state.scen_selected) if state.scen_mode != "none" else 0

    line1 = f" {src_count} source(s), {scen_count} scenario(s)"
    cmd = state.build_command_preview()
    line2 = f" {cmd}"
    line3 = " [G] Generate  [Q] Quit  [Space] Toggle  [Enter] Edit  [Arrow keys] Navigate"

    status_attr = curses.color_pair(CP_STATUS)
    # Use up to 3 lines at bottom
    status_y = max_y - 3
    if status_y > 0:
        safe_addstr(stdscr, status_y, 0, line1.ljust(max_x), status_attr)
    if status_y + 1 < max_y:
        safe_addstr(stdscr, status_y + 1, 0, line2.ljust(max_x),
                    curses.color_pair(CP_NORMAL))
    if status_y + 2 < max_y:
        safe_addstr(stdscr, status_y + 2, 0, line3.ljust(max_x),
                    curses.color_pair(CP_DIMMED))


def draw_screen(stdscr, state):
    """Draw the complete TUI screen."""
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    if max_y < MIN_ROWS or max_x < MIN_COLS:
        msg = f"Terminal too small ({max_x}x{max_y}). Need {MIN_COLS}x{MIN_ROWS}."
        safe_addstr(stdscr, 0, 0, msg, curses.color_pair(CP_NORMAL) | curses.A_BOLD)
        stdscr.refresh()
        return

    # Calculate panel widths (3 sections side by side)
    usable_w = max_x - 2  # outer borders only (dividers share a column)
    w1 = usable_w // 3
    w2 = usable_w // 3
    w3 = usable_w - w1 - w2

    # Box height: leave 3 rows for status bar + 1 for top margin
    box_h = max_y - 4
    if box_h < 5:
        box_h = 5

    # Draw the three-panel box
    draw_three_panel_box(stdscr, 0, 0, box_h, w1, w2, w3)

    # Inner content areas (1 inside each panel border)
    inner_h = box_h - 2  # top/bottom borders

    # Section 1: Sources
    src_x = 1
    src_inner_w = w1 - 1
    draw_sources(stdscr, state, 1, src_x, src_inner_w, inner_h + 1)

    # Section 2: Scenarios
    scen_x = w1 + 1
    scen_inner_w = w2
    draw_scenarios(stdscr, state, 1, scen_x, scen_inner_w, inner_h + 1)

    # Section 3: Config
    cfg_x = w1 + w2 + 2
    cfg_inner_w = w3 - 1
    draw_config(stdscr, state, 1, cfg_x, cfg_inner_w, inner_h + 1)

    # Status bar
    draw_status_bar(stdscr, state, max_y, max_x)

    stdscr.refresh()


# =============================================================================
# INPUT HANDLING
# =============================================================================

def handle_edit_key(state, key):
    """Handle keypress in edit mode. Returns True if edit mode ended."""
    if key == 27:  # Escape
        state.editing = False
        return True
    elif key in (curses.KEY_ENTER, 10, 13):  # Enter
        # Apply the edited value
        field = state.edit_field
        val = state.edit_value.strip()
        if field == "cfg_start_date":
            # Basic validation: must be YYYY-MM-DD format
            if len(val) == 10 and val[4] == "-" and val[7] == "-":
                state.cfg_start_date = val
        elif field == "cfg_days":
            try:
                d = int(val)
                if d > 0:
                    state.cfg_days = d
            except ValueError:
                pass
        elif field == "cfg_scale":
            try:
                s = float(val)
                if s > 0:
                    state.cfg_scale = s
            except ValueError:
                pass
        state.editing = False
        return True
    elif key in (curses.KEY_BACKSPACE, 127, 8):
        if state.edit_value:
            state.edit_value = state.edit_value[:-1]
    elif 32 <= key < 127:
        state.edit_value += chr(key)
    return False


def handle_navigation(state, key):
    """Handle navigation and action keys."""
    sec = state.section
    row_count = state.section_row_count(sec)

    # Movement within section
    if key in (curses.KEY_UP, ord("k")):
        if state.cursor[sec] > 0:
            state.cursor[sec] -= 1
    elif key in (curses.KEY_DOWN, ord("j")):
        if state.cursor[sec] < row_count - 1:
            state.cursor[sec] += 1

    # Movement between sections
    elif key in (curses.KEY_LEFT, ord("h")):
        if state.section > SEC_SOURCES:
            state.section -= 1
            # Clamp cursor
            new_count = state.section_row_count(state.section)
            if state.cursor[state.section] >= new_count:
                state.cursor[state.section] = max(0, new_count - 1)
    elif key in (curses.KEY_RIGHT, ord("l")):
        if state.section < SEC_CONFIG:
            state.section += 1
            new_count = state.section_row_count(state.section)
            if state.cursor[state.section] >= new_count:
                state.cursor[state.section] = max(0, new_count - 1)

    # Tab / Shift+Tab
    elif key == 9:  # Tab
        state.section = (state.section + 1) % 3
        new_count = state.section_row_count(state.section)
        if state.cursor[state.section] >= new_count:
            state.cursor[state.section] = max(0, new_count - 1)
    elif key == curses.KEY_BTAB:  # Shift+Tab
        state.section = (state.section - 1) % 3
        new_count = state.section_row_count(state.section)
        if state.cursor[state.section] >= new_count:
            state.cursor[state.section] = max(0, new_count - 1)

    # Space: toggle
    elif key == ord(" "):
        if sec == SEC_SOURCES:
            state.toggle_source(state.cursor[sec])
        elif sec == SEC_SCENARIOS:
            state.toggle_scenario(state.cursor[sec])
        elif sec == SEC_CONFIG:
            fields = state.config_fields()
            idx = state.cursor[sec]
            if idx < len(fields):
                _, value, field_name, ftype = fields[idx]
                if ftype == "bool":
                    cur = getattr(state, field_name)
                    setattr(state, field_name, not cur)

    # Enter: edit config value
    elif key in (curses.KEY_ENTER, 10, 13):
        if sec == SEC_CONFIG:
            fields = state.config_fields()
            idx = state.cursor[sec]
            if idx < len(fields):
                _, value, field_name, ftype = fields[idx]
                if ftype == "bool":
                    # Toggle booleans on Enter too
                    cur = getattr(state, field_name)
                    setattr(state, field_name, not cur)
                else:
                    # Enter edit mode
                    state.editing = True
                    state.edit_field = field_name
                    state.edit_value = str(value)
                    state.edit_cursor = len(state.edit_value)


def run_generation(stdscr, state):
    """Run the generation process."""
    # Restore terminal
    curses.endwin()

    # Build sys.argv and call main
    old_argv = sys.argv
    sys.argv = state.build_argv()

    print("\n--- FAKE_DATA Generation ---\n")

    try:
        from fake_data.main_generate import main
        main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"\nError during generation: {e}")
    finally:
        sys.argv = old_argv

    print("\nPress Enter to return to TUI...")
    input()

    # Re-initialize curses
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()
    return stdscr


# =============================================================================
# MAIN LOOP
# =============================================================================

def tui_main(stdscr):
    """Main TUI entry point, called by curses.wrapper()."""
    # Setup
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    # Check terminal size
    max_y, max_x = stdscr.getmaxyx()
    if max_y < MIN_ROWS or max_x < MIN_COLS:
        safe_addstr(stdscr, 0, 0,
                    f"Terminal too small ({max_x}x{max_y}). "
                    f"Need at least {MIN_COLS}x{MIN_ROWS}.",
                    curses.A_BOLD)
        safe_addstr(stdscr, 1, 0, "Press any key to exit.")
        stdscr.getch()
        return

    # Initialize state
    state = TUIState()
    state.discover()

    # Main loop
    while True:
        draw_screen(stdscr, state)

        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break

        if key == curses.KEY_RESIZE:
            continue

        if state.editing:
            handle_edit_key(state, key)
            continue

        # Global keys
        if key in (ord("q"), ord("Q")):
            break
        elif key in (ord("g"), ord("G")):
            if state.active_sources():
                stdscr = run_generation(stdscr, state)
        else:
            handle_navigation(state, key)


def main():
    """Standalone entry point."""
    try:
        curses.wrapper(tui_main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

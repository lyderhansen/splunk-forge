# fd-generate + TUI Design Spec

## Goal

Two complementary interfaces for running log generation:
1. `tui_generate.py` — curses-based interactive TUI for offline use
2. `/fd-generate` — Claude Code skill wrapper for interactive generation

## Architecture

- **`templates/runtime/tui_generate.py`** — Python stdlib curses TUI, copied by fd-init. Discovers generators and scenarios from workspace, provides checkbox selection, config editing, dependency auto-inclusion, and runs main_generate.py.
- **`.claude/skills/fd-generate/SKILL.md`** — Claude Code skill that asks wizard questions and runs main_generate.py via Bash.

---

## 1. TUI (`tui_generate.py`)

### 1.1 Screen Layout

Single screen, 3 sections + status bar:

```
╔═══════════════════╦══════════════════╦═══════════════════╗
║ SOURCES           ║ SCENARIOS        ║ CONFIG            ║
║ [x] all           ║ [x] all          ║ Start: 2026-01-01 ║
║ [ ] fortigate     ║ [ ] brute_force  ║ Days:  31         ║
║ [+] linux (dep)   ║ [ ] disk_filling ║ Scale: 1.0        ║
║ [ ] test_kv       ║                  ║                   ║
╚═══════════════════╩══════════════════╩═══════════════════╝
 Status: 3 sources, 2 scenarios | Est: ~45,000 events
 Command: python3 main_generate.py --sources=all --scenarios=all --days=31

 [G] Generate  [Q] Quit
```

### 1.2 Discovery

On startup, TUI discovers:
- **Generators**: scan `fake_data/generators/` for SOURCE_META (same as main_generate.py's discover_generators)
- **Scenarios**: scan `fake_data/scenarios/` for SCENARIO_META (same as config.py's discover_scenarios)
- **Dependencies**: read `depends_on` from each SOURCE_META

### 1.3 Sections

**SOURCES (left):**
- "all" toggle at top
- One row per discovered generator (source_id from SOURCE_META)
- Checkbox: `[x]` selected, `[ ]` not selected, `[+]` auto-included dependency
- When a generator is selected, auto-include any generators listed in its `depends_on`
- Auto-included deps shown with `(dep)` suffix and `[+]` marker
- User cannot deselect a `[+]` dependency while the dependent generator is selected

**SCENARIOS (middle):**
- "all" toggle at top
- One row per discovered scenario (scenario_id from SCENARIO_META)
- Show day range: `brute_force (D3-5)`
- Scenarios beyond the configured --days value: shown dimmed with "(skip)" suffix
- "none" option at top (mutually exclusive with "all")

**CONFIG (right):**
- Start Date: editable (YYYY-MM-DD)
- Days: editable (integer)
- Scale: editable (float)
- Show Files: toggle [x]/[ ]
- Quiet: toggle [x]/[ ]

### 1.4 Navigation

| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Move within section |
| `←`/`→` or `h`/`l` | Move between sections (Sources ↔ Scenarios ↔ Config) |
| `Tab`/`Shift+Tab` | Cycle sections |
| `Space` | Toggle checkbox |
| `Enter` | Edit config value (inline editing mode) |
| `Escape` | Cancel edit |
| `Backspace` | Delete character in edit mode |
| `G` | Generate (launch main_generate.py) |
| `Q` | Quit |

### 1.5 Status Bar

Bottom of screen, auto-updates on any change:
- Source count, scenario count
- Event estimate (optional — if estimation logic exists)
- Preview command string

### 1.6 Dependency Handling

When user selects a generator that has `depends_on`:
1. For each dependency, check if it exists in discovered generators
2. If exists and not selected, auto-select with `[+]` marker
3. Show `(dep)` suffix on auto-included generators
4. If user deselects the dependent generator, remove `[+]` from its dependencies (unless another selected generator also depends on them)

### 1.7 Generation

When user presses `G`:
1. Build command args from selections
2. Clear screen
3. Call `main_generate.main()` directly (same-process, no subprocess)
4. After completion, show summary and "Press any key to return to TUI"

### 1.8 Integration

- `python3 fake_data/tui_generate.py` — standalone entry point
- `python3 fake_data/main_generate.py --tui` — flag added to main_generate.py that launches TUI
- TUI imports `discover_generators` from main_generate.py and `discover_scenarios` from config.py

### 1.9 Minimum Terminal Size

80 columns x 20 rows. Show error and exit if smaller.

### 1.10 Error Handling

- Safe text rendering with bounds checking
- Graceful exit on KeyboardInterrupt
- curses.wrapper() for proper cleanup

---

## 2. fd-generate Skill

### 2.1 Invocation

`/fd-generate [--days=N] [--scenarios=X] [--sources=X]`

### 2.2 Phases

**Phase A — Pre-flight:**
- Find workspace root
- Discover generators and scenarios

**Phase B — Wizard (skip if all flags provided):**
- Show available generators: "Sources: fortigate, linux, test_kv. Which to run? [all]"
- Show available scenarios: "Scenarios: brute_force (D3-5), disk_filling (D0-4). Which to activate? [none]"
- "Days? [31]"
- "Scale? [1.0]"

**Phase C — Run:**
- Execute via Bash: `python3 fake_data/main_generate.py --sources=<X> --days=<N> --scenarios=<X>`
- Stream output to user

**Phase D — Handoff:**
- Show output file locations
- Suggest Splunk import or next steps

---

## 3. Files

| File | Type | Description |
|------|------|-------------|
| `templates/runtime/tui_generate.py` | CREATE | Curses TUI template |
| `.claude/skills/fd-generate/SKILL.md` | CREATE | Claude Code skill |
| `templates/runtime/main_generate.py` | MODIFY | Add `--tui` flag |
| `CLAUDE.md` | MODIFY | Update directory layout |
| `CHANGEHISTORY.md` | MODIFY | Add entry |

## 4. Scope Boundaries

**In scope:**
- Curses TUI with 3 sections
- Dependency auto-inclusion
- fd-generate skill
- --tui flag in main_generate.py

**Out of scope:**
- Parallel generation (TUI uses main_generate.py's existing sequential execution)
- Event volume estimation (can add later)
- Animation/visual effects
- Color themes

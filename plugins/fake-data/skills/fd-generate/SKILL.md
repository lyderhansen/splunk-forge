---
name: fd-generate
description: Generate demo log data for Splunk. Use when you need to create synthetic logs for testing, demos, or training.
version: 0.1.0
metadata:
  argument-hint: "[--days=N] [--scenarios=X] [--sources=X]"
---

# fd-generate -- Generate demo log data for Splunk

Wizard-based skill that discovers generators and scenarios, asks
configuration questions, and runs main_generate.py to produce synthetic
log files for Splunk testing, demos, or training.

**Source of truth:** `docs/superpowers/specs/2026-04-12-fd-generate-tui-design.md`

---

## Phase A -- Pre-flight

### A.1 Find workspace root

Walk up from the current working directory looking for `fake_data/manifest.py`:

```
Check: ./fake_data/manifest.py
Check: ../fake_data/manifest.py
Check: ../../fake_data/manifest.py
(up to 5 levels)
```

If not found, stop:
> "No FAKE_DATA workspace found. Run `/fd-init` first."

If found, set the workspace root to the directory containing `fake_data/`.

### A.2 Discover generators

Scan `fake_data/generators/` for Python files with `SOURCE_META`. For each file, extract:
- `source_id`
- `category`
- `description`

Build list: `[{"source_id": "...", "category": "...", "description": "..."}]`

### A.3 Discover scenarios

If `fake_data/scenarios/` exists, scan for Python files with `SCENARIO_META`. For each, extract:
- `scenario_id`
- `start_day`
- `end_day`
- `description`

Build list: `[{"scenario_id": "...", "start_day": N, "end_day": N, "description": "..."}]`

---

## Phase B -- Wizard (skip if all flags provided on invocation)

Ask one question at a time. If a flag was provided on invocation, skip that question.

### B.1 Sources

Show available generators with their category. Example:

> "Available sources: fortigate (network), linux (linux), test_kv (network). Which to run? [all]"

Accept: `all`, or a comma-separated list of source IDs.

### B.2 Scenarios

If any scenarios were discovered, show them with day ranges. Example:

> "Available scenarios: brute_force (D3-5), disk_filling (D0-4). Which to activate? [none]"

Accept: `none`, `all`, or a comma-separated list of scenario IDs.

If no scenarios directory or no scenarios found, skip this question and default to `none`.

### B.3 Days

If scenarios were selected, suggest the minimum days needed:

> "brute_force needs at least 6 days. Days? [7]"

Otherwise:

> "Days? [31]"

Accept: positive integer.

### B.4 Scale

> "Scale? [1.0]"

Accept: positive float.

---

## Phase C -- Run

Build and execute the command via Bash tool from the workspace root:

```bash
cd <workspace_root> && python3 fake_data/main_generate.py --sources=<X> --days=<N> --scale=<S> --scenarios=<X>
```

Where:
- `<X>` for sources: `all` or comma-separated source IDs
- `<N>`: integer number of days
- `<S>`: float scale factor
- `<X>` for scenarios: `none`, `all`, or comma-separated scenario IDs

Stream output to the user.

---

## Phase D -- Handoff

### D.1 Print output summary

```
Generation complete!

Output files:
  ls fake_data/output/
```

### D.2 Chain to fd-build-app

Ask the user:

> "Logs generated. Build the Splunk app now?
>
>   1. **yes** — Run /fd-build-app to package everything as an installable Splunk TA
>   2. **skip** — I just wanted the log files, thanks
> [1]"

If **yes**: invoke `/fd-build-app`
If **skip**: print a tip:

```
Tip: Launch the TUI for interactive re-runs:
  python3 fake_data/tui_generate.py
```

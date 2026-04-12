---
name: fd-add-scenario
description: Create a new attack or operational scenario. Use when adding coordinated events across multiple log sources.
version: 0.1.0
metadata:
  argument-hint: "<scenario_id_or_description> [--auto]"
---

# fd-add-scenario -- Create a scenario for correlated events

Create a multi-phase scenario that injects realistic, correlated events
across multiple generators. Scenarios tag all events with `demo_id` for
Splunk correlation.

**Key principle:** Research fills in realistic phases, IOCs, and event
details. The user describes *what* should happen; the skill figures out *how*.

**Source of truth:** `docs/superpowers/specs/2026-04-12-fd-add-scenario-design.md`

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

### A.2 Parse input

Expected invocation: `/fd-add-scenario <scenario_id_or_description> [--auto]`

If no argument provided, prompt:

> "Describe the scenario you want to create, or give a type (brute_force,
> data_exfil, disk_filling, cert_expiry, ransomware, etc.)"

If the argument looks like a description (contains spaces), extract a
scenario_id from the first meaningful noun/verb pair (e.g., "brute force
login attack" -> `brute_force`).

If `--auto` is present, note it for later phases (skip interactive prompts).

### A.3 Normalize scenario_id

- Lowercase the value
- Replace every run of non-alphanumeric characters with a single underscore
- Strip leading/trailing underscores
- Reject if empty or starts with a digit:
  > "scenario_id must start with a letter and contain at least one alphanumeric character."

### A.4 Check collision

Check if `fake_data/scenarios/<scenario_id>.py` exists.

If it does:
> "Scenario '<scenario_id>' already exists at `fake_data/scenarios/<scenario_id>.py`.
> Overwrite or abort? [abort]"

If overwrite: continue. If abort: stop.

### A.5 Scan generators

List all `fake_data/generators/generate_*.py` files. For each, read the
file and extract the `SOURCE_META` dict to build an available-sources list:

```python
available_sources = []
for gen_file in sorted(generators_dir.glob("generate_*.py")):
    # Read file, find SOURCE_META dict, extract source_id, category, description
```

Store as: `[{"source_id": "...", "category": "...", "description": "..."}]`

If no generators found:
> "No generators found in `fake_data/generators/`. Add at least one generator with `/fd-add-generator` first."

### A.6 Check _base.py

Check if `fake_data/scenarios/_base.py` exists.

If it does NOT exist, note that Phase E must bootstrap the scenario runtime
(copy `_base.py`, `__init__.py`, and update `config.py`).

---

## Phase B -- Research

### B.1 Gather world state

Read `fake_data/world.py` to extract context for the research subagent:
- `ORG_NAME` (or org name from manifest.py)
- `USERS` -- count and sample usernames
- `LOCATIONS` -- list of location names
- `INFRASTRUCTURE` -- list of hostnames (if present; note "basic world.py" if absent)
- `EXTERNAL_IP_POOL` -- whether it exists

### B.2 Dispatch sonnet subagent

Use the **Agent tool** with `model: sonnet` to dispatch a research
subagent. The subagent runs in isolated context.

**Subagent prompt:**

```
You are researching a realistic scenario for synthetic log generation.

Scenario type: <scenario_id>
User description: <user_description or "none">
Available generators in workspace: <comma-separated list of source_id values>
Organization: <ORG_NAME from world.py>
Locations: <list of location names from world.py>
User count: <len(USERS)>
Infrastructure: <list of hostnames if INFRASTRUCTURE exists, else "basic world.py, no infrastructure list">

Design a realistic multi-phase scenario that produces correlated events
across the available generators. The scenario will be used for Splunk
security/IT demos, so it needs to be realistic and tell a coherent story.

Return your answer in this exact format:

SCENARIO_RESEARCH:
category: <attack|ops|network>
description: <one-sentence description of the scenario>
start_day: <int, typically 2-4, must be >= 1>
end_day: <int, typically 4-7, must be > start_day>

PHASES:
<phase_name> | <start_day> | <end_day> | <description>
<phase_name> | <start_day> | <end_day> | <description>
<phase_name> | <start_day> | <end_day> | <description>
END_PHASES

SUGGESTED_SOURCES:
<source_id> | <why this source is involved and what events it produces>
END_SUGGESTED_SOURCES

CONFIG_FIELDS:
<field_name> | <type> | <default_value> | <description>
END_CONFIG_FIELDS

EVENT_DESCRIPTIONS:
<source_id> | <phase_name> | <detailed description of what events look like, including key fields, values, and log format specifics>
END_EVENT_DESCRIPTIONS

Guidelines:
- Phases should span 2-5 days total (within a typical 7-31 day generation window)
- Start on day 2+ so days 0-1 have baseline-only traffic
- ONLY suggest sources from the available generators list provided above
- Config fields should use "auto" as the default when the value should be
  resolved from world.py at runtime (e.g., target_user, target_host,
  attacker_ip). Use "auto" for users, hosts, and IPs.
- Always include demo_id as the first config field with the scenario_id as default
- Event descriptions must be specific enough to generate realistic log lines
  in the correct format for each generator
- Every event MUST include demo_id=<scenario_id> for Splunk correlation
- For attack scenarios: include reconnaissance, exploitation, and
  post-exploitation phases
- For ops scenarios: include degradation, alert, and resolution phases
- For network scenarios: include detection, impact, and remediation phases
- Be specific about field names and values in EVENT_DESCRIPTIONS
```

### B.3 Parse subagent response

Parse the structured response into:
- `category`, `description`, `start_day`, `end_day`
- `phases`: list of `{name, start_day, end_day, description}`
- `suggested_sources`: list of `{source_id, reason}`
- `config_fields`: list of `{name, type, default, description}`
- `event_descriptions`: list of `{source_id, phase, description}`

If parsing fails (subagent returned free-form text), extract what you can
and fill gaps with reasonable defaults based on the scenario_id.

---

## Phase C -- Source matching

### C.1 Match sources

Compare `suggested_sources` from research against `available_sources`
from Phase A.5:
- **matched**: source_id exists in available generators
- **missing**: source_id was suggested but no generator exists

### C.2 Show source status (skip if --auto)

```
Sources for this scenario:
  [x] fortigate   (exists)
  [x] linux       (exists)
  [ ] entra_id    (missing -- run /fd-add-generator entra_id to add)

Proceed with available sources? [yes/auto/cancel]
```

- **yes**: proceed with matched sources only
- **auto**: proceed and remember preference for remaining prompts
- **cancel**: exit without creating anything

If `--auto` flag was set: skip this prompt, proceed with matched sources.

If NO sources matched:
> "None of the suggested sources exist in your workspace. Add generators
> first with `/fd-add-generator`, then re-run this skill."

---

## Phase D -- Review gate

Display the complete scenario overview:

```
Scenario: fake_data/scenarios/<scenario_id>.py

  Scenario ID:    <scenario_id>
  Category:       <category>
  Demo ID:        <scenario_id>
  Description:    <description>

  Timeline (days <start_day>-<end_day>):
    Day <N>:  <phase_name>  -- <phase_description>
    Day <N>:  <phase_name>  -- <phase_description>
    ...

  Config:
    demo_id:       <scenario_id>
    <field_name>:  <default> -> (<auto-resolution hint>)
    ...

  Affected generators:
    <source_id>  -- <summary of events per phase>
    ...

Create this scenario? [yes/edit/cancel]
```

- **yes**: proceed to Phase E
- **edit**: ask what to change, incorporate edits, re-display this gate
- **cancel**: exit without creating anything

If `--auto`: skip this prompt, proceed directly to Phase E.

---

## Phase E -- Code generation

### E.1 Bootstrap runtime (first scenario only)

If `fake_data/scenarios/_base.py` does NOT exist (noted in A.6):

1. Create directory:
   ```bash
   mkdir -p fake_data/scenarios
   ```

2. Write `fake_data/scenarios/__init__.py` (empty package marker):
   ```python
   # Scenario package marker.
   ```

3. Read `_base.py` from the plugin repo using the Read tool:
   `../../../templates/scenarios/_base.py` (relative to this SKILL.md)
   Write it to `fake_data/scenarios/_base.py`.

4. Update `fake_data/config.py` -- read the current user config.py, then
   read the updated template from the plugin repo:
   `../../../templates/runtime/config.py` (relative to this SKILL.md)
   Copy the `discover_scenarios()` and `expand_scenarios()` functions from
   the template into the user's `fake_data/config.py`, replacing the old
   placeholder implementation. Preserve all other content in the user's
   config.py (volume settings, output paths, etc.).

### E.2 Generate scenario file

Write a complete Python file to `fake_data/scenarios/<scenario_id>.py`
with this structure:

```python
#!/usr/bin/env python3
"""
<Description> scenario for FAKE_DATA.

Generated by fd-add-scenario. This file is yours -- edit freely.

Phases:
  - <phase_name> (days <start>-<end>): <description>
  ...
"""

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Bootstrap sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fake_data.scenarios._base import BaseScenario
from fake_data.time_utils import ts_iso

# =============================================================================
# SCENARIO METADATA
# =============================================================================

SCENARIO_META = {
    "scenario_id": "<scenario_id>",
    "category": "<category>",
    "sources": [<list of matched source_ids as strings>],
    "demo_id": "<scenario_id>",
    "description": "<description>",
    "start_day": <start_day>,
    "end_day": <end_day>,
    "phases": [
        {
            "name": "<phase_name>",
            "start_day": <N>,
            "end_day": <N>,
            "description": "<phase_description>",
        },
        # ... one dict per phase
    ],
}


# =============================================================================
# SCENARIO CONFIG
# =============================================================================

@dataclass
class <PascalCaseScenarioId>Config:
    demo_id: str = "<scenario_id>"
    <for each config_field from research>
    <field_name>: <type> = "<default>"
    </for each>
    start_day: int = <start_day>
    end_day: int = <end_day>


# =============================================================================
# SCENARIO CLASS
# =============================================================================

class <PascalCaseScenarioId>Scenario(BaseScenario):

    def meta(self) -> dict:
        return SCENARIO_META

    def default_config(self):
        return <PascalCaseScenarioId>Config()

    # -----------------------------------------------------------------
    # Generator-specific methods
    # -----------------------------------------------------------------

    def <source_id>_hour(self, day: int, hour: int) -> List[str]:
        """Return <source_id>-formatted log lines for this hour."""
        if not self.is_active(day):
            return []
        phase = self.get_phase(day)
        events = []
        # Phase-specific event generation using EVENT_DESCRIPTIONS
        # from research. Each event string MUST include demo_id.
        ...
        return events

    # Repeat for each matched source_id. Method name MUST be
    # exactly <source_id>_hour (matching SOURCE_META["source_id"]
    # of the target generator).

    # -----------------------------------------------------------------
    # Internal event builders
    # -----------------------------------------------------------------

    # Helper methods for building source-specific event strings.
    # Use self.config for resolved values (target_user, attacker_ip, etc.)
    # Every event string MUST include demo_id for Splunk correlation:
    #   KV format:  demo_id=<scenario_id>
    #   JSON format: "demo_id": "<scenario_id>"
    #   Syslog:     demo_id=<scenario_id> in the message body


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    s = <PascalCaseScenarioId>Scenario()
    print(f"Scenario: {SCENARIO_META['scenario_id']}")
    print(f"Config: {s.config}")
    print(f"Active days: {SCENARIO_META['start_day']}-{SCENARIO_META['end_day']}")
    for phase in SCENARIO_META["phases"]:
        print(f"  {phase['name']} (days {phase['start_day']}-{phase['end_day']}): "
              f"{phase['description']}")
    # Test event generation for each source
    for source_id in SCENARIO_META["sources"]:
        method = getattr(s, f"{source_id}_hour", None)
        if method:
            test_events = method(SCENARIO_META["start_day"], 10)
            print(f"\n{source_id} sample events "
                  f"(day {SCENARIO_META['start_day']}, hour 10):")
            for ev in test_events[:3]:
                print(f"  {ev[:120]}")
```

**Critical rules for generated code:**

- Method names MUST be `<source_id>_hour` (e.g., `fortigate_hour`, `linux_hour`)
  matching `SOURCE_META["source_id"]` of the target generator exactly.
- Every event string MUST include `demo_id=<scenario_id>` (KV) or
  `"demo_id": "<scenario_id>"` (JSON) for Splunk correlation.
- Use `self.config.<field>` for all resolved values (target_user, attacker_ip, etc.).
- Use `self.get_phase(day)` to determine which phase is active.
- Use `self.is_active(day)` to short-circuit when the scenario is not running.
- Event strings must match the format of the target generator (KV, JSON, syslog, etc.).
  Read the target generator files if needed to match their format exactly.
- PascalCase class names: `brute_force` -> `BruteForce`, `disk_filling` -> `DiskFilling`.
- Use `ts_iso` from `fake_data.time_utils` for timestamps.

### E.3 Syntax check

Run via Bash:
```bash
python3 -c "import ast; ast.parse(open('fake_data/scenarios/<scenario_id>.py').read()); print('Syntax OK')"
```

If syntax check fails, fix the file and re-check.

### E.4 Update existing generators

For each matched source in the workspace, read the generator file and
check if it still has the commented scenario stub:

```python
            # Scenario events (future): active_scenarios would inject here
            # for scenario in active_scenarios:
            #     events.extend(scenario.source_hour(day, hour))
```

If found, replace with the active 3-line integration:

```python
            # Inject scenario events
            for scenario in active_scenarios:
                method = getattr(scenario, f"{SOURCE_META['source_id']}_hour", None)
                if method:
                    events.extend(method(day, hour))
```

If the generator already has the active integration code (no commented
stub), leave it unchanged.

---

## Phase F -- Verification

### F.1 Import test

Run via Bash from the workspace root:

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data.scenarios.<scenario_id> import <PascalCaseScenarioId>Scenario, SCENARIO_META
s = <PascalCaseScenarioId>Scenario()
print(f'Config: {s.config}')
print(f'Phase on day {SCENARIO_META[\"start_day\"]}: {s.get_phase(SCENARIO_META[\"start_day\"])}')
for src in SCENARIO_META['sources']:
    method = getattr(s, f'{src}_hour', None)
    if method:
        evts = method(SCENARIO_META['start_day'], 10)
        print(f'{src}: {len(evts)} events')
        if evts:
            print(f'  sample: {evts[0][:100]}')
print('Verification OK')
"
```

If this fails:
- If `_base.py` resolver crashes (e.g., world.py missing INFRASTRUCTURE),
  fix the scenario or _base.py and re-test.
- If import fails, fix the syntax error and re-test.
- If events are empty, check the phase/day logic and fix.

---

## Phase G -- Handoff

### G.1 Print summary

```
Scenario created: fake_data/scenarios/<scenario_id>.py
  Phases:  <N>  (days <start_day>-<end_day>)
  Sources: <comma-separated source_ids>
```

### G.2 Chain to fd-generate

Ask the user:

> "Scenario created. Generate logs with this scenario now?
>
>   1. **yes** — Run /fd-generate with --scenarios=<scenario_id> and a
>      day count that covers the scenario window (<end_day + 2>)
>   2. **skip** — I'll do it myself later
> [1]"

If **yes**: invoke `/fd-generate --scenarios=<scenario_id> --days=<end_day+2>`

If **skip**: print the manual commands:

```
Manual commands:
  Review:     open fake_data/scenarios/<scenario_id>.py
  Generate:   python3 fake_data/main_generate.py --days=<N> --scenarios=<scenario_id>
  All:        python3 fake_data/main_generate.py --days=31 --scenarios=all
  Splunk:     index=* demo_id=<scenario_id> | stats count by sourcetype
```

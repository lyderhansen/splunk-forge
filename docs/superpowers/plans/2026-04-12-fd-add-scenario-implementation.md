# Implementation Plan: fd-add-scenario

## Goal

Implement the scenario system for FAKE_DATA: BaseScenario class with auto-resolver, runtime discovery/integration, and the fd-add-scenario skill that uses research-based generation to create realistic multi-phase scenarios.

## Architecture

- **BaseScenario** (`templates/scenarios/_base.py`) -- base class with `_resolve_auto_values()`, `get_phase()`, `is_active()`
- **Runtime** -- `discover_scenarios()` + real `expand_scenarios()` in config.py
- **Generator hook** -- 3-line scenario injection replacing commented stub in template
- **Skill** (`.claude/skills/fd-add-scenario/SKILL.md`) -- phases A-G wizard + research + code generation

## Tech Stack

stdlib-only Python 3.9+, template-only runtime (fd-init copies files to user workspace).

## Execution

Use [subagent-driven-development](superpowers:subagent-driven-development) -- tasks are independent and can be parallelized.

---

## Task 1: Create scenario templates (`_base.py` + `__init__.py`)

### Files
- `templates/scenarios/_base.py` (CREATE)
- `templates/scenarios/__init__.py` (CREATE)

### Steps

- [ ] 1.1 Create directory

```bash
mkdir -p templates/scenarios
```

- [ ] 1.2 Write `templates/scenarios/__init__.py`

```python
# Scenario package marker — copied by fd-init into user workspace.
```

- [ ] 1.3 Write `templates/scenarios/_base.py`

```python
"""
Base scenario class for FAKE_DATA.

Provides auto-resolution of 'auto' config sentinels from world.py,
phase tracking, and the interface contract for generator-specific methods.

Copied into user workspace by fd-init. Edit freely.
"""

import hashlib
import ipaddress
import random
from dataclasses import fields as dataclass_fields
from typing import Dict, List, Optional


class BaseScenario:
    """Base class for all scenarios."""

    def __init__(self, config=None):
        self.config = config or self.default_config()
        self._resolve_auto_values()

    def default_config(self):
        """Return the default config dataclass instance. Override in subclass."""
        raise NotImplementedError

    def meta(self) -> dict:
        """Return the SCENARIO_META dict. Override in subclass."""
        raise NotImplementedError

    # -----------------------------------------------------------------
    # Phase helpers
    # -----------------------------------------------------------------

    def get_phase(self, day: int) -> Optional[str]:
        """Return phase name for given day, or None if outside scenario window."""
        for phase in self.meta().get("phases", []):
            if phase["start_day"] <= day <= phase["end_day"]:
                return phase["name"]
        return None

    def is_active(self, day: int) -> bool:
        """Check if scenario is active on this day."""
        m = self.meta()
        return m["start_day"] <= day <= m["end_day"]

    # -----------------------------------------------------------------
    # Auto-resolver
    # -----------------------------------------------------------------

    def _resolve_auto_values(self):
        """Replace 'auto' sentinels with real values from world.py.

        Handles both enriched world.py (with role, INFRASTRUCTURE) and
        basic world.py (only username, email, location, department).
        Missing world.py exports are silently ignored.
        """
        try:
            from fake_data import world
        except ImportError:
            return

        users = getattr(world, "USERS", [])
        infrastructure = getattr(world, "INFRASTRUCTURE", [])
        external_pool = getattr(world, "EXTERNAL_IP_POOL", [])

        seed = self._stable_seed(self.meta().get("scenario_id", "default"))

        for field in dataclass_fields(self.config):
            value = getattr(self.config, field.name)
            if value != "auto":
                continue

            resolved = self._resolve_field(
                field.name, users, infrastructure, external_pool, seed
            )
            if resolved is not None:
                setattr(self.config, field.name, resolved)

    def _resolve_field(
        self,
        field_name: str,
        users: list,
        infrastructure: list,
        external_pool: list,
        seed: int,
    ) -> Optional[str]:
        """Resolve a single 'auto' field based on naming conventions."""
        fn = field_name.lower()

        # User fields
        if "user" in fn:
            user = self._pick_user(users, seed, field_name)
            return user["username"] if user else None

        # Host IP fields (must check before plain host)
        if "host_ip" in fn or ("host" in fn and "ip" in fn):
            host_field = fn.replace("_ip", "")
            host_val = getattr(self.config, host_field, None) if hasattr(self.config, host_field) else None
            if host_val and host_val != "auto" and infrastructure:
                match = self._find_infra_by_hostname(infrastructure, host_val)
                if match:
                    return match.get("ip", None)
            # Fallback: pick any infra IP
            if infrastructure:
                entry = self._pick_infra(infrastructure, seed, field_name)
                return entry.get("ip", None) if entry else None
            return None

        # Host fields (without ip)
        if "host" in fn:
            entry = self._pick_infra(infrastructure, seed, field_name)
            return entry.get("hostname", None) if entry else None

        # Attacker / external IP fields
        if "attacker" in fn or "external" in fn or fn.endswith("_ip"):
            return self._pick_external_ip(external_pool, seed, field_name)

        return None

    # -----------------------------------------------------------------
    # Deterministic pickers
    # -----------------------------------------------------------------

    def _pick_user(self, users: list, seed: int, field_name: str) -> Optional[dict]:
        """Pick a user deterministically. Prefers admin/IT for attack scenarios."""
        if not users:
            return None
        key = self._field_hash(seed, field_name)

        # Try role-based filtering for enriched world.py
        category = self.meta().get("category", "")
        if category == "attack":
            # Prefer IT/admin users if role field exists, else department=it
            filtered = [u for u in users if u.get("role") in ("admin", "it_admin")]
            if not filtered:
                filtered = [u for u in users if u.get("department") == "it"]
            if filtered:
                return filtered[key % len(filtered)]

        return users[key % len(users)]

    def _pick_infra(self, infrastructure: list, seed: int, field_name: str) -> Optional[dict]:
        """Pick an infrastructure entry deterministically."""
        if not infrastructure:
            return None
        key = self._field_hash(seed, field_name)
        return infrastructure[key % len(infrastructure)]

    def _find_infra_by_hostname(self, infrastructure: list, hostname: str) -> Optional[dict]:
        """Find an infrastructure entry by hostname."""
        for entry in infrastructure:
            if entry.get("hostname") == hostname:
                return entry
        return None

    def _pick_external_ip(self, pool: list, seed: int, field_name: str) -> str:
        """Pick a deterministic external IP from CIDR pool."""
        if not pool:
            return "198.51.100.1"
        key = self._field_hash(seed, field_name)
        cidr = pool[key % len(pool)]
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            # Pick a host address deterministically
            num_hosts = max(1, network.num_addresses - 2)
            offset = (key % num_hosts) + 1
            return str(network.network_address + offset)
        except (ValueError, TypeError):
            return "198.51.100.1"

    # -----------------------------------------------------------------
    # Hashing utilities
    # -----------------------------------------------------------------

    @staticmethod
    def _stable_seed(scenario_id: str) -> int:
        """Produce a stable integer seed from scenario_id."""
        return int(hashlib.sha256(scenario_id.encode()).hexdigest()[:8], 16)

    @staticmethod
    def _field_hash(seed: int, field_name: str) -> int:
        """Combine seed + field_name for per-field determinism."""
        combined = f"{seed}:{field_name}"
        return int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
```

- [ ] 1.4 Syntax check

```bash
python3 -c "import ast; ast.parse(open('templates/scenarios/_base.py').read()); print('OK')"
```

- [ ] 1.5 Commit

```bash
git add templates/scenarios/__init__.py templates/scenarios/_base.py
git commit -m "Add BaseScenario template with auto-resolver

Templates for scenarios/_base.py and __init__.py. BaseScenario provides
auto-resolution of 'auto' config values from world.py, phase tracking,
and deterministic entity picking. Handles both enriched and basic world.py."
```

---

## Task 2: Update config.py (replace expand_scenarios placeholder)

### Files
- `templates/runtime/config.py` (MODIFY)

### Steps

- [ ] 2.1 Replace the `expand_scenarios` placeholder (lines 155-172) with real implementation

Replace the entire SCENARIO SUPPORT section:

```python
# =============================================================================
# SCENARIO SUPPORT
# =============================================================================

def discover_scenarios() -> dict:
    """Scan fake_data/scenarios/ for modules with SCENARIO_META.

    Returns dict mapping scenario_id -> {"meta": dict, "instance": BaseScenario}.
    """
    import importlib
    import pkgutil

    scenarios_dir = Path(__file__).resolve().parent / "scenarios"
    if not scenarios_dir.is_dir():
        return {}

    discovered = {}
    for finder, name, _ in pkgutil.iter_modules([str(scenarios_dir)]):
        if name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"fake_data.scenarios.{name}")
        except (ImportError, SyntaxError) as e:
            print(f"  Warning: could not import scenarios/{name}.py: {e}")
            continue

        meta = getattr(module, "SCENARIO_META", None)
        if meta is None:
            continue

        # Find the scenario class (convention: class ending in "Scenario")
        cls = None
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (isinstance(obj, type)
                    and attr_name.endswith("Scenario")
                    and attr_name != "BaseScenario"):
                cls = obj
                break

        if cls:
            try:
                discovered[meta["scenario_id"]] = {
                    "meta": meta,
                    "instance": cls(),
                }
            except Exception as e:
                print(f"  Warning: could not instantiate {attr_name}: {e}")

    return discovered


def expand_scenarios(scenarios: str) -> list:
    """Expand a scenario specification string into active scenario instances.

    Args:
        scenarios: Comma-separated list of scenario names, "all", or "none".

    Returns:
        List of scenario instances.
    """
    if scenarios == "none":
        return []

    discovered = discover_scenarios()

    if scenarios == "all":
        return [info["instance"] for info in discovered.values()]

    names = [n.strip() for n in scenarios.split(",")]
    active = []
    for name in names:
        if name in discovered:
            active.append(discovered[name]["instance"])
        else:
            print(f"  Warning: scenario '{name}' not found, skipping")
    return active
```

- [ ] 2.2 Syntax check

```bash
python3 -c "import ast; ast.parse(open('templates/runtime/config.py').read()); print('OK')"
```

- [ ] 2.3 Commit

```bash
git add templates/runtime/config.py
git commit -m "Replace expand_scenarios placeholder with real discovery

Adds discover_scenarios() that scans fake_data/scenarios/ using
pkgutil.iter_modules (same pattern as discover_generators). expand_scenarios
now resolves 'all', 'none', or comma-separated scenario names."
```

---

## Task 3: Update template generator (activate scenario injection)

### Files
- `templates/generators/_template_generator.py` (MODIFY)

### Steps

- [ ] 3.1 Replace the commented scenario stub (lines 81-83) with active code

Find:
```python
            # Scenario events (future): active_scenarios would inject here
            # for scenario in active_scenarios:
            #     events.extend(scenario.source_hour(day, hour))
```

Replace with:
```python
            # Inject scenario events
            for scenario in active_scenarios:
                method = getattr(scenario, f"{SOURCE_META['source_id']}_hour", None)
                if method:
                    events.extend(method(day, hour))
```

- [ ] 3.2 Syntax check

```bash
python3 -c "import ast; ast.parse(open('templates/generators/_template_generator.py').read()); print('OK')"
```

- [ ] 3.3 Commit

```bash
git add templates/generators/_template_generator.py
git commit -m "Activate scenario injection in template generator

Replaces commented stub with active 3-line integration. New generators
scaffolded by fd-add-generator will automatically call scenario methods."
```

---

## Task 4: Create SKILL.md for fd-add-scenario

### Files
- `.claude/skills/fd-add-scenario/SKILL.md` (CREATE)

### Steps

- [ ] 4.1 Create directory

```bash
mkdir -p .claude/skills/fd-add-scenario
```

- [ ] 4.2 Write `.claude/skills/fd-add-scenario/SKILL.md`

```markdown
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

Walk up from the current working directory looking for `fake_data/manifest.py`
(up to 5 levels). If not found:

> "No FAKE_DATA workspace found. Run `/fd-init` first."

Set workspace root to the directory containing `fake_data/`.

### A.2 Parse input

Expected: `/fd-add-scenario <scenario_id_or_description> [--auto]`

If no argument provided, prompt:

> "Describe the scenario you want to create, or give a type (brute_force,
> data_exfil, disk_filling, cert_expiry, ransomware, etc.)"

If the argument looks like a description (contains spaces), extract a
scenario_id from the first meaningful noun/verb pair (e.g., "brute force
login attack" -> `brute_force`).

### A.3 Normalize scenario_id

- Lowercase
- Replace non-alphanumeric runs with underscore
- Strip leading/trailing underscores
- Reject if empty or starts with digit

### A.4 Check collision

If `fake_data/scenarios/<scenario_id>.py` exists:

> "Scenario '<scenario_id>' already exists. Overwrite or abort? [abort]"

### A.5 Scan generators

List all `fake_data/generators/generate_*.py` files. For each, read the
file and extract `SOURCE_META` dict to build an available-sources list:

```python
available_sources = []
for gen_file in sorted(generators_dir.glob("generate_*.py")):
    # Read file, find SOURCE_META dict, extract source_id and category
```

Store: `[{"source_id": "...", "category": "...", "description": "..."}]`

### A.6 Check _base.py

If `fake_data/scenarios/_base.py` does NOT exist, note that Phase E must
bootstrap the scenario runtime (copy _base.py and __init__.py).

---

## Phase B -- Research

### B.1 Dispatch sonnet subagent

Use the **Agent tool** with `model: sonnet` to dispatch a research
subagent. Provide this prompt:

```
You are researching a realistic scenario for synthetic log generation.

Scenario type: <scenario_id>
User description: <user_description or "none">
Available generators in workspace: <list of source_id values>
Organization: <ORG_NAME from world.py>
Locations: <list of location names>
User count: <len(USERS)>
Infrastructure: <list of hostnames if INFRASTRUCTURE exists, else "basic world.py, no infrastructure list">

Design a realistic multi-phase scenario. Return your answer in this
exact format:

SCENARIO_RESEARCH:
category: <attack|ops|network>
description: <one-sentence description>
start_day: <int, typically 2-4>
end_day: <int, typically 4-7>

PHASES:
<phase_name> | <start_day> | <end_day> | <description>
<phase_name> | <start_day> | <end_day> | <description>
<phase_name> | <start_day> | <end_day> | <description>
END_PHASES

SUGGESTED_SOURCES:
<source_id> | <why this source is involved>
END_SUGGESTED_SOURCES

CONFIG_FIELDS:
<field_name> | <type> | <default_value> | <description>
END_CONFIG_FIELDS

EVENT_DESCRIPTIONS:
<source_id> | <phase_name> | <what events look like, including key fields and values>
END_EVENT_DESCRIPTIONS

Guidelines:
- Phases should span 2-5 days total (within a typical 7-31 day generation window)
- Start on day 2+ (day 0-1 = baseline only)
- Only suggest sources from the available generators list
- Config fields should use "auto" as default when the value should be resolved from world.py
- Event descriptions must be specific enough to generate realistic log lines
- Include demo_id tagging in all events
- For attack scenarios: include reconnaissance, exploitation, and post-exploitation phases
- For ops scenarios: include degradation, alert, and resolution phases
```

### B.2 Parse subagent response

Parse the structured response into:
- `category`, `description`, `start_day`, `end_day`
- `phases`: list of `{name, start_day, end_day, description}`
- `suggested_sources`: list of `{source_id, reason}`
- `config_fields`: list of `{name, type, default, description}`
- `event_descriptions`: list of `{source_id, phase, description}`

---

## Phase C -- Source matching

### C.1 Match sources

Compare `suggested_sources` from research against `available_sources`
from Phase A.5. Categorize as `matched` or `missing`.

### C.2 Show source status (skip if --auto)

```
Sources for this scenario:
  [x] fortigate   (exists)
  [x] linux       (exists)
  [ ] entra_id    (missing -- run /fd-add-generator entra_id to add)

Proceed with available sources? [yes/auto/cancel]
```

If `--auto` flag: skip this prompt, use matched sources only.

---

## Phase D -- Review gate

Display the complete scenario overview:

```
Scenario: fake_data/scenarios/<scenario_id>.py

  Scenario ID:    <scenario_id>
  Category:       <category>
  Demo ID:        <scenario_id>
  Description:    <description>

  Timeline (days <start>-<end>):
    Day <N>:  <phase_name>  -- <phase_description>
    ...

  Config:
    <field_name>:  <default> -> (<resolution description>)
    ...

  Affected generators:
    <source_id>  -- <summary of events>
    ...

Create this scenario? [yes/edit/cancel]
```

- **yes**: proceed to Phase E
- **edit**: re-run research with user corrections
- **cancel**: exit

---

## Phase E -- Code generation

### E.1 Bootstrap runtime (first scenario only)

If `fake_data/scenarios/_base.py` does NOT exist:

1. Create `fake_data/scenarios/__init__.py` (empty package marker)
2. Read `templates/scenarios/_base.py` from the plugin repo:
   `../../../templates/scenarios/_base.py` (relative to this SKILL.md)
   Write it to `fake_data/scenarios/_base.py`
3. Update `fake_data/config.py` -- replace the `expand_scenarios`
   placeholder with the real discovery implementation. Read the
   updated template from:
   `../../../templates/runtime/config.py` (relative to this SKILL.md)
   Copy the `discover_scenarios()` and `expand_scenarios()` functions
   into the user's `fake_data/config.py`, replacing the old placeholder.

### E.2 Generate scenario file

Write a complete Python file to `fake_data/scenarios/<scenario_id>.py`
with this structure:

```python
#!/usr/bin/env python3
"""
<Description> scenario for FAKE_DATA.

Generated by fd-add-scenario. This file is yours -- edit freely.

Phases:
<for each phase>
  - <phase_name> (days <start>-<end>): <description>
</for each phase>
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
    "sources": [<list of matched source_ids>],
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
class <ScenarioId>Config:
    demo_id: str = "<scenario_id>"
    <for each config_field>
    <field_name>: <type> = "<default>"
    </for each>
    start_day: int = <start_day>
    end_day: int = <end_day>


# =============================================================================
# SCENARIO CLASS
# =============================================================================

class <ScenarioId>Scenario(BaseScenario):

    def meta(self) -> dict:
        return SCENARIO_META

    def default_config(self):
        return <ScenarioId>Config()

    # -----------------------------------------------------------------
    # Generator-specific methods
    # -----------------------------------------------------------------

    <for each matched source_id>
    def <source_id>_hour(self, day: int, hour: int) -> List[str]:
        """Return <source_id>-formatted log lines for this hour."""
        if not self.is_active(day):
            return []
        phase = self.get_phase(day)
        events = []
        <phase-specific event generation logic from research>
        return events
    </for each>

    # -----------------------------------------------------------------
    # Internal event builders
    # -----------------------------------------------------------------

    <helper methods for building source-specific event strings>


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    s = <ScenarioId>Scenario()
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
            print(f"\n{source_id} sample events (day {SCENARIO_META['start_day']}, hour 10):")
            for ev in test_events[:3]:
                print(f"  {ev[:120]}")
```

The `<source_id>_hour()` methods MUST generate properly formatted log
strings matching the generator's format (KV, JSON, syslog, etc.).
Use the EVENT_DESCRIPTIONS from research to build realistic event content.
Every event string MUST include `demo_id=<scenario_id>` (for KV) or
`"demo_id": "<scenario_id>"` (for JSON).

### E.3 Syntax check

```bash
python3 -c "import ast; ast.parse(open('fake_data/scenarios/<scenario_id>.py').read()); print('Syntax OK')"
```

If this fails, fix the file and re-check.

### E.4 Update existing generators

For each matched source in the workspace, check if its generator file
still has the commented scenario stub:

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

---

## Phase F -- Verification

### F.1 Import test

```bash
cd <workspace_root>
python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data.scenarios.<scenario_id> import <ScenarioId>Scenario, SCENARIO_META
s = <ScenarioId>Scenario()
print(f'Config: {s.config}')
print(f'Phase on day {SCENARIO_META[\"start_day\"]}: {s.get_phase(SCENARIO_META[\"start_day\"])}')
for src in SCENARIO_META['sources']:
    method = getattr(s, f'{src}_hour', None)
    if method:
        evts = method(SCENARIO_META['start_day'], 10)
        print(f'{src}: {len(evts)} events')
        if evts:
            print(f'  sample: {evts[0][:100]}')
"
```

If the import test fails (e.g., world.py has no INFRASTRUCTURE and the
resolver crashes), fix _base.py or the scenario file and re-test.

---

## Phase G -- Handoff

Print:

```
Scenario created: fake_data/scenarios/<scenario_id>.py

Next steps:
  1. Review and tune the scenario:
     open fake_data/scenarios/<scenario_id>.py

  2. Test it standalone:
     python3 -c "from fake_data.scenarios.<scenario_id> import <Class>Scenario; s = <Class>Scenario(); print(s.config)"

  3. Generate logs with this scenario:
     python3 fake_data/main_generate.py --days=7 --scenarios=<scenario_id>

  4. Generate with all scenarios:
     python3 fake_data/main_generate.py --days=31 --scenarios=all

  5. Check for demo_id correlation in Splunk:
     index=* demo_id=<scenario_id> | stats count by sourcetype
```
```

- [ ] 4.3 Commit

```bash
git add .claude/skills/fd-add-scenario/SKILL.md
git commit -m "Add fd-add-scenario skill definition

Phases A-G: pre-flight, research via sonnet subagent, source matching,
review gate, code generation with runtime bootstrap, verification, and
handoff. Generates scenario files with SCENARIO_META, config dataclass,
and generator-specific _hour() methods."
```

---

## Task 5: Update CLAUDE.md + CHANGEHISTORY.md

### Files
- `CLAUDE.md` (MODIFY)
- `CHANGEHISTORY.md` (MODIFY)

### Steps

- [ ] 5.1 Update CLAUDE.md directory layout

Replace:
```
│       ├── fd-add-scenario/     # future (X5)
```
With:
```
│       ├── fd-add-scenario/     # ✅ X3 — scenario creation with research
│       │   └── SKILL.md
```

Also add to the templates section:
```
│   └── scenarios/
│       ├── __init__.py          # ✅ empty package marker
│       └── _base.py             # ✅ BaseScenario class + auto-resolver
```

- [ ] 5.2 Update CHANGEHISTORY.md

Add as the newest entry:

```markdown
## 2026-04-12 ~HH:MM UTC -- fd-add-scenario: scenario system

Files: `.claude/skills/fd-add-scenario/SKILL.md`, `templates/scenarios/_base.py`,
       `templates/scenarios/__init__.py`, `templates/runtime/config.py`,
       `templates/generators/_template_generator.py`

Adds the scenario system to FAKE_DATA. BaseScenario with auto-resolver handles
both enriched and basic world.py. discover_scenarios() replaces the expand_scenarios
placeholder. Template generator updated with active scenario injection hook.
fd-add-scenario skill provides research-based scenario creation (subagent) with
phases A-G: pre-flight, research, source matching, review gate, code generation
with runtime bootstrap, verification, and handoff.
```

- [ ] 5.3 Commit

```bash
git add CLAUDE.md CHANGEHISTORY.md
git commit -m "Update project docs for fd-add-scenario

Mark fd-add-scenario as complete in directory layout, add scenarios
templates to tree, add change history entry."
```

---

## Task 6: Canary test

### Steps

- [ ] 6.1 Verify template files parse

```bash
cd /path/to/fake-data
python3 -c "import ast; ast.parse(open('templates/scenarios/_base.py').read()); print('_base.py OK')"
python3 -c "import ast; ast.parse(open('templates/runtime/config.py').read()); print('config.py OK')"
python3 -c "import ast; ast.parse(open('templates/generators/_template_generator.py').read()); print('template OK')"
```

- [ ] 6.2 Test BaseScenario in canary workspace

```bash
cd /path/to/fake-data/tmp

# Copy scenario templates to canary workspace
mkdir -p fake_data/scenarios
cp ../templates/scenarios/__init__.py fake_data/scenarios/
cp ../templates/scenarios/_base.py fake_data/scenarios/

# Replace config.py with updated version
cp ../templates/runtime/config.py fake_data/config.py

# Test discover_scenarios with no scenarios present
python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data.config import expand_scenarios, discover_scenarios
print('discover (empty):', discover_scenarios())
print('expand none:', expand_scenarios('none'))
print('expand all:', expand_scenarios('all'))
print('expand missing:', expand_scenarios('nonexistent'))
"
```

Expected output:
```
discover (empty): {}
expand none: []
expand all: []
  Warning: scenario 'nonexistent' not found, skipping
expand missing: []
```

- [ ] 6.3 Test BaseScenario auto-resolver against basic world.py

The canary workspace has a basic world.py (no INFRASTRUCTURE, no role field
on users). The resolver must not crash.

```bash
cd /path/to/fake-data/tmp
python3 -c "
import sys; sys.path.insert(0, '.')
from dataclasses import dataclass
from fake_data.scenarios._base import BaseScenario

SCENARIO_META = {
    'scenario_id': 'test_canary',
    'category': 'attack',
    'sources': [],
    'demo_id': 'test_canary',
    'description': 'Canary test',
    'start_day': 2,
    'end_day': 4,
    'phases': [
        {'name': 'recon', 'start_day': 2, 'end_day': 2, 'description': 'Scanning'},
        {'name': 'exploit', 'start_day': 3, 'end_day': 4, 'description': 'Attack'},
    ],
}

@dataclass
class TestConfig:
    demo_id: str = 'test_canary'
    target_user: str = 'auto'
    attacker_ip: str = 'auto'
    start_day: int = 2
    end_day: int = 4

class TestScenario(BaseScenario):
    def meta(self): return SCENARIO_META
    def default_config(self): return TestConfig()

s = TestScenario()
print(f'target_user: {s.config.target_user}')
print(f'attacker_ip: {s.config.attacker_ip}')
print(f'phase day 2: {s.get_phase(2)}')
print(f'phase day 3: {s.get_phase(3)}')
print(f'active day 1: {s.is_active(1)}')
print(f'active day 3: {s.is_active(3)}')
assert s.config.target_user != 'auto', 'target_user not resolved'
assert s.config.attacker_ip != 'auto', 'attacker_ip not resolved'
assert s.get_phase(2) == 'recon'
assert s.get_phase(3) == 'exploit'
assert not s.is_active(1)
assert s.is_active(3)
print('All assertions passed')
"
```

- [ ] 6.4 Test generator integration with existing canary generator

If the canary workspace has a generator (e.g., `generate_world.py`), update
its scenario stub and verify the full pipeline still runs:

```bash
cd /path/to/fake-data/tmp
python3 fake_data/main_generate.py --days=1 --scenarios=none --quiet
echo "Exit code: $?"
```

Expected: exit 0, no errors.

- [ ] 6.5 Clean up canary test artifacts

```bash
rm -rf /path/to/fake-data/tmp/fake_data/scenarios
```

---

## Summary

| Task | Files | Commits |
|------|-------|---------|
| 1 | `templates/scenarios/_base.py`, `templates/scenarios/__init__.py` | 1 |
| 2 | `templates/runtime/config.py` | 1 |
| 3 | `templates/generators/_template_generator.py` | 1 |
| 4 | `.claude/skills/fd-add-scenario/SKILL.md` | 1 |
| 5 | `CLAUDE.md`, `CHANGEHISTORY.md` | 1 |
| 6 | (canary test, no commit) | 0 |
| **Total** | **7 files** | **5 commits** |

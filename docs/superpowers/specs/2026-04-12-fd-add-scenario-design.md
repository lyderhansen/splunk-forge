# fd-add-scenario Design Spec

## Goal

Add a skill that lets users create realistic, multi-phase scenarios (attacks, ops incidents, network issues) for their FAKE_DATA workspace. Scenarios inject correlated events across multiple generators, tagged with `demo_id` for Splunk correlation. The skill uses research-based generation (subagent) combined with world.py auto-resolution so scenarios "just work" without hardcoded names or IPs.

## Architecture

The scenario system has three layers:

1. **Skill layer** (`fd-add-scenario`) — wizard + research + code generation
2. **Scenario modules** (`fake_data/scenarios/*.py`) — scenario classes with metadata, config, and generator-specific methods
3. **Runtime integration** — `expand_scenarios()` discovery, generator event injection, `demo_id` tagging

All code is stdlib-only Python 3.9+, following the same patterns as generators (filesystem discovery via metadata dict, sys.path bootstrap, template-based scaffolding).

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Approach | Hybrid (C) | Research generates working code; user tunes afterward |
| World state binding | Explicit config with auto-defaults (B) | `"auto"` sentinel → resolver picks from world.py. User can override. |
| Generator coupling | Generator-specific methods (A) | Proven in TA-FAKE-TSHRT. Scenario owns event formatting per source. |
| Research | Subagent-based + user description | User describes what they want; research fills in realistic phases/IOCs |
| Generator selection | Research suggests, user confirms or auto (C) | Research knows which sources are relevant; auto mode skips confirmation |
| File structure | Flat (B) | `fake_data/scenarios/<scenario_id>.py`. Category in metadata, not directory. |
| Registry | SCENARIO_META per file (A) | Same pattern as SOURCE_META. Filesystem discovery, no central registry. |
| Phases | Defined in SCENARIO_META (A) | Explicit phase list with start/end days. `get_phase(day)` helper in base class. |

---

## 1. File Structure

```
fake_data/scenarios/
├── __init__.py              # empty package marker
├── _base.py                 # BaseScenario class + auto-resolver
├── brute_force.py           # example: attack scenario
├── disk_filling.py          # example: ops scenario
└── firewall_misconfig.py    # example: network scenario
```

Flat directory. No subdirectories for categories — category lives in `SCENARIO_META["category"]`.

## 2. SCENARIO_META

Every scenario file exports a `SCENARIO_META` dict at module level:

```python
SCENARIO_META = {
    "scenario_id": "brute_force",
    "category": "attack",               # attack | ops | network
    "sources": ["fortigate", "linux"],   # generators this scenario produces events for
    "demo_id": "brute_force",            # tag for Splunk correlation
    "description": "Brute force login attack against VPN/RDP endpoint",
    "start_day": 3,
    "end_day": 5,
    "phases": [
        {
            "name": "scanning",
            "start_day": 3,
            "end_day": 3,
            "description": "Port scanning and service enumeration",
        },
        {
            "name": "brute_force",
            "start_day": 4,
            "end_day": 4,
            "description": "Credential stuffing attempts against target",
        },
        {
            "name": "success",
            "start_day": 5,
            "end_day": 5,
            "description": "Successful login and initial lateral movement",
        },
    ],
}
```

Discovery: `expand_scenarios()` scans `fake_data/scenarios/` using the same `pkgutil.iter_modules` pattern as `discover_generators()` in main_generate.py. Modules with a `SCENARIO_META` dict are recognized as scenarios.

## 3. Config Dataclass with Auto-Defaults

Each scenario defines a config dataclass. Fields set to `"auto"` are resolved from world.py at instantiation:

```python
@dataclass
class BruteForceConfig:
    demo_id: str = "brute_force"
    target_user: str = "auto"       # → resolver picks an admin from USERS
    target_host: str = "auto"       # → resolver picks a firewall from INFRASTRUCTURE
    target_host_ip: str = "auto"    # → resolved from INFRASTRUCTURE after host is picked
    attacker_ip: str = "auto"       # → resolver picks from EXTERNAL_IP_POOL
    start_day: int = 3
    end_day: int = 5
```

Users can override any field:
```python
# In scenario file, change defaults:
target_user: str = "jane.doe"       # specific user instead of auto
```

## 4. BaseScenario Class (`_base.py`)

```python
class BaseScenario:
    """Base class for all scenarios."""

    def __init__(self, config=None):
        self.config = config or self.default_config()
        self._resolve_auto_values()

    def default_config(self):
        raise NotImplementedError

    def meta(self) -> dict:
        raise NotImplementedError

    def _resolve_auto_values(self):
        """Replace 'auto' sentinels with real values from world.py."""
        from fake_data.world import USERS, INFRASTRUCTURE, EXTERNAL_IP_POOL

        seed = hash(self.meta()["scenario_id"])

        for field_name in list(vars(self.config)):
            value = getattr(self.config, field_name)
            if value != "auto":
                continue
            if "user" in field_name:
                role = "admin" if self.meta()["category"] == "attack" else None
                user = self._pick_user(USERS, role, seed, field_name)
                setattr(self.config, field_name, user["username"])
            elif "host" in field_name and "ip" not in field_name:
                host = self._pick_infra(INFRASTRUCTURE, seed, field_name)
                setattr(self.config, field_name, host["hostname"])
            elif "host_ip" in field_name:
                # Resolve after host is set
                host = self._find_infra_by_hostname(
                    INFRASTRUCTURE, getattr(self.config, field_name.replace("_ip", ""))
                )
                if host:
                    setattr(self.config, field_name, host["ip"])
            elif "attacker" in field_name or "external" in field_name:
                setattr(self.config, field_name, self._pick_external_ip(EXTERNAL_IP_POOL, seed))

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

    # _pick_user, _pick_infra, _pick_external_ip: deterministic
    # selection using seed + field_name hash for stability
```

Resolver rules:
- `*_user` fields → pick from USERS filtered by role (admin for attack scenarios, any for ops)
- `*_host` fields (without `_ip`) → pick from INFRASTRUCTURE based on category (firewall for network, server for ops)
- `*_host_ip` fields → resolved from INFRASTRUCTURE after the corresponding host is picked
- `*attacker*` or `*external*` IP fields → pick from EXTERNAL_IP_POOL
- Deterministic: seed from `scenario_id` + field name ensures same scenario always selects same entities

## 5. Scenario Class Pattern

Each scenario class inherits BaseScenario and implements generator-specific methods:

```python
class BruteForceScenario(BaseScenario):

    def meta(self) -> dict:
        return SCENARIO_META

    def default_config(self):
        return BruteForceConfig()

    # --- Generator-specific methods ---

    def fortigate_hour(self, day: int, hour: int) -> List[str]:
        """Return FortiGate-formatted log lines for this hour."""
        if not self.is_active(day):
            return []
        phase = self.get_phase(day)
        events = []
        if phase == "scanning":
            events.extend(self._scanning_events(hour))
        elif phase == "brute_force":
            events.extend(self._brute_events(hour))
        elif phase == "success":
            events.extend(self._success_events(hour))
        return events

    def linux_hour(self, day: int, hour: int) -> List[str]:
        """Return Linux auth log lines for this hour."""
        ...

    # --- Internal event builders ---

    def _scanning_events(self, hour: int) -> List[str]:
        """Generate port scan events in FortiGate KV format."""
        ...
```

The `<source_id>_hour(day, hour)` convention:
- Method name matches the generator's `SOURCE_META["source_id"]`
- Returns a list of pre-formatted log line strings
- Each line includes `demo_id=<scenario_id>` for correlation
- Generator calls the method via `getattr(scenario, f"{source_id}_hour", None)`

## 6. Runtime Integration

### 6.1 expand_scenarios() — replaces placeholder in config.py

```python
def expand_scenarios(scenarios: str) -> List:
    """Discover and instantiate active scenarios."""
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

### 6.2 discover_scenarios() — new function in config.py

Same pattern as `discover_generators()` in main_generate.py:

```python
def discover_scenarios():
    """Scan fake_data/scenarios/ for modules with SCENARIO_META."""
    scenarios_dir = Path(__file__).parent / "scenarios"
    if not scenarios_dir.is_dir():
        return {}

    discovered = {}
    for finder, name, _ in pkgutil.iter_modules([str(scenarios_dir)]):
        if name.startswith("_"):
            continue
        module = importlib.import_module(f"fake_data.scenarios.{name}")
        meta = getattr(module, "SCENARIO_META", None)
        if meta is None:
            continue
        # Find the scenario class (convention: class ending in "Scenario")
        cls = None
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if isinstance(obj, type) and attr_name.endswith("Scenario") and attr_name != "BaseScenario":
                cls = obj
                break
        if cls:
            discovered[meta["scenario_id"]] = {
                "meta": meta,
                "instance": cls(),
            }
    return discovered
```

### 6.3 Generator integration — 3 lines per generator

In every generator's day/hour loop, the commented stub is replaced:

```python
# Inject scenario events
for scenario in active_scenarios:
    method = getattr(scenario, f"{SOURCE_META['source_id']}_hour", None)
    if method:
        events.extend(method(day, hour))
```

### 6.4 Template generator update

`templates/generators/_template_generator.py` is updated with the active scenario code (not commented), so new generators from fd-add-generator automatically support scenarios.

### 6.5 main_generate.py

No changes needed. The `--scenarios` flag already passes the string to generators, and `expand_scenarios()` already sits in the call path. Only the implementation of `expand_scenarios()` changes (from returning `[]` to actual discovery).

## 7. fd-add-scenario Skill Flow

### Phase A — Pre-flight

1. **Find workspace root** — walk up looking for `fake_data/manifest.py` (same as fd-add-generator)
2. **Parse input** — `/fd-add-scenario <scenario_id_or_description>`. If no argument, prompt: "Describe the scenario you want to create, or give a type (brute_force, data_exfil, disk_filling, cert_expiry, etc.)"
3. **Normalize scenario_id** — lowercase, underscores, reject if starts with digit (same rules as source_id)
4. **Check collision** — if `fake_data/scenarios/<scenario_id>.py` exists, ask overwrite/abort
5. **Scan generators** — list all `fake_data/generators/generate_*.py` files, extract SOURCE_META from each to build available sources list
6. **Check _base.py** — if `fake_data/scenarios/_base.py` doesn't exist, it will be created in Phase E (first scenario bootstraps the runtime)

### Phase B — Research

1. **User input** — if the user provided a description (not just a type keyword), use it. Otherwise ask: "Beskriv hva som skal skje i dette scenarioet, eller trykk enter for å la research finne ut av det."
2. **Dispatch sonnet subagent** with:
   - Scenario type/description from user
   - Available generators in workspace (from Phase A.5)
   - World state summary: org name, locations, user count, infrastructure list
   - Instruction: research realistic phases, timelines, IOCs, which log sources are typically involved
3. **Subagent returns** structured result:
   - `category`: attack | ops | network
   - `phases`: list of `{name, start_day, end_day, description}`
   - `suggested_sources`: which generators should produce events
   - `config_fields`: scenario-specific config beyond defaults (e.g., `target_service: str = "RDP"`)
   - `event_descriptions`: per source, per phase — what events should look like
   - `confidence`: overall research confidence

### Phase C — Source matching

1. Match `suggested_sources` against available generators from Phase A.5
2. Categorize: `matched` (generator exists), `missing` (generator not in workspace)
3. If `--auto` flag or user previously chose auto: skip to Phase D with matched sources
4. Otherwise show:
   ```
   Sources for this scenario:
     [x] fortigate  (exists)
     [x] linux      (exists)
     [ ] entra_id   (missing — run /fd-add-generator entra_id to add)

   Proceed with available sources? [yes/auto/cancel]
   ```
5. `auto` → remember preference for remaining questions in this session

### Phase D — Review gate

Display complete scenario overview:

```
Scenario to be created: fake_data/scenarios/brute_force.py

  Scenario ID:    brute_force
  Category:       attack
  Demo ID:        brute_force
  Description:    Brute force login attack against VPN/RDP endpoint

  Timeline (days 3-5 of generation window):
    Day 3:  scanning     — Port scanning and service enumeration
    Day 4:  brute_force  — Credential stuffing attempts
    Day 5:  success      — Successful login and lateral movement

  Config:
    target_user:   auto → (will resolve to an admin from USERS)
    target_host:   auto → (will resolve to a firewall from INFRASTRUCTURE)
    attacker_ip:   auto → (will resolve from EXTERNAL_IP_POOL)

  Affected generators:
    fortigate  — deny/drop events during scanning, auth failures during brute force
    linux      — failed SSH/auth entries, successful login on day 5

Create this scenario? [yes/edit/cancel]
```

### Phase E — Code generation

1. **Bootstrap runtime** (first scenario only):
   - Write `fake_data/scenarios/__init__.py` (empty)
   - Write `fake_data/scenarios/_base.py` (BaseScenario class + auto-resolver)
   - Update `expand_scenarios()` in `fake_data/config.py` (replace placeholder with real discovery)
   - Update template generator (`templates/generators/_template_generator.py`) — uncomment scenario hook
2. **Generate scenario file** — complete Python file with:
   - SCENARIO_META dict
   - Config dataclass with auto-defaults
   - Scenario class inheriting BaseScenario
   - Generator-specific `<source_id>_hour(day, hour)` methods with realistic event logic from research
   - `demo_id` tagging on all events
   - Standalone `if __name__ == "__main__"` block for testing
3. **Write** to `fake_data/scenarios/<scenario_id>.py`
4. **Syntax check** — `python3 -c "import ast; ast.parse(...)"`
5. **Update existing generators** — for each matched source, replace the commented scenario stub with the active 3-line integration code (if not already updated)

### Phase F — Handoff

```
Scenario created: fake_data/scenarios/brute_force.py

Next steps:
  1. Review and tune the scenario:
     open fake_data/scenarios/brute_force.py

  2. Test it standalone:
     python3 -c "from fake_data.scenarios.brute_force import BruteForceScenario; s = BruteForceScenario(); print(s.config)"

  3. Generate logs with this scenario:
     python3 fake_data/main_generate.py --days=7 --scenarios=brute_force

  4. Generate with all scenarios:
     python3 fake_data/main_generate.py --days=31 --scenarios=all

  5. Check for demo_id correlation in Splunk:
     index=* demo_id=brute_force | stats count by sourcetype
```

## 8. Scope Boundaries

**In scope:**
- fd-add-scenario SKILL.md
- `_base.py` (BaseScenario + auto-resolver)
- `expand_scenarios()` real implementation (replaces placeholder)
- `discover_scenarios()` function
- Template generator update (uncomment scenario hook)
- Generator update pattern (3-line integration)

**Out of scope:**
- Bundled preset scenarios (future — presets/ directory is reserved)
- Scenario-to-scenario dependencies (e.g., "run exfil only if brute_force also active")
- Multi-scenario conflict detection (warn if two scenarios target same host/day — nice-to-have, not v1)
- Scenario visualization / timeline view
- fd-generate skill (separate skill, next in roadmap)

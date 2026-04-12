# Design: Plan X1 — Framework core templates + init skill + add-generator

**Date:** 2026-04-12
**Status:** Draft — awaiting user review before implementation plan
**Author:** Brainstormed with Claude Code (superpowers:brainstorming)
**Supersedes:** Portions of `2026-04-11-handoff-from-planning-session.md` (scope expanded from pure X1 to X1+X3)

---

## Context

FAKE_DATA is a standalone Claude Code plugin (disk name: `fake-data`, brand name: FAKE_DATA) that helps users generate synthetic log data for Splunk. It is inspired by The FAKE T-Shirt Company project but is designed to be usable by anyone for any fictional organization.

This spec covers the first deliverable: `init` + `add-generator` + a working `main_generate.py` orchestrator. After this spec is implemented, a user can go from an empty repo to generated log files on disk in one session.

The handoff document (`2026-04-11-handoff-from-planning-session.md`) originally scoped X1 as init-only and X3 as add-generator. During brainstorming for this spec, the scope was expanded because an empty workspace without generator-creation capability does not deliver user-visible value. This spec merges X1 and X3 into a single deliverable and includes a light version of X2's format detector (Phase C only, no research) inside `add-generator`.

## North Star — what the plugin will be when complete

This section is not binding for this spec. It captures the full vision so that X1 design choices can be validated against the end state.

A user who installs the `fake-data` Claude Code plugin should eventually be able to do the following in their own empty repo, from start to Splunk:

1. **`/fake-data:init`** — interactive creation of a fictional organization workspace (world, users, locations, IP plan)
2. **`/fake-data:discover-logformat <source>`** — A-to-Z discovery: give a source name, get back format analysis, sample events, CIM mapping
3. **`/fake-data:add-generator <source>`** — scaffold a Python generator that reads world.py and produces realistic logs
4. **`/fake-data:add-scenario <scenario>`** — scaffold attack/incident scenarios across multiple sources
5. **`/fake-data:generate-logs`** — orchestrator that runs all generators and produces log files
6. **`/fake-data:build-splunk-app`** — produce a complete Splunk app/TA with props.conf, transforms.conf, inputs.conf, default dashboards, app.conf, packaged as SPL
7. **`/fake-data:package`** — bundle everything (generators, log files, Splunk app) as a deliverable
8. The user's only runtime dependency is standard Python 3.9+ and Splunk. No Claude Code in the hot loop.

Seven subsystems (handoff doc listed six; Splunk app/TA generation is new):

| # | Subsystem | Status |
|---|---|---|
| 1 | Framework core (generator runtime, world-state, source registration) | This spec |
| 2 | Onboarding wizard / init skill | This spec |
| 3 | Data source catalog (source selection UX, metadata) | Emergent from other work |
| 4 | Data format discovery (discover-logformat) | Validated in TA-FAKE-TSHRT, port later |
| 5 | Behavioral layer (world state + diurnal/causal/anomaly + formatter) | Future |
| 6 | Plugin packaging (distribution as Claude Code plugin) | Partial (manifest exists) |
| 7 | Splunk app/TA generation | Future |

**Core design principle:** each skill is a tool for creating the user's own content, not a runtime dependency. After each skill invocation, the user owns the result as plain Python/XML/conf files in their own repo. Claude is design-time assistance only; runtime is 100% standalone Python.

## Scope of this spec

### Includes

- `init` skill — interactive two-phase wizard, optional research phase for real companies, geo-IP defaults from locations, deterministic USERS generation, review gate before disk write
- `add-generator` skill — wizard mode + sample mode, shared format detector (JSON/KV/CSV/CEF/syslog/XML), field frequency analysis, category/volume guessing, review gate, template substitution
- Working `main_generate.py` orchestrator with filesystem-based generator discovery via `SOURCE_META`, topological sorting via `depends_on`, progress display
- Runtime templates: `world.py`, `config.py`, `time_utils.py`, `_template_generator.py`
- Workspace marker: `fake_data/manifest.py`
- Canary test that verifies the full pipeline: init -> add-generator -> python3 main_generate.py -> log files in output/

### Excludes (future plans)

- `discover-logformat` as a separate skill (but its Phase C format-detection logic is reused inside add-generator)
- Research phase (WebSearch/WebFetch) for discover-logformat
- Confidence gates / interactive Q&A based on confidence scores
- `add-scenario` skill
- `generate-logs` as a separate skill (user calls `python3 main_generate.py` directly)
- Splunk app/TA generation (props.conf, transforms.conf, inputs.conf)
- TUI for main_generate.py (curses-based, deferred to a short follow-up plan)
- Preset library for known source formats (directory reserved but empty)

## Locked architectural decisions

These decisions were made during the planning session documented in `2026-04-11-handoff-from-planning-session.md`. They are not reopened here unless explicitly noted.

1. **Plugin format: Claude Code canonical.** `.claude-plugin/plugin.json` manifest, loaded via Claude Code's plugin system. Skills are auto-namespaced as `fake-data:<skill-name>`.
2. **Name: `fake-data` on disk, "FAKE_DATA" as brand.** Matches Claude Code plugin conventions (lowercase, hyphenated).
3. **Runtime philosophy: template-only in v1.** `init` copies Python files into the user's repo. No pip package, no `from fake_data import ...` at runtime. Users own their scaffolded code outright.
4. **World-state schema: minimalistic, extensible.** Organization name, locations, users, network config. Custom fields allowed but not required. Rich features (OT zones, VPN pools, meeting schedules) become optional sections later.
5. **Repo location: standalone sibling.** Lives at `../../GIT-FAKE-DATA/fake-data/` — sibling to TA-FAKE-TSHRT. TA-FAKE-TSHRT is the first intended user, not the parent.

### Decisions made during this brainstorming session

6. **Config format: Python modules, not YAML/JSON.** `world.py`, `config.py` are plain Python with module-level constants. No external parser needed. Stdlib-only constraint (Python 3.9+, no PyYAML, no third-party packages).
7. **Runtime API: module-level globals mirroring TA-FAKE-TSHRT's `shared/company.py`.** Generators import `from fake_data.world import USERS, LOCATIONS, NETWORK_CONFIG`. Deliberately compatible API makes X6 migration (TA-FAKE-TSHRT port) trivial — one import-line change per generator.
8. **Workspace layout: `fake_data/` as visible subdir and Python package.** Not `.fake-data/` (leading dot breaks Python imports). `fake_data` matches the plugin ID with underscore instead of hyphen (Python naming requirement).
9. **Python imports: sys.path bootstrap in each generator file.** Each generator has `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` at the top. Matches TA-FAKE-TSHRT pattern. Both standalone execution and orchestrator execution work.
10. **Source registration: filesystem discovery via `SOURCE_META`.** `main_generate.py` scans `fake_data/generators/generate_*.py` at startup, imports each module dynamically, reads `SOURCE_META` dict. No separate registry file. `add-generator` just creates the file — no need to edit a central registry.
11. **Workspace marker: `fake_data/manifest.py` with versioned metadata.** Contains `FAKE_DATA_WORKSPACE_VERSION`, `INITIALIZED_AT`, `PLUGIN_VERSION_AT_INIT`. Skills check for this file to confirm they are inside a FAKE_DATA workspace. `init` refuses to run if `manifest.py` already exists.
12. **SERVERS/HOSTS are emergent, not init-produced.** `world.py` in X1 contains only ORG_NAME, TENANT, LOCATIONS, NETWORK_CONFIG, USERS. Generators derive their own hosts on-the-fly from a deterministic seed. A shared `derive_hosts()` helper comes in a later plan.
13. **External IP pools are geo-aware.** `init` auto-populates `EXTERNAL_IP_POOL` and `EXTERNAL_IP_POOL_BY_COUNTRY` based on the country codes in LOCATIONS, using a bundled `data/country_ip_ranges.py` lookup. Default fallback is RFC 5737 TEST-NET ranges. Users may add any public IP range they want — the data is FAKE, not a security risk.

## Python version and dependencies

**Target: Python 3.9+** (verified: user's system runs Python 3.9.6 via `/usr/bin/python3` on macOS).

Consequences for code style:
- No `dict | None` (PEP 604, requires 3.10) — use `Optional[Dict]` from `typing`
- No `list[dict]` lowercase in annotations — use `List[Dict]` from `typing`
- No `match`/`case` statements (3.10+)
- No `tomllib` (3.11+) — not needed since we use Python modules for config
- `dataclasses`, `pathlib`, `json`, `argparse`, `importlib`, `pkgutil` — all 3.9-compatible

**Runtime dependencies: zero.** Only Python stdlib. No pip packages. `main_generate.py` checks `sys.version_info >= (3, 9)` at startup and exits with a clear message if not met.

## Plugin repo layout

This is the layout of the `fake-data/` plugin repository itself (what the developer maintains). It is NOT what the user sees after running `init`.

```
fake-data/                          # plugin repo root
+-- .claude-plugin/
|   +-- plugin.json                 # Claude Code plugin manifest
|
+-- .claude/                        # Claude Code skill definitions
|   +-- skills/
|       +-- init/
|       |   +-- SKILL.md
|       +-- add-generator/
|       |   +-- SKILL.md
|       +-- discover-logformat/     # future (X2)
|       +-- add-scenario/           # future (X5)
|       +-- generate-logs/          # future (X5)
|
+-- templates/                      # files that init COPIES to user's repo
|   +-- runtime/
|   |   +-- world.py.tmpl           # template with {{ }} placeholders
|   |   +-- config.py               # copied as-is (generic)
|   |   +-- time_utils.py           # copied as-is (generic)
|   |   +-- main_generate.py        # copied as-is (generic)
|   |   +-- manifest.py.tmpl        # template with {{ }} placeholders
|   +-- generators/
|   |   +-- _template_generator.py  # copied as-is, used by add-generator
|   +-- workspace/
|       +-- README_workspace.md.tmpl
|
+-- data/                           # data that skills READ at invocation time (not copied)
|   +-- names_sample.py             # ~200 first names + ~200 last names
|   +-- country_ip_ranges.py        # ~20 countries -> public CIDR ranges
|
+-- presets/                        # empty in X1, populated in X2+
|   +-- README.md
|   +-- .gitkeep
|
+-- docs/
|   +-- superpowers/
|       +-- specs/                  # design documents (including this file)
|       +-- plans/                  # implementation plans
|
+-- README.md
+-- CLAUDE.md
+-- CHANGEHISTORY.md
```

### Key distinctions

| Directory | Role | Copied to user's repo? |
|---|---|---|
| `.claude/skills/` | Skill definitions (SKILL.md files) | No — loaded by Claude Code |
| `templates/` | Files that `init` copies to user's repo | Yes, at init time |
| `data/` | Lookup data used by skills at invocation time | No — read by init skill |
| `presets/` | Pre-built source definitions (empty in X1) | No — read by discover/add-generator |

## User workspace layout (after init)

This is what the user sees in their repo after running `/fake-data:init`:

```
<user's repo>/
+-- fake_data/
    +-- __init__.py              # empty, makes fake_data a Python package
    +-- manifest.py              # workspace marker + version metadata
    +-- world.py                 # ORG_NAME, TENANT, LOCATIONS, NETWORK_CONFIG, USERS
    +-- config.py                # DEFAULT_START_DATE, volume parameters, hour activity curves
    +-- time_utils.py            # ts_iso, ts_syslog, calc_natural_events, date_add
    +-- main_generate.py         # orchestrator, runnable: python3 fake_data/main_generate.py
    +-- README.md                # brief explanation of what init created + next steps
    +-- generators/
    |   +-- __init__.py          # empty
    |   +-- _template_generator.py   # copy-template, used by add-generator later
    +-- scenarios/
    |   +-- __init__.py          # empty
    +-- output/                  # empty, generators write here
        +-- .gitkeep
```

Nothing is created outside `fake_data/`. Init does not modify the user's repo root, `.gitignore`, or any existing files.

## Init skill design

### Invocation

```
/fake-data:init
```

No arguments. All configuration is gathered interactively during the wizard.

### Phase A — Pre-flight and collision check

1. Resolve current working directory. Verify write access.
2. Check if `<cwd>/fake_data/manifest.py` exists. If yes, stop: "A FAKE_DATA workspace already exists at `./fake_data/`. Delete it or run init from a different directory."
3. Check if `<cwd>/fake_data/` exists but without `manifest.py`. If yes, stop: "A `fake_data/` directory exists here but has no manifest.py. This looks like a partially-initialized or unrelated directory. Please remove or rename it before running init."
4. If no collisions, proceed to Phase B.

### Phase B — Interactive question gathering

Ask in order, one at a time:

1. **`ORG_NAME`** — free text. Default: `"Example Corp"`.
2. **"Is this a real company?"** — yes/no. Default: no.
   - If yes, run Phase B.1 (research) before continuing.
3. **`INDUSTRY`** — pick list: `retail`, `manufacturing`, `saas`, `financial`, `healthcare`, `generic`. Default from research if available, otherwise `generic`.
4. **Total employee count** — integer. Default from research or `100`.
5. **Number of locations** — integer. Default from research or `2`.
6. **For each location**: name, city, country (two-letter ISO code), timezone, percentage of employees. Research can prefill these.
7. **Primary domain** — free text. Default from research or `ORG_NAME_LOWER + ".com"`.
8. **Internal IP plan** — pick: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Default `10.0.0.0/8`.

### Phase B.1 — Research (only if "real company" = yes)

Runs WebSearch + WebFetch to gather publicly available company context. Time budget: max 60 seconds.

1. Search: `"<ORG_NAME>" company headquarters employees`.
2. Fetch top 2-3 results (prefer company's own about page, Wikipedia).
3. Extract with focused prompts: industry, headquarters (city, country), other known offices, approximate employee count, official domain.
4. Present findings with explicit attribution:
   > "Based on public information, I found:
   >   - Industry: retail (source: company-website.com/about)
   >   - HQ: London, GB
   >   - Approx. employees: 1200
   >   - Domain: example-company.com
   > These are prefilled as defaults. You can override any of them."
5. Continue to remaining Phase B questions with prefilled defaults.

**Privacy guardrail** (written explicitly into SKILL.md): research fetches only publicly available company context. It does NOT look up LinkedIn profiles, employee names, or actual IP addresses from the company's infrastructure. `USERS` are always generated from the bundled name list, never from research. The distinction is "fictional logs for a fictional IT environment that resembles real company X" versus "logs that impersonate real company X". Only the former is acceptable.

### Phase C — Generate content in memory

Before writing anything to disk, build up all file contents in memory:

1. Load `data/names_sample.py` (~200 first names + ~200 last names).
2. Seed deterministically from `ORG_NAME` (hash).
3. Generate `USERS` list: for each employee, pick first + last name, create username (`first.last`), email, assign location by distribution percentage, assign department randomly from `["engineering", "sales", "marketing", "finance", "hr", "it", "operations"]`.
4. Load `data/country_ip_ranges.py`, look up country codes from locations, build `EXTERNAL_IP_POOL` + `EXTERNAL_IP_POOL_BY_COUNTRY`. Countries not found in the bundled list get TEST-NET fallback silently.
5. Build `NETWORK_CONFIG` per location based on chosen internal IP plan (e.g. HQ1 = `10.10.0.0/16`, OFF1 = `10.20.0.0/16`).
6. Generate `TENANT_ID` deterministically from `ORG_NAME` (UUID5 with a fixed namespace).
7. Fill out `world.py.tmpl`, `config.py`, `manifest.py.tmpl`, `README_workspace.md.tmpl` with generated values.
8. Prepare the full file list to be written.

### Phase D — Review gate

Display a summary in chat:

```
Summary of your new FAKE_DATA workspace:

  Organization:   Example Corp
  Industry:       retail
  Locations:      2  (HQ1: London GB [60 users], OFF1: Manchester GB [40 users])
  Users:          100 generated (deterministic from org name)
  Domain:         example-corp.com
  Internal IPs:   10.0.0.0/8  (HQ1: 10.10.0.0/16, OFF1: 10.20.0.0/16)
  External IPs:   GB ranges + RFC 5737 fallback

  Files to be written under ./fake_data/:
    manifest.py, world.py, config.py, time_utils.py, main_generate.py,
    README.md, generators/_template_generator.py,
    generators/__init__.py, scenarios/__init__.py, __init__.py,
    output/.gitkeep

Proceed with creating workspace? [yes/edit/cancel]
```

- `yes` -> Phase E (disk writes)
- `edit` -> back to Phase B questions to override individual fields, then Phase C/D again
- `cancel` -> exit without writing anything

### Phase E — Write all files

1. Create `fake_data/` and all subdirectories.
2. Write each file from the pre-generated list.
3. Set `INITIALIZED_AT` in `manifest.py` to current UTC ISO-8601.
4. No rollback logic in X1. If writing fails partway, report to user. `init` will refuse to run again due to `manifest.py` check, so user must delete `fake_data/` manually to retry.

### Phase F — Handoff

Print handoff message:

```
FAKE_DATA workspace created at ./fake_data/

Next steps:
  1. Inspect fake_data/world.py  -- your organization's fictional state
  2. Verify the runtime:  python3 fake_data/main_generate.py --help
  3. Add your first generator:  /fake-data:add-generator <source_id>
     Use --sample=<path> if you have a log file, or answer wizard questions.

Currently 0 sources are registered. Generators live in fake_data/generators/
and are auto-discovered by main_generate.py at runtime.
```

### world.py content shape

After init, `world.py` contains module-level constants matching the API of TA-FAKE-TSHRT's `shared/company.py`:

```python
"""Fictional organization state for Example Corp.

Generated by fake-data:init. You can edit by hand. Generators import
constants from this module to produce realistic, cross-source-coherent
log data. HOSTS/SERVERS are intentionally NOT defined here -- generators
derive the hosts they need from USERS + LOCATIONS using a deterministic seed.
"""
from typing import Optional, List, Dict

# === Organization identity ===
ORG_NAME = "Example Corp"
ORG_NAME_LOWER = "examplecorp"
TENANT = "example.com"
TENANT_ID = "a1b2c3d4-0000-0000-0000-000000000001"  # deterministic from ORG_NAME
INDUSTRY = "generic"

# === Locations ===
LOCATIONS = {
    "HQ1": {
        "name": "Headquarters",
        "city": "Oslo",
        "country": "NO",
        "timezone": "Europe/Oslo",
        "employee_count": 60,
        "type": "headquarters",
    },
    # ...
}

# === Network configuration per location ===
NETWORK_CONFIG = {
    "HQ1": {"internal_cidr": "10.10.0.0/16", "gateway": "10.10.0.1",
             "dns": ["10.10.0.53"]},
    # ...
}

# === External IP pools ===
EXTERNAL_IP_POOL = [
    "77.40.0.0/16",        # NO -- Telenor (auto from locations)
    "198.51.100.0/24",     # RFC 5737 fallback
    "203.0.113.0/24",
]
EXTERNAL_IP_POOL_BY_COUNTRY = {
    "NO": ["77.40.0.0/16", "193.213.112.0/20"],
}

# === Users ===
USERS = [
    {"username": "alice.anderson", "full_name": "Alice Anderson",
     "email": "alice.anderson@example.com", "location": "HQ1",
     "department": "engineering"},
    # ... N more
]

# === Helper functions ===
def get_user_by_username(username: str) -> Optional[Dict]:
    for u in USERS:
        if u["username"] == username:
            return u
    return None

def users_at_location(location_id: str) -> List[Dict]:
    return [u for u in USERS if u["location"] == location_id]
```

### manifest.py content

```python
"""FAKE_DATA workspace manifest. Do not delete -- skills use this file
to verify that the current directory is a FAKE_DATA workspace."""

FAKE_DATA_WORKSPACE_VERSION = 1
INITIALIZED_AT = "2026-04-12T12:00:00Z"       # set by init
PLUGIN_VERSION_AT_INIT = "0.0.1"              # from plugin.json
ORG_NAME_AT_INIT = "Example Corp"             # audit only; world.py is source of truth
```

## Add-generator skill design

### Invocation

```
/fake-data:add-generator <source_id> [--sample=<path>] [--category=<cat>] [--format=<fmt>]
```

- `source_id` required, normalized to snake_case (lowercase, non-alphanumeric runs replaced with underscore, strip leading/trailing underscores, reject if empty or starts with digit).
- `--sample=<path>` optional, triggers sample mode.
- `--category=<cat>` optional hint (otherwise asked or guessed).
- `--format=<fmt>` optional hint (otherwise asked or detected).

### Phase A — Pre-flight

1. `find_workspace_root()` — walk up from cwd looking for `fake_data/manifest.py`. If not found: "No FAKE_DATA workspace found. Run /fake-data:init first."
2. Check that `fake_data/generators/generate_<source_id>.py` does not exist. If it does: "Generator for '<source_id>' already exists. Delete it first or pick a different source_id."
3. Normalize `source_id`.
4. Decide mode: if `--sample` is given -> sample mode, otherwise -> wizard mode.

### Phase B.sample — Sample mode (if `--sample=<path>`)

Light version of `discover-logformat` Phase C. No research, no confidence gates.

**B.sample.1 — Read sample** (max 500 lines).

**B.sample.2 — Format detection.** Test each line against patterns in order. First pattern with >50% match rate wins:

| Order | Pattern | Format value |
|---|---|---|
| 1 | starts with `{`, ends with `}` | `json` |
| 2 | `^CEF:\d` | `cef` |
| 3 | `^<\d+>` | `syslog_rfc5424` |
| 4 | `^\w{3} \d+ \d+:\d+:\d+` | `syslog_bsd` |
| 5 | `\w+=\S+( \w+=\S+)+` | `kv` |
| 6 | first line looks like CSV headers or `^\d+,.*,.*` | `csv` |
| 7 | starts with `<` and contains `>` | `xml` |
| 8 | none | `unknown` |

If `unknown`, continue anyway with `raw_line` as the only field.

**B.sample.3 — Field extraction** per format:

- `json`: parse each line with `json.loads`, flatten nested objects with dot-path keys. Infer type per value: `string`, `int`, `float`, `bool`, `ipv4` (dotted-quad pattern), `ipv6` (colon-hex pattern), `iso_timestamp` (ISO 8601 pattern).
- `kv`: split on whitespace, then split each token on first `=`. Infer types same as JSON.
- `csv`: first line as header if all values look like identifiers, otherwise `col_1`, `col_2`, etc. Infer types from remaining rows.
- `cef`: parse 7-field CEF header + extension block as KV pairs.
- `syslog_*`: attempt KV on message body, otherwise just `raw_line`.
- `xml`: top-level tag names as field names (best-effort).
- `unknown`: only `raw_line: string`.

**B.sample.4 — Field frequency.** For each field, count the fraction of lines where it appears:

- frequency >= 0.9 -> `required: True`
- otherwise -> `required: False`

**B.sample.5 — Category guessing** from tokens in `source_id`:

| Token match | Category |
|---|---|
| `firewall\|asa\|fortinet\|palo\|cisco_asa` | `network` |
| `aws\|gcp\|azure\|entra\|okta` | `cloud` |
| `wineventlog\|sysmon\|perfmon\|mssql` | `windows` |
| `linux\|syslog` | `linux` |
| `access\|apache\|nginx\|web` | `web` |
| `exchange\|office\|webex\|teams` | `collaboration` |
| `sap\|erp` | `erp` |
| `servicenow\|itsm` | `itsm` |
| `cybervision\|plc\|scada\|ot` | `ot` |
| none | `unknown` (user is asked) |

**B.sample.6 — Volume category guessing** for `calc_natural_events()`:

| Token match | Volume category |
|---|---|
| `network\|firewall` | `firewall` |
| `cloud` | `cloud` |
| `auth\|entra\|okta` | `auth` |
| `access\|web\|apache\|nginx` | `web` |
| `email\|exchange` | `email` |
| `ot\|plc\|scada` | `ot` |
| none | `firewall` (safe default) |

**B.sample.7 — Sample events.** Pick the first 2-3 non-empty lines as raw sample events for the docstring.

Output: `Findings` dict passed to Phase C.

### Phase B.wizard — Wizard mode (no `--sample`)

Same output structure as sample mode, but user answers instead of detector guessing:

1. **Category** (if not `--category`): pick from list. Default guessed from source_id tokens if possible.
2. **Format** (if not `--format`): pick from `[json, kv, csv, cef, syslog_rfc5424, syslog_bsd, xml, custom]`. Default `json`.
3. **Volume category**: pick from `[firewall, cloud, auth, web, email, ot]`. Default derived from category.
4. **Multi-file**: yes/no. Default no.
5. **Field mode**: pick one of:
   - "Minimal" — skill proposes 5 standard fields based on format + category (e.g. for `network/kv`: `timestamp, src_ip, dst_ip, action, port`).
   - "Paste fields" — user pastes a list, one per line, `name:type` format.
   - "Empty skeleton" — just `timestamp` and `raw_line`, user fills out manually later.
6. **Sample event (optional)** — user can paste one line as docstring example. Default: generator creates one from fields.

Output: same `Findings` dict as sample mode.

### Phase C — Review gate (both modes)

Display summary:

```
Generator to be created: fake_data/generators/generate_fortigate.py

  Source ID:       fortigate
  Category:        network
  Format:          kv
  Volume category: firewall
  Multi-file:      no
  Fields (8):
    timestamp     (required, iso_timestamp)
    srcip         (required, ipv4)
    dstip         (required, ipv4)
    action        (required, enum: accept|deny|drop|reset)
    policyid      (required, int)
    service       (optional, string)
    srcport       (optional, int)
    dstport       (optional, int)

  SOURCE_META:
    category: network
    volume_category: firewall
    depends_on: []
    description: "Fortinet FortiGate traffic logs"

Create this generator? [yes/edit/cancel]
```

- `yes` -> Phase D
- `edit` -> back to wizard questions to override individual fields
- `cancel` -> exit

### Phase D — Scaffolding

Read `templates/generators/_template_generator.py` from plugin repo, substitute placeholders, write result.

**Generator function signature** (matches TA-FAKE-TSHRT convention):

```python
def generate_<source_id>_logs(
    start_date: str = DEFAULT_START_DATE,
    days: int = DEFAULT_DAYS,
    scale: float = DEFAULT_SCALE,
    scenarios: str = "none",
    output_file: str = None,
    progress_callback=None,
    quiet: bool = False,
) -> int:
```

**SOURCE_META block** at top of each generator:

```python
SOURCE_META = {
    "source_id": "<source_id>",
    "category": "<category>",
    "source_groups": ["<category>"],
    "volume_category": "<volume_category>",
    "multi_file": False,
    "depends_on": [],
    "description": "<auto-generated or user-provided>",
}
```

**Field generation body** — for each field, realistic generation based on type:

- `ipv4` internal: derive from `NETWORK_CONFIG` per random location
- `ipv4` external: `random.choice` from `EXTERNAL_IP_POOL` subnet
- `int` (ports): `random.choice([80, 443, 22, 3389, 8080])` or `random.randint(1024, 65535)`
- `enum`: `random.choice([...])` with values from sample or wizard
- `string` (username): `random.choice(USERS)["username"]`
- `iso_timestamp`: `ts_iso(start_date, day, hour, minute, second)`
- unknown type: placeholder `"TODO_<field_name>"` — works but clearly marked

**Serialization body** varies with format:

- `json`: `return json.dumps(event)`
- `kv`: `return " ".join(f"{k}={v}" for k, v in event.items())`
- `csv`: `return ",".join(str(v) for v in event.values())`
- `cef`: standard CEF header + extension
- `syslog_*`: timestamp + host + message
- `xml`: tag-based
- `unknown`: `return event["raw_line"]`

**demo_id convention** (documented in generator as comments):

```python
# Scenario events (future) set event["demo_id"] = <scenario_name> here.
# Baseline events leave demo_id unset so props.conf can strip it at index time.
```

**Multi-file return convention:** generators with `multi_file: True` may return `{"total": N, "files": {...}}` instead of `int`. `main_generate.py` handles both.

### Phase E — Handoff

```
Generator created: fake_data/generators/generate_fortigate.py

Next steps:
  1. Review the generator and tune field values:
     $EDITOR fake_data/generators/generate_fortigate.py

  2. Test it standalone:
     python3 fake_data/generators/generate_fortigate.py --days=1 --quiet

  3. Run via orchestrator:
     python3 fake_data/main_generate.py --days=1

  4. Check the output:
     ls fake_data/output/network/
     head fake_data/output/network/fortigate.log

Fields with "TODO_<name>" placeholders need your manual attention.
```

## main_generate.py orchestrator

A working orchestrator shipped as part of init. Not a stub — it discovers, sorts, and runs generators.

### CLI

```
python3 fake_data/main_generate.py [--sources=<list>] [--days=N] [--start-date=YYYY-MM-DD]
                                     [--scale=F] [--scenarios=<list>] [--show-files]
                                     [--list] [--quiet]
```

| Flag | Default | Effect |
|---|---|---|
| `--sources=<list>` | `all` | Comma-separated source_ids, or `all` |
| `--days=N` | `31` | Days to generate |
| `--start-date` | `2026-01-01` | Start date |
| `--scale=F` | `1.0` | Volume scaling factor |
| `--scenarios=<list>` | `none` | No-op in X1, reserved for add-scenario |
| `--show-files` | off | List all expected output files without generating |
| `--list` | off | List all registered generators and exit |
| `--quiet` | off | Suppress progress output |
| `--test`, `--no-test` | n/a | Reserved for Splunk plan, exits with clear message |

### Runtime flow

1. Bootstrap `sys.path` so `fake_data` package is importable from any cwd.
2. Import `fake_data.manifest`, verify `FAKE_DATA_WORKSPACE_VERSION`. Incompatible version -> hard exit with migration pointer.
3. Generator discovery via `pkgutil.iter_modules` + `importlib.import_module` on `fake_data/generators/`. Skip modules starting with `_`. Read `SOURCE_META` from each.
4. Topological sort based on `SOURCE_META["depends_on"]`. Cycles -> error.
5. Source filter: if `--sources=a,b,c`, reduce to that set plus transitive dependencies.
6. Execute each generator in topological order. Look up function by name convention `generate_<source_id>_logs`. Call with `progress_callback` and `quiet`.
7. Progress display: single-line `\r`-updating format: `[3/8] fortigate: day 12/31`. Silent when `--quiet`.
8. Handle return values: `int` (single file) or `dict` with `{"total": N, "files": {...}}` (multi-file).
9. Summary after all generators: total events, total time, any errors per generator (one generator's failure does not stop others).
10. `--show-files`: skip execution, print `SOURCE_META` output paths for all discovered generators.
11. `--list`: skip execution, print table of `source_id | category | description | depends_on`.

### Error handling

- Generator import fails (SyntaxError, ImportError): catch, report filename, continue with next.
- Generator function has wrong signature: catch `TypeError`, report.
- Generator crashes at runtime: catch `Exception`, report stacktrace in error summary, continue with next.
- Missing `manifest.py` or wrong version: hard exit with clear message.

## Ported utilities from TA-FAKE-TSHRT

These files are copied into the user's workspace by init. They are generic and contain no TA-FAKE-TSHRT-specific references.

### config.py

Ported from `shared/config.py`. Contains:

- `DEFAULT_START_DATE = "2026-01-01"`, `DEFAULT_DAYS = 31`, `DEFAULT_SCALE = 1.0`
- `OUTPUT_BASE`, `OUTPUT_DIRS` dict (category -> Path)
- `get_output_path(category, filename) -> Path` — resolves output path, creates parent dirs
- `set_output_base(new_base)` — redirects all output (reserved for future test/production staging)
- `VOLUME_WEEKEND_FACTORS` dict — weekend traffic as percentage of weekday by source type
- `VOLUME_MONDAY_BOOST = 115` — 15% more traffic on Mondays
- `VOLUME_DAILY_NOISE_MIN = -15`, `VOLUME_DAILY_NOISE_MAX = 15`
- `HOUR_ACTIVITY_WEEKDAY` dict — activity level 0-100 per hour
- `HOUR_ACTIVITY_WEEKEND` dict — enterprise/office weekend pattern
- `HOUR_ACTIVITY_WEEKEND_ECOMMERCE` dict — consumer/retail weekend pattern
- `HOUR_ACTIVITY_WEEKEND_FIREWALL` dict — mixed perimeter pattern
- `Config` dataclass — container for `start_date`, `days`, `scale`, `scenarios`
- `expand_scenarios(scenarios: str) -> List` — placeholder no-op, returns `[]`. Real implementation comes with add-scenario skill.

### time_utils.py

Ported from `shared/time_utils.py`. Contains:

| Function | Format | Use for |
|---|---|---|
| `ts_iso(start_date, day, hour, min, sec)` | `2026-01-05T14:30:45Z` | JSON logs (AWS, GCP, cloud) |
| `ts_iso_ms(start_date, day, hour, min, sec, ms)` | `2026-01-05T14:30:45.123Z` | JSON with milliseconds |
| `ts_syslog(start_date, day, hour, min, sec)` | `Jan 05 2026 14:30:45` | Syslog (ASA, Meraki, Catalyst) |
| `ts_cef(start_date, day, hour, min, sec)` | CEF header format | CEF syslog |
| `ts_perfmon(start_date, day, hour, min, sec, ms)` | `01/05/2026 14:30:45.123` | Windows Perfmon |
| `calc_natural_events(base, start_date, day, hour, cat)` | int | Natural volume with weekend/hourly variation |
| `date_add(start_date, days)` | date string | Add days to a date |

`calc_natural_events` reads `VOLUME_WEEKEND_FACTORS`, `HOUR_ACTIVITY_*`, `VOLUME_MONDAY_BOOST`, and `VOLUME_DAILY_NOISE_*` from `config.py` to produce realistic volume variation.

## Workspace search utility

Used by all skills to find the workspace root:

```python
from pathlib import Path
from typing import Optional

def find_workspace_root(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from start (default cwd) looking for fake_data/manifest.py.
    Returns the directory containing fake_data/, or None."""
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "fake_data" / "manifest.py").exists():
            return candidate
    return None
```

This function lives in SKILL.md instructions, not in a copied file. Both `init/SKILL.md` and `add-generator/SKILL.md` include this function as inline instructions. The user's workspace does not need to contain this utility — it is only used by Claude at skill-invocation time, not by Python at runtime.

## Canary test — defines "this spec is done"

Run manually in a clean scratch directory after the plan is executed. All seven steps green = done.

```bash
# 1. Setup
mkdir /tmp/fake-data-canary && cd /tmp/fake-data-canary
claude

# 2. Init
> /fake-data:init
# Answer: "Acme Widgets", no on real company, "manufacturing", 50 employees,
# 2 locations (HQ in Oslo NO, branch in Stockholm SE), "acme-widgets.com",
# 10.0.0.0/8. Approve review gate.

# 3. Verify workspace
ls fake_data/
python3 -c "from fake_data.world import USERS, LOCATIONS; print(len(USERS), len(LOCATIONS))"
# Expected: 50 2
python3 -c "from fake_data.world import EXTERNAL_IP_POOL_BY_COUNTRY; print(list(EXTERNAL_IP_POOL_BY_COUNTRY.keys()))"
# Expected: ['NO', 'SE']

# 4. Add-generator sample mode
cat > /tmp/sample.log << 'EOF'
date=2026-01-05 time=14:30:45 srcip=10.10.30.55 dstip=198.51.100.42 action=deny port=443
date=2026-01-05 time=14:30:46 srcip=10.10.30.56 dstip=198.51.100.17 action=accept port=80
date=2026-01-05 time=14:30:47 srcip=10.10.30.57 dstip=198.51.100.99 action=deny port=3389
EOF

> /fake-data:add-generator acme_fw --sample=/tmp/sample.log
# Verify: format=kv, category=network, fields detected. Approve.

python3 fake_data/generators/generate_acme_fw.py --days=1 --quiet
# Expected: exits cleanly, creates fake_data/output/network/acme_fw.log

# 5. Add-generator wizard mode
> /fake-data:add-generator acme_web
# Pick: format=json, category=web, volume_category=web, field mode="Minimal". Approve.

# 6. Run orchestrator
python3 fake_data/main_generate.py --list
# Expected: table with acme_fw and acme_web

python3 fake_data/main_generate.py --days=2 --quiet
wc -l fake_data/output/network/acme_fw.log   # > 0
wc -l fake_data/output/web/acme_web.log      # > 0

# 7. Idempotency checks
> /fake-data:init           # Expected: refuses (workspace exists)
> /fake-data:add-generator acme_fw  # Expected: refuses (generator exists)
```

## Future plans — prioritized order after this spec

| # | Plan | What | Estimated size |
|---|---|---|---|
| 1 | **TUI plan** | `fake_data/tui_generate.py` + `--tui` flag. Curses-based grid UI, stdlib-only, visually compatible with TA-FAKE-TSHRT TUI. | Small (~500 LOC) |
| 2 | **discover-logformat** | Full port from TA-FAKE-TSHRT including research phase (WebSearch/WebFetch), confidence gates, metadata-only fallback. Produces `.planning/discover/<source_id>/SPEC.json`. | Large |
| 3 | **add-generator v2** | Consumes `SPEC.json` from discover-logformat as third input mode. Backward-compatible with wizard and sample modes. | Small |
| 4 | **add-scenario** | New skill. Scaffold scenario classes in `fake_data/scenarios/`. Fill in `expand_scenarios()` from no-op to real. | Medium |
| 5 | **generate-logs** | Thin skill wrapper around `python3 main_generate.py`. Claude-assisted "suggest scenarios" and "explain output" flow. | Small |
| 6 | **build-splunk-app** | Largest future plan. Generate complete Splunk TA with props.conf, transforms.conf, inputs.conf, app.conf, dashboards, packaged as SPL. Includes `output/tmp/` staging + atomic move + `--test`/`--no-test` flags. | Large |
| 7 | **package** | Bundle workspace + Splunk app as one deliverable. | Small |
| 8 | **TA-FAKE-TSHRT migration** | Migrate TA-FAKE-TSHRT to consume fake-data plugin. 26 generators, 11 scenarios, 195 users. **SAFETY: create a full copy of the TA-FAKE-TSHRT repo before starting. Work on a branch or a separate directory. The working original must never be touched directly.** | Large |

## Open questions

None remaining after brainstorming.

## Change history entry (to add after implementation)

```
## 2026-MM-DD ~HH:MM UTC -- Plan X1: Framework core + init + add-generator
Files: .claude/skills/init/SKILL.md, .claude/skills/add-generator/SKILL.md,
       templates/runtime/*, templates/generators/*, data/*
First functional version of the FAKE_DATA plugin. Users can run /fake-data:init
to create a workspace and /fake-data:add-generator to scaffold generators.
Includes working main_generate.py orchestrator with filesystem-based discovery.
```

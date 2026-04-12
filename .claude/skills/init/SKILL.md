---
name: init
description: Create a new FAKE_DATA workspace with a fictional organization. Generates world.py, config, runtime templates, and directory structure.
version: 0.1.0
metadata:
  argument-hint: "(no arguments — interactive wizard)"
---

# init — Create a FAKE_DATA workspace

Create a new FAKE_DATA workspace in the current directory. This skill generates a `fake_data/` directory with all runtime files needed to create and run log generators.

**No arguments.** All configuration is gathered interactively.

---

## Phase A — Pre-flight and collision check

Before asking any questions, verify the target directory is clean.

### A.1 Check for existing workspace

Run via Bash:
```bash
test -f fake_data/manifest.py && echo "EXISTS" || echo "CLEAN"
```

If `EXISTS`: stop immediately and print:
> "A FAKE_DATA workspace already exists at `./fake_data/`. Delete it or run init from a different directory."

### A.2 Check for stale fake_data/ directory

If manifest.py does not exist, also check:
```bash
test -d fake_data && echo "DIR_EXISTS" || echo "NO_DIR"
```

If `DIR_EXISTS`: stop and print:
> "A `fake_data/` directory exists here but has no manifest.py. This looks like a partially-initialized or unrelated directory. Please remove or rename it before running init."

### A.3 If clean, proceed to Phase B.

---

## Phase B — Interactive question gathering

Ask these questions **one at a time**. Wait for each answer before asking the next. Use defaults in brackets if the user just presses enter or says "default".

### B.1 Organization name

> "What is the name of the fictional organization? [Example Corp]"

Store as `ORG_NAME`. Default: `"Example Corp"`.

### B.2 Real company check

> "Is this based on a real company? If yes, I'll research public information to prefill defaults. [no]"

If yes: run **Phase B.1-research** below before continuing. If no: continue to B.3.

### B.3 Industry

> "What industry? Pick one: retail, manufacturing, saas, financial, healthcare, generic [generic]"

Store as `INDUSTRY`. Default: `"generic"` (or from research).

### B.4 Employee count

> "How many employees total? [100]"

Store as `employee_count`. Default: `100` (or from research).

### B.5 Number of locations

> "How many office locations? [2]"

Store as `location_count`. Default: `2` (or from research).

### B.6 Location details

For each location (1 through location_count), ask:

> "Location N — name, city, country code (2-letter ISO), timezone, and percentage of employees.
> Example: Headquarters, Oslo, NO, Europe/Oslo, 60%"

Parse each answer into: `name`, `city`, `country`, `timezone`, `employee_pct`. Generate a location ID from the name (uppercase first 3-4 chars, e.g. "Headquarters" -> "HQ1", "Branch Office" -> "OFF1").

If percentages don't sum to 100%, normalize them proportionally.

### B.7 Primary domain

> "What is the primary email/web domain? [<orgname_lower>.com]"

Store as `TENANT`. Default: derive from ORG_NAME (lowercase, remove spaces and special chars, append `.com`).

### B.8 Internal IP plan

> "Which internal IP range? Pick one: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 [10.0.0.0/8]"

Store as `ip_plan`. Default: `"10.0.0.0/8"`.

---

## Phase B.1-research — Company research (only if "real company" = yes)

Time budget: **60 seconds max**. Use WebSearch and WebFetch.

### Steps

1. Search: `"<ORG_NAME>" company headquarters employees site:wikipedia.org OR site:<orgname_lower>.com`
2. Fetch top 2-3 results. Prefer the company's own about page and Wikipedia.
3. Extract: industry, headquarters city/country, other known offices, approximate employee count, official domain.
4. Present findings:

> "Based on public information, I found:
>   - Industry: <industry> (source: <url>)
>   - HQ: <city>, <country>
>   - Approx. employees: <count>
>   - Domain: <domain>
> These are prefilled as defaults. You can override any of them in the following questions."

5. Use extracted values as defaults for B.3-B.7.

**Privacy guardrail:** Research fetches ONLY publicly available company context (about pages, Wikipedia, press releases). It does NOT look up LinkedIn profiles, employee names, or real IP addresses. The USERS list is ALWAYS generated from the bundled name list, never from research results. The output is "fictional logs for a fictional IT environment that resembles company X", not "logs that impersonate company X".

---

## Phase C — Generate content in memory

Build all file contents before writing anything. Do NOT write files yet.

### C.1 Load data files from plugin repo

Read these files using the Read tool (paths relative to this SKILL.md):
- `../../../data/names_sample.py` — extract `FIRST_NAMES` and `LAST_NAMES` lists
- `../../../data/country_ip_ranges.py` — extract `COUNTRY_RANGES` and `FALLBACK_RANGES`

### C.2 Generate deterministic values

Use Python-style logic (execute mentally or describe to yourself):

**ORG_NAME_LOWER:** lowercase ORG_NAME, remove all non-alphanumeric characters.

**TENANT_ID:** Generate a deterministic UUID from ORG_NAME using UUID5 with DNS namespace:
`uuid.uuid5(uuid.NAMESPACE_DNS, ORG_NAME.lower())` — write the result as a string.

**USERS list:** Seed a random generator with `hash(ORG_NAME)` for determinism. For each employee (up to `employee_count`):
- Pick a first name and last name from the bundled lists. Cycle through them if employee_count > list length.
- username: `firstname.lastname` (all lowercase). If duplicate, append a digit.
- email: `username@<TENANT>`
- location: distribute across locations by their employee percentages
- department: cycle through `["engineering", "sales", "marketing", "finance", "hr", "it", "operations"]`

Generate the full USERS list as Python code — each entry is a dict with keys: `username`, `full_name`, `email`, `location`, `department`.

**NETWORK_CONFIG:** Based on the chosen IP plan, assign a /16 subnet per location:
- If `10.0.0.0/8`: location 1 = `10.10.0.0/16`, location 2 = `10.20.0.0/16`, location 3 = `10.30.0.0/16`, etc.
- If `172.16.0.0/12`: location 1 = `172.16.0.0/16`, location 2 = `172.17.0.0/16`, etc.
- If `192.168.0.0/16`: location 1 = `192.168.1.0/24`, location 2 = `192.168.2.0/24`, etc.
- Gateway: first IP in subnet (e.g. `10.10.0.1`). DNS: `.0.53` suffix (e.g. `10.10.0.53`).

**EXTERNAL_IP_POOL:** Look up each unique country code from LOCATIONS in `COUNTRY_RANGES`. For hits, add those ranges. Always append `FALLBACK_RANGES` at the end.

**EXTERNAL_IP_POOL_BY_COUNTRY:** Dict mapping each country code to its ranges from `COUNTRY_RANGES`.

### C.3 Compose world.py content

Generate the full `world.py` file content as a Python module with:
- Module docstring mentioning ORG_NAME and generation date
- `from typing import Optional, List, Dict`
- `ORG_NAME`, `ORG_NAME_LOWER`, `TENANT`, `TENANT_ID`, `INDUSTRY` constants
- `LOCATIONS` dict (keyed by location ID)
- `NETWORK_CONFIG` dict (keyed by location ID)
- `EXTERNAL_IP_POOL` list
- `EXTERNAL_IP_POOL_BY_COUNTRY` dict
- `USERS` list (all generated users)
- Helper functions `get_user_by_username(username)` and `users_at_location(location_id)`

### C.4 Compose manifest.py content

```python
"""FAKE_DATA workspace manifest. Do not delete -- skills use this file
to verify that the current directory is a FAKE_DATA workspace."""

FAKE_DATA_WORKSPACE_VERSION = 1
INITIALIZED_AT = "<current UTC ISO-8601>"
PLUGIN_VERSION_AT_INIT = "0.1.0"
ORG_NAME_AT_INIT = "<ORG_NAME>"
```

### C.5 Compose README.md content

A brief markdown file explaining:
- What init created
- How to verify (`python3 fake_data/main_generate.py --help`)
- How to add a generator (`/fake-data:add-generator <source_id>`)
- Where world.py lives for manual editing
- That generators will be auto-discovered by main_generate.py

---

## Phase D — Review gate

Display a summary:

```
Summary of your new FAKE_DATA workspace:

  Organization:   <ORG_NAME>
  Industry:       <INDUSTRY>
  Locations:      <N>  (<loc1_id>: <city> <country> [<N> users], ...)
  Users:          <employee_count> generated (deterministic from org name)
  Domain:         <TENANT>
  Internal IPs:   <ip_plan>  (<loc1_id>: <subnet>, ...)
  External IPs:   <country list> ranges + RFC 5737 fallback

  Files to be written under ./fake_data/:
    manifest.py, world.py, config.py, time_utils.py, main_generate.py,
    README.md, generators/_template_generator.py,
    generators/__init__.py, scenarios/__init__.py, __init__.py,
    output/.gitkeep

Proceed with creating workspace? [yes/edit/cancel]
```

- **yes**: proceed to Phase E
- **edit**: go back to Phase B, let user change specific answers, then re-run Phase C and D
- **cancel**: exit without writing anything

---

## Phase E — Write all files

Use the **Write tool** for every file. Do NOT use Bash echo/cat/heredoc.

### E.1 Read template files from plugin repo

Read these files using the Read tool (relative to this SKILL.md):
- `../../../templates/runtime/config.py`
- `../../../templates/runtime/time_utils.py`
- `../../../templates/runtime/main_generate.py`
- `../../../templates/generators/_template_generator.py`

### E.2 Write all files

Write each file using the Write tool:

1. `fake_data/__init__.py` — empty file (just a newline)
2. `fake_data/manifest.py` — generated content from C.4
3. `fake_data/world.py` — generated content from C.3
4. `fake_data/config.py` — exact copy of templates/runtime/config.py
5. `fake_data/time_utils.py` — exact copy of templates/runtime/time_utils.py
6. `fake_data/main_generate.py` — exact copy of templates/runtime/main_generate.py
7. `fake_data/README.md` — generated content from C.5
8. `fake_data/generators/__init__.py` — empty file
9. `fake_data/generators/_template_generator.py` — exact copy of templates/generators/_template_generator.py
10. `fake_data/scenarios/__init__.py` — empty file
11. `fake_data/output/.gitkeep` — empty file

### E.3 Verify the workspace

Run via Bash:
```bash
python3 -c "from fake_data.world import USERS, LOCATIONS; print(f'{len(USERS)} users, {len(LOCATIONS)} locations')"
```

If this fails, something went wrong — report the error to the user.

---

## Phase F — Handoff

Print:

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

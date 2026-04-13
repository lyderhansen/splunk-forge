---
name: fd-add-generator
description: Scaffold a new log generator from a sample file or interactive wizard. Creates a Python generator in fake_data/generators/.
version: 0.1.0
metadata:
  argument-hint: "<source_id> [--sample=<path>] [--category=<cat>] [--format=<fmt>]"
---

# fd-add-generator — Scaffold a new log generator

Create a new Python log generator in an existing FAKE_DATA workspace. Supports two modes:
- **Sample mode** (`--sample=<path>`): detect format and fields from a log file
- **Wizard mode** (no --sample): ask interactive questions

The generated file lives at `fake_data/generators/generate_<source_id>.py` and is auto-discovered by `main_generate.py`.

---

## Phase A — Pre-flight

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

### A.2 Parse arguments

Expected invocation: `/fd-add-generator <source_id> [--sample=<path>] [--category=<cat>] [--format=<fmt>]`

`source_id` is required. If missing:
> "Missing source_id. Usage: `/fd-add-generator <source_id> [--sample=<path>]`"

### A.3 Normalize source_id

- Lowercase the value
- Replace every run of non-alphanumeric characters with a single underscore
- Strip leading/trailing underscores
- Reject if empty or starts with a digit:
  > "source_id must start with a letter and contain at least one alphanumeric character."

### A.4 Check for collision

Check if `fake_data/generators/generate_<source_id>.py` already exists.

If it does:
> "Generator for '<source_id>' already exists at `fake_data/generators/generate_<source_id>.py`. Delete it first or pick a different source_id."

### A.4b Check for existing SPEC.py

Check if `fake_data/discover/<source_id>/SPEC.py` exists.

If it exists:
- Read it using the Read tool
- Extract the SPEC dict: source, format, fields, sample_events, generator_hints, category
- Print: "Found discovery spec at `fake_data/discover/<source_id>/SPEC.py` (confidence: <overall_confidence>). Using it to scaffold the generator."
- **Skip Phase B entirely** — no sample parsing, no wizard questions
- Build Findings directly from SPEC:
  - `format` = SPEC["format"]["type"]
  - `category` = SPEC["category"]
  - `volume_category` = SPEC["generator_hints"]["volume_category"]
  - `fields` = SPEC["fields"]
  - `sample_events` = SPEC["sample_events"]
  - `description` = SPEC["source"]["description"]
  - `multi_file` = SPEC["generator_hints"]["multi_file"]
- Proceed directly to **Phase C** (review gate)

If it does not exist: continue to A.5.

### A.5 Decide mode

If `--sample=<path>` is provided: **sample mode** (Phase B.sample).
Otherwise: **wizard mode** (Phase B.wizard).

---

## Phase B.sample — Sample mode

### B.sample.1 Read the sample file

Use the Read tool to read `--sample=<path>`. Read at most 500 lines. If the file doesn't exist or is empty, report an error and stop.

### B.sample.2 Format detection

Test each line of the sample against these patterns **in order**. The first pattern where more than 50% of lines match wins:

| Order | Pattern | Format value |
|---|---|---|
| 1 | Line starts with `{` and ends with `}` | `json` |
| 2 | Line matches `^CEF:\d` | `cef` |
| 3 | Line matches `^<\d+>` | `syslog_rfc5424` |
| 4 | Line matches `^\w{3} \d+ \d+:\d+:\d+` | `syslog_bsd` |
| 5 | Line matches `\w+=\S+( \w+=\S+)+` | `kv` |
| 6 | First line looks like CSV headers (all values alphanumeric+underscore) or lines match `^\d+,.*,.*` | `csv` |
| 7 | Line starts with `<` and contains `>` | `xml` |
| 8 | None of the above | `unknown` |

If `unknown`, continue anyway — the generator will use `raw_line` as the only field.

### B.sample.3 Field extraction

Based on the detected format, extract fields from the sample lines:

**json:** Parse each line with `json.loads()`. Flatten nested objects with dot-path keys (e.g. `event.user.id`). For each value, infer type:
- Matches `^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$` → `ipv4`
- Matches `^[0-9a-fA-F:]+$` with colons → `ipv6`
- Matches `^\d{4}-\d{2}-\d{2}T` → `iso_timestamp`
- Is a Python int → `int`
- Is a Python float → `float`
- Is a Python bool → `bool`
- Otherwise → `string`

**kv:** Split each line on whitespace, then split each token on the first `=`. Left side is field name, right side is value. Infer types same as json.

**csv:** If the first line's values all look like identifiers (alphanumeric + underscore, no spaces), treat it as a header row. Otherwise generate field names `col_1`, `col_2`, etc. Infer types from remaining rows.

**cef:** Parse the 7-field CEF header: `CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity`. Then parse the extension block as KV pairs (space-separated `key=value`).

**syslog_rfc5424 / syslog_bsd:** Attempt KV parsing on the message body (everything after the syslog header). If KV parsing yields fields, use them. Otherwise, create a single `raw_line` field of type `string`.

**xml:** Extract top-level tag names as field names. All types default to `string`.

**unknown:** Single field: `raw_line` of type `string`.

### B.sample.4 Field frequency

For each extracted field, count the fraction of sample lines where it appears:
- frequency >= 0.9 → `required: True`
- frequency < 0.9 → `required: False`

Record one example value per field (from the first line where it appears).

### B.sample.5 Category guessing

Check if any of these tokens appear in `source_id` (first match wins):

| Token(s) in source_id | Category |
|---|---|
| firewall, asa, fortinet, palo, cisco_asa, meraki, catalyst | network |
| aws, gcp, azure, entra, okta | cloud |
| wineventlog, sysmon, perfmon, mssql | windows |
| linux, syslog | linux |
| access, apache, nginx, web | web |
| exchange, office, webex, teams | collaboration |
| sap, erp | erp |
| servicenow, itsm | itsm |
| cybervision, plc, scada, ot | ot |
| (no match) | unknown — ask the user |

If category is `unknown`, ask:
> "I couldn't guess the category from the source name. Pick one: network, cloud, windows, linux, web, retail, collaboration, itsm, erp, ot"

### B.sample.6 Volume category guessing

| Token(s) in source_id or category | Volume category |
|---|---|
| network, firewall | firewall |
| cloud | cloud |
| auth, entra, okta | auth |
| access, web, apache, nginx | web |
| email, exchange | email |
| ot, plc, scada | ot |
| (no match) | firewall (safe default) |

### B.sample.7 Sample events

Pick the first 2-3 non-empty, non-header lines from the sample file. These will be included as docstring examples in the generated file.

### B.sample.8 Build Findings

Assemble a `Findings` object (mental model — not a file) with:
- `source_id`, `format`, `category`, `volume_category`, `multi_file: False`
- `fields`: list of `{name, type, required, example}`
- `sample_events`: 2-3 raw lines
- `description`: auto-generated from source_id and format, e.g. "FortiGate KV-format traffic logs"

Proceed to Phase C.

---

## Phase B.wizard — Wizard mode

Ask these questions **one at a time**.

### W.1 Category

> "What category for this source? Pick one: network, cloud, windows, linux, web, retail, collaboration, itsm, erp, ot [<guess from source_id or 'network'>]"

### W.2 Format

> "What log format? Pick one: json, kv, csv, cef, syslog_rfc5424, syslog_bsd, xml, custom [json]"

### W.3 Volume category

> "What volume pattern? Pick one: firewall, cloud, auth, web, email, ot [<derived from category>]"

### W.4 Multi-file

> "Does this source produce multiple output files? [no]"

### W.5 Field mode

> "How should I set up the fields?
>   1. **Minimal** — I'll propose ~5 standard fields based on format and category
>   2. **Paste fields** — you provide a list (one per line, format: `name:type`)
>   3. **Empty skeleton** — just timestamp and raw_line, you fill in later
> Pick 1, 2, or 3: [1]"

If **Minimal**: propose fields based on category and format. Examples:
- network + kv: `timestamp:iso_timestamp`, `src_ip:ipv4`, `dst_ip:ipv4`, `action:enum:accept,deny,drop`, `port:int`
- cloud + json: `timestamp:iso_timestamp`, `event_type:string`, `user:string`, `source_ip:ipv4`, `result:enum:success,failure`
- windows + xml: `timestamp:iso_timestamp`, `event_id:int`, `computer:string`, `user:string`, `level:enum:Information,Warning,Error`
- web + json: `timestamp:iso_timestamp`, `client_ip:ipv4`, `method:enum:GET,POST,PUT,DELETE`, `uri:string`, `status:int`

Show the proposed fields and ask: "OK with these fields, or want to edit? [ok]"

If **Paste fields**: ask user to paste, parse each line as `name:type`. Supported types: `string`, `int`, `float`, `bool`, `ipv4`, `ipv6`, `iso_timestamp`, `enum:<values>`.

If **Empty skeleton**: use `[{name: "timestamp", type: "iso_timestamp", required: True}, {name: "raw_line", type: "string", required: True}]`.

### W.6 Sample event (optional)

> "Want to paste a sample log line as a docstring example? [skip]"

### W.7 Build Findings

Same as B.sample.8, using wizard answers.

Proceed to Phase C.

---

## Phase C — Review gate

Display:

```
Generator to be created: fake_data/generators/generate_<source_id>.py

  Source ID:       <source_id>
  Category:        <category>
  Format:          <format>
  Volume category: <volume_category>
  Multi-file:      <yes/no>
  Fields (<N>):
    <name>     (<required/optional>, <type>)
    ...

  SOURCE_META:
    category: <category>
    volume_category: <volume_category>
    depends_on: []
    description: "<description>"

Create this generator? [yes/edit/cancel]
```

- **yes**: proceed to Phase D
- **edit**: go back to the relevant questions, re-build Findings, re-show this gate
- **cancel**: exit without creating anything

---

## Phase D — Scaffolding

### D.1 Read the template

Read the generator template from the plugin repo using the Read tool:
`../../templates/generators/_template_generator.py`

### D.2 Generate the new file content

Create a complete Python file based on the template structure but customized for this source. The file must include:

**Header:** Module docstring with source_id, description, and generation date.

**Imports:**
```python
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fake_data.world import USERS, LOCATIONS, NETWORK_CONFIG, EXTERNAL_IP_POOL
from fake_data.config import (
    DEFAULT_START_DATE, DEFAULT_DAYS, DEFAULT_SCALE,
    get_output_path, expand_scenarios,
)
from fake_data.time_utils import ts_iso, calc_natural_events, date_add
```

Add format-specific imports if needed (e.g. `import csv` for CSV format).

**SOURCE_META:** Fill in with actual values from Findings:
```python
SOURCE_META = {
    "source_id": "<source_id>",
    "category": "<category>",
    "source_groups": ["<category>"],
    "volume_category": "<volume_category>",
    "multi_file": False,
    "depends_on": [],
    "description": "<description>",
}
```

**Generator function:** Use the exact signature:
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

The body follows the template pattern: loop days -> hours -> calc_natural_events -> _make_event -> sort -> write.

**`_make_event()` body:** For each field in Findings, generate a Python line based on type:

| Field type | Generated code |
|---|---|
| `iso_timestamp` | `ts_iso(start_date, day, hour, minute, second)` |
| `ipv4` (if name contains src/source/internal) | `f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"` |
| `ipv4` (if name contains dst/dest/external) | Use EXTERNAL_IP_POOL: pick a random range |
| `ipv4` (generic) | `f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"` |
| `int` (if name contains port) | `random.choice([80, 443, 22, 3389, 8080, 8443])` |
| `int` (generic) | `random.randint(1, 10000)` |
| `float` | `round(random.uniform(0, 100), 2)` |
| `bool` | `random.choice([True, False])` |
| `enum:<values>` | `random.choice([<values as strings>])` |
| `string` (if name contains user/username/account) | `random.choice(USERS)["username"]` |
| `string` (if name contains email) | `random.choice(USERS)["email"]` |
| `string` (if name contains host/computer/server) | `f"host-{random.randint(1,50)}"` |
| `string` (generic) | `f"TODO_<field_name>"` |
| `ipv6` | `f"fe80::{random.randint(1,9999):x}:{random.randint(1,9999):x}"` |
| unknown | `f"TODO_<field_name>"` |

**`_serialize()` body:** Based on format:

| Format | Serialization |
|---|---|
| `json` | `return json.dumps(event)` |
| `kv` | `return " ".join(f"{k}={v}" for k, v in event.items())` |
| `csv` | `return ",".join(str(event.get(f, "")) for f in FIELD_ORDER)` (define FIELD_ORDER at module level) |
| `cef` | Build CEF header + extension string |
| `syslog_rfc5424` / `syslog_bsd` | Syslog header + message body |
| `xml` | XML tags wrapping each field |
| `custom` / `unknown` | `return event.get("raw_line", json.dumps(event))` |

**Standalone block:** argparse with --start-date, --days, --scale, --scenarios, --output, --quiet.

**demo_id comment:** Include as a comment in `_make_event`:
```python
# Scenario events (future) set event["demo_id"] = <scenario_name> here.
# Baseline events leave demo_id unset.
```

### D.3 Write the file

Use the Write tool to write the complete generated Python file to:
`fake_data/generators/generate_<source_id>.py`

### D.4 Syntax check

Run via Bash:
```bash
python3 -c "import ast; ast.parse(open('fake_data/generators/generate_<source_id>.py').read()); print('Syntax OK')"
```

If syntax check fails, fix the file and re-check.

---

## Phase E — Handoff

### E.1 Print summary

```
Generator created: fake_data/generators/generate_<source_id>.py

Fields with "TODO_<name>" placeholders need your manual attention.
```

### E.2 Chain to next skill

Ask the user:

> "Generator created. What would you like to do next?
>
>   1. **Add CIM mapping** — Run /fd-cim <source_id> for proper Splunk field aliases
>   2. **Create a scenario** — Run /fd-add-scenario to inject correlated events using this generator
>   3. **Generate logs** — Run /fd-generate to produce output
>   4. **Skip** — I'll do it myself later
> [1]"

Based on the user's choice:
- **1**: invoke `/fd-cim <source_id>`
- **2**: invoke `/fd-add-scenario` (user will be prompted for scenario details)
- **3**: invoke `/fd-generate --sources=<source_id>`
- **4**: print the manual commands:

```
Manual commands:
  Review:      open fake_data/generators/generate_<source_id>.py
  Test:        python3 fake_data/generators/generate_<source_id>.py --days=1 --quiet
  Orchestrate: python3 fake_data/main_generate.py --days=1
```

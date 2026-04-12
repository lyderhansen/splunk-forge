---
name: fd-build-app
description: Generate a Splunk Technology Add-on (TA) from workspace generators, scenarios, and world state. Produces installable app with sourcetypes, CIM alignment, and tar.gz package.
version: 0.1.0
metadata:
  argument-hint: "[app_name]"
---

# fd-build-app -- Generate a Splunk Technology Add-on

Build a complete, installable Splunk TA from the current workspace. The app
includes inputs.conf monitor stanzas, sourcetype definitions with
`MAX_DAYS_HENCE`/`MAX_DAYS_AGO` for synthetic timestamps, indexed `demo_id`
extraction, and optionally full CIM alignment with field aliases, lookups,
eventtypes, and tags.

**Key principle:** The app is ready to install the moment packaging finishes.
The user copies the directory or uploads the tar.gz -- no hand-editing required.

**Source of truth:** `docs/superpowers/specs/2026-04-12-fd-build-app-design.md`

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

### A.2 Read world state

Read `fake_data/world.py` and extract:
- `ORG_NAME` -- the organization name (used for default app name)
- `TENANT` -- tenant identifier if present
- `USERS` -- list of user dicts (used for identity_inventory.csv)
- `LOCATIONS` -- list of location dicts
- `INFRASTRUCTURE` -- list of device dicts (used for asset_inventory.csv; may not exist in basic workspaces)
- `EXTERNAL_IP_POOL` -- if present

### A.3 Scan generators

List all `fake_data/generators/generate_*.py` files. For each, read the file
and extract:

- `SOURCE_META` dict: `source_id`, `category`, `description`, `volume_category`
- Log format from the `_serialize()` method (json, kv, csv, syslog_bsd, syslog_rfc5424, cef, xml)
- Field names from the `_make_event()` method (all dict keys or KV pairs produced)
- Output file path pattern from SOURCE_META

Store as a list of generator records:
```
[{
    "source_id": "...",
    "category": "...",
    "description": "...",
    "volume_category": "...",
    "format": "...",
    "fields": ["field1", "field2", ...],
    "output_path": "..."
}]
```

If no generators found:
> "No generators found. Run `/fd-add-generator` first."

### A.4 Scan scenarios

List all `fake_data/scenarios/*.py` files (excluding `_base.py`, `__init__.py`).
For each, extract `SCENARIO_META`: `scenario_id`, `demo_id`, `sources`.

### A.5 Check output directory

Check `fake_data/output/` -- list existing log files per generator to confirm
data has been generated. Note which generators have output and which do not
(informational only; missing output does not block app creation).

### A.6 Check for existing app

Check if `fake_data/splunk_app/` already contains an app directory. If it does,
note the existing app name for the user during configuration.

---

## Phase B -- Configuration

Ask one question at a time. Show defaults in brackets.

### B.1 App name

> "App name? [TA-<ORG_NAME_UPPER>]"

Where `<ORG_NAME_UPPER>` is `ORG_NAME` uppercased with spaces and special
characters replaced by hyphens.

Normalize the user's answer:
- Uppercase all letters
- Replace spaces and special characters (except hyphens) with hyphens
- Strip leading/trailing hyphens

If the user provided an app name as the skill argument, use it (still normalize).

### B.2 Log file location

> "Where are the log files? [<absolute_path_to_workspace>/fake_data/output]"

This becomes the base path for all `inputs.conf` monitor stanzas. The default
is the workspace's `fake_data/output/` directory as an absolute path.

### B.3 Index

> "Splunk index name? [main]"

Used in every `inputs.conf` monitor stanza.

### B.4 CIM level

> "CIM alignment level?
>   - **full**: Field aliases, lookups, eventtypes, tags -- data is Splunk ES ready
>   - **basic**: Just sourcetypes + demo_id extraction -- data gets in, you map later
> [full]"

If **full**: proceed to Phase C.
If **basic**: skip Phase C entirely.

---

## Phase C -- CIM Mapping (full CIM only)

Skip this entire phase if the user chose **basic** CIM level.

### C.1 Rule-based category-to-model mapping

For each generator, map its `category` to CIM data model(s) using this table:

| Category | CIM Model(s) | Standard Fields |
|---|---|---|
| network | Network Traffic | src, dest, src_port, dest_port, action, bytes_in, bytes_out, transport, protocol |
| cloud | Authentication, Change | user, action, src, result, object, object_category |
| windows | Endpoint, Authentication | EventCode, user, dest, process, parent_process |
| linux | Performance, Authentication | host, cpu_pct, mem_pct, user, src |
| web | Web | uri, status, method, src, http_user_agent, bytes |
| collaboration | Email | sender, recipient, subject, action |
| itsm | Change, Incident | priority, status, assigned_to, category |
| erp | Change, Audit | user, action, object, result |
| ot | ICS, Network Traffic | src, dest, protocol, action, severity |

If a generator's category is not in this table, flag it for C.3 research.

### C.2 Field alias generation

For each generator, compare its extracted field names (from A.3) against
this pattern table and produce FIELDALIAS/EVAL stanzas:

| Generator Field Pattern | CIM Field | Alias Rule |
|---|---|---|
| srcip, src_ip, source_ip | src | FIELDALIAS-src = <field> AS src |
| dstip, dst_ip, dest_ip | dest | FIELDALIAS-dest = <field> AS dest |
| srcport, src_port | src_port | FIELDALIAS-src_port = <field> AS src_port |
| dstport, dst_port | dest_port | FIELDALIAS-dest_port = <field> AS dest_port |
| username, user_name, srcuser | user | FIELDALIAS-user = <field> AS user |
| action, status | action | EVAL-action = case(...) (normalize to allowed/blocked/success/failure) |
| sentbyte, bytes_out | bytes_out | FIELDALIAS-bytes_out = <field> AS bytes_out |
| rcvdbyte, bytes_in | bytes_in | FIELDALIAS-bytes_in = <field> AS bytes_in |
| duration | duration | FIELDALIAS-duration = <field> AS duration |
| proto, protocol | transport | EVAL-transport = <field> (map int to name if needed) |
| hostname, host, computer | dest | FIELDALIAS-dest = <field> AS dest |
| severity, level | severity | FIELDALIAS-severity = <field> AS severity |

Matching is case-insensitive. If a generator field exactly matches a CIM
standard field name (e.g., the field is already called `src`), no alias is
needed -- skip it.

Track which generator fields were matched and which remain unmapped.

### C.3 Research for unknown fields

If any generator has fields that did NOT match a rule-based pattern from C.2,
AND those fields seem relevant (not purely internal like `raw_line`, `timestamp`,
`demo_id`), dispatch a **sonnet** subagent using the **Agent tool**:

**Subagent prompt:**

```
You are mapping log fields to Splunk CIM (Common Information Model) fields.

Source: <source_id>
Category: <category>
Format: <format>
Fields: <list of unmapped field names with sample values if available>
CIM Model: <model from C.1>

For each source field, determine:
1. Which CIM field it maps to (if any)
2. Whether it needs FIELDALIAS (direct rename) or EVAL (transformation)
3. The EVAL expression if needed

Return in this format:
CIM_MAPPINGS:
<source_field> | <cim_field> | <type: alias|eval> | <eval_expression_or_empty>
END_CIM_MAPPINGS
```

Parse the response and merge results into the field alias set from C.2.

If the subagent returns no useful mappings, skip those fields (they become
unaliased search-time extractions).

### C.4 Lookup generation from world.py

Generate lookup CSV content from world.py data structures.

**asset_inventory.csv** (only if `INFRASTRUCTURE` exists in world.py):

Build from `INFRASTRUCTURE` list. Columns:
```
ip,mac,nt_host,dns,owner,priority,lat,long,city,country,bunit,category,pci_domain,is_expected,should_timesync,should_update,requires_av
```

For each device in INFRASTRUCTURE:
- `ip` = device IP
- `nt_host` = device hostname
- `owner` = "it" (default)
- `priority` = "medium"
- `city` = device location city (from LOCATIONS cross-reference)
- `country` = device location country
- `category` = device role (firewall, server, switch, etc.)
- Leave unresolvable fields empty

**identity_inventory.csv** (from `USERS`):

Build from `USERS` list. Columns:
```
identity,prefix,nick,first,last,suffix,email,phone,managedBy,priority,bunit,category,watchlist,startDate,endDate,work_city,work_country,work_lat,work_long
```

For each user in USERS:
- `identity` = username
- `first` = first name
- `last` = last name
- `email` = email address
- `priority` = "high" if department is "it", else "medium"
- `bunit` = department
- `work_city` = user location city
- `work_country` = user location country
- Leave unresolvable fields empty

If INFRASTRUCTURE does not exist in world.py, skip asset_inventory.csv entirely.

### C.5 Build CIM summary

For each generator, compile:
- CIM model(s) it maps to
- List of FIELDALIAS stanzas
- List of EVAL stanzas
- Applicable LOOKUP stanzas
- Eventtype name: `fake_<source_id>_<model_tag>`
- Tag pairs for the eventtype

---

## Phase D -- Review gate

Display a complete overview of the app that will be built:

```
Splunk App: <APP_NAME>

  Sourcetypes (<N>):
    FAKE:<source_id>     (<category>, <format>)
    FAKE:<source_id>     (<category>, <format>)
    ...

  Monitor stanzas: <N>
  Index: <index_name>
  Log base path: <log_base_path>
  CIM models: <comma-separated list, or "none (basic mode)">
  Lookups: asset_inventory (<N> entries), identity_inventory (<N> entries)
           (or "none" if basic mode or no INFRASTRUCTURE)

  Output:
    fake_data/splunk_app/<APP_NAME>/
    fake_data/splunk_app/<APP_NAME>.tar.gz

Build this app? [yes/edit/cancel]
```

- **yes**: proceed to Phase E
- **edit**: ask what to change, incorporate edits, re-display this gate
- **cancel**: exit without creating anything

---

## Phase E -- Generate app

Create the full Splunk app directory structure and write all files.

### E.1 Directory structure

Create directories via Bash:

```bash
mkdir -p fake_data/splunk_app/<APP_NAME>/default
mkdir -p fake_data/splunk_app/<APP_NAME>/metadata
```

If full CIM:
```bash
mkdir -p fake_data/splunk_app/<APP_NAME>/local
mkdir -p fake_data/splunk_app/<APP_NAME>/lookups
```

### E.2 Write default/app.conf

```ini
[install]
is_configured = false
build = 1

[ui]
is_visible = false
label = <APP_NAME>

[launcher]
author = FAKE_DATA
description = Technology Add-on for <ORG_NAME> synthetic log data
version = 1.0.0
```

### E.3 Write default/inputs.conf

One monitor stanza per generator. The monitor path uses the user-configured
log base path from B.2:

```ini
[monitor://<log_base_path>/<category>/<source_id>.log]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

For generators with `multi_file: True` in SOURCE_META, use a wildcard:
```ini
[monitor://<log_base_path>/<category>/<source_id>/...]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

**CRITICAL:** Sourcetype naming is `FAKE:<source_id>` -- using the source_id
from SOURCE_META directly. NOT `FAKE:vendor:product` format.

### E.4 Write default/props.conf

**CRITICAL: Wildcard stanza MUST be included.** This is what makes Splunk
accept synthetic timestamps that are far in the past or future:

```ini
[FAKE:*]
MAX_DAYS_HENCE = 10000
MAX_DAYS_AGO = 10000
CHARSET = UTF-8
LINE_BREAKER = ([\r\n]+)
SHOULD_LINEMERGE = false
```

Then one stanza per generator with format-specific settings:

```ini
[FAKE:<source_id>]
TRANSFORMS-demo_id = extract_demo_id_indexed
```

Append format-specific settings based on the generator's `_serialize()` format:

| Format | Props Settings |
|---|---|
| json | `KV_MODE = json`, `TIME_PREFIX = "timestamp"` (or first timestamp field name) |
| kv | `KV_MODE = auto`, `TIME_FORMAT = %Y-%m-%dT%H:%M:%S` |
| csv | `INDEXED_EXTRACTIONS = csv`, `HEADER_FIELD_LINE_NUMBER = 1` |
| syslog_bsd | `TIME_FORMAT = %b %d %H:%M:%S` |
| syslog_rfc5424 | `TIME_FORMAT = %Y-%m-%dT%H:%M:%S` |
| cef | `TIME_FORMAT = %b %d %Y %H:%M:%S` |
| xml | `KV_MODE = xml` |

Read each generator's `_serialize()` method to determine the correct format.
If the timestamp field name differs from `timestamp`, adjust `TIME_PREFIX`
accordingly.

### E.5 Write default/transforms.conf

```ini
[extract_demo_id_indexed]
REGEX = (?:"demo_id":\s*"([^"]+)"|demo_id=(\S+))
FORMAT = IDX_demo_id::$1$2
WRITE_META = true
DEPTH_LIMIT = 99999
```

The regex handles both JSON format (`"demo_id": "value"`) and KV format
(`demo_id=value`). The `WRITE_META = true` directive writes the extracted
value as indexed metadata.

### E.6 Write default/fields.conf

```ini
[IDX_demo_id]
INDEXED = true
```

This declares `IDX_demo_id` as an indexed field, enabling fast searches like
`IDX_demo_id=brute_force`.

### E.7 Write local/props.conf (full CIM only)

Skip this file entirely if basic CIM mode.

One stanza per generator with CIM enrichment from Phase C:

```ini
[FAKE:<source_id>]
FIELDALIAS-src = <source_field> AS src
FIELDALIAS-dest = <source_field> AS dest
EVAL-action = case(action=="allow", "allowed", action=="deny", "blocked", action=="success", "success", action=="fail", "failure", 1=1, action)
LOOKUP-asset = asset_inventory ip AS src OUTPUTNEW nt_host, owner, bunit, city
LOOKUP-identity = identity_inventory email AS user OUTPUTNEW identity, first, last, managedBy, priority, bunit
```

Only include FIELDALIAS lines where an actual mapping was found in C.2/C.3.
Only include EVAL lines where a transformation is needed.
Only include LOOKUP-asset if asset_inventory.csv was generated.
Only include LOOKUP-identity if identity_inventory.csv was generated.

### E.8 Write local/transforms.conf (full CIM only)

Skip if basic CIM mode.

```ini
[asset_inventory]
filename = asset_inventory.csv

[identity_inventory]
filename = identity_inventory.csv
```

Only include stanzas for lookups that were actually generated.

### E.9 Write local/eventtypes.conf (full CIM only)

Skip if basic CIM mode.

One eventtype per generator, named to reflect the CIM model:

```ini
[fake_<source_id>_<model_tag>]
search = sourcetype="FAKE:<source_id>"
```

Where `<model_tag>` is derived from the primary CIM model (e.g., `traffic`
for Network Traffic, `authentication` for Authentication, `change` for Change,
`web` for Web, `email` for Email, `incident` for Incident, `endpoint` for
Endpoint, `performance` for Performance, `ics` for ICS, `audit` for Audit).

### E.10 Write local/tags.conf (full CIM only)

Skip if basic CIM mode.

Tags that associate the eventtype with the CIM data model:

```ini
[eventtype=fake_<source_id>_<model_tag>]
<tag1> = enabled
<tag2> = enabled
```

CIM model to tag mapping:

| CIM Model | Tags |
|---|---|
| Network Traffic | network, communicate |
| Authentication | authentication |
| Change | change |
| Web | web |
| Email | email |
| Endpoint | endpoint, process, report |
| Performance | performance, os |
| Incident | incident |
| ICS | ics |
| Audit | audit, change |

### E.11 Write lookups/ CSV files (full CIM only)

Skip if basic CIM mode.

Write the CSV content generated in Phase C.4:
- `lookups/asset_inventory.csv` (if INFRASTRUCTURE exists)
- `lookups/identity_inventory.csv` (always, from USERS)

### E.12 Write metadata/default.meta

```ini
[]
access = read : [ * ], write : [ admin ]
export = system
```

### E.13 Write README.md

Write a brief README describing the app:

```markdown
# <APP_NAME>

Technology Add-on for **<ORG_NAME>** synthetic log data, generated by FAKE_DATA.

## Sourcetypes

| Sourcetype | Category | Format | Description |
|---|---|---|---|
| FAKE:<source_id> | <category> | <format> | <description> |
| ... | ... | ... | ... |

## Installation

Copy to `$SPLUNK_HOME/etc/apps/` and restart Splunk, or install the .tar.gz
package via Splunk Web (Apps > Manage Apps > Install app from file).

## CIM Alignment

<If full: list CIM models and lookup tables>
<If basic: "Basic mode -- sourcetypes and demo_id extraction only.">

## Generated by

FAKE_DATA plugin -- https://github.com/your-org/fake-data
```

---

## Phase F -- Package

### F.1 Clean Mac artifacts

Run via Bash from the workspace root:

```bash
find fake_data/splunk_app/<APP_NAME> -name '.DS_Store' -delete 2>/dev/null
find fake_data/splunk_app/<APP_NAME> -name '._*' -delete 2>/dev/null
find fake_data/splunk_app/<APP_NAME> -name '__MACOSX' -type d -exec rm -rf {} + 2>/dev/null
```

### F.2 Create tar.gz package

```bash
cd fake_data/splunk_app && tar -czf <APP_NAME>.tar.gz <APP_NAME>/
```

### F.3 Verify package

```bash
tar -tzf fake_data/splunk_app/<APP_NAME>.tar.gz | head -20
```

Confirm the output shows the expected directory structure with `<APP_NAME>/`
as the top-level directory. If the structure looks wrong, diagnose and re-package.

---

## Phase G -- Handoff

Print the completion summary with install instructions:

```
Splunk app created:
  Directory: fake_data/splunk_app/<APP_NAME>/
  Package:   fake_data/splunk_app/<APP_NAME>.tar.gz

  Sourcetypes: <N>
  Monitor stanzas: <N>
  CIM models: <comma-separated list, or "none (basic mode)">

Install in Splunk:
  Option 1 -- Copy directory:
    cp -r fake_data/splunk_app/<APP_NAME> $SPLUNK_HOME/etc/apps/
    $SPLUNK_HOME/bin/splunk restart

  Option 2 -- Install package:
    $SPLUNK_HOME/bin/splunk install app fake_data/splunk_app/<APP_NAME>.tar.gz

  Option 3 -- Upload via Splunk Web:
    Apps > Manage Apps > Install app from file > <APP_NAME>.tar.gz

Verify in Splunk:
  index=<index> sourcetype=FAKE:* | stats count by sourcetype
  index=<index> sourcetype=FAKE:* IDX_demo_id=* | stats count by IDX_demo_id
```

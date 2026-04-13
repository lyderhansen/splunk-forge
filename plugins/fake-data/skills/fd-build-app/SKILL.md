---
name: fd-build-app
description: 'Build an installable Splunk TA. Args: [app_name]. Generates inputs.conf, props.conf (with MAX_DAYS_HENCE), CIM alignment, and tar.gz package.'
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

### A.5 Scan CIM mappings

Check if `fake_data/cim/` directory exists. If yes, for each `<source_id>.py` file
(excluding `__init__.py`):
- Read the file
- Extract the `CIM_MAPPING` dict (use `ast.literal_eval` or parse the Python source)
- Store in a dict: `cim_mappings = {source_id: CIM_MAPPING}`

If `fake_data/cim/` doesn't exist or is empty, `cim_mappings = {}`.

### A.6 Offer to fill CIM gaps

Count generators with pre-built CIM mappings vs without:
- `total_generators` = number of generators from A.3
- `has_cim` = number of generators where `source_id in cim_mappings`
- `missing_cim` = list of source_ids where `source_id not in cim_mappings`

If `len(missing_cim) > total_generators / 2` (more than 50% missing),
offer the user a chance to fill the gaps BEFORE continuing to Phase B:

> "You have <total_generators> generators but only <has_cim> have pre-built
> CIM mappings (from /fd-cim). The rest will get auto-generated CIM mappings
> based on field name patterns.
>
> For better CIM alignment, you can run /fd-cim for each missing generator
> first. Missing CIM mappings:
>   - <source_id_1>
>   - <source_id_2>
>   ...
>
> What would you like to do?
>   1. **Add CIM mappings now** — Run /fd-cim for each missing generator,
>      then continue here
>   2. **Continue with auto-generated** — Let fd-build-app generate CIM
>      mappings on the fly
>   3. **Cancel**
> [2]"

If **1**: For each missing generator, invoke `/fd-cim <source_id>`. After
all complete, re-run A.5 to re-scan CIM mappings, then continue to Phase B.

If **2**: Continue to Phase B with auto-generation fallback for missing ones.

If **3**: Stop.

If fewer than 50% are missing, skip this prompt entirely and continue to Phase B.

### A.7 Check output directory

Check `fake_data/output/` -- list existing log files per generator to confirm
data has been generated. Note which generators have output and which do not
(informational only; missing output does not block app creation).

### A.8 Check for existing app

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

### B.2 Log file location (no longer asked)

Logs are now bundled INSIDE the app at `<APP_NAME>/logs/`. The generated
`inputs.conf` uses `$SPLUNK_HOME/etc/apps/<APP_NAME>/logs/...` so the app is
fully portable — copy it to any Splunk install and it just works.

Skip this question. Phase E will:
1. Copy `fake_data/output/*` into `<APP_NAME>/logs/` (pre-generated turnkey data)
2. Copy the generator runtime into `<APP_NAME>/bin/` so the user can re-run
   `python3 main_generate.py` from inside the installed app to regenerate.

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

### C.0 Check for pre-generated CIM mappings

For each generator, check if `cim_mappings[source_id]` exists (from Phase A.5).

- **If yes:** Use the pre-generated mapping directly. Skip C.1 rule-based
  matching and C.3 research for this generator. Still run C.4 for lookup
  CSV generation from world.py.
- **If no:** Fall back to C.1 rule-based matching. If unmapped fields
  remain, optionally dispatch research subagent (C.3).

This lets users pre-build CIM mappings with `/fd-cim <source_id>` for
finer control, or let fd-build-app generate them on-the-fly.

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
    FAKE:<source_id>     (<category>, <format>)  (from fd-cim)
    FAKE:<source_id>     (<category>, <format>)  (auto-generated)
    ...

  Note: "(from fd-cim)" means a pre-generated CIM mapping in fake_data/cim/ was
  used. "(auto-generated)" means fd-build-app generated the mapping on-the-fly
  via rule-based matching + research.

  Monitor stanzas: <N>
  Index: <index_name>
  Log location: bundled inside app at <APP_NAME>/logs/  (turnkey)
  Runtime: bundled inside app at <APP_NAME>/bin/        (re-runnable)
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
mkdir -p fake_data/splunk_app/<APP_NAME>/bin
mkdir -p fake_data/splunk_app/<APP_NAME>/logs
```

If full CIM:
```bash
mkdir -p fake_data/splunk_app/<APP_NAME>/lookups
```

**Final app layout:**
```
<APP_NAME>/
├── README.md
├── default/         (app.conf, inputs.conf, props.conf, transforms.conf, ...)
├── metadata/        (default.meta)
├── lookups/         (asset_inventory.csv, identity_inventory.csv — full CIM only)
├── bin/             (main_generate.py + runtime — for re-generating in-place)
│   ├── main_generate.py
│   ├── config.py
│   ├── time_utils.py
│   ├── world.py
│   ├── manifest.py
│   ├── generators/
│   └── scenarios/   (only if workspace had scenarios)
└── logs/            (pre-generated log files, monitored by inputs.conf)
    └── <category>/<source_id>.log
```

**Note:** All config files (props.conf, transforms.conf, eventtypes.conf,
tags.conf) live in `default/`. We do NOT use `local/` because the generated
TA is a fresh build every time — there's no user customization to preserve.
Splunk treats `default/` as the canonical config location for shipped apps.

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

One monitor stanza per generator. The monitor path uses Splunk's
`$SPLUNK_HOME` substitution so the app is portable across hosts:

```ini
[monitor://$SPLUNK_HOME/etc/apps/<APP_NAME>/logs/<category>/<source_id>.log]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

For generators with `multi_file: True` in SOURCE_META, use a wildcard:
```ini
[monitor://$SPLUNK_HOME/etc/apps/<APP_NAME>/logs/<category>/<source_id>/...]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

**Why `$SPLUNK_HOME`:** Splunk expands this at parse time to the install
root, so the same `inputs.conf` works on any Splunk host without editing
absolute paths. Logs ship inside the app at `<APP_NAME>/logs/`, populated
in step E.14 below.

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
| json | `KV_MODE = json`, `TIME_PREFIX = "timestamp"\s*:\s*"` (or first timestamp field name) |
| kv | `KV_MODE = auto`, `TIME_PREFIX = timestamp=`, `TIME_FORMAT = %Y-%m-%dT%H:%M:%SZ` |
| csv | `INDEXED_EXTRACTIONS = csv`, `HEADER_FIELD_LINE_NUMBER = 1` |
| syslog_bsd | `TIME_FORMAT = %b %d %H:%M:%S` |
| syslog_rfc5424 | `TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3NZ`, `TZ = UTC` |
| cef | `TIME_FORMAT = %b %d %Y %H:%M:%S` |
| xml | `KV_MODE = xml`, `TIME_PREFIX = <Extended_Timestamp>` (or first timestamp tag), `TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%6NZ`, `TZ = UTC` |

Read each generator's `_serialize()` method to determine the correct format.
If the timestamp field name differs from `timestamp`, adjust `TIME_PREFIX`
accordingly.

**CRITICAL — ISO-8601 `Z` suffix is a literal, not a strptime token.**
`%Z` in `TIME_FORMAT` matches *named* timezones like `UTC` or `EST` and
will NOT match a trailing `Z`. To parse `2026-01-01T00:03:13.275303Z`:
- End the format with literal `Z` (e.g. `%Y-%m-%dT%H:%M:%S.%6NZ`).
- Always add `TZ = UTC` so Splunk applies the right offset.
- Use `%3N` for milliseconds, `%6N` for microseconds. Match the precision
  the generator actually emits — read `_serialize()` to confirm.

Never write `%Y-%m-%dT%H:%M:%S.%6N%Z` — it will silently fail to parse and
Splunk falls back to indexing-time.

### E.5 Write default/transforms.conf

```ini
[extract_demo_id_indexed]
REGEX = (?:"demo_id":\s*"([^"]+)"|demo_id=(\S+))
FORMAT = IDX_demo_id::$1$2
WRITE_META = true
DEPTH_LIMIT = 99999
```

**Write this stanza VERBATIM.** Do not interpolate skill arguments, source
IDs, scenario names, or any runtime values into the `REGEX` or `FORMAT`
lines. The regex has two capture groups and `$1$2` concatenates whichever
matched (only one will, since they are alternatives). Any other value in
`FORMAT` breaks indexed-time demo_id extraction.

The regex handles both JSON format (`"demo_id": "value"`) and KV format
(`demo_id=value`). The `WRITE_META = true` directive writes the extracted
value as indexed metadata.

### E.5a Indexed-time field overrides (host + sourcetype routing)

Read each generator's `SOURCE_META` dict and check for two optional keys:
`host_field` (or `host_regex`) and `sourcetype_routing`. These let Splunk
override the default host (forwarder hostname) with a value from inside
the event, and split one log stream into multiple sourcetypes based on
event content.

This step **appends** stanzas to `default/transforms.conf` and **appends**
TRANSFORMS- keys to the matching `[FAKE:<source_id>]` stanza in
`default/props.conf`. Skip a generator entirely if neither optional key
is set.

#### Host override

For each generator with `SOURCE_META["host_field"]` (or `host_regex`):

**If `host_regex` is set**, use it verbatim. **If only `host_field` is set**,
build a default regex based on the generator's format:

| Format | Default host regex from host_field |
|---|---|
| json | `"<host_field>"\s*:\s*"([^"]+)"` |
| kv | `<host_field>=(\S+)` |
| cef | `<host_field>=([^\s\|]+)` |
| syslog_bsd | `<host_field>=(\S+)` |
| syslog_rfc5424 | `<host_field>=(\S+)` |
| xml | `<<host_field>>([^<]+)</<host_field>>` |
| csv | (skip — host should be a column, use INDEXED_EXTRACTIONS) |

Append to `default/transforms.conf`:

```ini
[override_host_<source_id>]
REGEX = <regex>
FORMAT = host::$1
DEST_KEY = MetaData:Host
```

Append `TRANSFORMS-host = override_host_<source_id>` to the
`[FAKE:<source_id>]` stanza in `default/props.conf`. If a TRANSFORMS-demo_id
line already exists, add a SECOND TRANSFORMS- line — they coexist:

```ini
[FAKE:<source_id>]
TRANSFORMS-demo_id = extract_demo_id_indexed
TRANSFORMS-host = override_host_<source_id>
```

#### Sourcetype routing

For each generator with `SOURCE_META["sourcetype_routing"]`:

```python
routing = SOURCE_META["sourcetype_routing"]
# routing == {"field": "LogName", "template": "FAKE:WinEventLog:{value}"}
```

Build the regex from format (same table as host override above) using
`routing["field"]`. The capture group becomes `$1`. Render `routing["template"]`
by replacing the literal `{value}` with `$1`:

```python
format_str = routing["template"].replace("{value}", "$1")
# format_str == "FAKE:WinEventLog:$1"
```

Append to `default/transforms.conf`:

```ini
[route_sourcetype_<source_id>]
REGEX = <regex on routing.field>
FORMAT = <rendered format_str>
DEST_KEY = MetaData:Sourcetype
```

Append to the props stanza:

```ini
[FAKE:<source_id>]
TRANSFORMS-demo_id = extract_demo_id_indexed
TRANSFORMS-routing = route_sourcetype_<source_id>
```

**Concrete example — WinEventLog (KV format, LogName routing,
ComputerName host override):**

```ini
# props.conf
[FAKE:wineventlog]
TRANSFORMS-demo_id = extract_demo_id_indexed
TRANSFORMS-host = override_host_wineventlog
TRANSFORMS-routing = route_sourcetype_wineventlog
KV_MODE = auto
TIME_PREFIX = TimeCreated=
TIME_FORMAT = %Y-%m-%dT%H:%M:%SZ

# transforms.conf
[override_host_wineventlog]
REGEX = ComputerName=(\S+)
FORMAT = host::$1
DEST_KEY = MetaData:Host

[route_sourcetype_wineventlog]
REGEX = LogName=(\S+)
FORMAT = FAKE:WinEventLog:$1
DEST_KEY = MetaData:Sourcetype
```

After Splunk indexes a WinEventLog event with `LogName=Security` and
`ComputerName=BOS-WS-SWILSON01`, the search `host=BOS-WS-SWILSON01
sourcetype=FAKE:WinEventLog:Security` finds it.

#### Defaults from the category table

If a generator does NOT explicitly declare `host_field` in SOURCE_META,
fd-build-app may STILL apply a sensible default based on category. Use
this fallback table (only when the generator's field list contains a
matching field name):

| Category | Default host_field if not set |
|---|---|
| windows | ComputerName (if present in fields) |
| network (fortigate) | devname (if present) |
| network (palo) | dvc (if present) |
| linux | hostname (if present) |
| database (oracle) | Userhost (if present) |

Apply the fallback silently. If neither SOURCE_META nor the fallback
match a real field in the generator, skip host override entirely (the
default Splunk host will be used).

### E.6 Write default/fields.conf

```ini
[IDX_demo_id]
INDEXED = true
```

This declares `IDX_demo_id` as an indexed field, enabling fast searches like
`IDX_demo_id=brute_force`.

### E.7 Append CIM enrichment to default/props.conf (full CIM only)

Skip this step entirely if basic CIM mode.

APPEND one stanza per generator to the EXISTING `default/props.conf` file
created in E.4. Use the Edit tool to add new stanzas at the end of the
file, or re-write the full file with both base parsing AND CIM enrichment
sections combined. Either approach is fine — the result must be a single
`default/props.conf` containing everything.

CIM enrichment from Phase C.

**If `cim_mappings[source_id]` exists (pre-generated by fd-cim):** derive the
stanza directly from the `CIM_MAPPING` dict:
- `fieldalias` dict → `FIELDALIAS-<cim_field> = <generator_field> AS <cim_field>`
- `eval` dict → `EVAL-<cim_field> = <eval_expression>`
- `lookup` dict → `LOOKUP-<key> = <lookup_name> <input_field> AS <match_field> OUTPUTNEW <output_fields>`

**If no pre-generated mapping (auto-generated):** use field aliases and evals
from C.2/C.3 as before.

Example stanza structure (applies to both sources):

```ini
[FAKE:<source_id>]
FIELDALIAS-src = <source_field> AS src
FIELDALIAS-dest = <source_field> AS dest
EVAL-action = case(action=="allow", "allowed", action=="deny", "blocked", action=="success", "success", action=="fail", "failure", 1=1, action)
LOOKUP-asset = asset_inventory ip AS src OUTPUTNEW nt_host, owner, bunit, city
LOOKUP-identity = identity_inventory email AS user OUTPUTNEW identity, first, last, managedBy, priority, bunit
```

Only include FIELDALIAS lines where an actual mapping was found.
Only include EVAL lines where a transformation is needed.
Only include LOOKUP-asset if asset_inventory.csv was generated.
Only include LOOKUP-identity if identity_inventory.csv was generated.

### E.8 Append lookup definitions to default/transforms.conf (full CIM only)

Skip if basic CIM mode.

APPEND to the EXISTING `default/transforms.conf` file created in E.5:

```ini
[asset_inventory]
filename = asset_inventory.csv

[identity_inventory]
filename = identity_inventory.csv
```

Only include stanzas for lookups that were actually generated.

### E.9 Write default/eventtypes.conf (full CIM only)

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

### E.10 Write default/tags.conf (full CIM only)

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

The app is fully self-contained:
- Pre-generated logs ship in `logs/`
- `inputs.conf` monitors `$SPLUNK_HOME/etc/apps/<APP_NAME>/logs/`
- Splunk starts indexing immediately after install + restart

## Re-generating logs

The full generator runtime ships in `bin/`. To produce fresh logs after install:

```bash
cd $SPLUNK_HOME/etc/apps/<APP_NAME>/bin
python3 main_generate.py --days=31 --scenarios=all
```

Output lands in `../logs/<category>/<source_id>.log` and is picked up by
the existing `inputs.conf` monitors. Splunk will index the new lines on
its next file scan (typically within 60 seconds).

Common flags:
- `--days=N` — how many days of history to generate (default 31)
- `--sources=src1,src2` — comma-separated subset (default: all)
- `--scenarios=none|all|<id>` — which scenarios to inject
- `--scale=2.0` — multiply event volume

Re-running overwrites existing files in `logs/`. Splunk's `crcSalt = <SOURCE>`
in `inputs.conf` ensures the file is re-read from the start.

## CIM Alignment

<If full: list CIM models and lookup tables>
<If basic: "Basic mode -- sourcetypes and demo_id extraction only.">

## Generated by

FAKE_DATA plugin -- https://github.com/lyderhansen/splunk-forge
```

### E.14 Copy fake_data/ runtime into bin/ + logs/ payload

This step makes the app self-contained. The trick: mirror the workspace
`fake_data/` package structure inside `bin/` so existing imports
(`from fake_data.config import ...`) keep working unchanged.

Run from the workspace root:

```bash
APP=fake_data/splunk_app/<APP_NAME>

# 1. Mirror the entire fake_data/ package into bin/fake_data/
mkdir -p "$APP/bin/fake_data"
cp fake_data/__init__.py     "$APP/bin/fake_data/__init__.py"
cp fake_data/main_generate.py "$APP/bin/fake_data/main_generate.py"
cp fake_data/config.py        "$APP/bin/fake_data/config.py"
cp fake_data/time_utils.py    "$APP/bin/fake_data/time_utils.py"
cp fake_data/world.py         "$APP/bin/fake_data/world.py"
cp fake_data/manifest.py      "$APP/bin/fake_data/manifest.py"

# 2. Copy generators (skip __pycache__, _template_generator.py)
mkdir -p "$APP/bin/fake_data/generators"
cp fake_data/generators/__init__.py "$APP/bin/fake_data/generators/__init__.py"
for f in fake_data/generators/generate_*.py; do
    cp "$f" "$APP/bin/fake_data/generators/$(basename $f)"
done

# 3. Copy scenarios if they exist
if [ -d fake_data/scenarios ]; then
    mkdir -p "$APP/bin/fake_data/scenarios"
    cp fake_data/scenarios/__init__.py "$APP/bin/fake_data/scenarios/__init__.py" 2>/dev/null
    cp fake_data/scenarios/_base.py    "$APP/bin/fake_data/scenarios/_base.py"    2>/dev/null
    for f in fake_data/scenarios/*.py; do
        name=$(basename "$f")
        if [ "$name" != "__init__.py" ] && [ "$name" != "_base.py" ]; then
            cp "$f" "$APP/bin/fake_data/scenarios/$name"
        fi
    done
fi

# 4. Copy pre-generated logs into logs/
if [ -d fake_data/output ] && [ "$(find fake_data/output -name '*.log' 2>/dev/null | wc -l)" -gt 0 ]; then
    cp -R fake_data/output/* "$APP/logs/" 2>/dev/null
fi

# 5. Drop a thin convenience wrapper at bin/main_generate.py so users
#    can run `python3 main_generate.py` instead of `python3 fake_data/main_generate.py`
cat > "$APP/bin/main_generate.py" <<'WRAPPER'
#!/usr/bin/env python3
"""Convenience wrapper — forwards to fake_data.main_generate."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_data.main_generate import main
sys.exit(main() if callable(main) else 0)
WRAPPER
chmod +x "$APP/bin/main_generate.py"

# 6. Strip __pycache__
find "$APP/bin" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
```

**Patch `bin/fake_data/config.py` so `OUTPUT_BASE` resolves to `<app>/logs/`:**

The workspace `config.py` defines:
```python
OUTPUT_BASE = Path(__file__).resolve().parent / "output"
```
From `bin/fake_data/config.py`, that resolves to `bin/fake_data/output/` —
wrong. Use the Edit tool to rewrite the copied file's `OUTPUT_BASE` to:

```python
OUTPUT_BASE = Path(__file__).resolve().parent.parent.parent / "logs"
```

(`config.py` → `fake_data/` → `bin/` → `<app>/` → `logs/`)

Apply the same fix to the assignment inside `set_output_base()` if it
hardcodes the same expression. Do NOT modify the workspace
`fake_data/config.py` — only the copy under `bin/fake_data/`.

**Verify `main()` is exported.** The wrapper assumes `fake_data.main_generate.main`
is callable. If main_generate.py uses `if __name__ == "__main__":` without a
`main()` function, simplify the wrapper to:

```python
import runpy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
runpy.run_module("fake_data.main_generate", run_name="__main__")
```

### E.15 Verify the in-app runtime

Quick smoke test from the workspace root:

```bash
APP=fake_data/splunk_app/<APP_NAME>
cd "$APP/bin" && python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data import config, world
print('OUTPUT_BASE:', config.OUTPUT_BASE)
print('Users:', len(world.USERS))
assert str(config.OUTPUT_BASE).endswith('/logs'), 'OUTPUT_BASE not patched correctly'
" && cd -
```

Then exercise the orchestrator's `--list` to confirm generators load:

```bash
cd "$APP/bin" && python3 main_generate.py --list && cd -
```

Both checks must pass before proceeding to Phase F. If imports fail,
inspect the patched config.py and the wrapper.

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

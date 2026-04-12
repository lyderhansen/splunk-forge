# fd-build-app Design Spec

## Goal

Generate a complete Splunk Technology Add-on (TA) from a FAKE_DATA workspace. The TA includes inputs.conf monitor stanzas, sourcetype definitions, demo_id indexed field extraction, and optionally full CIM alignment with field aliases, lookups, eventtypes, and tags.

## Architecture

Single SKILL.md that reads workspace state (generators, scenarios, world.py) and generates a complete Splunk app directory + tar.gz package. Uses hybrid CIM mapping: rule-based for common categories, research-subagent for unknowns.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| CIM scope | Full CIM default, ask user if basic is enough | Most value from CIM alignment, but some users just want data in Splunk |
| inputs.conf paths | Configurable, default to workspace output/ | Users may have logs anywhere |
| CIM mapping | Hybrid: rule-based + research for unknowns | Categories map predictably to CIM models |
| App naming | User chooses, default TA-<ORG_NAME> | Flexible |
| Output location | fake_data/splunk_app/ in workspace | Safe default, user copies to Splunk |
| Packaging | tar.gz with Mac artifacts cleaned | Ready for Splunk install |

---

## 1. Invocation

`/fd-build-app [app_name]`

Requires existing workspace with at least one generator.

## 2. Phase A — Pre-flight

1. Find workspace root (`fake_data/manifest.py`, up to 5 levels)
2. Read `fake_data/world.py` — extract ORG_NAME, TENANT, LOCATIONS, USERS, INFRASTRUCTURE (if exists)
3. Scan generators (`fake_data/generators/`) — for each, extract SOURCE_META: source_id, category, description, volume_category
4. Scan scenarios (`fake_data/scenarios/`) — for each, extract SCENARIO_META: scenario_id, demo_id
5. Check `fake_data/output/` — list existing log files per generator
6. Read each generator file to determine:
   - Log format (json, kv, csv, syslog, cef, xml) from `_serialize()` method
   - Field names from `_make_event()` method
   - Output file path from SOURCE_META

If no generators found:
> "No generators found. Run `/fd-add-generator` first."

## 3. Phase B — Configuration

Ask one at a time:

### B.1 App name
> "App name? [TA-<ORG_NAME_UPPER>]"

Normalize: uppercase, replace spaces/special chars with hyphens.

### B.2 Log file location
> "Where are the log files? [<absolute_path_to_workspace>/fake_data/output]"

This becomes the base path for inputs.conf monitor stanzas.

### B.3 Index
> "Splunk index name? [main]"

Used in every inputs.conf monitor stanza.

### B.4 CIM level
> "CIM alignment level?
>   - **full**: Field aliases, lookups, eventtypes, tags — data is Splunk ES ready
>   - **basic**: Just sourcetypes + demo_id extraction — data gets in, you map later
> [full]"

## 4. Phase C — CIM Mapping (if full CIM)

### C.1 Rule-based mapping

For each generator, map category to CIM data model(s):

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

### C.2 Field alias generation

For each generator, read the field names from `_make_event()` and map to CIM fields:

| Generator Field Pattern | CIM Field | Alias Rule |
|---|---|---|
| srcip, src_ip, source_ip | src | FIELDALIAS-src |
| dstip, dst_ip, dest_ip | dest | FIELDALIAS-dest |
| srcport, src_port | src_port | FIELDALIAS-src_port |
| dstport, dst_port | dest_port | FIELDALIAS-dest_port |
| username, user_name, srcuser | user | FIELDALIAS-user |
| action, status | action | EVAL-action (normalize to allowed/blocked/success/failure) |
| sentbyte, bytes_out | bytes_out | FIELDALIAS-bytes_out |
| rcvdbyte, bytes_in | bytes_in | FIELDALIAS-bytes_in |
| duration | duration | FIELDALIAS-duration |
| proto, protocol | transport | EVAL-transport (map int to name) |
| hostname, host, computer | dest | FIELDALIAS-dest |
| severity, level | severity | FIELDALIAS-severity |

### C.3 Research for unknowns (optional)

If a generator has fields that don't match any rule-based pattern, dispatch a sonnet subagent:

```
You are mapping log fields to Splunk CIM (Common Information Model) fields.

Source: <source_id>
Category: <category>
Format: <format>
Fields: <list of field names with types>
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

### C.4 Lookup generation from world.py

**asset_inventory.csv** (from INFRASTRUCTURE, if exists):
```csv
ip,mac,nt_host,dns,owner,priority,lat,long,city,country,bunit,category,pci_domain,is_expected,should_timesync,should_update,requires_av
10.10.1.1,,FW-HQ1-01,,it,medium,,,New York,US,IT,firewall,,,,,
```

**identity_inventory.csv** (from USERS):
```csv
identity,prefix,nick,first,last,suffix,email,phone,managedBy,priority,bunit,category,watchlist,startDate,endDate,work_city,work_country,work_lat,work_long
aaron.wallace,,Aaron,Aaron,Wallace,,aaron.wallace@examplecorp.com,,,medium,engineering,,,,New York,US,,
```

If INFRASTRUCTURE doesn't exist, skip asset_inventory.csv.
If USERS don't have role field, set priority based on department (it=high, others=medium).

## 5. Phase D — Generate App Structure

### D.1 Directory structure

```
fake_data/splunk_app/<APP_NAME>/
├── default/
│   ├── app.conf
│   ├── inputs.conf
│   ├── props.conf
│   ├── transforms.conf
│   └── fields.conf
├── local/                    # only if full CIM
│   ├── props.conf
│   ├── transforms.conf
│   ├── eventtypes.conf
│   └── tags.conf
├── lookups/                  # only if full CIM
│   ├── asset_inventory.csv
│   └── identity_inventory.csv
├── metadata/
│   └── default.meta
└── README.md
```

### D.2 app.conf

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

### D.3 inputs.conf

One monitor stanza per generator output file:

```ini
[monitor://<log_base_path>/<category>/<source_id>.log]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

For generators with `multi_file: True`, use a wildcard:
```ini
[monitor://<log_base_path>/<category>/<source_id>/...]
disabled = false
sourcetype = FAKE:<source_id>
index = <index_name>
crcSalt = <SOURCE>
```

### D.4 default/props.conf

**Wildcard stanza for all FAKE sourcetypes:**
```ini
[FAKE:*]
MAX_DAYS_HENCE = 10000
MAX_DAYS_AGO = 10000
CHARSET = UTF-8
LINE_BREAKER = ([\r\n]+)
SHOULD_LINEMERGE = false
```

**Per-generator stanza:**
```ini
[FAKE:<source_id>]
TRANSFORMS-demo_id = extract_demo_id_indexed
<format-specific settings based on _serialize() format>
```

Format-specific settings:

| Format | Props Settings |
|---|---|
| json | `KV_MODE = json`, `TIME_PREFIX = "timestamp"` or first timestamp field |
| kv | `KV_MODE = auto`, `TIME_FORMAT = %Y-%m-%dT%H:%M:%S` |
| csv | `INDEXED_EXTRACTIONS = csv`, `HEADER_FIELD_LINE_NUMBER = 1` |
| syslog_bsd | `TIME_FORMAT = %b %d %H:%M:%S` |
| syslog_rfc5424 | `TIME_FORMAT = %Y-%m-%dT%H:%M:%S` |
| cef | `TIME_FORMAT = %b %d %Y %H:%M:%S` |
| xml | `KV_MODE = xml` |

### D.5 default/transforms.conf

```ini
[extract_demo_id_indexed]
REGEX = (?:"demo_id":\s*"([^"]+)"|demo_id=(\S+))
FORMAT = IDX_demo_id::$1$2
WRITE_META = true
DEPTH_LIMIT = 99999
```

### D.6 default/fields.conf

```ini
[IDX_demo_id]
INDEXED = true
```

### D.7 local/props.conf (full CIM only)

Per-generator CIM enrichment:
```ini
[FAKE:<source_id>]
FIELDALIAS-src = <source_field> AS src
FIELDALIAS-dest = <source_field> AS dest
EVAL-action = case(...)
LOOKUP-asset = asset_inventory ip AS src OUTPUTNEW nt_host, owner, bunit, city
LOOKUP-identity = identity_inventory email AS user OUTPUTNEW identity, first, last, managedBy, priority, bunit
```

### D.8 local/transforms.conf (full CIM only)

```ini
[asset_inventory]
filename = asset_inventory.csv

[identity_inventory]
filename = identity_inventory.csv
```

### D.9 local/eventtypes.conf (full CIM only)

Per CIM model:
```ini
[fake_<source_id>_traffic]
search = sourcetype="FAKE:<source_id>"
```

### D.10 local/tags.conf (full CIM only)

```ini
[eventtype=fake_<source_id>_traffic]
network = enabled
communicate = enabled
```

### D.11 metadata/default.meta

```ini
[]
access = read : [ * ], write : [ admin ]
export = system
```

### D.12 README.md

Brief description of the app, sourcetypes, and how to install.

## 6. Phase E — Review Gate

```
Splunk App: <APP_NAME>

  Sourcetypes (<N>):
    FAKE:fortigate     (network, kv)
    FAKE:linux          (linux, json)
    ...

  Monitor stanzas: <N>
  Index: <index_name>
  CIM models: Network Traffic, Authentication, ...
  Lookups: asset_inventory (<N> entries), identity_inventory (<N> entries)

  Output:
    fake_data/splunk_app/<APP_NAME>/
    fake_data/splunk_app/<APP_NAME>.tar.gz

Build this app? [yes/edit/cancel]
```

## 7. Phase F — Write Files + Package

1. Create directory structure
2. Write all .conf files using Write tool
3. Generate lookup CSVs from world.py
4. Write README.md
5. Clean Mac artifacts:
   ```bash
   find fake_data/splunk_app/<APP_NAME> -name '.DS_Store' -delete
   find fake_data/splunk_app/<APP_NAME> -name '._*' -delete
   find fake_data/splunk_app/<APP_NAME> -name '__MACOSX' -type d -exec rm -rf {} +
   ```
6. Package:
   ```bash
   cd fake_data/splunk_app && tar -czf <APP_NAME>.tar.gz <APP_NAME>/
   ```
7. Verify:
   ```bash
   tar -tzf fake_data/splunk_app/<APP_NAME>.tar.gz | head -20
   ```

## 8. Phase G — Handoff

```
Splunk app created:
  Directory: fake_data/splunk_app/<APP_NAME>/
  Package:   fake_data/splunk_app/<APP_NAME>.tar.gz

  Sourcetypes: <N>
  Monitor stanzas: <N>
  CIM models: <list>

Install in Splunk:
  Option 1 — Copy directory:
    cp -r fake_data/splunk_app/<APP_NAME> $SPLUNK_HOME/etc/apps/
    $SPLUNK_HOME/bin/splunk restart

  Option 2 — Install package:
    $SPLUNK_HOME/bin/splunk install app fake_data/splunk_app/<APP_NAME>.tar.gz

  Option 3 — Upload via Splunk Web:
    Apps → Manage Apps → Install app from file → <APP_NAME>.tar.gz

Verify:
  index=<index> sourcetype=FAKE:* | stats count by sourcetype
  index=<index> sourcetype=FAKE:* IDX_demo_id=* | stats count by IDX_demo_id
```

## 9. Scope Boundaries

**In scope:**
- fd-build-app SKILL.md
- app.conf, inputs.conf, props.conf, transforms.conf, fields.conf generation
- CIM alignment (FIELDALIAS, EVAL, LOOKUP, eventtypes, tags)
- Lookup generation from world.py (asset_inventory, identity_inventory)
- tar.gz packaging with Mac artifact cleanup
- MAX_DAYS_HENCE / MAX_DAYS_AGO wildcard stanza

**Out of scope:**
- Splunk deployment (user handles installation)
- Dashboard generation
- Saved searches / alerts
- Custom commands
- REST API endpoints
- UCC framework
- Splunkbase packaging (appinspect, icon, screenshots)

---
name: fd-cim
description: Map generator fields to Splunk CIM (Common Information Model). Produces CIM mapping files consumed by fd-build-app.
version: 0.1.0
metadata:
  argument-hint: "<source_id>"
---

# fd-cim -- Map generator fields to Splunk CIM

Map a generator's output fields to Splunk CIM (Common Information Model)
data model fields. Produces `fake_data/cim/<source_id>.py` containing a
`CIM_MAPPING` dict that fd-build-app reads when generating the Splunk TA.

**Key principle:** Rule-based matching handles common fields automatically.
A research subagent fills gaps for domain-specific or ambiguous fields.
The user reviews everything before anything is written.

**Source of truth:** `docs/superpowers/specs/2026-04-12-fd-cim-design.md`

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

Expected invocation: `/fd-cim <source_id>`

If no argument provided, list available generators and prompt:

> "Which generator do you want to map to CIM? Available: <comma-separated list>"

### A.3 Verify generator exists

Check that `fake_data/generators/generate_<source_id>.py` exists.

If it does not:
> "Generator `generate_<source_id>.py` not found. Run `/fd-add-generator <source_id>` first."

### A.4 Read generator metadata

Read `fake_data/generators/generate_<source_id>.py`. Extract:

1. **SOURCE_META dict** -- source_id, category, description, sourcetype
2. **Field names from `_make_event()`** -- scan the function body for all
   keys used in the event dict or format string. Build a flat list:
   `["srcip", "dstip", "srcport", "dstport", "action", ...]`

If `_make_event()` returns a dict, extract the dict keys directly.
If it builds a string (KV or syslog), extract the key names from the format.

### A.5 Check for existing CIM mapping

Check if `fake_data/cim/<source_id>.py` already exists.

If it does:
> "CIM mapping for `<source_id>` already exists at `fake_data/cim/<source_id>.py`.
> Overwrite or abort? [abort]"

If overwrite: continue. If abort: stop.

---

## Phase B -- Rule-based mapping

### B.1 Apply field pattern table

For each field extracted in A.4, attempt to match against this pattern table
(case-insensitive, also match common variants with underscores removed):

| Generator field pattern        | CIM field     | Notes                          |
|-------------------------------|---------------|--------------------------------|
| srcip, src_ip, source_ip      | src           |                                |
| dstip, dst_ip, dest_ip        | dest          |                                |
| srcport, src_port, source_port| src_port      |                                |
| dstport, dst_port, dest_port  | dest_port     |                                |
| sentbyte, bytes_sent, sent    | bytes_out     |                                |
| rcvdbyte, bytes_recv, received| bytes_in      |                                |
| proto, protocol, transport    | transport     |                                |
| username, user, src_user      | user          |                                |
| action, verdict               | action        | Needs EVAL normalization       |
| status, http_status, response | status        |                                |
| url, uri, request_url         | url           |                                |
| method, http_method           | http_method   |                                |
| hostname, host, src_host      | src_host      |                                |
| dsthost, dst_host, dest_host  | dest_host     |                                |
| app, application, service     | app           |                                |
| duration, elapsed             | duration      |                                |
| bytes, total_bytes            | bytes         |                                |
| category, threat_category     | category      |                                |
| severity, risk_level          | severity      |                                |
| msg, message, description     | signature     |                                |
| pid, process_id               | process_id    |                                |
| process, proc, process_name   | process       |                                |
| parent_process, ppid          | parent_process|                                |
| user_agent                    | http_user_agent|                               |
| src_mac, mac_address          | src_mac       |                                |
| dest_mac, dst_mac             | dest_mac      |                                |
| vendor, vendor_name           | vendor        |                                |
| product, product_name         | product       |                                |
| dvc, device, device_name      | dvc           |                                |
| file_name, filename           | file_name     |                                |
| file_path, filepath           | file_path     |                                |
| file_hash, hash, sha256, md5  | file_hash     |                                |
| file_size, size               | file_size     |                                |
| dest_port, dport              | dest_port     |                                |
| src_zone, zone                | src_zone      |                                |
| dest_zone, dst_zone           | dest_zone     |                                |
| direction, dir                | direction     |                                |
| icmp_type                     | icmp_type     |                                |
| icmp_code                     | icmp_code     |                                |
| cve, vuln_id                  | cve           |                                |
| cvss, risk_score              | cvss          |                                |
| answer, dns_answer            | answer        | DNS model                      |
| query, dns_query              | query         | DNS model                      |
| subject, email_subject        | subject       | Email model                    |
| recipient, to                 | recipient     | Email model                    |
| sender, from_address          | src_user      | Email model                    |

Build two lists:
- `mapped`: `[{"field": "srcip", "cim_field": "src", "method": "fieldalias"}, ...]`
- `unmapped`: `["field1", "field2", ...]` -- fields with no rule match

### B.2 Determine CIM data model from category

Use SOURCE_META["category"] to select the primary CIM model:

| Category            | Primary model         | Additional models          |
|---------------------|-----------------------|----------------------------|
| network             | Network_Traffic       |                            |
| firewall            | Network_Traffic       | Intrusion_Detection        |
| cloud               | Authentication        | Change                     |
| windows             | Endpoint              | Authentication             |
| linux               | Performance           | Authentication             |
| web                 | Web                   |                            |
| auth                | Authentication        |                            |
| endpoint            | Endpoint              | Malware                    |
| dns                 | Network_Resolution    |                            |
| email               | Email                 |                            |
| ids / ips           | Intrusion_Detection   | Network_Traffic            |
| proxy               | Web                   | Network_Traffic            |
| vpn                 | Authentication        | Network_Sessions           |
| database            | Databases             |                            |
| dlp                 | Data_Loss_Prevention  |                            |
| vulnerability       | Vulnerabilities       |                            |
| ot                  | Network_Traffic       | Intrusion_Detection        |
| itsm                | Ticket_Management     | Change                     |
| certificate         | Certificates          |                            |
| alerts              | Alerts                |                            |

**CIM field reference:** https://help.splunk.com/en/splunk-enterprise-security-8/common-information-model/5.1/data-models/cim-fields-per-associated-data-model

If category does not match, default to `Network_Traffic` and note it as
uncertain for the research subagent in Phase C.

### B.3 Flag EVAL candidates

Fields mapped to `action` or `status` almost always need an EVAL to normalize
vendor-specific values to CIM-compliant values. Mark these as
`"method": "eval"` and set a placeholder eval expression:

```python
"action": 'case(action=="accept", "allowed", action=="deny", "blocked", 1==1, action)'
```

Add a TODO comment noting that the user should update these with real values
from the generator's field value vocabulary.

---

## Phase C -- Research for unmapped fields

### C.1 Skip if all fields mapped

If `unmapped` list is empty, skip to Phase D.

### C.2 Dispatch sonnet subagent

Use the **Agent tool** with `model: sonnet` to dispatch a research subagent.
The subagent runs in isolated context.

**Subagent prompt:**

```
You are a Splunk CIM (Common Information Model) expert helping map log
generator fields to standard CIM field names.

Source: <source_id>
Category: <SOURCE_META["category"]>
Sourcetype: <SOURCE_META["sourcetype"]>
Description: <SOURCE_META["description"]>
Detected CIM model: <detected_model from Phase B>

Already mapped fields (for context):
<for each mapped field: "  <generator_field> -> <cim_field>">

Unmapped fields that need CIM mapping:
<unmapped field list, one per line>

For each unmapped field, determine:
1. The best matching CIM field name (or "no_cim_match" if none exists)
2. Whether it needs a fieldalias (direct rename) or eval (value transformation)
3. If eval: provide an example eval expression

Return your answer in this EXACT format:

FIELD_MAPPINGS:
<generator_field> | <cim_field_or_no_cim_match> | <fieldalias|eval|none> | <eval_expression_or_empty>
END_FIELD_MAPPINGS

CIM_MODEL_NOTES:
<any notes about the CIM model selection, additional models to consider, or caveats>
END_CIM_MODEL_NOTES

Guidelines:
- Prefer standard CIM field names from the Splunk CIM documentation
- For vendor-specific fields with no CIM equivalent, use "no_cim_match"
- EVAL expressions should use SPL syntax
- If the field value needs normalization (e.g. vendor action -> allowed/blocked),
  provide a case() expression as the eval
- Consider the sourcetype and category context when mapping
- Fields like vendor product, version, or internal IDs often have no CIM match
```

### C.3 Parse subagent response

Parse `FIELD_MAPPINGS:` block into additional mapped/unmapped entries.
Add research results to the `mapped` list (or mark as `no_cim_match`).

If parsing fails, treat all remaining fields as `no_cim_match` and proceed.

---

## Phase D -- Review gate

Display the complete proposed mapping:

```
CIM mapping for: <source_id>
  Model(s): <models list>

  Field aliases (direct rename):
    <generator_field>  ->  <cim_field>
    ...

  Eval fields (computed):
    <cim_field>  =  <eval_expression>
    ...

  No CIM match (will be kept as-is):
    <field1>, <field2>, ...

  Standard lookups (included by default):
    asset_inventory   (src -> ip -> nt_host, owner, bunit, city)
    identity_inventory (user -> email -> identity, first, last, bunit)

  Eventtypes:
    fake_<source_id>_<category>:
      search: sourcetype="<sourcetype>"
      tags: <tag list from model>

Approve this mapping? [yes/edit/cancel]
```

- **yes**: proceed to Phase E
- **edit**: ask what to change, incorporate edits, re-display this gate
- **cancel**: exit without writing anything

---

## Phase E -- Write CIM mapping file

### E.1 Ensure directory exists

```bash
mkdir -p fake_data/cim
```

### E.2 Write mapping file

Write `fake_data/cim/<source_id>.py` with this exact structure:

```python
"""
CIM mapping for <source_id>.

Generated by fd-cim. This file is yours -- edit freely.
fd-build-app reads this file when generating local/props.conf and
local/transforms.conf for the Splunk TA.

Model(s): <models list>
"""

CIM_MAPPING = {
    "source_id": "<source_id>",
    "models": [<quoted model names>],
    "fieldalias": {
        # Direct field renames: generator_field -> CIM_field
        "<generator_field>": "<cim_field>",
        # ... one entry per fieldalias mapping
    },
    "eval": {
        # Computed CIM fields using SPL eval syntax
        "<cim_field>": '<eval_expression>',
        # Standard vendor_product eval
        "vendor_product": '"<SOURCE_META["description"]>"',
        # ... one entry per eval mapping
    },
    "lookup": {
        "asset": {
            "lookup_name": "asset_inventory",
            "input_field": "src",
            "match_field": "ip",
            "output_fields": ["nt_host", "owner", "bunit", "city"],
        },
        "identity": {
            "lookup_name": "identity_inventory",
            "input_field": "user",
            "match_field": "email",
            "output_fields": ["identity", "first", "last", "managedBy", "priority", "bunit"],
        },
    },
    "eventtypes": {
        "fake_<source_id>_<category>": {
            "search": 'sourcetype="<SOURCE_META["sourcetype"]>"',
            "tags": [<tag list from model>],
        },
    },
}
```

**Tag list by model:**

| Model               | Tags                          |
|---------------------|-------------------------------|
| Network_Traffic     | ["network", "communicate"]    |
| Authentication      | ["authentication"]            |
| Endpoint            | ["endpoint"]                  |
| Web                 | ["web"]                       |
| Intrusion_Detection | ["ids", "attack"]             |
| Network_Resolution  | ["network", "dns"]            |
| Email               | ["email"]                     |
| Performance         | ["performance"]               |
| Databases           | ["database"]                  |
| Change              | ["change"]                    |

If `fieldalias` dict is empty, omit the `fieldalias` key entirely.
If `eval` dict has only `vendor_product`, keep it.
Always include the `lookup` block (fd-build-app decides whether to render it).
Always include the `eventtypes` block.

### E.3 Create __init__.py if missing

Check if `fake_data/cim/__init__.py` exists. If not, create it:

```python
# CIM mapping package marker.
```

### E.4 Syntax check

Run via Bash:
```bash
python3 -c "import ast; ast.parse(open('fake_data/cim/<source_id>.py').read()); print('Syntax OK')"
```

If syntax check fails, fix the file and re-check.

---

## Phase F -- Handoff

Print:

```
CIM mapping created: fake_data/cim/<source_id>.py
  Model(s): <models list>
  Aliases:  <count> field mappings
  Evals:    <count> calculated fields
  Lookups:  asset_inventory, identity_inventory

Next: /fd-build-app will use this mapping when generating the Splunk TA.
  Run: /fd-build-app <source_id>
```

If `fake_data/cim/__init__.py` was just created, also print:
```
  Created: fake_data/cim/__init__.py (package marker)
```

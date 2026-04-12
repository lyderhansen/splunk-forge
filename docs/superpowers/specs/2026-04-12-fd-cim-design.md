# fd-cim Design Spec

## Goal

Map a generator's fields to Splunk CIM (Common Information Model) fields. Produces a CIM mapping file that fd-build-app consumes when building the Splunk TA.

## Architecture

`/fd-cim <source_id>` reads the generator's fields, uses rule-based matching + optional research to determine CIM data model and field mappings, and writes `fake_data/cim/<source_id>.py` with a `CIM_MAPPING` dict. fd-build-app reads all files in `fake_data/cim/` when generating local/props.conf.

## Output format

`fake_data/cim/<source_id>.py`:

```python
CIM_MAPPING = {
    "source_id": "fortigate",
    "models": ["Network_Traffic"],
    "fieldalias": {
        "srcip": "src",
        "dstip": "dest",
        "srcport": "src_port",
        "dstport": "dest_port",
        "sentbyte": "bytes_out",
        "rcvdbyte": "bytes_in",
        "proto": "transport",
    },
    "eval": {
        "action": 'case(action=="accept", "allowed", action=="deny", "blocked", 1==1, action)',
        "vendor_product": '"Fortinet FortiGate"',
        "direction": 'if(srcintfrole=="lan", "outbound", "inbound")',
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
        "fake_fortigate_traffic": {
            "search": 'sourcetype="FAKE:fortigate"',
            "tags": ["network", "communicate"],
        },
    },
}
```

## Skill flow

### Phase A — Pre-flight
- Find workspace root
- Verify generator exists: `fake_data/generators/generate_<source_id>.py`
- Read generator file, extract SOURCE_META and field names from `_make_event()`
- Check if CIM mapping already exists: `fake_data/cim/<source_id>.py`

### Phase B — Rule-based mapping
Apply pattern matching (same rules as fd-build-app spec section C.2):
- srcip/src_ip → src
- dstip/dst_ip → dest
- username/user → user
- action/status → action (with EVAL normalization)
- etc.

Determine CIM model from category:
- network → Network_Traffic
- cloud → Authentication, Change
- windows → Endpoint, Authentication
- linux → Performance, Authentication
- web → Web
- etc.

### Phase C — Research (for unmapped fields)
If fields remain unmapped after rules, dispatch sonnet subagent:
- Source_id, category, field list, detected CIM model
- Ask: which CIM fields do these map to? Any EVAL needed?

### Phase D — Review gate
Show complete mapping. User approves or edits.

### Phase E — Write
Write `fake_data/cim/<source_id>.py` with CIM_MAPPING dict.
Create `fake_data/cim/__init__.py` if it doesn't exist.

### Phase F — Handoff
```
CIM mapping created: fake_data/cim/<source_id>.py
  Model: Network_Traffic
  Aliases: 7 field mappings
  Evals: 3 calculated fields
  Lookups: asset_inventory, identity_inventory

Next: /fd-build-app will use this mapping when generating the Splunk TA.
```

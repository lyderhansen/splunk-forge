---
name: fd-cim
description: 'Map generator fields to Splunk CIM. Args: <source_id>. Produces CIM_MAPPING file in fake_data/cim/ for fd-build-app to use.'
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
| hostname, host, src_host      | src_nt_host   | Windows Authentication model — use `dvc` for Network_Traffic |
| dsthost, dst_host, dest_host  | dest_nt_host  | Same — `dest` for Network_Traffic |
| app, application, service     | app           |                                |
| duration, elapsed             | duration      |                                |
| bytes, total_bytes            | bytes         |                                |
| category, threat_category     | category      |                                |
| severity, risk_level          | severity      |                                |
| event_name, event_type, evt   | signature     | `signature` = short symbolic event name, NOT message body. Leave `msg`/`message` unmapped unless you really mean the signature. |
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

### B.1.5 Canonical CIM field reference — NEVER invent field names

Every `cim_field` value written to a FIELDALIAS or used in an EVAL target
MUST be a real CIM field. The research subagent has a tendency to invent
plausible-looking names like `authentication_method_id`, `severity_level`,
`host_category`, or `log_type_id` — none of which exist in the official
CIM. These hallucinations pass syntax checks but silently break
`| datamodel ...` searches.

The lists below are the authoritative field sets per model. If a proposed
CIM field is NOT in the matching model's list, treat it as `no_cim_match`
and leave the generator field unaliased.

**Authentication** (https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

```
action, app, authentication_method, authentication_service, dest,
dest_bunit, dest_category, dest_nt_domain, dest_nt_host, dest_priority,
duration, reason, response_time, signature, signature_id, src,
src_bunit, src_category, src_nt_domain, src_nt_host, src_priority,
src_user, src_user_bunit, src_user_category, src_user_id,
src_user_priority, src_user_type, status, user, user_bunit,
user_category, user_id, user_priority, user_type, vendor_account
```

Common attempted hallucinations — DO NOT USE: `authentication_method_id`,
`logon_type`, `logon_id`, `authentication_package_name`, `auth_type`.

**Endpoint** (https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)

```
action, dest, dest_bunit, dest_category, dest_priority, dest_requires_av,
file_access_time, file_create_time, file_hash, file_modify_time,
file_name, file_path, file_size, object, object_category, object_id,
object_path, parent_process, parent_process_exec, parent_process_guid,
parent_process_id, parent_process_name, parent_process_path,
process, process_exec, process_guid, process_hash, process_id,
process_name, process_path, process_current_directory, registry_hive,
registry_key_name, registry_path, registry_value_data,
registry_value_name, registry_value_type, service, service_dll,
service_dll_path, service_id, service_name, service_path, signature,
signature_id, status, user, vendor_product
```

**Change** (https://docs.splunk.com/Documentation/CIM/latest/User/Change)

```
action, change_type, command, dest, dest_bunit, dest_category,
dest_priority, dvc, object, object_attrs, object_category, object_id,
object_path, result, result_id, src, src_bunit, src_category,
src_priority, src_user, src_user_bunit, src_user_category,
src_user_priority, status, user, user_agent, user_bunit,
user_category, user_priority, vendor_account, vendor_product
```

**Network_Traffic** (https://docs.splunk.com/Documentation/CIM/latest/User/NetworkTraffic)

```
action, app, bytes, bytes_in, bytes_out, channel, dest, dest_bunit,
dest_category, dest_interface, dest_ip, dest_mac, dest_port,
dest_priority, dest_translated_ip, dest_translated_port, dest_zone,
direction, duration, dvc, dvc_bunit, dvc_category, dvc_priority,
dvc_ip, dvc_mac, dvc_zone, flow_id, icmp_code, icmp_type, packets,
packets_in, packets_out, protocol, protocol_version, response_time,
rule, session_id, src, src_bunit, src_category, src_interface,
src_ip, src_mac, src_port, src_priority, src_translated_ip,
src_translated_port, src_zone, ssl_cert_hash, tcp_flag, transport,
tun_dst_ip, tun_dst_port, tun_src_ip, tun_src_port, user,
vendor_product, vlan_id, wifi
```

Note: Network_Traffic does NOT have `src_host`/`dest_host`. The host
fields are `dvc` (the reporting device) and `src`/`dest` (IPs). For
Windows-style hostnames, use Authentication model's `src_nt_host`.

**Web** (https://docs.splunk.com/Documentation/CIM/latest/User/Web)

```
action, app, bytes, bytes_in, bytes_out, cached, cookie, dest,
dest_bunit, dest_category, dest_priority, duration, http_content_type,
http_method, http_referrer, http_referrer_domain, http_user_agent,
http_user_agent_length, response_time, site, src, src_bunit,
src_category, src_priority, status, uri_path, uri_query, uri, url,
url_domain, url_length, user, user_bunit, user_category,
user_priority, vendor_product
```

**Intrusion_Detection** (https://docs.splunk.com/Documentation/CIM/latest/User/IntrusionDetection)

```
action, category, dest, dest_bunit, dest_category, dest_priority,
dvc, dvc_bunit, dvc_category, dvc_priority, file_hash, file_name,
file_path, ids_type, severity, severity_id, signature, signature_id,
src, src_bunit, src_category, src_priority, transport, user,
user_bunit, user_category, user_priority, vendor_account,
vendor_product
```

**Network_Resolution** (DNS)

```
action, additional_answer_count, answer, answer_count, authority_answer_count,
dest, dest_bunit, dest_category, dest_port, dest_priority, dns, duration,
message_type, name, query, query_count, query_type, record_type, reply_code,
reply_code_id, response_time, src, src_bunit, src_category, src_port,
src_priority, transaction_id, transport, ttl, user, vendor_product
```

**Email**

```
action, delay, dest, dest_bunit, dest_category, dest_priority, duration,
file_hash, file_name, file_path, file_size, internal_message_id,
message_id, message_info, orig_dest, orig_recipient, orig_src,
orig_subject, process, process_id, protocol, recipient, recipient_count,
recipient_domain, recipient_status, response_time, retries, return_addr,
sender, sender_domain, signature, signature_id, size, src, src_bunit,
src_category, src_priority, src_user, src_user_bunit, src_user_category,
src_user_domain, src_user_priority, status, status_code, subject, url,
user, user_bunit, user_category, user_priority, vendor_product,
xdelay, xref
```

**Performance** (Linux)

```
cpu_load_mhz, cpu_load_percent, dest, dest_bunit, dest_category,
dest_priority, fan_speed, hypervisor_id, id, inline_power_status,
mem, mem_committed, mem_free, mem_used, parent, power, power_status,
signature, signature_id, src, storage, storage_free, storage_free_percent,
storage_used, storage_used_percent, swap, swap_free, swap_used, tag,
thruput, user, vendor_product
```

**Databases**

```
action, dest, dest_bunit, dest_category, dest_priority, duration,
instance_name, instance_version, lock_mode, lock_session_id,
object, object_attrs, object_category, object_id, object_path,
query, query_id, query_time, records_affected, response_time,
session_id, session_limit, src, src_bunit, src_category, src_priority,
src_user, src_user_bunit, src_user_category, src_user_priority,
statements, status, tablespace_name, tablespace_reclaimable,
tablespace_size, tablespace_status, tablespace_used, user, user_bunit,
user_category, user_priority, vendor_product
```

Note: Databases uses `query` and `query_id` for SQL statements.
`Sql_Text` → `query` is correct. There is no `sql_statement` field.

**Rule:** if a proposed `cim_field` is not in the matching model's list
above, stop and reconsider. Either the field should not be aliased
(leave as vendor field), or it should be an eval target in a different
model. Never invent a field to make a mapping "fit".

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

CRITICAL — NEVER invent CIM field names:
- Only map to fields in the canonical CIM field list for the detected
  model (the parent skill provides this list in Phase B.1.5 of SKILL.md
  — if you haven't been given it explicitly, DEFAULT TO "no_cim_match"
  for any field you're not 100% certain about).
- NEVER write "authentication_method_id", "logon_type", "severity_level",
  "host_category", or any other plausible-sounding field name that isn't
  in the official Authentication / Endpoint / Change / Network_Traffic /
  Web / Intrusion_Detection / Network_Resolution / Email / Performance /
  Databases field lists.
- When unsure, prefer "no_cim_match" over a guess. False mappings
  silently break | datamodel searches at query time.
- For Windows Logon_Type (int 2/3/5/10/etc), do NOT try to alias it —
  leave as the original vendor field, and instead write an EVAL that
  produces `authentication_method` (string, one of
  Interactive/Network/Batch/Service/RemoteInteractive) from the code.
- For Authentication_Package (Kerberos/NTLM/Negotiate), alias to
  `authentication_method` — that IS the canonical field name.
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

### F.1 Print summary

```
CIM mapping created: fake_data/cim/<source_id>.py
  Model(s): <models list>
  Aliases:  <count> field mappings
  Evals:    <count> calculated fields
  Lookups:  asset_inventory, identity_inventory
```

If `fake_data/cim/__init__.py` was just created, also print:
```
  Created: fake_data/cim/__init__.py (package marker)
```

### F.2 Chain to fd-build-app

Ask the user:

> "CIM mapping saved. Build the Splunk app now?
>
>   1. **yes** — Run /fd-build-app to generate the Splunk TA using this CIM mapping
>   2. **skip** — I'll add CIM mappings for more generators first (or build later)
> [2]"

Default is **skip** because users often want to add CIM mappings for
multiple generators before building the final TA.

If **yes**: invoke `/fd-build-app`
If **skip**: stop here.

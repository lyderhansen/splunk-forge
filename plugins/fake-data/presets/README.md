# Presets

Pre-built log format specifications bundled with FAKE_DATA. Each preset is a Python file containing a `PRESET` dict with the same shape as a SPEC produced by `/fd-discover`.

When `/fd-discover <source_id>` runs, it checks this directory first. If a preset exists, research is skipped — the preset is copied directly as the spec, saving time and API calls.

## Available presets (21)

### Network / Firewall (6)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `fortigate` | Fortinet FortiGate | kv | `fgt_traffic` | [2846](https://splunkbase.splunk.com/app/2846) |
| `cisco_asa` | Cisco ASA Firewall | syslog_bsd | `cisco:asa` | [1620](https://splunkbase.splunk.com/app/1620) |
| `cisco_ios` | Cisco Catalyst IOS-XE | syslog_bsd | `cisco:ios` | [7538](https://splunkbase.splunk.com/app/7538) |
| `palo_alto_traffic` | Palo Alto NGFW | csv | `pan:traffic` | [491](https://splunkbase.splunk.com/app/491) |
| `cisco_meraki_mx` | Cisco Meraki MX | kv | `meraki:securityappliance` | [5580](https://splunkbase.splunk.com/app/5580) |
| `checkpoint_traffic` | Check Point | kv | `cp_log` | [4293](https://splunkbase.splunk.com/app/4293) |

### Cloud (5)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `aws_cloudtrail` | AWS CloudTrail | json | `aws:cloudtrail` | [1876](https://splunkbase.splunk.com/app/1876) |
| `aws_guardduty` | AWS GuardDuty | json | `aws:cloudwatch:guardduty` | [1876](https://splunkbase.splunk.com/app/1876) |
| `entraid_signin` | Microsoft Entra ID | json | `azure:aad:signin` | [3110](https://splunkbase.splunk.com/app/3110) |
| `gcp_audit` | Google Cloud Platform | json | `google:gcp:pubsub:audit` | [3088](https://splunkbase.splunk.com/app/3088) |
| `o365_management` | Microsoft 365 | json | `o365:management:activity` | [4055](https://splunkbase.splunk.com/app/4055) |

### Endpoint / Windows (3)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `wineventlog_security` | Windows Security Event Log | kv | `WinEventLog:Security` | [742](https://splunkbase.splunk.com/app/742) |
| `sysmon` | Microsoft Sysmon | kv | `WinEventLog:Microsoft-Windows-Sysmon/Operational` | [5709](https://splunkbase.splunk.com/app/5709) |
| `crowdstrike_falcon` | CrowdStrike Falcon EDR | json | `crowdstrike:falcon` | [5082](https://splunkbase.splunk.com/app/5082) |

### Linux (1)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `linux_auth` | Linux auth.log | syslog_bsd | `linux_secure` | [833](https://splunkbase.splunk.com/app/833) |

### Web (2)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `apache_access` | Apache HTTP Server | combined | `access_combined` | native |
| `nginx_access` | Nginx | combined | `nginx:plus:access` | [3258](https://splunkbase.splunk.com/app/3258) |

### Collaboration (1)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `cisco_webex` | Cisco Webex | json | `cisco:webex:meetings` | GitHub ([cisco-webex-add-on-for-splunk](https://github.com/splunk/cisco-webex-add-on-for-splunk)) — no official Splunkbase app |

### ITSM / ERP / DB (3)
| Source ID | Vendor / Product | Format | Sourcetype | Splunkbase |
|-----------|------------------|--------|------------|------------|
| `servicenow_incident` | ServiceNow ITSM | kv | `snow:incident` | [1928](https://splunkbase.splunk.com/app/1928) |
| `sap_audit` | SAP S/4HANA | pipe-delimited | `sap:auditlog` | [3153](https://splunkbase.splunk.com/app/3153) |
| `mssql_errorlog` | Microsoft SQL Server | text | `mssql:errorlog` | [2648](https://splunkbase.splunk.com/app/2648) |

## Usage

```bash
# Use a preset directly (fd-discover finds it automatically)
/fd-discover fortigate

# Then scaffold the generator
/fd-add-generator fortigate
```

Since the preset already has the complete field spec, `/fd-add-generator` will skip the wizard and generate the Python file directly.

## PRESET dict schema

Each preset file contains a `PRESET = {...}` at module level with this structure:

```python
PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "<source_id>",
        "display_name": "<Display Name>",
        "vendor": "<Vendor>",
        "product": "<Product>",
        "description": "<one-sentence description>",
    },

    "category": "network|cloud|windows|linux|web|itsm|erp",
    "source_groups": ["<list of categories>"],

    "format": {
        "type": "kv|csv|json|syslog_bsd|syslog_rfc5424|cef|xml",
        "confidence": 0.9,
        # format-specific details
    },

    "sourcetype": {
        "name": "<Splunk sourcetype>",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #N) — <vendor>",
    },

    "fields": [
        {"name": "<field>", "type": "<type>", "required": True|False,
         "example": "<example>", "confidence": 0.9, "description": "<description>"},
        # ...
    ],

    "sample_events": [
        {"raw": "<realistic raw log line>"},
        # ...
    ],

    "generator_hints": {
        "module_name": "generate_<source_id>",
        "function_name": "generate_<source_id>_logs",
        "volume_category": "firewall|web|cloud|auth|email|ot",
        "baseline_events_per_day": 500,
        # source-specific hints
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "<url>", "kind": "vendor_doc|splunkbase", "trust": 0.95,
             "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "research_mode": "preset",
        "overall_confidence": 0.9,
    },
}
```

## Contributing a new preset

1. Copy an existing preset as a starting point: `cp presets/fortigate.py presets/my_source.py`
2. Update the `PRESET` dict with your source's details
3. Verify it parses: `python3 -c "import ast; ast.parse(open('presets/my_source.py').read())"`
4. Test with `/fd-discover my_source` in a workspace
5. Submit a pull request

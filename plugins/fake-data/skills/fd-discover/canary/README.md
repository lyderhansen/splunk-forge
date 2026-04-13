# fd-discover canary tests

## Fixtures

- `test_kv_sample.log` — 5-line KV-format firewall log. Fields: date, time, devname, srcip, dstip, action, srcport, dstport, proto, bytes_sent, bytes_recv, policy_id.

## Canary 1: Offline sample (structural assertions)

```
/fd-discover test_kv --sample=skills/fd-discover/canary/test_kv_sample.log --no-search
```

Pass criteria:
- `fake_data/discover/test_kv/SPEC.py` exists
- SPEC["format"]["type"] == "kv"
- SPEC["fields"] contains at least 5 entries
- SPEC["format"]["confidence"] > 0.5
- `fake_data/discover/test_kv/REPORT.md` exists
- `fake_data/discover/test_kv/research.json` exists (empty or minimal)
- No web research was performed

## Canary 2: Research mode (structural assertions only)

```
/fd-discover fortigate --description="FortiGate NGFW traffic logs"
```

Pass criteria:
- `fake_data/discover/fortigate/SPEC.py` exists
- SPEC["source"]["vendor"] is not "unknown"
- SPEC["fields"] has at least 3 entries
- `fake_data/discover/fortigate/research.json` has at least 1 source
- SPEC["research_metadata"]["total_research_time_sec"] > 0

## Canary 3: Offline unknown source

```
/fd-discover custom_thing --sample=skills/fd-discover/canary/test_kv_sample.log --no-search
```

Pass criteria:
- Same as Canary 1
- SPEC["source"]["id"] == "custom_thing"

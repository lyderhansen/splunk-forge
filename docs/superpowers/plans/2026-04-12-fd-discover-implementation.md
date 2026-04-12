# fd-discover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the discover-logformat skill to the FAKE_DATA plugin as `/fd-discover` — a skill that takes a source name (and optional sample/doc/description) and produces a SPEC.py with format analysis, field definitions, and research metadata.

**Architecture:** Claude Code skill (SKILL.md) with subagent-based web research. Research runs in an isolated Agent context to keep the main skill's context clean. Output is a Python module (SPEC.py) importable by fd-add-generator. Preset check shortcuts research when a bundled preset exists.

**Tech Stack:** Claude Code skill (SKILL.md), Agent tool for research subagent, WebSearch/WebFetch for research, Python 3.9+ stdlib for SPEC.py output

**Spec:** `docs/superpowers/specs/2026-04-12-fd-discover-design.md`
**Original spec (still source of truth for unchanged phases):** `docs/superpowers/specs/2026-04-11-discover-logformat-design.md`

---

## File Map

### Files to create

- `.claude/skills/fd-discover/SKILL.md` — the main skill, all 7 phases (A, A.5, B, C, D, E, F)
- `.claude/skills/fd-discover/canary/test_kv_sample.log` — 5-line KV fixture for canary test
- `.claude/skills/fd-discover/canary/README.md` — canary test instructions and pass criteria

### Files to modify

- `.claude/skills/fd-add-generator/SKILL.md` — add SPEC.py auto-detection in Phase A (change #8 from spec)
- `CLAUDE.md` — update skill listing to include fd-discover
- `CHANGEHISTORY.md` — add entry

### Verification approach

Same as X1: canary runs in a scratch workspace. Three canary tests defined in the spec:
1. Sample-based (offline, uses fixture)
2. Research-only (live web search, structural assertions only)
3. Offline unknown source (sample + --no-search)

---

## Task Index

| # | Task | Creates/Modifies | Depends on |
|---|---|---|---|
| 1 | Canary fixture | `.claude/skills/fd-discover/canary/` | — |
| 2 | fd-discover SKILL.md — Phase A + A.5 | `.claude/skills/fd-discover/SKILL.md` (partial) | — |
| 3 | fd-discover SKILL.md — Phase B (research subagent) | SKILL.md (append) | Task 2 |
| 4 | fd-discover SKILL.md — Phase C (analysis) | SKILL.md (append) | Task 3 |
| 5 | fd-discover SKILL.md — Phase D (confidence gates) | SKILL.md (append) | Task 4 |
| 6 | fd-discover SKILL.md — Phase E + F (artifacts + handoff) | SKILL.md (append) | Task 5 |
| 7 | Update fd-add-generator for SPEC.py auto-detection | `.claude/skills/fd-add-generator/SKILL.md` | Task 6 |
| 8 | Update CLAUDE.md + CHANGEHISTORY.md | docs | Task 7 |
| 9 | Canary test — offline sample | — | Task 8 |
| 10 | Canary test — research mode | — | Task 9 |

---

### Task 1: Canary fixture

**Files:**
- Create: `.claude/skills/fd-discover/canary/test_kv_sample.log`
- Create: `.claude/skills/fd-discover/canary/README.md`

- [ ] **Step 1: Create the KV sample fixture**

A 5-line KV-format log file used for offline canary testing. Must contain enough variety to exercise format detection and field extraction.

```
date=2026-01-15 time=09:30:01 devname=FW-01 srcip=10.10.10.55 dstip=203.0.113.42 action=deny srcport=49152 dstport=443 proto=tcp bytes_sent=0 bytes_recv=0 policy_id=47
date=2026-01-15 time=09:30:02 devname=FW-01 srcip=10.10.10.56 dstip=198.51.100.17 action=accept srcport=50211 dstport=80 proto=tcp bytes_sent=1240 bytes_recv=5680 policy_id=12
date=2026-01-15 time=09:30:03 devname=FW-01 srcip=10.10.10.57 dstip=203.0.113.99 action=deny srcport=51003 dstport=3389 proto=tcp bytes_sent=0 bytes_recv=0 policy_id=47
date=2026-01-15 time=09:30:04 devname=FW-01 srcip=10.10.20.12 dstip=198.51.100.8 action=accept srcport=49500 dstport=443 proto=tcp bytes_sent=3200 bytes_recv=15400 policy_id=5
date=2026-01-15 time=09:30:05 devname=FW-01 srcip=10.10.10.58 dstip=203.0.113.200 action=drop srcport=52100 dstport=22 proto=tcp bytes_sent=0 bytes_recv=0 policy_id=99
```

Write to `.claude/skills/fd-discover/canary/test_kv_sample.log`.

- [ ] **Step 2: Create the canary README**

```markdown
# fd-discover canary tests

## Fixtures

- `test_kv_sample.log` — 5-line KV-format firewall log. Fields: date, time, devname, srcip, dstip, action, srcport, dstport, proto, bytes_sent, bytes_recv, policy_id.

## Canary 1: Offline sample (structural assertions)

```
/fd-discover test_kv --sample=.claude/skills/fd-discover/canary/test_kv_sample.log --no-search
```

Pass criteria:
- `fake_data/discover/test_kv/SPEC.py` exists
- SPEC["format"]["type"] == "kv"
- SPEC["fields"] contains at least 5 entries
- SPEC["format"]["confidence"] > 0.5
- `fake_data/discover/test_kv/REPORT.md` exists
- `fake_data/discover/test_kv/research.json` exists (empty or minimal)
- No web research was performed (research_metadata.sources_consulted is empty or only has "explicit" entries)

## Canary 2: Research mode (structural assertions only — content is non-deterministic)

```
/fd-discover fortigate --description="FortiGate NGFW traffic logs"
```

Pass criteria:
- `fake_data/discover/fortigate/SPEC.py` exists
- SPEC["source"]["vendor"] is not "unknown" (research found something)
- SPEC["fields"] has at least 3 entries
- `fake_data/discover/fortigate/research.json` has at least 1 source consulted
- SPEC["research_metadata"]["total_research_time_sec"] > 0

## Canary 3: Offline unknown source

```
/fd-discover custom_thing --sample=.claude/skills/fd-discover/canary/test_kv_sample.log --no-search
```

Pass criteria:
- Same structural assertions as Canary 1
- SPEC["source"]["id"] == "custom_thing"
- No research performed
```

Write to `.claude/skills/fd-discover/canary/README.md`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/fd-discover/canary/
git commit -m "feat: add canary fixture and test criteria for fd-discover"
```

---

### Task 2: fd-discover SKILL.md — Phase A + A.5

**Files:**
- Create: `.claude/skills/fd-discover/SKILL.md`

This task creates the SKILL.md with frontmatter, intro, Phase A (input validation, workspace check, source_id normalization), and Phase A.5 (preset check). Later tasks append phases B through F.

- [ ] **Step 1: Create the SKILL.md with frontmatter + Phase A + Phase A.5**

The subagent must read the fd-discover spec at `docs/superpowers/specs/2026-04-12-fd-discover-design.md` and the original spec at `docs/superpowers/specs/2026-04-11-discover-logformat-design.md` (sections "Invocation & input flags" and "Phase A") for exact details.

The SKILL.md must contain:

**Frontmatter:**
```yaml
---
name: fd-discover
description: Discover and analyze a log format from a source name, sample file, or vendor documentation. Produces a SPEC.py that fd-add-generator can consume.
version: 0.1.0
metadata:
  argument-hint: "<source_id> [--sample=<path>] [--doc=<url>] [--description=<text>] [--no-search]"
---
```

**Phase A — Input validation:**
- Parse `source_id` (required) and flags (--sample, --doc, --ta, --description, --no-search, --batch, --interactive, --threshold, --min-sources, --max-research-time)
- Find workspace root via `fake_data/manifest.py` check (same as fd-add-generator)
- Normalize source_id to snake_case (same rules as fd-add-generator)
- If no input flags given, ask: "Would you like to paste a log sample, provide a doc URL, or should I rely on research only? [paste/url/research-only]"
- Check collision: if `fake_data/discover/<source_id>/SPEC.py` exists, ask: "Discovery for '<source_id>' already exists. 1. Overwrite 2. Keep and abort [1/2]"
- Validate --sample file exists and is readable (if given)

**Phase A.5 — Preset check:**
- Check if `../../../presets/<source_id>.py` exists (relative to SKILL.md)
- If exists: Read it, extract PRESET dict, print "Found bundled preset for '<source_id>'. Skipping research.", proceed to Phase C with preset data
- If not exists: proceed to Phase B

- [ ] **Step 2: Verify frontmatter**

```bash
head -7 .claude/skills/fd-discover/SKILL.md
```

Expected: YAML frontmatter with `name: fd-discover`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/fd-discover/SKILL.md
git commit -m "feat: fd-discover Phase A (input validation) and A.5 (preset check)"
```

---

### Task 3: fd-discover SKILL.md — Phase B (research subagent)

**Files:**
- Modify: `.claude/skills/fd-discover/SKILL.md` (append)

- [ ] **Step 1: Append Phase B to SKILL.md**

Read the fd-discover spec section "4. Research: subagent-based from the start" and the original spec sections "Research pipeline (Phase B)" and "Research loop" for the complete algorithm.

Phase B must contain:

**B.1 — Decide whether research runs:**
- If `--no-search` AND no `--doc` URLs → skip Phase B, proceed to Phase C with empty ResearchFindings
- Otherwise → proceed

**B.2 — Dispatch research subagent:**
- Use the Agent tool with `model: sonnet`
- The prompt to the subagent must include:
  - source_id and any explicit inputs (sample path, doc URLs, description, TA ID)
  - Time budget (default 300 seconds)
  - Research priority order (vendor docs → Splunkbase → sample search → community → fallback)
  - Exact instructions for what to extract: sample log lines, vendor name, product name, description, field hints with descriptions
  - Instruction to return findings as structured text in a specific format
- Wait for subagent completion, parse the returned ResearchFindings

**B.3 — Fetch explicit --doc URLs (if research subagent didn't already):**
- If --doc URLs were provided, ensure they were fetched (subagent should handle this, but verify)

**B.4 — Merge explicit inputs with research findings:**
- User-provided samples have highest trust
- Research samples are secondary
- Deduplicate samples by exact line match

**ResearchFindings struct** (mental model, returned as text by subagent):
```
samples_found: list of raw log lines (max 20)
vendor_hint: string or null
product_hint: string or null
description_hint: string or null
field_hints: list of {name, description} pairs
sources_consulted: list of {url, kind, trust, retrieved_at, note?}
elapsed_sec: number
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/fd-discover/SKILL.md
git commit -m "feat: fd-discover Phase B (subagent-based research)"
```

---

### Task 4: fd-discover SKILL.md — Phase C (analysis)

**Files:**
- Modify: `.claude/skills/fd-discover/SKILL.md` (append)

- [ ] **Step 1: Append Phase C to SKILL.md**

Read the original spec sections "Format detection", "Field extraction", "Sourcetype suggestion priority" for the exact algorithms. Also read the fd-discover spec section "Metadata-only fallback".

Phase C must contain:

**C.1 — Build working sample set:**
- Union of user-provided samples (from --sample) and research-found samples (from ResearchFindings.samples_found)
- Deduplicate by exact line match, user samples first
- Cap at 500 lines
- If empty → metadata-only mode (see below)

**C.2 — Format detection:**
The exact 8-pattern table from the original spec. Test each line, first pattern with >50% match rate wins. If <10 samples, cap confidence at 0.7.

| Order | Pattern | Format |
|---|---|---|
| 1 | starts with `{`, ends with `}` | json |
| 2 | `^CEF:\d` | cef |
| 3 | `^<\d+>` | syslog_rfc5424 |
| 4 | `^\w{3} \d+ \d+:\d+:\d+` | syslog_bsd |
| 5 | `\w+=\S+( \w+=\S+)+` | kv |
| 6 | CSV header detection or `^\d+,.*,.*` | csv |
| 7 | starts with `<` containing `>` | xml |
| 8 | none | unknown |

**C.3 — Field extraction** per format (exact rules from original spec: JSON flatten, KV split on =, CEF header+extensions, CSV header detection, syslog KV-on-body, XML tag names, unknown → raw_line only).

Type inference: ipv4 (dotted quad), ipv6 (colon hex), iso_timestamp (ISO 8601 pattern), int, float, bool, string.

Field confidence: frequency ≥0.8 → 1.0, 0.5-0.8 → 0.8, 0.3-0.5 → 0.6, <0.3 → 0.5. +0.2 bonus if confirmed by research field_hints.

**C.4 — Sourcetype suggestion:**
1. If research found a Splunkbase TA sourcetype → use it (highest confidence)
2. CIM convention: `vendor:product:datasource` if vendor and product known
3. Fallback: `<source_id>:events` (confidence 0.6)

**C.5 — Category mapping** (same table as fd-add-generator):
firewall/asa/fortinet/palo → network, aws/gcp/azure → cloud, etc.

**C.6 — Volume category mapping** (same as fd-add-generator)

**C.7 — Build Findings struct** with all derived values. Calculate overall_confidence as mean of format, sourcetype, and mean field confidence. In metadata-only mode, exclude format confidence from mean.

**Metadata-only mode:** When combined sample set is empty:
- format.type = "unknown", format.confidence = 0.0
- Fields from ResearchFindings.field_hints only (confidence 0.7 each)
- Skip C.2 format detection
- sample_events = empty

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/fd-discover/SKILL.md
git commit -m "feat: fd-discover Phase C (format analysis + metadata-only fallback)"
```

---

### Task 5: fd-discover SKILL.md — Phase D (confidence gates)

**Files:**
- Modify: `.claude/skills/fd-discover/SKILL.md` (append)

- [ ] **Step 1: Append Phase D to SKILL.md**

Read the original spec section "Confidence gates and interactive Q&A (Phase D)".

Phase D must contain:

**D.1 — Auto-triggered gates** (only fire when confidence < threshold, default 0.75):

| Gate | Fires when | Example question |
|---|---|---|
| Format gate | format.confidence < threshold | "I'm 65% confident this is KV format, 35% suggests JSON. Which is correct?" |
| Sourcetype gate | sourcetype.confidence < threshold | "Two candidates: `fortinet:fortigate:traffic` or `syslog:fortigate`. Which?" |
| Field gate | any field confidence < 0.5 | "`policy_id` appeared in 3/20 samples. Keep as optional field or drop?" |
| Unresolved gate | unresolved_questions non-empty | Show each unresolved question from research |

**D.2 — Mandatory Q&A** (always asked):

1. **Baseline volume:** "Default is 1000 events/day with automatic weekend/time-of-day variation. OK, or another number? [1000]"
2. **Scenarios:** Show discovered/suggested scenarios (if any). Ask user to confirm existing + propose new. Capture under generator_hints.scenarios.

**D.3 — Batch mode:** When --batch is set, skip all D.1 and D.2 questions. Use defaults. Mark in REPORT.md as "assumed (batch mode)".

**Minimal questions principle:** Do NOT ask about things that have high confidence. Only surface the low-confidence areas. If everything is above threshold, Phase D becomes just the two mandatory questions.

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/fd-discover/SKILL.md
git commit -m "feat: fd-discover Phase D (confidence gates + Q&A)"
```

---

### Task 6: fd-discover SKILL.md — Phase E + F (artifacts + handoff)

**Files:**
- Modify: `.claude/skills/fd-discover/SKILL.md` (append)

- [ ] **Step 1: Append Phase E and F to SKILL.md**

Read the fd-discover spec sections "3. Artifact placement" and "6. Infrastructure suggestion in handoff" and "7. Handoff points to /fd-add-generator".

**Phase E — Artifact writing:**

E.1 — Create directory structure:
```
fake_data/discover/<source_id>/
fake_data/discover/<source_id>/samples/
```

E.2 — Write `fake_data/discover/<source_id>/__init__.py` (empty)

E.3 — Write `fake_data/discover/<source_id>/SPEC.py`:
- Python module with `SPEC = { ... }` dict
- Full schema as shown in the fd-discover spec section "2. SPEC format"
- All values from the Findings struct
- Use `repr()` for string values to get proper Python quoting

E.4 — Write `fake_data/discover/<source_id>/REPORT.md`:
- Human-readable narrative using the template from the original spec section "REPORT.md template"
- Sections: Summary, Format, Sourcetype, Fields table, Sources Consulted, Unresolved Questions, User-confirmed defaults, Next Steps

E.5 — Copy sample files to `fake_data/discover/<source_id>/samples/`:
- User-provided sample → `user_provided.log`
- Research-found samples → `research_sample_01.log`, etc.

E.6 — Write `fake_data/discover/<source_id>/research.json`:
- JSON file (stdlib json.dumps) with full audit trail
- Contains: every URL fetched, timestamp, response status, token count estimate
- This is the one place where we DO use JSON (not Python) — it's an audit log, not config

E.7 — Verify SPEC.py is importable:
```bash
python3 -c "import sys; sys.path.insert(0, '.'); from fake_data.discover.<source_id>.SPEC import SPEC; print(f'OK: {len(SPEC[\"fields\"])} fields, confidence {SPEC[\"research_metadata\"][\"overall_confidence\"]}')"
```

**Phase F — Handoff:**

F.1 — Check infrastructure implications:
- Read `fake_data/world.py`, find INFRASTRUCTURE list
- Map source category to implied infra role (network→firewall, windows→directory_server, web→web_server, ot→plc)
- Check which locations have that role
- If any missing: ask one yes/skip question

F.2 — If user says yes to infra: read world.py, add new infra entry to INFRASTRUCTURE list, write back

F.3 — Print handoff message:
```
Discovery complete for '<source_id>' (confidence: <score>)

Artifacts written to fake_data/discover/<source_id>/:
  - SPEC.py        (machine-readable, for fd-add-generator)
  - REPORT.md      (human-readable summary)
  - samples/       (<N> log samples)
  - research.json  (audit trail)

Next step: review REPORT.md, then run:
  /fd-add-generator <source_id>
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/fd-discover/SKILL.md
git commit -m "feat: fd-discover Phase E (artifacts) and Phase F (handoff with infra suggestion)"
```

---

### Task 7: Update fd-add-generator for SPEC.py auto-detection

**Files:**
- Modify: `.claude/skills/fd-add-generator/SKILL.md`

- [ ] **Step 1: Add SPEC.py check to Phase A of fd-add-generator**

Read the current `.claude/skills/fd-add-generator/SKILL.md` Phase A section.

After A.4 (collision check) and before A.5 (decide mode), insert a new step:

**A.4b — Check for existing SPEC.py:**

Check if `fake_data/discover/<source_id>/SPEC.py` exists.

If it exists:
- Read it using the Read tool
- Print: "Found discovery spec at `fake_data/discover/<source_id>/SPEC.py` (confidence: <overall_confidence>). Using it to scaffold the generator."
- **Skip** Phase B entirely (no sample parsing, no wizard questions)
- Use SPEC data to populate the Findings struct directly:
  - format, category, volume_category from SPEC
  - fields from SPEC["fields"]
  - sample_events from SPEC["sample_events"]
  - description from SPEC["source"]["description"]
- Proceed to Phase C (review gate) with pre-populated Findings

If not exists: continue to A.5 (decide mode) as before.

This means fd-add-generator now has THREE modes:
1. **From SPEC** (SPEC.py exists) → auto-detected, no questions
2. **Sample mode** (--sample given, no SPEC.py) → format detection
3. **Wizard mode** (no sample, no SPEC.py) → interactive questions

- [ ] **Step 2: Also update the sample mode to use fd-discover internally**

In Phase B.sample, add a note at the top:

> "When --sample is provided and fd-discover is available, this mode internally follows the same format detection and field extraction logic as fd-discover Phase C. In a future update, this mode may dispatch fd-discover with --no-search instead of duplicating the analysis logic."

This is a documentation note only — no code change. The actual delegation to fd-discover will happen when we refactor in a future plan.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/fd-add-generator/SKILL.md
git commit -m "feat: fd-add-generator auto-detects SPEC.py from fd-discover"
```

---

### Task 8: Update CLAUDE.md + CHANGEHISTORY.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `CHANGEHISTORY.md`

- [ ] **Step 1: Update CLAUDE.md**

In the directory layout, update the fd-discover line from "future (X2)" to show it's implemented:

```
│       ├── fd-discover/         # ✅ X2 — log format discovery with research
│       │   └── SKILL.md
```

- [ ] **Step 2: Update CHANGEHISTORY.md**

Add entry at top:

```markdown
## 2026-04-12 ~HH:MM UTC — fd-discover: log format discovery skill
Files: `.claude/skills/fd-discover/SKILL.md`, `.claude/skills/fd-discover/canary/`,
       `.claude/skills/fd-add-generator/SKILL.md` (updated for SPEC.py auto-detection)

Ports the discover-logformat skill from TA-FAKE-TSHRT to the FAKE_DATA plugin.
Subagent-based research (vendor docs, Splunkbase, sample search), format detection
(8 patterns), field extraction, confidence gates, SPEC.py output. Preset check
shortcuts research when bundled preset exists. Infrastructure suggestions in handoff.
fd-add-generator updated to auto-detect SPEC.py and skip wizard when available.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md CHANGEHISTORY.md
git commit -m "docs: update project docs for fd-discover completion"
```

---

### Task 9: Canary test — offline sample

**Files:** None — verification task (interactive).

- [ ] **Step 1: Run canary in existing workspace**

From the plugin repo's tmp/ workspace (or create a fresh one with `/fd-init`):

```
/fd-discover test_kv --sample=.claude/skills/fd-discover/canary/test_kv_sample.log --no-search
```

- [ ] **Step 2: Verify structural assertions**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data.discover.test_kv.SPEC import SPEC
print(f'format: {SPEC[\"format\"][\"type\"]}')
print(f'confidence: {SPEC[\"format\"][\"confidence\"]}')
print(f'fields: {len(SPEC[\"fields\"])}')
print(f'research sources: {len(SPEC[\"research_metadata\"][\"sources_consulted\"])}')
assert SPEC['format']['type'] == 'kv', f'Expected kv, got {SPEC[\"format\"][\"type\"]}'
assert len(SPEC['fields']) >= 5, f'Expected >=5 fields, got {len(SPEC[\"fields\"])}'
assert SPEC['format']['confidence'] > 0.5
print('CANARY 1: PASS')
"
```

- [ ] **Step 3: Record result**

If pass: note in CHANGEHISTORY.md. If fail: fix and re-run.

---

### Task 10: Canary test — research mode

**Files:** None — verification task (interactive, requires web access).

- [ ] **Step 1: Run research canary**

```
/fd-discover fortigate --description="FortiGate NGFW traffic logs"
```

- [ ] **Step 2: Verify structural assertions**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from fake_data.discover.fortigate.SPEC import SPEC
print(f'vendor: {SPEC[\"source\"][\"vendor\"]}')
print(f'fields: {len(SPEC[\"fields\"])}')
print(f'research sources: {len(SPEC[\"research_metadata\"][\"sources_consulted\"])}')
print(f'research time: {SPEC[\"research_metadata\"][\"total_research_time_sec\"]}s')
assert SPEC['source']['vendor'] != 'unknown', 'Research should have found vendor'
assert len(SPEC['fields']) >= 3, f'Expected >=3 fields, got {len(SPEC[\"fields\"])}'
assert SPEC['research_metadata']['total_research_time_sec'] > 0
print('CANARY 2: PASS')
"
```

Note: Content assertions are structural only (vendor is not "unknown", fields exist). Exact values are non-deterministic because web search results vary.

- [ ] **Step 3: Record result**

If pass: fd-discover is complete. If fail: investigate which phase failed and fix.

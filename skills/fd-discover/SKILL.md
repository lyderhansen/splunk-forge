---
name: fd-discover
description: Discover and analyze a log format from a source name, sample file, or vendor documentation. Produces a SPEC.py that fd-add-generator can consume.
version: 0.1.0
metadata:
  argument-hint: "<source_id> [--sample=<path>] [--doc=<url>] [--description=<text>] [--no-search]"
---

# fd-discover — Log format discovery

Analyze a data source and produce a structured SPEC.py with format analysis, field definitions, and research metadata. The SPEC.py is consumable by `/fd-add-generator` for automatic generator scaffolding.

**Key principle:** Research is the default mode. Most users arrive with just a source name ("I want Palo Alto logs") and no sample file. The skill must produce a usable SPEC from research alone.

**Source of truth for unchanged algorithms:** `docs/superpowers/specs/2026-04-11-discover-logformat-design.md`

---

## Phase A — Input validation

### A.1 Find workspace root

Check for `fake_data/manifest.py` in the current directory and up to 5 parent directories. If not found:

> "No FAKE_DATA workspace found. Run `/fd-init` first."

### A.2 Parse arguments

```
/fd-discover <source_id> [--sample=<path>] [--doc=<url>] [--ta=<id>]
             [--description=<text>] [--no-search] [--batch] [--interactive]
             [--threshold=0.75] [--min-sources=5] [--max-research-time=300]
```

`source_id` is required. If missing:
> "Missing source_id. Usage: `/fd-discover <source_id> [--sample=<path>] [--doc=<url>] [--description=<text>]`"

### A.3 Normalize source_id

Same rules as fd-add-generator:
- Lowercase
- Replace non-alphanumeric runs with underscore
- Strip leading/trailing underscores
- Reject if empty or starts with digit

### A.4 Handle no-input case

If no `--sample`, `--doc`, `--ta`, or `--description` is given, ask once:

> "No inputs provided. How should I discover the format for '<source_id>'?
>   1. **Paste a log sample** — I'll read the file and analyze it
>   2. **Provide a doc URL** — I'll fetch vendor documentation
>   3. **Research only** — I'll search the web using the source name
>
> Pick 1, 2, or 3: [3]"

If 1: ask for file path, set as --sample.
If 2: ask for URL, set as --doc.
If 3: proceed with source_id as the only search seed.

### A.5 Check collision

Check if `fake_data/discover/<source_id>/SPEC.py` exists.

If it exists:
> "Discovery for '<source_id>' already exists (created <date from SPEC>).
>   1. **Overwrite** — run discovery again, replace old artifacts
>   2. **Keep and abort** — leave existing discovery
>
> Pick 1 or 2: [2]"

If overwrite: delete `fake_data/discover/<source_id>/` and proceed.
If abort: stop.

### A.6 Validate --sample file

If `--sample=<path>` given:
- Resolve relative to current working directory
- Verify file exists and is readable
- Read at most 500 lines
- If file is empty or doesn't exist: error and stop

---

## Phase A.5 — Preset check

Before doing any research, check if a bundled preset exists in the plugin repo.

Read (using the Read tool): `../../presets/<source_id>.py` (relative to this SKILL.md)

**If file exists:**
- Parse it — it contains a `PRESET` dict with the same shape as SPEC
- Print: "Found bundled preset for '<source_id>'. Skipping research."
- Use PRESET data as the Findings (no research, no format detection needed)
- Set `research_metadata.sources_consulted = [{"kind": "preset", "trust": 1.0}]`
- Proceed directly to **Phase D** (confidence gates — presets may still have gaps the user should confirm)

**If file does not exist:** proceed to Phase B.

---

## Phase B — Research (subagent-based)

### B.1 Decide whether research runs

- If `--no-search` is true AND no `--doc` URLs → skip Phase B entirely. Proceed to Phase C with empty ResearchFindings.
- If `--no-search` is true but `--doc` URLs exist → fetch only the explicit docs (no web search). Use WebFetch on each URL.
- Otherwise → dispatch research subagent.

### B.2 Dispatch research subagent

Use the **Agent tool** with `model: sonnet` to dispatch a research subagent. The subagent runs in isolated context so web-fetch results don't pollute the main skill's context.

**Subagent prompt template:**

```
You are researching the log format for a data source called "<source_id>".

Goal: Find enough information to produce a structured format specification.
You need: sample log lines, vendor name, product name, field definitions,
log format type (JSON, KV, CSV, CEF, syslog, XML), and sourcetype conventions.

Explicit inputs provided by the user:
- Sample file: <path or "none">
- Doc URLs: <urls or "none">
- Description: <text or "none">
- Splunkbase TA ID: <id or "none">

Time budget: <budget> seconds. Work efficiently.

Research priority (follow this order, stop when you have high confidence):

1. If doc URLs were provided, fetch them first using WebFetch. Extract any
   log examples, field tables, and format descriptions.

2. Search vendor documentation:
   WebSearch "<source_id> log format" (try adding site:docs.<vendor>.com if
   you know the vendor)
   Fetch the top 2-3 most relevant results.

3. Search Splunkbase for an existing TA:
   WebSearch "<source_id> splunkbase splunk add-on"
   If found, fetch the app page and look for README content, props.conf
   field extractions, and sourcetype definitions.

4. Search for sample log lines:
   WebSearch "<source_id> sample logs example"
   Look for raw log lines in documentation, training materials, or blog posts.

5. Community forums (only if steps 1-4 gave thin results):
   WebSearch "<source_id> log format site:community.splunk.com"

Return your findings in this exact format:

RESEARCH_FINDINGS:
vendor: <vendor name or "unknown">
product: <product name or "unknown">
description: <one-sentence description or "unknown">
format_hint: <json|kv|csv|cef|syslog|xml|unknown>

SAMPLE_LINES:
<paste each raw log line on its own line, max 20 lines>
END_SAMPLE_LINES

FIELD_HINTS:
<field_name> | <description>
<field_name> | <description>
END_FIELD_HINTS

SOURCES_CONSULTED:
<url> | <kind: vendor_doc|splunkbase|search_result|community> | <trust: 0.0-1.0>
END_SOURCES_CONSULTED

SPLUNKBASE_SOURCETYPE: <sourcetype name if found, or "none">
```

### B.3 Parse subagent response

When the subagent returns, parse its response into a `ResearchFindings` struct:

- `samples_found`: lines between SAMPLE_LINES and END_SAMPLE_LINES
- `vendor_hint`: from RESEARCH_FINDINGS vendor field
- `product_hint`: from RESEARCH_FINDINGS product field
- `description_hint`: from RESEARCH_FINDINGS description field
- `format_hint`: from RESEARCH_FINDINGS format_hint field
- `field_hints`: parse FIELD_HINTS section into `[{name, description}]` pairs
- `sources_consulted`: parse SOURCES_CONSULTED into `[{url, kind, trust}]` with `retrieved_at` = current UTC
- `splunkbase_sourcetype`: from SPLUNKBASE_SOURCETYPE field
- `elapsed_sec`: time between dispatch and completion

### B.4 Fetch explicit --doc URLs (if not already fetched by subagent)

If `--doc` URLs were provided AND `--no-search` was set (subagent didn't run), fetch each URL directly using WebFetch with prompt:

> "Extract log format information: example log events, field names with descriptions, vendor name, product name, format type."

Add results to ResearchFindings.

### B.5 Build combined sample set

Merge samples from all sources:
1. User-provided samples (from --sample file) — first, highest trust
2. Research-found samples (from subagent) — second
3. Deduplicate by exact line match
4. Cap at 500 lines total

Pass ResearchFindings and combined sample set to Phase C.

---

## Phase C — Format analysis

### C.0 Check for metadata-only mode

If the combined sample set from Phase B is **empty** (user gave only --description, and research found no raw log lines — only field descriptions and vendor text):

- Set `format.type = "unknown"` and `format.confidence = 0.0`
- Skip C.1 and C.2 entirely
- Populate fields from `ResearchFindings.field_hints[]` — each hint becomes a field with `type: "string"`, `required: False`, `confidence: 0.7`
- Jump to C.4 (sourcetype suggestion)

If samples exist, proceed normally through C.1-C.6.

### C.1 Format detection

Test each sample line against these patterns **in order**. Count matches per pattern. The first pattern where more than 50% of lines match wins.

| Order | Pattern | Format value |
|---|---|---|
| 1 | Line starts with `{` and ends with `}` | `json` |
| 2 | Line matches `^CEF:\d` | `cef` |
| 3 | Line matches `^<\d+>` | `syslog_rfc5424` |
| 4 | Line matches `^\w{3} \d+ \d+:\d+:\d+` | `syslog_bsd` |
| 5 | Line contains `\w+=\S+( \w+=\S+)+` | `kv` |
| 6 | First line looks like CSV headers or lines match `^\d+,.*,.*` | `csv` |
| 7 | Line starts with `<` and contains `>` | `xml` |
| 8 | None of the above | `unknown` |

Confidence = matches / total_lines. If fewer than 10 lines available, cap confidence at 0.7.

If research provided a `format_hint`, use it to break ties when two formats are close.

### C.2 Field extraction

Based on the detected format, extract fields from sample lines:

**json:** Parse each line with `json.loads()`. Flatten nested objects with dot-path keys (e.g. `event.user.id`). For each value, infer type:
- Matches `^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$` → `ipv4`
- Matches colon-separated hex → `ipv6`
- Matches `^\d{4}-\d{2}-\d{2}T` → `iso_timestamp`
- Python int → `int`
- Python float → `float`
- Python bool → `bool`
- Otherwise → `string`

**kv:** Split each line on whitespace, then split each token on the first `=`. Left = field name, right = value. Same type inference as json.

**csv:** First line as header if all values are identifiers (alphanumeric + underscore), otherwise generate `col_1`, `col_2`, etc. Infer types from remaining rows.

**cef:** Parse 7-field CEF header (`CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity`). Parse extension block as KV pairs.

**syslog_rfc5424 / syslog_bsd:** Attempt KV parsing on the message body. If KV yields fields, use them. Otherwise: single `raw_line` field of type `string`.

**xml:** Extract top-level tag names as field names. All types default to `string`.

**unknown:** Single field: `raw_line` of type `string`.

### C.3 Field confidence

For each field, compute frequency (fraction of lines where it appears):
- frequency >= 0.8 → confidence `1.0`, required `True` (if >=0.9)
- 0.5 <= frequency < 0.8 → confidence `0.8`
- 0.3 <= frequency < 0.5 → confidence `0.6`
- frequency < 0.3 → confidence `0.5`

**Research bonus:** If a field name matches a `field_hint` from research, add +0.2 to its confidence (cap at 1.0).

Record one example value per field.

### C.4 Sourcetype suggestion

Priority order:
1. If research found a Splunkbase TA sourcetype (`splunkbase_sourcetype` != "none") → use it, confidence 0.95
2. If vendor and product are known → CIM convention `vendor:product:datasource`, confidence 0.8
3. Fallback → `<source_id>:events`, confidence 0.6

### C.5 Category mapping

Same table as fd-add-generator. Check tokens in source_id:

| Tokens | Category |
|---|---|
| firewall, asa, fortinet, palo, meraki, catalyst | network |
| aws, gcp, azure, entra, okta | cloud |
| wineventlog, sysmon, perfmon, mssql | windows |
| linux, syslog | linux |
| access, apache, nginx, web | web |
| exchange, office, webex, teams | collaboration |
| sap, erp | erp |
| servicenow, itsm | itsm |
| cybervision, plc, scada, ot | ot |
| no match | unknown (ask user) |

### C.6 Build Findings

Assemble all derived values into a Findings struct:
- `source`: id, display_name, vendor, product, description
- `format`: type, confidence, timestamp info if detected
- `sourcetype`: name, confidence
- `category`, `volume_category`
- `fields`: list of {name, type, required, example, confidence}
- `sample_events`: up to 3 raw lines with parsed representation
- `generator_hints`: suggested module name, function name, volume category, baseline 1000/day
- `research_metadata`: sources consulted, elapsed time, overall confidence
- `overall_confidence`: mean of format.confidence, sourcetype.confidence, and mean field confidence. In metadata-only mode, exclude format.confidence.

---

## Phase D — Confidence gates + Q&A

### D.1 Auto-triggered gates

Only fire when the relevant confidence is below threshold (default 0.75). Skip gates where confidence is sufficient. The goal is **minimal questions**.

| Gate | Fires when | What to ask |
|---|---|---|
| Format | format.confidence < threshold | "I'm <N>% confident the format is <type>. Does that look right, or is it something else?" |
| Sourcetype | sourcetype.confidence < threshold | "Suggested sourcetype: `<name>`. Is that correct, or do you have a different one?" |
| Fields | any field confidence < 0.5 | "These fields had low confidence: <list>. Keep them, or remove?" |
| Unresolved | unresolved questions from research | Show each question, ask user to resolve |

Present all gates **in one message** as a numbered list. User answers everything at once.

### D.2 Mandatory Q&A

Always asked (unless --batch):

1. **Baseline volume:** "Default is 1000 events/day with automatic variation. OK? [1000]"
2. **Scenarios:** If research found applicable scenarios, list them. Otherwise just note "No scenarios suggested yet — you can add them later with /fd-add-scenario."

### D.3 Batch mode

When `--batch` is set: skip all D.1 and D.2 questions. Use defaults. Mark every default in REPORT.md under a "Assumed defaults (batch mode)" section.

---

## Phase E — Artifact writing

Write ALL files using the **Write tool**. Do not use Bash for file creation.

### E.1 Create directory structure

Create (via Bash mkdir):
```bash
mkdir -p fake_data/discover/<source_id>/samples
```

### E.2 Write __init__.py

Write `fake_data/discover/__init__.py` (empty, if it doesn't exist).
Write `fake_data/discover/<source_id>/__init__.py` (empty).

### E.3 Write SPEC.py

Write `fake_data/discover/<source_id>/SPEC.py` with the full SPEC dict. Use the schema shape from the fd-discover design spec. All string values properly quoted. Generated_at = current UTC ISO-8601. Generated_by = "fd-discover v0.1.0".

The file must be importable:
```python
"""Discovery spec for <source_id>. Generated by fd-discover."""

SPEC = {
    "schema_version": 1,
    "generated_at": "<UTC ISO-8601>",
    "generated_by": "fd-discover v0.1.0",
    "source": { ... },
    "category": "<category>",
    "source_groups": ["<category>"],
    "format": { ... },
    "sourcetype": { ... },
    "fields": [ ... ],
    "sample_events": [ ... ],
    "generator_hints": { ... },
    "research_metadata": { ... },
}
```

### E.4 Write REPORT.md

Write `fake_data/discover/<source_id>/REPORT.md` with human-readable narrative:

```markdown
# Discovery Report: <source_id>

**Generated:** <UTC timestamp>
**Overall confidence:** <score>

## Summary
<one-paragraph description of what was discovered>

## Format
- Type: <format.type>
- Confidence: <format.confidence>

## Sourcetype
- Suggested: `<sourcetype.name>`
- Confidence: <sourcetype.confidence>

## Fields (<N> total)
| Name | Type | Required | Confidence | Example |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Sources Consulted
| # | URL | Kind | Trust |
|---|---|---|---|
| ... | ... | ... | ... |

## Next Steps
1. Review SPEC.py and correct any guesses
2. Run `/fd-add-generator <source_id>`
```

### E.5 Copy samples

If user provided --sample: copy to `fake_data/discover/<source_id>/samples/user_provided.log`
If research found samples: write to `fake_data/discover/<source_id>/samples/research_sample_01.log`, etc.

### E.6 Write research.json

Write `fake_data/discover/<source_id>/research.json` using json.dumps (stdlib). Contents:
```json
{
    "source_id": "<source_id>",
    "started_at": "<UTC>",
    "completed_at": "<UTC>",
    "sources_consulted": [ ... ],
    "total_samples_found": <N>,
    "research_mode": "<full|no-search|preset|doc-only>"
}
```

### E.7 Verify SPEC.py

Run via Bash:
```bash
python3 -c "import sys; sys.path.insert(0, '.'); from fake_data.discover.<source_id>.SPEC import SPEC; print(f'OK: {len(SPEC[\"fields\"])} fields')"
```

If this fails, fix the SPEC.py and re-verify.

---

## Phase F — Handoff

### F.1 Check infrastructure implications

Read `fake_data/world.py` and check the `INFRASTRUCTURE` list.

Map the discovered source's category to an implied infrastructure role:

| Category | Implied role |
|---|---|
| network | firewall |
| cloud | proxy |
| windows | directory_server |
| web | web_server |
| ot | plc |
| other | no suggestion |

Check which locations have that role in INFRASTRUCTURE. If any are missing, ask:

> "Your workspace has <role> devices at <locations_with_role> but not at <locations_without_role>. Add <role> to <missing_location>? [yes/skip]"

If yes: read world.py, find the INFRASTRUCTURE list, append a new entry with appropriate hostname pattern and IP, write world.py back.

If skip: note in REPORT.md as "Infrastructure suggestion: <role> missing at <location>, user skipped."

### F.2 Print handoff

```
Discovery complete for '<source_id>' (confidence: <overall_confidence>)

Artifacts written to fake_data/discover/<source_id>/:
  - SPEC.py        (machine-readable, for fd-add-generator)
  - REPORT.md      (human-readable summary)
  - samples/       (<N> log samples)
  - research.json  (audit trail)
```

### F.3 Offer to save as preset

**Only offer this if Phase A.5 did NOT find a bundled preset AND
`overall_confidence >= 0.8`.** We don't want to save low-quality research
as a preset.

Check: `../../presets/<source_id>.py` exists? If yes, skip this step.

If no (fresh research) AND confidence is high enough, ask:

> "This research produced a high-confidence SPEC.py (<overall_confidence>).
> Want to save it as a bundled preset so future runs of `/fd-discover
> <source_id>` skip research entirely?
>
>   1. **yes** — Save to `presets/<source_id>.py` (in the plugin repo).
>      Future runs of /fd-discover will find it instantly.
>   2. **skip** — Keep it local to this workspace only
> [1]"

If **yes**:

1. Read the generated `fake_data/discover/<source_id>/SPEC.py`
2. Copy the content to `../../presets/<source_id>.py` (relative to this SKILL.md — i.e. the plugin repo's presets/ directory)
3. Replace `SPEC = {` with `PRESET = {` in the copied file
4. Replace the docstring at the top:
   ```python
   """Bundled preset for <source_id>. Generated from /fd-discover research.
   Used when --preset is selected or when no --sample/--doc is provided."""
   ```
5. Update `research_metadata.research_mode` to `"preset"` in the copied file
6. Print:
   ```
   Saved preset: presets/<source_id>.py
   This preset is now available in the plugin repo. To share it with
   others, commit it and push:
     git add presets/<source_id>.py
     git commit -m "Add preset for <source_id>"
     git push
   ```

If **skip**: continue to F.4.

### F.4 Chain to fd-add-generator

Ask the user:

> "Want me to scaffold the generator now? SPEC.py is ready, so I can
> create `fake_data/generators/generate_<source_id>.py` immediately.
>
>   1. **yes** — Run /fd-add-generator <source_id> now
>   2. **skip** — I'll do it myself later
> [1]"

If **yes**: invoke `/fd-add-generator <source_id>` directly. The generator
skill will auto-detect the SPEC.py and skip its wizard.

If **skip**: stop here. The user can run the command manually.

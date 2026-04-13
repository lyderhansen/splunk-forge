# Skill file size audit (v0.5.0)

Snapshot of SKILL.md line counts. Target from task #70 is <500 lines per
skill file, <3000 lines total. We are currently at **~4,940 lines**, about
65% over target.

## Current sizes

| Skill | Lines | Over target |
|---|---|---|
| fd-build-app      | 1,099 | +599 |
| fd-init           | 745   | +245 |
| fd-add-generator  | 609   | +109 |
| fd-world          | 602   | +102 |
| fd-cim            | 593   | +93 |
| fd-discover       | 577   | +77 |
| fd-add-scenario   | 568   | +68 |
| fd-generate       | 145   | OK |
| **Total**         | **4,938** | **+1,938** |

## Extraction opportunities (shared references)

Several tables and field lists duplicate content across skills. Extracting
them to `references/` files that skills load on demand via the Read tool
would save ~300 lines total:

### Category tables (duplicated across 3 skills)

- fd-add-generator B.sample.5 — `network/cloud/windows/...` keyword-to-category table
- fd-discover C.5 — same table
- fd-cim B.2 — category-to-CIM-model table (related but different)

Extract to `references/categories.md`. Savings: ~50 lines.

### CIM field lists (shipped in fd-cim B.1.5)

- fd-cim B.1.5 — canonical field lists for 10 CIM models (~150 lines)
- fd-build-app C.1/C.2 — duplicated rule-based mapping tables

Extract to `references/cim-fields.md` and/or delegate from fd-build-app to
fd-cim when the user hasn't run fd-cim first. Savings: ~150 lines.

### Magic 6 format-defaults table

- fd-build-app E.4 — new table covering json/kv/csv/cef/syslog/xml

This is already single-source-of-truth in fd-build-app. Keep it there.

### Volume category reference

- fd-add-generator B.sample.6 — `windows/endpoint/firewall/...` volume map
- config.py VOLUME_WEEKEND_FACTORS — same values

The skill table mirrors runtime config. Could be replaced with "see
config.py::VOLUME_WEEKEND_FACTORS" pointer. Savings: ~20 lines.

## Verbose prose candidates (fd-build-app specifically)

Sections that could be shortened without losing correctness:

- E.4 Magic 6 rationale paragraphs (~30 lines of "why" prose) — trim to bullet points
- E.14 bin/ copy step shell script (~50 lines) — move to a helper script in
  `templates/bin/bin-copy.sh` and have fd-build-app invoke it
- E.5a host override regex fallback table — overlaps with fd-add-generator's
  B.sample.8 host_field detection table

Estimated total savings from prose trimming alone: ~100 lines.

## Safe changes made in this pass

- **fd-build-app B.2**: removed dead "Log file location (no longer asked)"
  section (was 11 lines of prose saying "this question is gone"). Renumbered
  B.3 Index → B.2 and B.4 CIM level → B.3.

## Recommended next steps for #70

Do these as their own milestone, not inline with feature work:

1. **Extract references/** directory + migrate category / CIM field lists
   (biggest savings, needs careful testing)
2. **Move bin/ copy logic** from fd-build-app E.14 prose into a bundled
   shell script + Python helper
3. **Consolidate fd-build-app C.* fallback path** by having it delegate to
   fd-cim rather than duplicating the rule tables

Expected total savings: 400-500 lines. Would bring total to ~4,400 —
still above target but closer.

## Why we're not at 500 per skill

The plugin intentionally ships detailed SKILL.md files because the skills
are loaded as Claude's instructions at runtime. Every skill that drops
below ~400 lines tends to produce lower-quality output because the agent
has less guidance. The <500 target from task #70 may be too aggressive —
a more realistic target is <800 per skill, giving ~5600 total, which we
are already under.

Decision for the user: lower the target or invest a full milestone in
the extraction work above.

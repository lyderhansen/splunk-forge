# Change History

Newest entries first.

## 2026-04-15 — v0.6.1 — fd-build-app packaging fix for macOS AppleDouble

- Fix Splunk "archive contains more than one immediate subdirectory" rejection caused by BSD tar emitting `._<APP_NAME>` AppleDouble entries from extended attributes during archiving. OneDrive-synced source trees were the common trigger.
- `fd-build-app` Phase F.1: add `xattr -cr` to strip extended attributes before tar.
- `fd-build-app` Phase F.2: prefix tar command with `COPYFILE_DISABLE=1` so BSD tar does not synthesize AppleDouble entries from xattrs.
- `fd-build-app` Phase F.3: hard-fail the build if the produced tarball contains more than one top-level entry or a top-level entry that is not `<APP_NAME>`. Prevents shipping packages Splunk will reject.

## 2026-04-14 20:46 UTC — v0.6.0 — Narrative foundation (#79a)

- Add `templates/runtime/narrative.py` stub module with ACTORS, STORYLINE, JOIN_KEYS constants and get_actor/get_phase/has_scenario_events helpers. Shipped empty; populated by fd-init when the user opts into a demo narrative.
- Add `templates/runtime/correlation.py` with deterministic `active_user(day, hour, users, bucket_hours=4)` and `active_host(day, hour, infra, category)` fallback pickers. Used when narrative.py is absent or has empty ACTORS.
- Add `data/world_enrich.py` with `enrich_user`, `enrich_infra`, and batch helpers that add `entra_object_id`, `aws_principal_id`, `vpn_ip`, `employee_id`, `mac_address`, and `asset_tag` with deterministic seeding on `(workspace_name, identifier, field)`.
- Add pytest harness at `plugins/fake-data/tests/` with full coverage for the three new modules (36 tests).
- No skill changes in this release. Generator, fd-init wizard, and scenario/build-app integration land in #79b–e.

## 2026-04-12 ~10:00 UTC — Bundled presets library
Files: `presets/*.py` (20 files), `presets/README.md`

Added 19 bundled log format presets covering the most common Splunk
demo sources: Fortinet FortiGate, Cisco ASA/IOS/Meraki, Palo Alto,
Check Point, AWS CloudTrail/GuardDuty, Azure Entra ID, GCP audit,
Microsoft 365, Windows Security, Sysmon, CrowdStrike Falcon, Linux
auth.log, Apache/Nginx, ServiceNow, SAP, MSSQL. Each preset contains
complete field definitions, realistic sample events, and Splunkbase
TA references. fd-discover automatically uses these when available,
skipping research and saving ~60-90 seconds per source.

## 2026-04-12 ~09:00 UTC — fd-cim: CIM field mapping skill
Files: `.claude/skills/fd-cim/SKILL.md`, `docs/superpowers/specs/2026-04-12-fd-cim-design.md`

Maps generator fields to Splunk CIM data models. Rule-based pattern matching
with sonnet research fallback for unmapped fields. Produces CIM_MAPPING files
in fake_data/cim/ that fd-build-app consumes when generating local/props.conf
with FIELDALIAS, EVAL, LOOKUP, eventtypes, and tags.

## 2026-04-12 ~08:00 UTC — fd-build-app: Splunk TA generation
Files: `.claude/skills/fd-build-app/SKILL.md`

Generates a complete Splunk Technology Add-on from workspace state.
Produces app.conf, inputs.conf, props.conf (with MAX_DAYS_HENCE/AGO
wildcard for synthetic data), transforms.conf (demo_id indexed extraction),
fields.conf, and optional full CIM alignment with FIELDALIAS, EVAL, LOOKUP,
eventtypes, tags, and lookup CSVs from world.py. Packages as tar.gz with
Mac artifact cleanup.

## 2026-04-12 ~07:00 UTC — fd-generate + TUI: generation interfaces
Files: `.claude/skills/fd-generate/SKILL.md`, `templates/runtime/tui_generate.py`,
       `templates/runtime/main_generate.py` (--tui flag)

Two interfaces for running log generation: curses-based TUI (tui_generate.py)
with 3-section layout, dependency auto-inclusion, and inline config editing;
and fd-generate Claude Code skill with wizard-based source/scenario selection.
main_generate.py updated with --tui flag to launch TUI directly.

## 2026-04-12 ~06:00 UTC — fd-world: interactive world.py editing
Files: `.claude/skills/fd-world/SKILL.md`

Interactive CRUD skill for viewing and modifying world.py after init.
Add/edit/remove users, locations, and infrastructure with review gates.
Direct file editing preserves manual changes. Handles both enriched and
basic world.py variants.

## 2026-04-12 ~05:00 UTC — fd-add-scenario: scenario system
Files: `.claude/skills/fd-add-scenario/SKILL.md`, `templates/scenarios/_base.py`,
       `templates/scenarios/__init__.py`, `templates/runtime/config.py`,
       `templates/generators/_template_generator.py`

Adds the scenario system to FAKE_DATA. BaseScenario with auto-resolver handles
both enriched and basic world.py. discover_scenarios() replaces the expand_scenarios
placeholder. Template generator updated with active scenario injection hook.
fd-add-scenario skill provides research-based scenario creation (subagent) with
phases A-G: pre-flight, research, source matching, review gate, code generation
with runtime bootstrap, verification, and handoff.

## 2026-04-12 ~03:00 UTC — fd-discover: log format discovery skill
Files: `.claude/skills/fd-discover/SKILL.md`, `.claude/skills/fd-discover/canary/`,
       `.claude/skills/fd-add-generator/SKILL.md` (updated for SPEC.py auto-detection)

Initial implementation of the discover-logformat skill for the FAKE_DATA plugin.
Subagent-based research (vendor docs, Splunkbase, sample search), format detection
(8 patterns), field extraction, confidence gates, SPEC.py output. Preset check
shortcuts research when bundled preset exists. Infrastructure suggestions in handoff.
fd-add-generator updated to auto-detect SPEC.py and skip wizard when available.

## 2026-04-12 ~01:30 UTC — Plan X1: Framework core + init + add-generator
Files: `.claude/skills/init/SKILL.md`, `.claude/skills/add-generator/SKILL.md`,
       `templates/runtime/{config,time_utils,main_generate}.py`,
       `templates/generators/_template_generator.py`,
       `data/{names_sample,country_ip_ranges}.py`, `presets/`

First functional version of the FAKE_DATA plugin. Users can run `/fake-data:init`
to create a workspace and `/fake-data:add-generator` to scaffold generators.
Includes working `main_generate.py` orchestrator with filesystem-based discovery,
topological dependency sorting, and progress display. All runtime code is
stdlib-only Python 3.9+. Config uses Python modules (not YAML/JSON).

## 2026-04-11 ~18:35 UTC — Plugin scaffold
Files: `.claude-plugin/plugin.json`, `README.md`, `CLAUDE.md`, `CHANGEHISTORY.md`, `.gitignore`, empty directory structure.

Initial scaffold for the FAKE_DATA plugin. Creates the canonical Claude Code plugin manifest, project guide for future Claude Code sessions, and the directory skeleton for skills, templates, specs, and plans. No functional code yet.

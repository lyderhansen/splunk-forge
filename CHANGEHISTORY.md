# Change History

Newest entries first.

## 2026-04-12 ~03:00 UTC — fd-discover: log format discovery skill
Files: `.claude/skills/fd-discover/SKILL.md`, `.claude/skills/fd-discover/canary/`,
       `.claude/skills/fd-add-generator/SKILL.md` (updated for SPEC.py auto-detection)

Ports the discover-logformat skill from TA-FAKE-TSHRT to the FAKE_DATA plugin.
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

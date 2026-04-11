# CLAUDE.md — Project Guide for FAKE_DATA plugin

## What this is

**FAKE_DATA** is a standalone Claude Code plugin (name on disk: `fake-data`) that helps users generate synthetic log data for Splunk. It ships skills to:

1. **Discover** log formats from vendor docs, samples, or free-text (`discover-logformat`)
2. **Scaffold** Python generators from discovered specs (`add-generator`)
3. **Author** scenarios (attack paths, ops incidents) (`add-scenario`)
4. **Run** the generators to produce log files (`generate-logs`)
5. **Init** a new FAKE_DATA workspace in an empty repo (`init`)

## Hard constraints

- **No references to any specific organization.** This plugin is inspired by — but MUST be usable without — The FAKE T-Shirt Company project. Do not hardcode "Boston", "Atlanta", "Austin", "Detroit", "Alex Miller", "FW-EDGE-01", or any other FAKE T-Shirt specifics into plugin code, templates, or skills. Use placeholders and example values in documentation only.
- **Template-only runtime in v1.** When a user runs the init skill, templates are COPIED into their repo. There is no import from FAKE_DATA at runtime. Each user owns their scaffolded code outright.
- **Plugin name vs brand.** On disk and in manifests the name is `fake-data` (lowercase, hyphenated, matches Claude Code plugin conventions). In docs, README, and user-facing strings, refer to the plugin as "FAKE_DATA" as a brand mark.

## Documentation language

All markdown files, code comments, and docstrings MUST be written in English.

## Change history

All meaningful changes MUST be documented in `CHANGEHISTORY.md`, newest first, with UTC date/time and a short description.

## Directory layout (planned)

```
fake-data/
├── .claude-plugin/
│   └── plugin.json              # plugin manifest
├── .claude/
│   └── skills/                  # the skills this plugin ships
│       ├── init/
│       ├── discover-logformat/
│       ├── add-generator/
│       ├── add-scenario/
│       └── generate-logs/
├── templates/
│   ├── runtime/                 # Python files copied into user repo
│   │   ├── time_utils.py
│   │   ├── config.py
│   │   ├── world_loader.py
│   │   └── main_generate.py
│   ├── generators/
│   │   └── _template_generator.py
│   └── schema/
│       ├── world.yaml.example
│       ├── sources.yaml.example
│       └── scenarios.yaml.example
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── README.md
├── CLAUDE.md                    # this file
├── CHANGEHISTORY.md
└── LICENSE
```

## Design process

This plugin is built using the superpowers workflow: brainstorming → spec → plan → subagent-driven execution. Specs live in `docs/superpowers/specs/`, plans in `docs/superpowers/plans/`. Every meaningful task is committed atomically.

## Relationship to The FAKE T-Shirt Company

The FAKE T-Shirt Company Splunk TA (lives at `../../../GIT-TA-FAKE-TSHRT/The-Fake-T-Shirt-Company/` relative to this file) contains the original implementation of the four skills and the generator framework. Use it as INSPIRATION only. Do not copy files directly — reimplement cleanly in this plugin. The final milestone of this plugin is to migrate The FAKE T-Shirt Company to consume this plugin as its runtime, proving the decoupling works.

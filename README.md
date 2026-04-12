# FAKE_DATA

> An A-to-Z Claude Code plugin for generating synthetic Splunk data.

FAKE_DATA helps you build a fictional world (organization, locations, users, infrastructure) and then research, scaffold, and run Python generators that produce realistic log events for Splunk ingestion. It covers the entire pipeline from "install plugin" to "data in Splunk" — including scenario-driven attack and ops incident simulation, interactive world editing, and Splunk TA generation.

## Pipeline

```
/fd-init  →  /fd-discover  →  /fd-add-generator  →  /fd-add-scenario  →  /fd-generate  →  /fd-build-app
   ↓              ↓                  ↓                     ↓                   ↓               ↓
 world.py      SPEC.py        generator.py          scenario.py          log files        Splunk TA
```

## Skills

| Skill | What it does |
|-------|-------------|
| `/fd-init` | Create a workspace with a fictional org — world.py with users, locations, infrastructure, network config. Quick/custom/just-data modes. Researches real companies to prefill defaults. |
| `/fd-discover` | Research a log format (e.g. "fortigate") using vendor docs, Splunkbase, and samples. Produces a SPEC.py with fields, format, and confidence scores. |
| `/fd-add-generator` | Scaffold a Python log generator from a SPEC.py or interactive wizard. Auto-detects format, fields, and volume patterns. |
| `/fd-add-scenario` | Create multi-phase scenarios (attacks, ops incidents, network issues) with research-driven event generation. Events are correlated across generators via `demo_id`. |
| `/fd-world` | View and edit the organization's world state. Add/edit/remove users, locations, and infrastructure with review gates. |
| `/fd-generate` | Guided generation wizard. Also ships a curses TUI (`python3 fake_data/tui_generate.py`) for offline interactive use. |
| `/fd-build-app` | Generate a Splunk Technology Add-on (TA) with inputs.conf, props.conf, transforms.conf, CIM alignment, and tar.gz packaging. |

## Architecture

### Template-only runtime

When `/fd-init` runs, it copies Python templates into the user's repo. There is no runtime dependency on FAKE_DATA — the user owns all generated code. This means:

- No pip packages, no virtual environments
- stdlib-only Python 3.9+
- Works offline after init (generators, TUI, main_generate.py)
- Claude Code skills assist with scaffolding, not execution

### Workspace structure

```
your-repo/
└── fake_data/
    ├── manifest.py          # workspace marker + metadata
    ├── world.py             # org, users, locations, infrastructure, network
    ├── config.py            # volume patterns, output paths, scenario discovery
    ├── time_utils.py        # timestamp formatters
    ├── main_generate.py     # orchestrator (filesystem discovery, topo sort)
    ├── tui_generate.py      # curses TUI for interactive generation
    ├── generators/
    │   ├── generate_fortigate.py   # each generator has SOURCE_META
    │   ├── generate_linux.py
    │   └── ...
    ├── scenarios/
    │   ├── _base.py                # BaseScenario with auto-resolver
    │   ├── brute_force.py          # each scenario has SCENARIO_META
    │   └── ...
    ├── output/                     # generated log files
    │   ├── network/fortigate.log
    │   └── ...
    └── splunk_app/                 # generated Splunk TA
        ├── TA-YOURORG/
        └── TA-YOURORG.tar.gz
```

### Key patterns

**Filesystem discovery:** Generators and scenarios are auto-discovered by scanning their directories for `SOURCE_META` / `SCENARIO_META` dicts. No central registry — add a file and it's found.

**World state binding:** Scenarios use a config dataclass with `"auto"` sentinel values. The `BaseScenario._resolve_auto_values()` method maps these to real users, hosts, and IPs from `world.py` at instantiation. Attack scenarios prefer admin/IT users; ops scenarios pick servers.

**Scenario correlation:** Every scenario event includes a `demo_id` field. The Splunk TA extracts this as an indexed field (`IDX_demo_id`) for fast `tstats` correlation across sourcetypes.

**Research-driven scaffolding:** `/fd-discover` and `/fd-add-scenario` use Claude subagents to research vendor documentation, log formats, attack techniques, and CIM mappings. Results are structured and parsed — the user gets working code, not just documentation.

**Dependency management:** Generators declare `depends_on` in SOURCE_META. The orchestrator topologically sorts them before execution. The TUI auto-includes dependencies with `[+]` markers.

## Quick start

```bash
# 1. Install the plugin (from the fake-data directory)
cd fake-data

# 2. Create a workspace in any empty directory
cd /path/to/your/repo
/fd-init

# 3. Discover and create a generator
/fd-discover fortigate
/fd-add-generator fortigate

# 4. Create a scenario
/fd-add-scenario brute_force

# 5. Generate logs
python3 fake_data/main_generate.py --days=7 --scenarios=brute_force

# 6. Build Splunk app
/fd-build-app
```

## Design process

This plugin is built using the superpowers workflow: brainstorming → spec → plan → subagent-driven execution. Design documents live in `docs/superpowers/specs/`, implementation plans in `docs/superpowers/plans/`.

## Lineage

FAKE_DATA is a standalone reimplementation of the skills and framework originally built inside the [FAKE T-Shirt Company](https://github.com/lyderhansen/The-Fake-T-Shirt-Company) Splunk TA. The existing FAKE T-Shirt project is the first intended *user* of this plugin — not its parent.

## License

MIT

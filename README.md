# fake-data — FAKE_DATA plugin

> An A-to-Z Claude Code plugin for generating synthetic Splunk log data.

**Plugin name:** `fake-data` (on disk, in manifests)
**Brand name:** FAKE_DATA (in docs, user-facing strings)

FAKE_DATA helps you build a fictional world (organization, locations, users, infrastructure) and then research, scaffold, and run Python generators that produce realistic log events for Splunk ingestion. It covers the entire pipeline from "install plugin" to "data in Splunk" — including scenario-driven attack and ops incident simulation, interactive world editing, Splunk CIM alignment, and Splunk TA generation.

## Installation

This repo is structured as a **Claude Code marketplace** (named `splunk-forge`) containing one plugin (`fake-data`). Pick the install method that fits your situation.

### Option 1 — Install via Claude Code plugin manager (public repo)

If you have access to the GitHub repo, install directly from the URL:

1. In Claude Code, run `/plugin`
2. Go to the **Marketplaces** tab → **Add Marketplace**
3. Paste: `lyderhansen/splunk-forge` (or full URL: `https://github.com/lyderhansen/splunk-forge`)
4. Press Enter — Claude Code clones the marketplace
5. Go to the **Discover** tab → search "fake-data" → Install
6. Restart Claude Code (or run `/reload-plugins`)

### Option 2 — Manual install (private repo, no GitHub access needed)

If the repo is private or you have a local clone:

```bash
# 1. Clone (or pull latest) into the marketplaces directory
git clone https://github.com/lyderhansen/splunk-forge.git \
          ~/.claude/plugins/marketplaces/splunk-forge

# OR if you already have a local copy elsewhere, symlink it:
ln -s /path/to/your/fake-data \
      ~/.claude/plugins/marketplaces/splunk-forge

# 2. In Claude Code, register the marketplace:
#    /plugin → Marketplaces → Add Marketplace → ~/.claude/plugins/marketplaces/splunk-forge

# 3. Install the plugin:
#    /plugin → Discover → fake-data → Install for you (user scope)

# 4. Restart Claude Code or /reload-plugins
```

**Updating later:**
```bash
cd ~/.claude/plugins/marketplaces/splunk-forge && git pull
# Then in Claude Code: /reload-plugins
```

### Option 2b — From a downloaded ZIP file

If you don't have git installed, or you got the plugin as a ZIP file (e.g.
GitHub's "Download ZIP" button), you can install manually:

```bash
# 1. Download the ZIP from GitHub
#    Go to: https://github.com/lyderhansen/splunk-forge
#    Click: Code → Download ZIP
#    Save to: ~/Downloads/fake-data-main.zip

# 2. Remove any old version of the marketplace
rm -rf ~/.claude/plugins/marketplaces/splunk-forge

# 3. Unzip and rename
unzip ~/Downloads/fake-data-main.zip -d ~/Downloads/
mv ~/Downloads/fake-data-main ~/.claude/plugins/marketplaces/splunk-forge

# 4. Verify the structure
ls ~/.claude/plugins/marketplaces/splunk-forge/.claude-plugin/marketplace.json
ls ~/.claude/plugins/marketplaces/splunk-forge/plugins/fake-data/.claude-plugin/plugin.json
# Both files should exist

# 5. In Claude Code:
#    /plugin → Marketplaces → Add Marketplace → ~/.claude/plugins/marketplaces/splunk-forge
#    /plugin → Discover → fake-data → Install for you
#    Restart Claude Code or run /reload-plugins
```

**Important:** The folder MUST be renamed from `fake-data-main` (the GitHub ZIP default) to `splunk-forge`. The folder name is what Claude Code uses to identify the marketplace.

**Updating later:** Repeat steps 1-4 with a fresh ZIP, then run `/reload-plugins` in Claude Code. (Or just use `git clone` from Option 2 — much easier for repeat updates.)

### Option 3 — Development mode (--plugin-dir)

If you're actively developing the plugin, skip the marketplace dance entirely and load it directly:

```bash
# Add to ~/.zshrc or ~/.bashrc:
alias claude='claude --plugin-dir /path/to/fake-data/plugins/fake-data'
```

Now `claude` always loads the plugin from your source directory. Edits become live with `/reload-plugins` — no reinstall needed.

### Verify installation

After installation (any method), open Claude Code in any directory. You should see:

1. **SessionStart announcement** at the top: `🎯 FAKE_DATA plugin loaded — 8 skills available...`
2. **Skills available** when you type `/fake` or `/fd-` — both `fake-data:fd-init` and `/fd-init` should work
3. **`/plugin → Installed`** lists `fake-data` from marketplace `splunk-forge`

## Quick start

**One-shot mode (YOLO) — from zero to Splunk TA:**
```bash
mkdir my-demo && cd my-demo
/fd-init firewall.log --description="SOC demo for energy company" --scenario="brute_force" --yolo
```

That's it. YOLO mode runs the entire pipeline automatically and stops at the packaging step for confirmation.

**Step-by-step:**
```bash
mkdir my-demo && cd my-demo
/fd-init                          # Create workspace (interactive wizard)
/fd-discover fortigate            # Research the log format
/fd-add-generator fortigate       # Scaffold the Python generator
/fd-cim fortigate                 # Map fields to Splunk CIM
/fd-add-scenario brute_force      # Create a correlated attack scenario
/fd-generate                      # Produce log files
/fd-build-app                     # Package as installable Splunk TA
```

## Pipeline

```
/fd-init → /fd-discover → /fd-add-generator → /fd-cim → /fd-add-scenario → /fd-generate → /fd-build-app
    ↓           ↓                ↓               ↓              ↓                ↓               ↓
 world.py    SPEC.py      generator.py    CIM_MAPPING   scenario.py       log files     TA-*.tar.gz
```

Each skill offers to chain to the next, so you rarely need to type more than one command in a row.

## Skills

| Skill | What it does |
|-------|-------------|
| `/fd-init` | Create a workspace with a fictional org — world.py with users, locations, infrastructure, network config. Quick/custom/just-data/YOLO modes. Researches real companies to prefill defaults. |
| `/fd-discover` | Research a log format (e.g. "fortigate") using vendor docs, Splunkbase, and samples. Produces a `SPEC.py`. Checks bundled presets first for instant match. |
| `/fd-add-generator` | Scaffold a Python log generator from a SPEC.py or interactive wizard. Auto-detects format, fields, and volume patterns. |
| `/fd-add-scenario` | Create multi-phase scenarios (attacks, ops incidents, network issues) with research-driven event generation. Events correlated across generators via `demo_id`. |
| `/fd-world` | View and edit the organization's world state. Add/edit/remove users, locations, and infrastructure with review gates. |
| `/fd-generate` | Guided generation wizard. Also ships a curses TUI (`python3 fake_data/tui_generate.py`) for offline interactive use. |
| `/fd-cim` | Map generator fields to Splunk CIM data models (Network_Traffic, Authentication, Endpoint, etc.) with rule-based matching and research fallback. |
| `/fd-build-app` | Generate a Splunk Technology Add-on (TA) with inputs.conf, props.conf, transforms.conf, CIM alignment, and tar.gz packaging. |

## Bundled presets (21)

Pre-built log format specs for common Splunk sources. `/fd-discover <source>` checks these first and skips research if a match is found.

**Network/firewall:** fortigate, cisco_asa, cisco_ios, palo_alto_traffic, cisco_meraki_mx, checkpoint_traffic
**Cloud:** aws_cloudtrail, aws_guardduty, entraid_signin, gcp_audit, o365_management
**Endpoint:** wineventlog_security, sysmon, crowdstrike_falcon
**Linux:** linux_auth
**Web:** apache_access, nginx_access
**Collaboration:** cisco_webex
**ITSM/ERP/DB:** servicenow_incident, sap_audit, mssql_errorlog

See [`presets/README.md`](presets/README.md) for the full catalog with Splunkbase references.

## Architecture

### Template-only runtime

When `/fd-init` runs, it copies Python templates into the user's repo. There is no runtime dependency on FAKE_DATA — the user owns all generated code. This means:

- No pip packages, no virtual environments
- stdlib-only Python 3.9+
- Works offline after init (generators, TUI, main_generate.py)
- Claude Code skills assist with scaffolding, not execution

### Workspace structure

After `/fd-init` the user's directory looks like this:

```
your-repo/
└── fake_data/
    ├── manifest.py          # workspace marker + metadata
    ├── world.py             # org, users, locations, infrastructure, network
    ├── config.py            # volume patterns, output paths, scenario discovery
    ├── time_utils.py        # timestamp formatters
    ├── main_generate.py     # orchestrator (filesystem discovery, topo sort)
    ├── tui_generate.py      # curses TUI for interactive generation
    ├── generators/          # each generator has SOURCE_META
    ├── scenarios/           # each scenario has SCENARIO_META
    │   └── _base.py         # BaseScenario with auto-resolver
    ├── cim/                 # CIM mappings per generator (from /fd-cim)
    ├── output/              # generated log files
    └── splunk_app/          # generated Splunk TA (from /fd-build-app)
```

### Key patterns

**Filesystem discovery:** Generators and scenarios are auto-discovered by scanning their directories for `SOURCE_META` / `SCENARIO_META` dicts. No central registry — add a file and it's found.

**World state binding:** Scenarios use a config dataclass with `"auto"` sentinel values. The `BaseScenario._resolve_auto_values()` method maps these to real users, hosts, and IPs from `world.py` at instantiation. Attack scenarios prefer admin/IT users; ops scenarios pick servers.

**Scenario correlation:** Every scenario event includes a `demo_id` field. The Splunk TA extracts this as an indexed field (`IDX_demo_id`) for fast `tstats` correlation across sourcetypes.

**Research-driven scaffolding:** `/fd-discover`, `/fd-add-scenario`, and `/fd-cim` use Claude subagents to research vendor documentation, log formats, attack techniques, and CIM mappings. Results are structured and parsed — the user gets working code, not just documentation.

**Dependency management:** Generators declare `depends_on` in SOURCE_META. The orchestrator topologically sorts them before execution. The TUI auto-includes dependencies with `[+]` markers.

## Plugin layout

```
fake-data/
├── .claude-plugin/plugin.json    # plugin manifest
├── skills/                       # 8 Claude Code skills
├── hooks/                        # SessionStart announcement
├── templates/                    # runtime files copied by /fd-init
├── data/                         # name + IP data (used by skills)
├── presets/                      # 21 bundled log format specs
├── README.md
├── CLAUDE.md
├── CHANGEHISTORY.md
└── LICENSE
```

## Lineage

FAKE_DATA is a standalone reimplementation of the skills and framework originally built inside the [FAKE T-Shirt Company](https://github.com/lyderhansen/The-Fake-T-Shirt-Company) Splunk TA. The existing FAKE T-Shirt project is the first intended *user* of this plugin — not its parent.

## License

MIT — see [LICENSE](LICENSE)

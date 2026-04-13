# splunk-forge

> Claude Code plugins for Splunk — forge new tools for synthetic data, queries, dashboards, and more.

A [Claude Code marketplace](https://code.claude.com/docs/en/plugin-marketplaces) hosting plugins that make working with Splunk faster and more enjoyable. Currently ships with `fake-data` for synthetic log generation. More plugins coming.

---

## Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| **[fake-data](plugins/fake-data)** | 0.1.0 | A-to-Z plugin for generating synthetic Splunk log data. 8 skills cover the full pipeline: workspace creation, log format discovery, generator scaffolding, scenario authoring, CIM mapping, log generation, and Splunk TA packaging. |

*More plugins planned: SPL helper, dashboard scaffolding, alert tuning, ...*

---

## Install the marketplace

Once you add this marketplace to Claude Code, all plugins become discoverable in the `/plugin` UI. Pick the install method that fits your situation.

### Option 1 — Install via Claude Code plugin manager (public repo)

If you have access to the GitHub repo, install directly from the URL:

1. In Claude Code, run `/plugin`
2. Go to the **Marketplaces** tab → **Add Marketplace**
3. Paste: `lyderhansen/splunk-forge` (or full URL: `https://github.com/lyderhansen/splunk-forge`)
4. Press Enter — Claude Code clones the marketplace
5. Go to the **Discover** tab → search "fake-data" → Install
6. Restart Claude Code (or run `/reload-plugins`)

### Option 2 — Manual install (private repo or local clone)

If the repo is private or you have a local clone:

```bash
# 1. Clone (or pull latest) into the marketplaces directory
git clone https://github.com/lyderhansen/splunk-forge.git \
          ~/.claude/plugins/marketplaces/splunk-forge

# OR symlink an existing local copy:
ln -s /path/to/your/splunk-forge \
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

If you don't have git installed, or you got the marketplace as a ZIP file:

```bash
# 1. Download the ZIP from GitHub
#    Go to: https://github.com/lyderhansen/splunk-forge
#    Click: Code → Download ZIP
#    Save to: ~/Downloads/splunk-forge-main.zip

# 2. Remove any old version
rm -rf ~/.claude/plugins/marketplaces/splunk-forge

# 3. Unzip and rename
unzip ~/Downloads/splunk-forge-main.zip -d ~/Downloads/
mv ~/Downloads/splunk-forge-main ~/.claude/plugins/marketplaces/splunk-forge

# 4. Verify the structure
ls ~/.claude/plugins/marketplaces/splunk-forge/.claude-plugin/marketplace.json
ls ~/.claude/plugins/marketplaces/splunk-forge/plugins/fake-data/.claude-plugin/plugin.json

# 5. In Claude Code:
#    /plugin → Marketplaces → Add Marketplace → ~/.claude/plugins/marketplaces/splunk-forge
#    /plugin → Discover → fake-data → Install for you
#    Restart Claude Code or run /reload-plugins
```

**Important:** The folder MUST be renamed from `splunk-forge-main` (the GitHub ZIP default) to `splunk-forge`. The folder name is what Claude Code uses to identify the marketplace.

### Option 3 — Development mode (--plugin-dir)

If you're actively developing one of the plugins, skip the marketplace and load it directly:

```bash
# Add to ~/.zshrc or ~/.bashrc:
alias claude='claude --plugin-dir /path/to/splunk-forge/plugins/fake-data'
```

Now `claude` always loads the plugin from your source directory. Edits become live with `/reload-plugins` — no reinstall needed.

---

## Verify installation

After installation (any method), open Claude Code in any directory. You should see:

1. **SessionStart announcement** at the top:
   ```
   🎯 FAKE_DATA plugin loaded — 8 skills available...
   ```
2. **Skills available** when you type `/fake` or `/fd-` — both `fake-data:fd-init` and `/fd-init` should work
3. **`/plugin → Installed`** lists `fake-data` from marketplace `splunk-forge`

---

## Marketplace structure

```
splunk-forge/
├── .claude-plugin/
│   └── marketplace.json       # marketplace manifest
├── plugins/
│   └── fake-data/             # plugin #1
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/            # 8 Claude Code skills
│       ├── hooks/             # SessionStart announcement
│       ├── templates/         # runtime files copied by /fd-init
│       ├── data/              # name + IP data
│       ├── presets/           # 21 bundled log format specs
│       ├── README.md          # plugin-specific docs
│       └── ...
├── README.md                  # this file (marketplace docs)
└── LICENSE                    # MIT
```

---

## Adding a new plugin to splunk-forge

To contribute a new plugin to this marketplace:

1. Create `plugins/<your-plugin>/.claude-plugin/plugin.json`
2. Add the plugin's `skills/`, `hooks/`, etc. under `plugins/<your-plugin>/`
3. Add an entry to `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "your-plugin",
     "description": "...",
     "source": "./plugins/your-plugin",
     "category": "productivity"
   }
   ```
4. Commit and push

All users who have the splunk-forge marketplace installed will see your plugin in `/plugin → Discover` after running `/plugin → Marketplaces → splunk-forge → u` (update).

---

## License

MIT — see [LICENSE](LICENSE)

## Author

**Lyder Hansen** — [@lyderhansen](https://github.com/lyderhansen)

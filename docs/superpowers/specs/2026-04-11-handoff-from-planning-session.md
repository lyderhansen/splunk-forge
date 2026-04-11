# Handoff from planning session — 2026-04-11

**Read this first.** This document captures the full context from the planning session in which the decision was made to pivot from building tooling *inside* The FAKE T-Shirt Company repo to building **FAKE_DATA** as a standalone Claude Code plugin. Without it, the next Claude Code session will have to re-derive many decisions from scratch.

The session lived in the TA-FAKE-TSHRT repo and produced: a validated design spec for `discover-logformat`, two executed implementation plans (v1 offline MVP and v2 research-enabled), a working skill with real canary test runs, and finally the realization that everything built was too coupled to TA-FAKE-TSHRT to ever be used as a plugin by anyone else. This repo — `fake-data/` — is the clean-slate rebuild.

---

## Locked-in architectural decisions

These five decisions are settled. Do not re-open them unless there is new information that invalidates them.

### 1. Plugin format: Claude Code canonical

Use the canonical Claude Code plugin format from day one. Not a "repo with skills" that users clone manually — a real plugin with `.claude-plugin/plugin.json` manifest, loaded via Claude Code's plugin system. The manifest is already in place at `.claude-plugin/plugin.json` (version 0.0.1).

Why: the whole point of the pivot is "usable by anyone". Plugin manifest is the only mechanism that makes that true without friction.

### 2. Name: `fake-data` on disk, "FAKE_DATA" as brand

Plugin ID in all technical files (`plugin.json`, directory name, skill namespace) is `fake-data` — lowercase with hyphen, matching Claude Code convention. When loaded, skills will be auto-namespaced by the plugin system as `fake-data:discover-logformat`, `fake-data:add-generator`, etc.

In README, CHANGEHISTORY, docs, and any user-facing strings, refer to the plugin as **FAKE_DATA** as a brand mark. This mirrors the `FAKE:` sourcetype prefix used in TA-FAKE-TSHRT at Splunk index-time — a conscious brand continuity between the plugin and its first-known user (the FAKE T-Shirt Company project).

Skill names inside the plugin: `discover-logformat`, `add-generator`, `add-scenario`, `generate-logs`, plus a new `init` skill that scaffolds a fresh FAKE_DATA workspace in an empty user repo.

### 3. Runtime philosophy: template-only in v1

When a user runs the init skill, the plugin COPIES Python runtime files (time_utils.py, config.py, world_loader.py, main_generate.py, the generator template) into the user's repo. The user owns those files outright. There is no `from fake_data import ...` at runtime. No pip package. No import coupling.

Pros of template-only:
- Zero infrastructure — ship a Claude Code plugin, nothing else
- User can modify anything
- No version-compatibility problems
- Fastest path to a working v1

Cons (accepted):
- Bug fixes do not propagate to existing user repos
- Each user's scaffolded code will slowly diverge

The alternative (library-based runtime, where users import from a pip package) was considered and deferred. It may become the right choice later; for v1 it adds infrastructure that slows us down without changing what the plugin can do for the user's first hour.

A hybrid (runtime-as-library, generators-as-templates) was also considered and deferred for the same reason.

### 4. World-state schema: minimalistic, extensible

First-version `world.yaml` schema covers the 80%-case: organization name, a small set of locations, a list of users, a list of servers. Nothing fancy. Custom fields are allowed — generators can read them if they want, but the plugin runtime does not require or validate them.

Rich features (OT zones, VPN pools, Webex rooms, meeting schedules, IEC 62443 classification, etc. — all things TA-FAKE-TSHRT hardcodes) become OPTIONAL sections in world.yaml. A generator that needs them declares that requirement; the runtime fails gracefully if they are absent.

Why: a schema rich enough to express every TA-FAKE-TSHRT concept would take weeks to design and would still be specific to enterprise IT/OT scenarios. A minimal schema ships now and extends forever.

### 5. Repo location: standalone sibling

Plugin lives in a new repo at `../../GIT-FAKE-DATA/fake-data/` — sibling to `../../GIT-TA-FAKE-TSHRT/The-Fake-T-Shirt-Company/` on disk. No git remote yet. Local-only until something actually works. Migration to GitHub happens later.

TA-FAKE-TSHRT is the **first intended user**, not the parent. The final milestone of plugin development is to migrate TA-FAKE-TSHRT to consume FAKE_DATA, at which point its own `shared/company.py`, `bin/generators/*.py`, and scenario framework become client code of the plugin rather than the plugin's origin.

---

## Scope decomposition — the six subsystems

During brainstorming the full plugin vision was broken into six independent subsystems. Status and priority below are current as of this handoff.

| # | Subsystem | Status | Priority |
|---|---|---|---|
| 1 | **Framework core** — generator runtime, world-state loader, source registration, FAKE: prefix handling | ❌ Not started | **High (blocks most other work)** |
| 2 | **Onboarding wizard / init skill** — "create a new fictional world" UX | ❌ Not started | **High** |
| 3 | **Data source catalog** — source selection UX, metadata about each generator | ❌ Not started | Low (emergent from other work) |
| 4 | **Data format discovery** — `discover-logformat` skill | 🟡 **Validated in TA-FAKE-TSHRT, ready to port** | **High** |
| 5 | **Behavioral layer** — three-layer architecture (world state + diurnal/causal/anomaly + formatter) | ❌ Not started | Low (defer to later milestone) |
| 6 | **Plugin packaging** — distribution as Claude Code plugin | 🟡 Partial (manifest + directory skeleton exist) | Medium |

The recommended order of attack (see the roadmap below) is roughly: init + framework core first (subsystems 1 + 2), then port discover-logformat (subsystem 4), then add-generator / add-scenario / generate-logs (still subsystem 1 but now user-facing), then TA-FAKE-TSHRT migration as the lakmus test, then behavioral layer.

---

## Roadmap — Plan X1 through X7

This is a sketch, not a commitment. Each plan will be written and executed with the standard superpowers discipline (brainstorm → spec → plan → subagent-driven execution). Scope may shift based on what each plan teaches.

| Plan | Goal | Why this order |
|---|---|---|
| **X1** | **Framework core templates + `init` skill.** User runs `/fake-data:init` in an empty repo and gets: `.fake-data/` layout with `world.yaml` (stub), `sources.yaml` (empty), `scenarios.yaml` (empty), `runtime/` (time_utils.py, config.py, world_loader.py, main_generate.py), `generators/` (empty), `output/` (empty). The `world_loader.py` can read the stub `world.yaml` and expose USERS, SERVERS, LOCATIONS in a deliberately-compatible API with TA-FAKE-TSHRT's `shared/company.py`. No actual generators yet — just the empty workspace. | Foundational. Nothing else can run without this. Also the smallest possible first thing that proves the plugin mechanism works end-to-end. |
| **X2** | **Port `discover-logformat`** (offline MVP — Phase A, C, E only, no research). Takes inspiration from the TA-FAKE-TSHRT `.claude/skills/discover-logformat/SKILL.md` but is rewritten for the plugin's path conventions. Canary test: given a sample file, produce a draft `SPEC.yaml` in `.fake-data/discover/<source_id>/`. | This is the most-validated piece from the TA-FAKE-TSHRT session. Porting it second gives us an end-to-end "input → draft" flow without yet needing add-generator. |
| **X3** | **Port `add-generator` as first real consumer of `SPEC.yaml`.** Reads a `SPEC.yaml` from `.fake-data/discover/<source_id>/`, generates a Python generator file in `generators/generate_<source_id>.py` that imports from the local `runtime/world_loader.py`, and registers the generator in `sources.yaml`. Canary: run the full pipe — discover → add-generator → inspect the generated Python. | First place the full pipeline actually runs. This is where design gaps between SPEC.yaml schema and real Python scaffolding are exposed. |
| **X4** | **Add the research phase back to `discover-logformat`** (the equivalent of TA-FAKE-TSHRT Plan v2). WebSearch + WebFetch, research_metadata in SPEC.yaml, metadata-only fallback. Canary: fortigate with `--description` only, offline regression with `--no-search`. | Could be done earlier but offers less learning value than X3. The TA-FAKE-TSHRT session already validated the approach. |
| **X5** | **Port `generate-logs` and `add-scenario`.** Generate-logs becomes the user-facing command that runs the generators registered in `sources.yaml`. Add-scenario stubs out scenarios that live in `scenarios.yaml`. Canary: run the full pipe end-to-end in an empty test repo with one toy source. | After this plan, the plugin is MVP-complete for a new user starting from scratch. |
| **X6** | **Migrate TA-FAKE-TSHRT to consume FAKE_DATA.** Write its `world.yaml` with the 195 employees, migrate one generator at a time, delete `shared/company.py` and the four project-local skills, verify all 26 sources still produce identical output. | The lakmus test. If this works, the plugin is real. If it doesn't, we have concrete gaps to close in the plugin. |
| **X7+** | **Behavioral layer** (three-layer architecture: world state + diurnal/causal/anomaly + formatter). Larger research-heavy milestone. Not started until X1-X6 are solid. | Biggest, riskiest, least understood. Last. |

**Risk points:**
- **X1 is deceptively big.** Getting `init` to produce a working workspace in an empty repo requires every path, every default, every copy-on-init to be right. Budget extra care.
- **X3 will reveal that the SPEC.yaml schema has gaps.** Expect at least one round of schema tweaks.
- **X6 will expose that `shared/company.py` is more than just data.** Some logic (IP allocation, user lookup, meeting schedules) is embedded in Python and will need to become either config or runtime helpers. Budget several days.

---

## Inspiration sources in TA-FAKE-TSHRT

Concrete files to read for inspiration during FAKE_DATA development. **Read for structure and ideas; do NOT copy directly.** All TA-FAKE-TSHRT-specific paths, names, and hardcodings must be removed when reimplementing in FAKE_DATA.

Relative path from this plugin repo: `../../GIT-TA-FAKE-TSHRT/The-Fake-T-Shirt-Company/`

### Most valuable (read first)

| File | Why |
|---|---|
| `docs/superpowers/specs/2026-04-11-discover-logformat-design.md` | The 486-line validated design spec. **A near-verbatim copy lives in this repo at `docs/superpowers/specs/2026-04-11-discover-logformat-design.md`.** That copy is your starting point for the `discover-logformat` skill. |
| `.claude/skills/discover-logformat/SKILL.md` | The working v2 skill (~400 lines) with all four phases (A input, B research, C format analysis, E artifact writing). Use as a concrete implementation reference, but the paths and handoff messages must be rewritten for the plugin layout. |
| `.claude/skills/discover-logformat/canary/` | Canary fixture (custom_internal_app.log, 12 lines KV) and README.md with pass criteria. The methodology — minimum-viable fixture + structural assertions — is worth copying. The specific fixture is not. |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/shared/time_utils.py` | Generic helper module. `calc_natural_events`, `ts_iso`, `ts_syslog`, weekend factors, Monday boost, hourly activity curves. Essentially copy-pasteable for the plugin runtime. |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/shared/config.py` | Defaults, volume patterns, output paths. Most of it generalizes cleanly. |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/generators/_template_generator.py` | The existing generator template. Use as structural inspiration — but the plugin's template must read from `world_loader.py` via a relative import, not from `shared.company`. |

### Second-tier (read when relevant)

| File | Why |
|---|---|
| `.claude/skills/add-generator/SKILL.md` | Current add-generator skill. Heavily TA-FAKE-TSHRT-coupled. Use as a structural template for FAKE_DATA's add-generator, but every path, every import, every code example must be rewritten. |
| `.claude/skills/add-scenario/SKILL.md` | Same pattern as add-generator — useful structure, wrong specifics. |
| `.claude/skills/generate-logs/SKILL.md` | Same. Shows how the user-facing "run the generators" command is documented. |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/main_generate.py` | The orchestrator. 700+ lines. Shows how parallel execution, dependency resolution, scenario injection, and volume estimation fit together. Mostly genericizable. |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/shared/company.py` | The thing we're replacing with `world.yaml`. Read it to understand what shape of data the generators actually depend on. 195 employees, 17 servers, 4 locations, VPN pools, OT zones. **This is the contract `world_loader.py` must satisfy, not the code to copy.** |
| `TheFakeTshirtCompany/TA-FAKE-TSHRT/bin/scenarios/registry.py` | Scenario registry. Shows how the scenario-to-generator binding works today. The `scenarios.yaml` schema will be inspired by this but will not be Python. |
| `docs/superpowers/plans/2026-04-11-discover-logformat.md` | Plan v1 (offline MVP) execution history. Read the task decomposition for structure; skip the execution details. |
| `docs/superpowers/plans/2026-04-11-discover-logformat-v2-research.md` | Plan v2 (research) execution history. Same guidance — read for structure. |

### Do NOT copy (explicit forbidden list)

| File / pattern | Reason |
|---|---|
| `shared/company.py` (the Python module) | The plugin replaces this with `world.yaml` + `world_loader.py`. Copying `company.py` defeats the entire pivot. |
| Any of the 26 actual generator files in `bin/generators/generate_*.py` | Specific to FAKE T-Shirt. Every one of them imports from `shared.company` and references specific users, IPs, servers. Plugin ships with ZERO generators; users create their own. |
| Any of the 11 scenario files in `bin/scenarios/` | Same reason. Plugin ships with ZERO scenarios; users create their own. |
| `bin/main_generate.py` verbatim | Has a hardcoded `GENERATORS` dict and `SOURCE_GROUPS` dict. The plugin version must be dynamic — read from `sources.yaml` at runtime. Copy the *ideas* (parallel execution, Phase 1 vs Phase 2 dependencies, time estimation), not the code. |
| `CLAUDE.md` from TA-FAKE-TSHRT | Describes a specific fictional company. The plugin has its own (already written) `CLAUDE.md`. |
| Any lookups CSV in `TA-FAKE-TSHRT/lookups/` | Company-specific data. |
| Any dashboard XML in `TA-FAKE-TSHRT/data/ui/views/` | Not part of the plugin's scope at all. |
| Names: "Boston", "Atlanta", "Austin", "Detroit", "Alex Miller", "Jessica Brown", "Brooklyn White", "FW-EDGE-01", "DC-BOS-01", "185.220.101.42", "FAKE T-Shirt", "theTshirtCompany.com", etc. | All specific to one fictional organization. Plugin must be universe-agnostic. |

---

## Session learnings — what Plan v1 and v2 taught us

These are worth remembering because they are not written down in the spec documents and will be re-learned painfully otherwise.

### Sample data is usually unavailable

The single biggest design pivot during the session was making `--sample` OPTIONAL in discover-logformat. The original design required it. The realization: **the whole point of the tool is to help when you do NOT have a sample.** A user who has a sample already knows most of what they need. A user who has only "I want to generate fake Okta logs" is who the tool exists for.

Consequence: `discover-logformat` must accept any of `{--sample, --doc, --description}` as a seed (at least one required), with research filling in the gaps. The research path should be first-class, not an afterthought.

### Phase B research runs by default

Following from the above: research should be the default behavior, not an opt-in. `--no-search` disables it. `--doc` URLs are always fetched regardless of `--no-search`. This is how v2 of the TA-FAKE-TSHRT skill ended up shaped, and the canary test against a real `fortigate` description confirmed it works.

### Metadata-only fallback is important

During the fortigate canary test, Phase B found vendor docs with field tables but no raw log-line examples. The skill correctly fell through to metadata-only mode: format.type = "unknown", fields populated from research field hints at confidence 0.7. The user got a usable draft SPEC.yaml anyway. **Without the metadata-only path, that run would have failed entirely.**

### Canary structural assertions > content assertions

When research uses live WebSearch results, content is non-deterministic — the same query returns different pages on different days. Canary tests for research paths must assert on structural properties (files exist, lists non-empty, vendor field is not the default "unknown") rather than specific content. The TA-FAKE-TSHRT session's fortigate canary did exactly this and passed cleanly.

### Grep thresholds in plans were too strict

During Plan v1/v2 execution, a subagent flagged a verification grep that expected a specific phrase to appear ≥ N times, when the actual prescribed text used different wording. The content was correct; the grep was over-specified. Lesson: when writing verification greps in a plan, prefer checking for multiple alternative phrases or count the higher-level structure (e.g. "does this section contain at least one field description" rather than "does the exact string 'combined sample set' appear twice").

### Plan bodies can be filled incrementally

One-shot plan generation got interrupted repeatedly in the TA-FAKE-TSHRT session because the plan document grew beyond what could be written in a single turn. The successful pattern was: write the plan scaffold + empty task index first, commit, then fill in one task body per turn with a commit between. This allows the user to course-correct between task-body fills without losing progress. Use the same pattern here.

### Subagent-driven execution works well for exact-content markdown

All five execution tasks in Plan v1 and all five in Plan v2 succeeded on the first subagent dispatch. The key was writing task descriptions that included the exact content to produce, not just "implement X". Subagents on `haiku` handled trivial file scaffolding; `sonnet` handled tasks that required reading multiple sections of SKILL.md or running non-deterministic canary tests. Keep that model selection pattern.

### Read-before-edit hook fires noisily but does not block

Throughout the session, edits to files that had been recently read still triggered the read-before-edit reminder from the hook. The edits themselves succeeded — the warning is a reminder, not a failure. Expect the same in this repo and do not interpret the warning as an error.

---

## Open questions for the next session

These were identified during the planning session but not resolved. The next session should work through them during its own brainstorming pass for whichever plan it tackles first.

1. **Exact `world.yaml` schema.** How expressive is the minimum viable v1? Is a simple `{organization, locations[], users[], servers[]}` enough, or do we also need `networks[]` and `subnets` from day one? TA-FAKE-TSHRT treats IP allocation as a Python function — the plugin needs to decide whether that becomes config data or a small helper module.

2. **What does `init` actually scaffold?** The directory layout in `.fake-data/` is unclear. Does it live at the user's repo root or in a subdirectory? Does it use `.fake-data/` or `fakedata/` or just files in the root? What files are copied, and what do their initial contents look like?

3. **Relative-path imports in copied templates.** When `_template_generator.py` is copied into `user-repo/generators/`, it needs to import from `user-repo/runtime/world_loader.py`. How does that import work? Is there an `__init__.py`? Is the user expected to run with a specific PYTHONPATH? Needs to be worked out in Plan X1.

4. **Source registration mechanism.** When `add-generator` creates a new generator file, it needs to be findable by `generate-logs`. TA-FAKE-TSHRT uses a hardcoded `GENERATORS` dict in `main_generate.py`. The plugin should probably use a `sources.yaml` registry that `main_generate.py` reads at startup. Design needed.

5. **Scenario file layout.** Each scenario in TA-FAKE-TSHRT is a Python class in `scenarios/security/<name>.py` with methods like `asa_hour(day, hour) → List[str]`. The plugin should probably keep that structure — scenarios are code, not config — but register them via `scenarios.yaml`. Design needed.

6. **Collision handling in discover-logformat.** Current v2 design refuses to overwrite an existing `.planning/discover/<source_id>/`. In the plugin, should this path become `.fake-data/discover/<source_id>/`? Or somewhere else? And what does the init skill do if a `.fake-data/` directory already exists?

7. **How does the user pick `source_id`?** Is the naming convention snake_case enforced (as in TA-FAKE-TSHRT)? Are collisions with existing generator files detected early?

8. **How do the skills know they're inside a FAKE_DATA workspace?** The plugin's skills will be available in every project once installed. But `add-generator` should only work when the user's current working directory has `.fake-data/` or `world.yaml` or some marker. Decide on a marker file and document the "skill refuses if not in a workspace" behavior.

---

## What to do next

The recommended first action in the new session, after reading CLAUDE.md and this handoff document:

1. **Invoke `superpowers:brainstorming`** with a scope of "Plan X1 — framework core templates + init skill". Do NOT attempt to brainstorm the whole plugin at once. Stick to X1.

2. During that brainstorming, lean heavily on the decisions in this document. Do not re-open the architectural choices unless new information says you should.

3. Resolve as many open questions from the list above as are relevant to X1 (especially questions 2, 3, 4, 8).

4. Produce a spec document at `docs/superpowers/specs/2026-MM-DD-plan-x1-design.md`.

5. Then invoke `superpowers:writing-plans` to produce an executable plan at `docs/superpowers/plans/2026-MM-DD-plan-x1.md`.

6. Execute with `superpowers:subagent-driven-development`, committing each task atomically.

7. Before declaring X1 done: create a scratch empty git repo somewhere (e.g. `/tmp/fake-data-canary-test/`) and run `/fake-data:init` in it end-to-end. If the result is not a working skeleton workspace that at least parses, X1 is not done.

---

## Files in this handoff

Two files were created in `docs/superpowers/specs/` as part of this handoff:

1. `2026-04-11-handoff-from-planning-session.md` — this file.
2. `2026-04-11-discover-logformat-design.md` — adapted copy of the validated discover-logformat design spec from the TA-FAKE-TSHRT session. Status note at top explains the adaptation context.

No plans, no code, no skills have been ported yet. The repo is a clean slate with a complete handoff.

---
name: fd-init
description: 'Create a new FAKE_DATA workspace. Args: [<source>] [--description=...] [--scenario=...] [--yolo]. Use --yolo for full pipeline automation from source to logs.'
version: 0.1.0
metadata:
  argument-hint: "[<log-file>] [--description=...] [--scenario=...] [--yolo]"
---

# fd-init — Create a FAKE_DATA workspace

Create a new FAKE_DATA workspace in the current directory. This skill generates a `fake_data/` directory with all runtime files needed to create and run log generators.

**Two modes:**

1. **Interactive (default)** — `/fd-init` with no arguments. Wizard-based setup with defaults.
2. **Full pipeline (`--yolo`)** — `/fd-init <source> [--description="..."] [--scenario="..."] --yolo`. Runs the entire pipeline from init all the way through log generation, stopping at the Splunk TA build step. The `<source>` can be either a log file path OR a free-text description ("aws cloudtrail", "oracle database audit logs", "fortigate firewall"). When given a description, fd-discover does pure research (no sample needed). YOLO is supposed to be YOLO — minimal friction.

**Examples:**
```
# YOLO with a sample log file
/fd-init firewall.log --yolo

# YOLO with just a description (research-only, no sample)
/fd-init "fortigate firewall" --yolo
/fd-init "oracle database audit logs" --yolo
/fd-init "aws cloudtrail" --description="cloud security demo" --scenario="data_exfil" --yolo

# Interactive (no --yolo)
/fd-init
```

---

## Phase A — Pre-flight and collision check

Before asking any questions, verify the target directory is clean.

### A.1 Check for existing workspace

Run via Bash:
```bash
test -f fake_data/manifest.py && echo "EXISTS" || echo "CLEAN"
```

If `EXISTS`: ask the user:

> "A FAKE_DATA workspace already exists at `./fake_data/` (created <read INITIALIZED_AT from manifest.py>).
>
>   1. **Start fresh** — delete the existing workspace and create a new one
>   2. **Cancel** — keep the existing workspace
>
> Pick 1 or 2: [2]"

If **Start fresh (1):** Delete the entire `fake_data/` directory via Bash:
```bash
rm -rf fake_data/
```
Then proceed to Phase B.

If **Cancel (2):** Stop. Print:
> "Keeping existing workspace. Run `/fd-add-generator` to add generators to it."

### A.2 Check for stale fake_data/ directory

If manifest.py does not exist, also check:
```bash
test -d fake_data && echo "DIR_EXISTS" || echo "NO_DIR"
```

If `DIR_EXISTS`: ask the user:

> "A `fake_data/` directory exists here but has no manifest.py. This could be a partially-initialized or unrelated directory.
>
>   1. **Delete and start fresh** — remove it and create a new workspace
>   2. **Cancel** — leave it alone
>
> Pick 1 or 2: [2]"

If **Delete (1):** `rm -rf fake_data/` and proceed to Phase B.
If **Cancel (2):** Stop.

### A.3 If clean (no fake_data/ directory exists), proceed to Phase B.

---

## Phase B — Setup mode selection

### B.yolo — Full pipeline mode (if --yolo flag provided)

If the invocation included `--yolo`, skip ALL questions in this phase and
execute the full pipeline automatically. This is the "I trust you, just do
everything" mode.

**Required argument:** A `<source>` — first positional argument. Can be EITHER:
- A log file path (e.g. `firewall.log`, `/tmp/sample.json`), OR
- A free-text description of the source (e.g. `"fortigate firewall"`,
  `"oracle database audit logs"`, `"aws cloudtrail"`)

**Optional arguments:**
- `--description="..."` — Sets the workspace purpose. If it describes a real
  company, fd-init will research it for locations and industry.
- `--scenario=<type>` — Creates a scenario after the generator is in place.
  Type can be a keyword like `brute_force`, `data_exfil`, `disk_filling`,
  or a free-text description.

**Detect source type:** Before starting, check if `<source>` is a file:

```python
import os
is_file = os.path.isfile(source) or os.path.isfile(os.path.expanduser(source))
```

If `is_file`: treat as `--sample=<path>` for fd-discover.
If NOT a file: treat as a free-text source description for fd-discover research mode.

**Important:** YOLO is YOLO. Do NOT block on "I can't guess the format without
a sample". If the source isn't a file, just pass it as a description string
and let fd-discover do pure research (vendor docs, Splunkbase, samples). That's
literally what fd-discover is designed for. Only stop with an error if BOTH
the file path doesn't exist AND the string is so vague it can't even be turned
into a source_id (e.g. empty string, single character).

**YOLO pipeline execution:**

1. **fd-init workspace** — Use Phase B.quick defaults silently. If
   `--description` hints at a real company (e.g. "NTE energy company"),
   run Phase B.1-research to get industry/locations. Otherwise use
   "Example Corp" defaults. SKIP the review gate. Go directly to Phase E
   (write files).

2. **fd-discover <source>** — After Phase F writes the workspace, invoke
   `/fd-discover` with one of two paths:

   **A) If `<source>` is a file:**
   - Derive source_id from filename (strip extension, normalize)
   - Invoke `/fd-discover <source_id> --sample=<path>`
   - fd-discover detects format from the sample

   **B) If `<source>` is a description (text, not a file):**
   - Derive source_id from the description by extracting the most distinctive
     noun phrase. Examples:
     - `"fortigate firewall"` → `fortigate`
     - `"oracle database audit logs"` → `oracle_audit`
     - `"aws cloudtrail"` → `aws_cloudtrail`
     - `"palo alto ngfw traffic"` → `palo_alto_traffic`
   - Invoke `/fd-discover <source_id>` (no --sample flag)
   - fd-discover does its normal preset check first (might match a bundled
     preset for instant results), then runs the research subagent if no
     preset is found.

   In BOTH cases: auto-accept all fd-discover confidence gates. Do not
   prompt the user. If research yields a low-confidence result (< 0.6),
   note it in the summary at the end but proceed anyway.

3. **fd-add-generator <source_id>** — Invoke after fd-discover completes.
   It will auto-detect the SPEC.py. Auto-accept the review gate.

4. **fd-cim <source_id>** — Invoke after generator is scaffolded. Use
   rule-based mapping only (skip research subagent for unmapped fields).
   Auto-accept the review gate.

5. **fd-add-scenario <scenario>** — Only if `--scenario` was provided.
   Use `--auto` internally to skip source-matching prompts. Auto-accept
   the review gate.

6. **fd-generate** — Auto-run with `--days=7` (or `end_day + 2` if a
   scenario is active), `--sources=<source_id>`, `--scenarios=<scenario or none>`.
   Stream output to user.

7. **Print summary and prompt to build the app.** After fd-generate
   completes, show the summary and ask one question:

   ```
   🚀 YOLO pipeline complete!

   Workspace:  ./fake_data/ (<ORG_NAME>)
   Generator:  fake_data/generators/generate_<source_id>.py
   CIM:        fake_data/cim/<source_id>.py
   Scenario:   fake_data/scenarios/<scenario>.py  (if --scenario was set)
   Output:     fake_data/output/<category>/<source_id>.log
               <N> events over <days> days
   ```

   Then ask:

   > "Build the Splunk TA now?
   >
   >   1. **yes** — Run /fd-build-app with full CIM alignment and auto app name
   >   2. **skip** — I'll review the output and build it myself later
   > [1]"

8. **Handle the answer:**

   - **yes**: invoke `/fd-build-app` — it will use the CIM mappings created
     in step 4, default to full CIM level, and name the app `TA-<ORG_NAME_UPPER>`.
     Pass these as answers to fd-build-app's Phase B questions so it doesn't
     prompt again. After fd-build-app completes, print the final path to
     the `.tar.gz` package.

   - **skip**: stop here and print:
     ```
     Run /fd-build-app when you're ready. It will detect the CIM mappings
     and generators automatically.
     ```

**YOLO mode does NOT auto-confirm the build step** — the user still gets
one explicit "yes" before the Splunk TA is generated, because packaging
has consequences (app name, files written to splunk_app/, tar.gz created).
But it does offer the next step inline instead of requiring a separate
skill invocation.

**IMPORTANT:** In YOLO mode, every skill invocation passes `--auto` or
equivalent flags so no interactive prompts surface. If any skill genuinely
can't proceed without user input (e.g. fd-discover can't detect format and
has no preset), surface the error clearly and stop — do not guess.

---

### B.0 Mode selection (interactive, no --yolo)

If `--yolo` was NOT provided, ask this question:

> "How would you like to set up your FAKE_DATA workspace?
>
>   1. **Quick start** — I'll create a workspace with sensible defaults in seconds. You can edit world.py afterwards.
>   2. **Custom setup** — You control the organization name, industry, locations, IP plan, and more.
>   3. **Just data** — Minimal workspace with generic defaults. Skip straight to creating generators.
>
> Pick 1, 2, or 3: [1]"

**If Quick start (1):** Use these defaults silently, skip to Phase B.quick below.
**If Custom setup (2):** Continue to Phase B.custom below (the full wizard).
**If Just data (3):** Use same defaults as Quick start, skip to Phase B.quick, and after Phase F handoff, immediately suggest: "Ready to create your first generator. What data source would you like? (e.g. `firewall`, `web_access`, `cloud_audit`)" and then invoke `/fd-add-generator` with the user's answer.

---

### Phase B.quick — Quick start defaults

Use these values without asking any questions:

- `ORG_NAME` = `"Example Corp"`
- `INDUSTRY` = `"generic"`
- `employee_count` = `100`
- `location_count` = `2`
- Location 1: `HQ1`, "Headquarters", "New York", "US", "America/New_York", 60%
- Location 2: `OFF1`, "Branch Office", "London", "GB", "Europe/London", 40%
- `TENANT` = `"examplecorp.com"`
- `ip_plan` = `"10.0.0.0/8"`
- `purpose` = not set (generic)

Skip directly to **Phase C** (generate content in memory). The review gate in Phase D will show the defaults so the user can still edit before writing.

---

### Phase B.custom — Full interactive wizard

This wizard gathers information through **at most 3 prompts**: org name + purpose, optional research, then a single review gate with everything filled in.

#### B.custom.1 Organization name + purpose (single prompt)

> "Two quick questions to get started:
>
>   **Organization name?** [Example Corp]
>   **What are these logs for?** (e.g. 'SOC training with attack scenarios', 'CISO security visibility', 'test Splunk dashboards') [just generic logs]"

Store `ORG_NAME` and `purpose`. Purpose is saved in manifest.py as `PURPOSE_AT_INIT`.

#### B.custom.2 Research check

> "Is this based on a real company? If yes, I'll research public info to fill in industry, locations, and domain. [no]"

If yes: run **Phase B.research** below. Research fills ALL defaults (industry, locations, domain, employee count). If no: use generic defaults.

#### B.custom.3 Present everything as one review gate

After research (or using defaults), present ALL configuration at once:

> "Here's what I'll create. Edit anything, or say **ok** to proceed:
>
>   Organization:   <ORG_NAME>
>   Industry:       <industry>
>   Purpose:        <purpose>
>   Domain:         <tenant>
>   IP range:       10.0.0.0/8
>
>   Locations (<N>):
>     HQ1:  <city>, <country>  (<pct>% of users)
>     OFF1: <city>, <country>  (<pct>% of users)
>
>   Users: <generated_count> will be generated
>     (Real company has ~<real_count> employees, but we generate
>      max 100 for efficient log data. Say 'more users <N>' to override.)
>
>   Infrastructure per location:
>     HQ1:  FW-HQ1-01 (firewall), SW-HQ1-01 (switch), SRV-HQ1-01 (server)
>           + DS-HQ1-01 (directory_server), VPN-HQ1-01 (vpn_gateway)  [from purpose]
>     OFF1: FW-OFF1-01 (firewall), SW-OFF1-01 (switch), SRV-OFF1-01 (server)
>
>   To edit, say what to change. Examples:
>     'change domain to example.no'
>     'remove VPN-HQ1-01'
>     'add wap to OFF1'
>     'change industry to manufacturing'
>     'more users 200'
>
> [ok]"

This replaces B.custom.4 through B.custom.9 — NO separate questions for industry, employee count, locations, domain, or IP range. Everything is presented at once with smart defaults from research.

**User count constraint:** Generate at most **100 users** by default, regardless of real employee count. 100 gives enough variety for realistic cross-source correlation (admins, power users, service accounts, multiple departments and locations). If the user explicitly asks for more (e.g. "more users 500"), honor the request up to 500. Beyond 500, warn that world.py will be very large.

**Infrastructure editing:** The user edits by describing changes in natural language ("remove X", "add Y to Z"). Do NOT show fake checkboxes that can't be toggled.

The user can say "ok" to accept, or describe any number of changes. Apply changes and re-display if they edit. Only proceed to Phase C when the user approves.

---

## Phase B.1-research — Company research (only if "real company" = yes)

Time budget: **60 seconds max**. Use WebSearch and WebFetch.

### Steps

1. Search: `"<ORG_NAME>" company headquarters employees site:wikipedia.org OR site:<orgname_lower>.com`
2. Fetch top 2-3 results. Prefer the company's own about page and Wikipedia.
3. Extract: industry, headquarters city/country, other known offices, approximate employee count, official domain.
4. Present findings:

> "Based on public information, I found:
>   - Industry: <industry> (source: <url>)
>   - HQ: <city>, <country>
>   - Approx. employees: <count>
>   - Domain: <domain>
> These are prefilled as defaults. You can override any of them in the following questions."

5. Use extracted values as defaults for B.3-B.7.

**Privacy guardrail:** Research fetches ONLY publicly available company context (about pages, Wikipedia, press releases). It does NOT look up LinkedIn profiles, employee names, or real IP addresses. The USERS list is ALWAYS generated from the bundled name list, never from research results. The output is "fictional logs for a fictional IT environment that resembles company X", not "logs that impersonate company X".

---

## Phase C — Generate content in memory

Build all file contents before writing anything. Do NOT write files yet.

### C.1 Load data files from plugin repo

Read these files using the Read tool (paths relative to this SKILL.md):
- `../../data/names_sample.py` — extract `FIRST_NAMES` and `LAST_NAMES` lists
- `../../data/country_ip_ranges.py` — extract `COUNTRY_RANGES` and `FALLBACK_RANGES`

### C.2 Generate deterministic values

Use Python-style logic (execute mentally or describe to yourself):

**ORG_NAME_LOWER:** lowercase ORG_NAME, remove all non-alphanumeric characters.

**TENANT_ID:** Generate a deterministic UUID from ORG_NAME using UUID5 with DNS namespace:
`uuid.uuid5(uuid.NAMESPACE_DNS, ORG_NAME.lower())` — write the result as a string.

**ROLES:** Define a fixed set of roles used across the organization. Each user gets one role. Roles determine access levels in generated logs (e.g. admin users trigger privileged-access events in WinEventLog, Entra ID, etc.):

```python
ROLES = [
    "user",           # standard employee — ~70% of users
    "power_user",     # elevated access (developers, analysts) — ~15%
    "admin",          # IT admin, domain admin — ~10%
    "service_account", # non-human accounts (backups, monitoring) — ~5%
]
```

Always ensure at least 2 admin users and 2 service accounts exist, regardless of employee_count. Distribute remaining users as: ~70% user, ~15% power_user, ~10% admin, ~5% service_account.

**USERS list:** The number of generated users is `min(employee_count, 100)` by default — capped at 100 for efficient log data, unless the user explicitly requested more in the review gate. Seed a random generator with `hash(ORG_NAME)` for determinism. For each employee (up to the generated count):
- Pick a first name and last name from the bundled lists. Cycle through them if employee_count > list length.
- username: `firstname.lastname` (all lowercase). If duplicate, append a digit. Service accounts use format: `svc.<function>` (e.g. `svc.backup`, `svc.monitoring`).
- email: `username@<TENANT>`
- location: distribute across locations by their employee percentages
- department: cycle through `["engineering", "sales", "marketing", "finance", "hr", "it", "operations"]`. Admins and service accounts always belong to `"it"`.
- role: assign from ROLES distribution above
- title: derive from role + department (e.g. role=admin + dept=it -> "IT Administrator", role=user + dept=sales -> "Sales Representative")
- user_id: deterministic GUID via `uuid.uuid5(uuid.NAMESPACE_DNS, ORG_NAME.lower() + "." + username)` — consistent across re-runs
- workstation: `WS-<LOC>-<NNN>` where LOC is the location ID and NNN is a zero-padded index per location (e.g. `WS-HQ1-001`). Service accounts get `SRV-<LOC>-<NN>` instead.
- workstation_ip: assigned sequentially from the location's subnet. If subnet is `10.10.0.0/16`, first user at that location gets `10.10.10.1`, second gets `10.10.10.2`, etc. Start at `.10.1` to leave room for infrastructure IPs (.0.x = gateways/DNS).
- mac_address: deterministic from global user index: `AA:BB:CC:<loc_octet>:<hi>:<lo>` where loc_octet is derived from location index (01, 02, 03...).
- phone: `+1-555-<NNNN>` where NNNN is zero-padded user index. Service accounts have no phone (set to `null`).
- manager: for role=user and role=power_user, pick a random user with role=admin or role=power_user from the same location. For role=admin, manager is `null` (top of hierarchy). For service_account, manager is `null`.

Generate the full USERS list as Python code — each entry is a dict with keys: `username`, `full_name`, `email`, `location`, `department`, `role`, `title`, `user_id`, `workstation`, `workstation_ip`, `mac_address`, `phone`, `manager`.

Also generate a module-level constant:
```python
ROLES = ["user", "power_user", "admin", "service_account"]
```

**NETWORK_CONFIG:** Based on the chosen IP plan, assign a /16 subnet per location:
- If `10.0.0.0/8`: location 1 = `10.10.0.0/16`, location 2 = `10.20.0.0/16`, location 3 = `10.30.0.0/16`, etc.
- If `172.16.0.0/12`: location 1 = `172.16.0.0/16`, location 2 = `172.17.0.0/16`, etc.
- If `192.168.0.0/16`: location 1 = `192.168.1.0/24`, location 2 = `192.168.2.0/24`, etc.
- Gateway: first IP in subnet (e.g. `10.10.0.1`). DNS: `.0.53` suffix (e.g. `10.10.0.53`).

**EXTERNAL_IP_POOL:** Look up each unique country code from LOCATIONS in `COUNTRY_RANGES`. For hits, add those ranges. Always append `FALLBACK_RANGES` at the end.

**EXTERNAL_IP_POOL_BY_COUNTRY:** Dict mapping each country code to its ranges from `COUNTRY_RANGES`.

**INFRASTRUCTURE:** Generate infrastructure devices per location. Two tiers:

**Minimum per location (always generated):**

| Role | Hostname pattern | IP offset | Description |
|---|---|---|---|
| `firewall` | `FW-<LOC>-01` | `.0.1` (same as gateway) | Perimeter firewall |
| `switch` | `SW-<LOC>-01` | `.0.2` | Core switch |
| `server` | `SRV-<LOC>-01` | `.0.10` | General purpose server |

**Purpose-driven additions (suggested, user can remove in review gate):**

Analyze the `purpose` text (from B.custom.3 or empty for quick/just-data modes). If purpose contains keywords, suggest additional roles:

| Purpose keywords | Extra roles suggested |
|---|---|
| network, firewall, visibility, netflow | `router` (RTR, .0.3) |
| windows, AD, endpoint, identity | `directory_server` (DS, .0.11), `file_server` (FS, .0.12) |
| web, retail, e-commerce, application | `web_server` (WEB, .0.80), `database` (DB, .0.90), `load_balancer` (LB, .0.5) |
| cloud, hybrid, proxy | `proxy` (PRX, .0.8), `vpn_gateway` (VPN, .0.9) |
| email, collaboration, messaging | `mail_server` (MAIL, .0.25) |
| OT, manufacturing, SCADA, industrial | `plc` (PLC, .0.20), `hmi` (HMI, .0.21) |
| SOC, security, SIEM, detection | `log_collector` (LOG, .0.14) |
| no match / generic | no extras — just minimum |

These are **suggestions only**. The review gate (Phase D) shows them with checkboxes so the user can remove any they do not need. For quick mode and just-data mode (no purpose set), only generate the minimum set.

Each infrastructure entry is a dict:
```python
{"hostname": "FW-HQ1-01", "ip": "10.10.0.1", "location": "HQ1", "role": "firewall", "description": "Perimeter firewall"}
```

Infrastructure roles are technology-agnostic — `firewall` could be FortiGate, Palo Alto, or ASA. The technology choice is made later by `fd-add-generator`, not by init.

### C.3 Compose world.py content

Generate the full `world.py` file content as a Python module with:
- Module docstring mentioning ORG_NAME and generation date
- `from typing import Optional, List, Dict`
- `ORG_NAME`, `ORG_NAME_LOWER`, `TENANT`, `TENANT_ID`, `INDUSTRY` constants
- `ROLES` list
- `LOCATIONS` dict (keyed by location ID)
- `NETWORK_CONFIG` dict (keyed by location ID)
- `EXTERNAL_IP_POOL` list
- `EXTERNAL_IP_POOL_BY_COUNTRY` dict
- `INFRASTRUCTURE` list (all generated infra devices)
- `USERS` list (all generated users, each with full field set: username, full_name, email, location, department, role, title, user_id, workstation, workstation_ip, mac_address, phone, manager)
- Helper functions:
  - `get_user_by_username(username: str) -> Optional[Dict]`
  - `users_at_location(location_id: str) -> List[Dict]`
  - `users_by_role(role: str) -> List[Dict]` — filter USERS by role
  - `get_user_by_ip(ip: str) -> Optional[Dict]` — find user by workstation_ip
  - `get_user_by_workstation(hostname: str) -> Optional[Dict]` — find user by workstation name
  - `admins() -> List[Dict]` — shortcut for `users_by_role("admin")`
  - `service_accounts() -> List[Dict]` — shortcut for `users_by_role("service_account")`
  - `infra_at_location(location_id: str) -> List[Dict]` — infrastructure at a location
  - `infra_by_role(role: str) -> List[Dict]` — infrastructure by role (e.g. `infra_by_role("firewall")`)
  - `get_infra_by_hostname(hostname: str) -> Optional[Dict]` — find infra device by hostname

### C.4 Compose manifest.py content

```python
"""FAKE_DATA workspace manifest. Do not delete -- skills use this file
to verify that the current directory is a FAKE_DATA workspace."""

FAKE_DATA_WORKSPACE_VERSION = 1
INITIALIZED_AT = "<current UTC ISO-8601>"
PLUGIN_VERSION_AT_INIT = "0.1.0"
ORG_NAME_AT_INIT = "<ORG_NAME>"
SETUP_MODE = "<quick|custom|just-data|yolo>"
PURPOSE_AT_INIT = "<purpose or empty string if not set>"
```

**Compute `INITIALIZED_AT` at write time — do not hard-code.**
Shell out via Bash to get the real timestamp so the manifest reflects when
this run actually happened:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

Interpolate that value into the file. Never write a guessed date (the
agent's conversation date is not the same as wall-clock UTC, and different
runs on the same day still deserve distinct timestamps to the second).

**Allowed `SETUP_MODE` values:** `quick`, `custom`, `just-data`, `yolo`.
Use `yolo` when the run was invoked with `--yolo`, even if the underlying
defaults match `quick` — downstream skills may key off this to adjust
prompting behavior.

### C.5 Compose README.md content

A brief markdown file explaining:
- What init created
- How to verify (`python3 fake_data/main_generate.py --help`)
- How to add a generator (`/fd-add-generator <source_id>`)
- Where world.py lives for manual editing
- That generators will be auto-discovered by main_generate.py

---

## Phase D — Review gate

Display a summary. For custom mode with purpose, include the infrastructure section with checkboxes:

```
Summary of your new FAKE_DATA workspace:

  Organization:   <ORG_NAME>
  Industry:       <INDUSTRY>
  Purpose:        <purpose or "generic">
  Locations:      <N>  (<loc1_id>: <city> <country> [<N> users], ...)
  Users:          <employee_count> generated
    - <N> standard users, <N> power users, <N> admins, <N> service accounts
  Domain:         <TENANT>
  Internal IPs:   <ip_plan>  (<loc1_id>: <subnet>, ...)
  External IPs:   <country list> ranges + RFC 5737 fallback

  Infrastructure per location:
    HQ1:
      FW-HQ1-01    firewall       10.10.0.1     Perimeter firewall
      SW-HQ1-01    switch         10.10.0.2     Core switch
      SRV-HQ1-01   server         10.10.0.10    General purpose server
      PLC-HQ1-01   plc            10.10.0.20    Programmable logic controller  (suggested)
      HMI-HQ1-01   hmi            10.10.0.21    Human-machine interface        (suggested)
    OFF1:
      FW-OFF1-01   firewall       10.20.0.1     Perimeter firewall
      SW-OFF1-01   switch         10.20.0.2     Core switch
      SRV-OFF1-01  server         10.20.0.10    General purpose server

  To edit, say what to change. Examples:
    'remove PLC-HQ1-01, HMI-HQ1-01'
    'add vpn_gateway to HQ1'

Proceed with creating workspace? [yes/edit/cancel]
```

The user can tell you to remove specific infrastructure items (e.g. "remove HMI"). Update the INFRASTRUCTURE list accordingly before proceeding.

- **yes**: proceed to Phase E with current infrastructure selection
- **edit**: go back to Phase B to change org details, or just remove/add specific infrastructure items
- **cancel**: exit without writing anything

---

## Phase E — Write all files

Use the **Write tool** for every file. Do NOT use Bash echo/cat/heredoc.

### E.1 Read template files from plugin repo

Read these files using the Read tool (relative to this SKILL.md):
- `../../templates/runtime/config.py`
- `../../templates/runtime/time_utils.py`
- `../../templates/runtime/main_generate.py`
- `../../templates/runtime/tui_generate.py`
- `../../templates/generators/_template_generator.py`
- `../../templates/scenarios/_base.py`
- `../../templates/scenarios/__init__.py`

### E.2 Write all files

First, ensure the `fake_data/scenarios/` directory exists:
```bash
mkdir -p fake_data/scenarios
```

Write each file using the Write tool:

1. `fake_data/__init__.py` — empty file (just a newline)
2. `fake_data/manifest.py` — generated content from C.4
3. `fake_data/world.py` — generated content from C.3
4. `fake_data/config.py` — exact copy of templates/runtime/config.py
5. `fake_data/time_utils.py` — exact copy of templates/runtime/time_utils.py
6. `fake_data/main_generate.py` — exact copy of templates/runtime/main_generate.py
7. `fake_data/tui_generate.py` — exact copy of templates/runtime/tui_generate.py
8. `fake_data/README.md` — generated content from C.5
9. `fake_data/generators/__init__.py` — empty file
10. `fake_data/generators/_template_generator.py` — exact copy of templates/generators/_template_generator.py
11. `fake_data/scenarios/__init__.py` — exact copy of templates/scenarios/__init__.py
12. `fake_data/scenarios/_base.py` — exact copy of templates/scenarios/_base.py
13. `fake_data/output/.gitkeep` — empty file

### E.3 Verify the workspace

Run via Bash:
```bash
python3 -c "from fake_data.world import USERS, LOCATIONS; print(f'{len(USERS)} users, {len(LOCATIONS)} locations')"
```

If this fails, something went wrong — report the error to the user.

---

## Phase F — Handoff

### F.1 Print workspace summary

```
FAKE_DATA workspace created at ./fake_data/

  Organization:  <ORG_NAME>
  Users:         <employee_count>
  Locations:     <location_count>
```

### F.2 Suggest next steps based on purpose and mode

**If mode was "just-data":** Skip the "inspect world.py" step and go straight to suggesting a generator. Ask:

> "Workspace ready. What data source would you like to generate first?
> Examples: `firewall`, `web_access`, `cloud_audit`, `wineventlog`
>
> Or paste a log sample file path and I'll detect the format automatically."

Then invoke `/fd-add-generator` with the user's answer.

**If purpose was set (custom mode):** Analyze the purpose text and suggest specific generators. Examples:

- Purpose mentions "firewall" or "network visibility" → suggest: `fortigate`, `cisco_asa`, `meraki`
- Purpose mentions "SOC" or "attack" or "security" → suggest: `wineventlog`, `sysmon`, `entraid`, and mention that attack scenarios come in a future version
- Purpose mentions "retail" or "e-commerce" → suggest: `access_combined`, `orders`
- Purpose mentions "cloud" → suggest: `aws_cloudtrail`, `gcp_audit`, `entraid`
- Purpose mentions "Splunk dashboards" or "testing" → suggest: whatever fits the industry

Print:

```
Based on your goal ("<purpose>"), I'd suggest these generators:
  1. <suggestion_1> — <why>
  2. <suggestion_2> — <why>
  3. <suggestion_3> — <why>
  ...

Want me to create them now?
  - **all** — Create all suggested generators (I'll run /fd-discover + /fd-add-generator for each)
  - **pick** — Choose which ones (e.g. "1, 3, 5")
  - **skip** — I'll just show the commands, you do it yourself later
[all]
```

If the user picks **all** or **pick**: For each selected generator, invoke
`/fd-discover <source_id>` followed by `/fd-add-generator <source_id>` in
sequence. Show progress: "Creating generator 1/3: fortigate..."

If the user picks **skip**: Print the manual commands:
```
To create generators yourself:
  /fd-discover <source_id>         (research the log format)
  /fd-add-generator <source_id>    (scaffold the generator from SPEC.py)
```

**If purpose was not set (quick mode or skipped):** Print generic next steps with the same choice:

```
Next steps — add some generators to start producing logs:

Suggested starting points:
  1. fortigate — firewall traffic logs (network visibility)
  2. wineventlog — Windows Security events (auth, account changes)
  3. linux — Linux syslog and metrics

Want me to create them now? [all/pick/skip]
```

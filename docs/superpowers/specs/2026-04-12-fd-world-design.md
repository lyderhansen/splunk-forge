# fd-world Design Spec

## Goal

Interactive skill for viewing and modifying the organization's world state (users, locations, infrastructure) after initial workspace creation. Full CRUD with review gates.

## Architecture

Single SKILL.md — no new Python files. The skill reads and edits `fake_data/world.py` directly using Claude Code's Read/Edit tools. Changes are surgical (preserve manual edits) rather than regenerating the file.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Interface | Interactive menu (C) | User sees current state and picks what to change |
| Operations | Full CRUD (C) | Add, edit, remove users/locations/infra |
| File strategy | Direct edit (A) | Preserves manual changes to world.py |
| New entity generation | Auto with review (B) | Deterministic generation, user confirms before apply |

---

## 1. Invocation

`/fd-world` — no arguments. Requires existing workspace (`fake_data/manifest.py`).

## 2. Phase 1 — Status Overview

Read `fake_data/world.py` and display:

```
FAKE_DATA World: <ORG_NAME>

  Locations (<N>):
    <LOC_ID>  <city>, <country>   <N> users

  Users (<N>):
    <N> user, <N> power_user, <N> admin, <N> service_account

  Infrastructure (<N>):
    <hostname> (<role>), ...

  Network:
    <LOC_ID>: <subnet>

What would you like to do?
  1. Add users
  2. Add location
  3. Add infrastructure
  4. Edit user
  5. Edit location
  6. Edit infrastructure
  7. Remove user(s)
  8. Remove location
  9. Remove infrastructure
  10. Done
```

If world.py lacks INFRASTRUCTURE or role fields (basic world.py from early init), show what's available and note missing sections.

## 3. Phase 2 — Operations

### 3.1 Add users

Questions:
- "How many? [10]"
- "Which location? [<first location>]"
- "Role distribution? [auto — 70% user, 15% power_user, 10% admin, 5% service_account]"

Generate deterministically using the same logic as fd-init:
- Names from plugin's `data/names_sample.py` (avoid duplicates with existing users)
- Sequential workstation IPs from location's subnet
- Deterministic MAC addresses, GUIDs, workstations
- Manager assignment for user/power_user roles

Review gate: "Adding 10 users to HQ1: 7 user, 2 power_user, 1 admin. OK? [yes/edit/cancel]"

### 3.2 Add location

Questions:
- "Location ID? (e.g., OFF2, DC1)"
- "City?"
- "Country code? (e.g., US, GB, NO)"
- "Employee percentage? (current total: 100%, will be rebalanced)"

Auto-generate:
- Subnet: next available 10.X.0.0/16 (scan existing subnets)
- Gateway: 10.X.0.1
- DNS: 10.X.0.53
- EXTERNAL_IP_POOL entries from country_ip_ranges.py

Review gate before applying.

### 3.3 Add infrastructure

Questions:
- "Type? (firewall/switch/server/wap/load_balancer/other)"
- "Location? [<first location>]"
- "How many? [1]"

Auto-generate:
- Hostname: `<TYPE_PREFIX>-<LOC>-<NN>` (e.g., FW-HQ1-02)
- IP: next available from location's infrastructure subnet range

Review gate before applying.

### 3.4 Edit user/location/infrastructure

- List entities with index numbers
- User picks one
- Show current fields
- "Which field to edit? (username/role/location/department/...)"
- User provides new value
- Review gate: "Change <field> from '<old>' to '<new>'? [yes/no]"

### 3.5 Remove user(s)/location/infrastructure

- List entities with index numbers
- User picks one or more (comma-separated)
- Warning: "Removing <entity>. Generators or scenarios referencing this may break. Confirm? [yes/no]"
- For location removal: also warn about users at that location

## 4. Phase 3 — Review Gate

After each operation, show a summary of what will change:
```
Changes to apply:
  + 10 new users at HQ1
  ~ Updated USERS list (100 -> 110 entries)

Apply? [yes/no]
```

## 5. Phase 4 — Apply

Use Claude Code's Edit tool to make surgical changes to world.py:
- Add entries: insert new dict entries into USERS/LOCATIONS/INFRASTRUCTURE/NETWORK_CONFIG lists
- Edit entries: replace specific field values
- Remove entries: remove dict entries from lists

After applying, return to Phase 1 (menu) for additional operations. User selects "Done" to exit.

## 6. Handoff

On exit:
```
World updated: fake_data/world.py

Changes this session:
  + 10 users added to HQ1
  + 1 location added (OFF2, Oslo, NO)
  ~ 1 user role changed (jane.doe: user -> admin)

Tip: Run your generators to include new entities:
  python3 fake_data/main_generate.py --days=7
```

## 7. Scope Boundaries

**In scope:**
- fd-world SKILL.md
- CRUD for USERS, LOCATIONS, INFRASTRUCTURE, NETWORK_CONFIG, EXTERNAL_IP_POOL

**Out of scope:**
- Editing config.py (volume settings, output paths)
- Editing scenarios or generators
- Bulk import from CSV/JSON
- Undo/rollback (user can git checkout)

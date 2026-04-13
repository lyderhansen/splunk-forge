---
name: fd-world
description: View and modify the organization world state (users, locations, infrastructure). Interactive CRUD for world.py.
version: 0.1.0
---

# fd-world -- View and modify the organization world state

Interactive CRUD for users, locations, and infrastructure in `fake_data/world.py`.
Surgical editing preserves manual changes. Every mutation goes through a review gate
before applying.

**No arguments.** Requires an existing workspace (`fake_data/manifest.py`).

**Source of truth:** `docs/superpowers/specs/2026-04-12-fd-world-design.md`

---

## Phase A -- Pre-flight

### A.1 Find workspace root

Walk up from the current working directory looking for `fake_data/manifest.py`:

```
Check: ./fake_data/manifest.py
Check: ../fake_data/manifest.py
Check: ../../fake_data/manifest.py
(up to 5 levels)
```

If not found, stop:
> "No FAKE_DATA workspace found. Run `/fd-init` first."

If found, set the workspace root to the directory containing `fake_data/`.

### A.2 Read and parse world.py

Use the **Read tool** to read `fake_data/world.py` in its entirety.

Parse the following from the file contents:

| Symbol | Required | Notes |
|---|---|---|
| `ORG_NAME` | yes | String constant |
| `LOCATIONS` | yes | Dict keyed by location ID |
| `USERS` | yes | List of dicts. Count total, and count by `role` field if present |
| `INFRASTRUCTURE` | no | List of dicts. May not exist in basic world.py |
| `NETWORK_CONFIG` | yes | Dict keyed by location ID |
| `EXTERNAL_IP_POOL` | yes | List of CIDR strings |
| `EXTERNAL_IP_POOL_BY_COUNTRY` | no | Dict keyed by country code |
| `ROLES` | no | List of role strings. May not exist in basic world.py |

Determine the **world.py variant**:

- **Enriched:** USERS entries have `role`, `workstation_ip`, `mac_address`, `workstation`, `user_id`, `phone`, `manager` fields. INFRASTRUCTURE section exists.
- **Basic:** USERS entries only have `username`, `email`, `location`, `department` (and possibly `full_name`). No INFRASTRUCTURE section.

Note the variant -- it affects how add/edit operations work.

---

## Phase B -- Status overview

Display a formatted status overview of the world state:

```
FAKE_DATA World: <ORG_NAME>

  Locations (<N>):
    <LOC_ID>  <city>, <country>   <N> users

  Users (<N>):
    <N> user, <N> power_user, <N> admin, <N> service_account
```

If the world.py is **basic** (no role field), show users by location only:

```
  Users (<N>):
    <N> at HQ1, <N> at OFF1
    (basic world.py -- no role/workstation fields)
```

If INFRASTRUCTURE exists:

```
  Infrastructure (<N>):
    <hostname> (<role>), ...
```

If INFRASTRUCTURE does NOT exist:

```
  Infrastructure: (not present -- will be created when you add infrastructure)
```

Show network summary:

```
  Network:
    <LOC_ID>: <subnet>
```

Then show the interactive menu:

```
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

Wait for the user to pick a number. If they pick an infrastructure operation (3, 6, 9) and INFRASTRUCTURE does not exist yet, note that the section will be created.

---

## Phase C -- Execute operation

Based on the user's menu choice, execute one of the following operations.
Each operation ends with a **review gate** (Phase D) before applying changes (Phase E).

---

### Operation 1: Add users

Ask these questions one at a time:

> "How many users to add? [10]"

> "Which location? [<first location ID>]"

List available locations with their IDs for reference.

> "Role distribution? [auto -- 70% user, 15% power_user, 10% admin, 5% service_account]"

Accept "auto" for the default distribution, or let the user specify counts
(e.g. "5 user, 3 power_user, 2 admin").

**Generate users deterministically:**

1. **Load name data** from the plugin repo using the Read tool:
   `../../data/names_sample.py` (relative to this SKILL.md)
   Extract `FIRST_NAMES` and `LAST_NAMES` lists.

2. **Collect existing usernames** from the current USERS list to avoid duplicates.

3. For each new user, generate:
   - **first_name, last_name:** Pick from the loaded name lists. Cycle through
     if needed. Skip any combination that would create a duplicate username.
   - **username:** `firstname.lastname` (lowercase). If duplicate with existing
     users, append a digit (e.g. `john.smith2`).
   - **full_name:** `Firstname Lastname`
   - **email:** `username@<TENANT>`
   - **location:** The chosen location ID
   - **department:** Cycle through `["engineering", "sales", "marketing", "finance", "hr", "it", "operations"]`.
     Admins and service accounts always get `"it"`.
   - **role:** From the distribution above

   If the world.py is **enriched** (or we are upgrading a basic world.py),
   also generate these fields:
   - **title:** Derive from role + department (e.g. role=admin + dept=it -> "IT Administrator")
   - **user_id:** Deterministic GUID: `uuid.uuid5(uuid.NAMESPACE_DNS, ORG_NAME.lower() + "." + username)` -- write the computed string
   - **workstation:** `WS-<LOC>-<NNN>` where NNN is zero-padded, sequential
     after the highest existing workstation number at that location.
     Service accounts get `SRV-<LOC>-<NN>`.
   - **workstation_ip:** Next sequential IP from the location's subnet.
     Parse NETWORK_CONFIG to find the subnet. Start at `.10.1` offset from
     subnet base (to leave room for infrastructure). Continue from the highest
     existing workstation_ip at that location.
   - **mac_address:** Deterministic: `AA:BB:CC:<loc_octet>:<hi>:<lo>` where
     loc_octet is derived from location index, and hi:lo increment per user.
   - **phone:** `+1-555-<NNNN>` where NNNN continues from highest existing.
     Service accounts get `null`.
   - **manager:** For user/power_user roles, pick an admin or power_user from
     the same location. For admin and service_account, set to `null`.

   When adding users to a **basic** world.py, include the enriched fields.
   This effectively upgrades the world.py. Also add a `ROLES` constant if
   it does not exist:
   ```python
   ROLES = ["user", "power_user", "admin", "service_account"]
   ```

4. Proceed to **Phase D** (review gate) showing a summary:
   > "Adding <N> users to <LOC>: <N> user, <N> power_user, <N> admin, <N> service_account. Apply? [yes/no]"

---

### Operation 2: Add location

Ask these questions one at a time:

> "Location ID? (e.g., OFF2, DC1)"

Validate: uppercase, no spaces, not already in LOCATIONS.

> "City?"

> "Country code? (e.g., US, GB, NO)"

Validate: 2-letter ISO code.

> "Employee percentage? (current total: <sum of existing pcts>%, will be rebalanced)"

**Auto-generate network config:**

1. **Subnet:** Scan existing subnets in NETWORK_CONFIG to find the next available
   `10.X.0.0/16` block. For example, if HQ1 uses `10.10.0.0/16` and OFF1 uses
   `10.20.0.0/16`, assign `10.30.0.0/16`.
2. **Gateway:** `10.X.0.1`
3. **DNS:** `10.X.0.53`

**Auto-generate external IP pool entries:**

1. Load country IP ranges from the plugin repo using the Read tool:
   `../../data/country_ip_ranges.py` (relative to this SKILL.md)
2. Look up the country code in `COUNTRY_RANGES`.
3. Add those ranges to `EXTERNAL_IP_POOL` (if not already present).
4. Add an entry to `EXTERNAL_IP_POOL_BY_COUNTRY` for the new country (if not
   already present).

**Compose the location entry:**

```python
"<LOC_ID>": {
    "name": "<name derived from city or user input>",
    "city": "<city>",
    "country": "<country_code>",
    "timezone": "<auto-detected from city/country>",
    "employee_pct": <percentage>,
},
```

Proceed to **Phase D** (review gate).

---

### Operation 3: Add infrastructure

If INFRASTRUCTURE does not exist in world.py, note that it will be created
as a new section.

Ask these questions one at a time:

> "Type? (firewall/switch/server/wap/load_balancer/other)"

> "Location? [<first location ID>]"

List available locations.

> "How many? [1]"

**Auto-generate infrastructure entries:**

For each device, generate:
- **hostname:** `<TYPE_PREFIX>-<LOC>-<NN>` where TYPE_PREFIX is:
  - firewall -> `FW`
  - switch -> `SW`
  - server -> `SRV`
  - wap -> `WAP`
  - load_balancer -> `LB`
  - router -> `RTR`
  - proxy -> `PRX`
  - vpn_gateway -> `VPN`
  - directory_server -> `DS`
  - file_server -> `FS`
  - web_server -> `WEB`
  - database -> `DB`
  - mail_server -> `MAIL`
  - log_collector -> `LOG`
  - plc -> `PLC`
  - hmi -> `HMI`
  - other -> `DEV`

  NN is zero-padded, sequential after the highest existing device of that
  type at that location (e.g. if FW-HQ1-01 exists, next is FW-HQ1-02).

- **ip:** Next available from the location's infrastructure subnet range.
  Infrastructure IPs use the `.0.x` range of the subnet (e.g. `10.10.0.2`,
  `10.10.0.3`, etc.). Scan existing INFRASTRUCTURE entries at that location
  to find the next available IP.

- **location:** The chosen location ID.
- **role:** The device type.
- **description:** Auto-generated from type (e.g. "Perimeter firewall",
  "Core switch", "General purpose server", "Wireless access point").

Each entry is a dict:
```python
{"hostname": "FW-HQ1-02", "ip": "10.10.0.4", "location": "HQ1", "role": "firewall", "description": "Perimeter firewall"}
```

Proceed to **Phase D** (review gate).

---

### Operation 4: Edit user

1. Display users with index numbers (show username, location, department,
   and role if available):

```
Users:
  [1] aaron.wallace     HQ1   engineering   user
  [2] abigail.campbell  HQ1   sales         user
  ...
```

For large user lists (>30), ask:
> "Filter by location or search by name? [show all]"

2. User picks an index number.

3. Show all fields of the selected user:
```
Editing: aaron.wallace
  username:       aaron.wallace
  full_name:      Aaron Wallace
  email:          aaron.wallace@examplecorp.com
  location:       HQ1
  department:     engineering
  role:           user
  ...
```

4. Ask:
> "Which field to edit? (username/full_name/email/location/department/role/...)"

5. User provides the field name.

6. Ask:
> "New value for <field>?"

7. Proceed to **Phase D** (review gate) showing:
> "Change <field> from '<old_value>' to '<new_value>'? Apply? [yes/no]"

If the user changes `username`, also update `email` to match (unless they
explicitly set email separately). If the user changes `location`, offer to
update `workstation`, `workstation_ip`, and `mac_address` to match the new
location's subnet and naming conventions.

---

### Operation 5: Edit location

1. Display locations with index numbers:
```
Locations:
  [1] HQ1   Headquarters, New York, US   60 users
  [2] OFF1  Branch Office, London, GB    40 users
```

2. User picks an index number.

3. Show all fields of the selected location.

4. Ask which field to edit and the new value.

5. Proceed to **Phase D** (review gate) showing old and new values.

---

### Operation 6: Edit infrastructure

1. If INFRASTRUCTURE does not exist, inform the user:
> "No infrastructure defined. Use option 3 (Add infrastructure) first."
Return to Phase B menu.

2. Display infrastructure with index numbers:
```
Infrastructure:
  [1] FW-HQ1-01    firewall   10.10.0.1   HQ1   Perimeter firewall
  [2] SW-HQ1-01    switch     10.10.0.2   HQ1   Core switch
  ...
```

3. User picks an index number.

4. Show all fields. Ask which field to edit and the new value.

5. Proceed to **Phase D** (review gate).

---

### Operation 7: Remove user(s)

1. Display users with index numbers (same as Operation 4 step 1).

2. Ask:
> "Which user(s) to remove? (enter index numbers, comma-separated)"

3. Show a warning:
> "Removing <N> user(s): <username1>, <username2>, ...
> Generators or scenarios referencing these users may break.
> Confirm? [yes/no]"

This IS the review gate for remove operations -- proceed directly to Phase E
on "yes".

---

### Operation 8: Remove location

1. Display locations with index numbers and user counts.

2. User picks a location.

3. Show warning:
> "Removing location <LOC_ID> (<city>, <country>).
> This location has <N> users and <N> infrastructure devices.
> Users and infrastructure at this location will also be removed.
> Generators or scenarios referencing this location may break.
> Confirm? [yes/no]"

On "yes", remove:
- The location from LOCATIONS
- Its entry from NETWORK_CONFIG
- All users at that location from USERS
- All infrastructure at that location from INFRASTRUCTURE (if exists)
- Its external IP entries from EXTERNAL_IP_POOL and EXTERNAL_IP_POOL_BY_COUNTRY
  (only if no other location shares the same country)

Proceed directly to Phase E on "yes".

---

### Operation 9: Remove infrastructure

1. If INFRASTRUCTURE does not exist, inform the user and return to menu.

2. Display infrastructure with index numbers.

3. Ask:
> "Which device(s) to remove? (enter index numbers, comma-separated)"

4. Show warning:
> "Removing <N> device(s): <hostname1>, <hostname2>, ...
> Generators or scenarios referencing these devices may break.
> Confirm? [yes/no]"

Proceed directly to Phase E on "yes".

---

## Phase D -- Review gate

For add and edit operations, show a summary of what will change before applying:

```
Changes to apply:
  + <N> new users at <LOC>
  ~ Updated USERS list (<old_count> -> <new_count> entries)
```

Or for edits:

```
Changes to apply:
  ~ <entity_type>[<identifier>].<field>: '<old_value>' -> '<new_value>'
```

Or for new location:

```
Changes to apply:
  + Location <LOC_ID> (<city>, <country>)
  + NETWORK_CONFIG entry: <subnet>
  + EXTERNAL_IP_POOL entries for <country>
```

Ask:

> "Apply? [yes/no]"

- **yes:** Proceed to Phase E.
- **no:** Discard changes and return to Phase B menu.

---

## Phase E -- Apply changes

Use the **Edit tool** to make surgical changes to `fake_data/world.py`.
Each change uses a targeted find-and-replace to preserve all other content
in the file.

### For add operations (users, location, infrastructure):

**Adding users:**
Find the closing bracket `]` of the USERS list. Insert the new user dicts
immediately before it. Each new entry should be on a single line matching
the existing format:

```python
    {"username": "new.user", "full_name": "New User", "email": "new.user@examplecorp.com", ...},
```

If upgrading a basic world.py to enriched format:
1. Add `ROLES = ["user", "power_user", "admin", "service_account"]` after the
   INDUSTRY constant (or after ORG_NAME if no INDUSTRY).
2. Add the enriched fields to each new user entry.
3. Do NOT retroactively add enriched fields to existing basic users. Only new
   users get the full field set. The user can use Edit operations to enrich
   existing users individually if desired.

**Adding a location:**
1. Find the closing `}` of the LOCATIONS dict. Insert the new location entry
   before it.
2. Find the closing `}` of NETWORK_CONFIG. Insert the new network entry.
3. If new country IP ranges are needed, find the closing `]` of EXTERNAL_IP_POOL
   and insert before it (before the fallback entries).
4. If EXTERNAL_IP_POOL_BY_COUNTRY exists, add the new country entry.

**Adding infrastructure:**
- If INFRASTRUCTURE section exists: find the closing `]` of the INFRASTRUCTURE
  list and insert new entries before it.
- If INFRASTRUCTURE does NOT exist: insert a new section after EXTERNAL_IP_POOL
  (or EXTERNAL_IP_POOL_BY_COUNTRY if it exists). Create the full section:

```python

# =============================================================================
# INFRASTRUCTURE
# =============================================================================

INFRASTRUCTURE = [
    {"hostname": "...", "ip": "...", "location": "...", "role": "...", "description": "..."},
]
```

Also add helper functions if they do not exist:
```python
def infra_at_location(location_id: str) -> List[Dict]:
    """Return all infrastructure devices at a given location."""
    return [d for d in INFRASTRUCTURE if d["location"] == location_id]

def infra_by_role(role: str) -> List[Dict]:
    """Return all infrastructure devices with a given role."""
    return [d for d in INFRASTRUCTURE if d["role"] == role]

def get_infra_by_hostname(hostname: str) -> Optional[Dict]:
    """Look up an infrastructure device by hostname."""
    for d in INFRASTRUCTURE:
        if d["hostname"] == hostname:
            return d
    return None
```

### For edit operations:

Find the specific value being changed and replace it. For example, to change
a user's department from "engineering" to "sales", find the exact dict entry
line and replace the old value with the new one.

Use the Edit tool with enough surrounding context to ensure uniqueness of
the match string.

### For remove operations:

Find the dict entry (or entries) to remove and delete them. For user removal,
find and remove the entire line(s) containing the user dict(s). Ensure no
trailing comma issues by checking the surrounding context.

### After applying:

Re-read the updated `fake_data/world.py` using the Read tool to verify the
edit was applied correctly. If the file looks malformed, fix it immediately.

Then return to **Phase B** (status overview and menu) for additional operations.

---

## Phase F -- Handoff (on "Done")

When the user selects option 10 (Done), show a session summary:

```
World updated: fake_data/world.py

Changes this session:
  + <N> users added to <LOC>
  + 1 location added (<LOC_ID>, <city>, <country>)
  ~ 1 user role changed (<username>: <old_role> -> <new_role>)
  - 2 users removed (<username1>, <username2>)
  ...

Tip: Run your generators to include new entities:
  python3 fake_data/main_generate.py --days=7
```

If no changes were made this session:

```
No changes made. World state is unchanged.
```

# Plan X1: Framework Core + Init + Add-Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the first functional version of the FAKE_DATA plugin — a user installs the plugin, runs `/fake-data:init` to create a workspace, runs `/fake-data:add-generator` to scaffold a generator, then runs `python3 fake_data/main_generate.py` to produce log files.

**Architecture:** Claude Code plugin with skills (SKILL.md files) that read templates and data from the plugin repo and write Python files into the user's workspace. All runtime code is stdlib-only Python 3.9+. Generator discovery is filesystem-based via `SOURCE_META` dicts. No YAML/JSON parsers, no pip dependencies.

**Tech Stack:** Python 3.9+ stdlib, Claude Code plugin system (SKILL.md skills), Markdown

**Spec:** `docs/superpowers/specs/2026-04-12-plan-x1-design.md`

---

## File Map

### Files to create in this plan

**Plugin data files (read by skills at invocation time, not copied to user):**
- `data/names_sample.py` — ~200 first names + ~200 last names for deterministic user generation
- `data/country_ip_ranges.py` — ~20 countries mapped to public CIDR ranges

**Template files (copied or templated into user's workspace by init):**
- `templates/runtime/config.py` — defaults, volume params, hour activity curves, `get_output_path()`
- `templates/runtime/time_utils.py` — timestamp formatters, `calc_natural_events()`
- `templates/runtime/main_generate.py` — orchestrator with filesystem discovery + topological sort
- `templates/generators/_template_generator.py` — generator skeleton used by add-generator

**Skill files:**
- `.claude/skills/init/SKILL.md` — interactive workspace creation wizard
- `.claude/skills/add-generator/SKILL.md` — generator scaffolding (wizard + sample mode)

**Placeholder directories:**
- `presets/README.md` + `presets/.gitkeep`

### Files to modify

- `CLAUDE.md` — update status to reflect X1 completion
- `CHANGEHISTORY.md` — add entry for X1

### Verification approach

This is a Claude Code plugin, not a pytest project. "Tests" are canary runs: invoke the skill in a scratch directory and verify the output. Each task that produces a Python file includes a standalone verification step (`python3 -c "import ..."` or `python3 <file> --help`).

---

## Task Index

| # | Task | Creates | Depends on |
|---|---|---|---|
| 1 | Data: names_sample.py | `data/names_sample.py` | — |
| 2 | Data: country_ip_ranges.py | `data/country_ip_ranges.py` | — |
| 3 | Template: config.py | `templates/runtime/config.py` | — |
| 4 | Template: time_utils.py | `templates/runtime/time_utils.py` | Task 3 |
| 5 | Template: main_generate.py | `templates/runtime/main_generate.py` | Tasks 3, 4 |
| 6 | Template: _template_generator.py | `templates/generators/_template_generator.py` | Tasks 3, 4 |
| 7 | Presets placeholder | `presets/README.md`, `presets/.gitkeep` | — |
| 8 | Skill: init/SKILL.md | `.claude/skills/init/SKILL.md` | Tasks 1-6 |
| 9 | Skill: add-generator/SKILL.md | `.claude/skills/add-generator/SKILL.md` | Tasks 3-6 |
| 10 | Update CLAUDE.md + CHANGEHISTORY.md | docs | Tasks 1-9 |
| 11 | End-to-end canary test | — | Tasks 1-10 |

---

### Task 1: Data — names_sample.py

**Files:**
- Create: `data/names_sample.py`

- [ ] **Step 1: Create `data/names_sample.py` with ~200 first names and ~200 last names**

Write a Python module with two lists. Names should be generic, multicultural, and not tied to any specific company. The init skill uses these to generate deterministic USERS lists.

```python
"""Bundled name lists for deterministic user generation.

Used by the init skill to produce USERS lists without external dependencies.
~200 first names and ~200 last names, mixed gender and cultural origin.
Not exhaustive — just enough for realistic-looking employee directories
up to ~500 people (beyond that, duplicates will appear).
"""

FIRST_NAMES = [
    "Aaron", "Abigail", "Adam", "Adrian", "Aisha", "Alex", "Alice", "Amir",
    "Amy", "Andrea", "Andrew", "Angela", "Anna", "Anthony", "Arjun", "Ashley",
    "Benjamin", "Beth", "Blake", "Brandon", "Brian", "Bridget", "Cameron",
    "Carlos", "Carmen", "Caroline", "Catherine", "Charles", "Charlotte", "Chen",
    "Chris", "Christina", "Claire", "Colin", "Connor", "Courtney", "Craig",
    "Daniel", "David", "Dean", "Diana", "Diego", "Donna", "Dylan",
    "Edward", "Elena", "Elizabeth", "Emily", "Emma", "Eric", "Erik", "Eva",
    "Fatima", "Felix", "Fiona", "Frances", "Frank", "Gabriel", "Gary", "George",
    "Grace", "Graham", "Grant", "Hannah", "Harold", "Hassan", "Heather", "Helen",
    "Henry", "Holly", "Hugo", "Ian", "Ibrahim", "Ingrid", "Isaac", "Isabella",
    "Jack", "Jacob", "James", "Jane", "Janet", "Jason", "Jennifer", "Jessica",
    "Jill", "Joan", "Joel", "John", "Jonathan", "Jordan", "Joseph", "Julia",
    "Justin", "Karen", "Karl", "Kate", "Katherine", "Keith", "Kelly", "Kenneth",
    "Kevin", "Kim", "Kyle", "Laura", "Lauren", "Lawrence", "Leah", "Leo",
    "Linda", "Lisa", "Logan", "Louise", "Lucas", "Lucy", "Luis", "Luke",
    "Marcus", "Margaret", "Maria", "Mark", "Martin", "Mary", "Mason", "Matthew",
    "Maya", "Megan", "Michael", "Michelle", "Miguel", "Mohammed", "Monica",
    "Nancy", "Nathan", "Nicholas", "Nicole", "Nina", "Noah", "Nora", "Oliver",
    "Olivia", "Omar", "Oscar", "Pamela", "Patricia", "Patrick", "Paul", "Peter",
    "Philip", "Priya", "Rachel", "Ralph", "Rebecca", "Richard", "Robert", "Robin",
    "Roger", "Rosa", "Ross", "Ruby", "Ryan", "Samantha", "Samuel", "Sandra",
    "Sara", "Sarah", "Scott", "Sean", "Sharon", "Simon", "Sofia", "Sophia",
    "Stephen", "Steven", "Susan", "Tara", "Thomas", "Timothy", "Tracy", "Tyler",
    "Uma", "Valentina", "Vanessa", "Victor", "Victoria", "Vincent", "Virginia",
    "Walter", "Wayne", "Wei", "William", "Xavier", "Yasmin", "Yuki", "Zachary",
    "Zoe",
]

LAST_NAMES = [
    "Adams", "Ahmed", "Allen", "Alvarez", "Anderson", "Andrews", "Armstrong",
    "Baker", "Banks", "Barnes", "Barrett", "Bell", "Bennett", "Berg", "Black",
    "Blake", "Bond", "Boyd", "Bradley", "Brooks", "Brown", "Bryant", "Burns",
    "Butler", "Campbell", "Carter", "Castro", "Chan", "Chang", "Chapman",
    "Chen", "Clark", "Cole", "Coleman", "Collins", "Cook", "Cooper", "Cox",
    "Craig", "Cruz", "Daniels", "Davis", "Dean", "Diaz", "Dixon", "Douglas",
    "Edwards", "Ellis", "Evans", "Ferguson", "Fernandez", "Fisher", "Fleming",
    "Fletcher", "Ford", "Foster", "Fox", "Francis", "Freeman", "Garcia",
    "Gibson", "Gonzalez", "Gordon", "Graham", "Grant", "Gray", "Green",
    "Griffin", "Hall", "Hamilton", "Hansen", "Harper", "Harris", "Harrison",
    "Hart", "Harvey", "Hayes", "Henderson", "Henry", "Hernandez", "Hill",
    "Holland", "Holmes", "Howard", "Hughes", "Hunt", "Hunter", "Jackson",
    "James", "Jensen", "Johnson", "Jones", "Jordan", "Kelly", "Kennedy",
    "Kim", "King", "Knight", "Kumar", "Lane", "Larsen", "Lawrence", "Lee",
    "Lewis", "Li", "Lin", "Liu", "Lloyd", "Lopez", "Marshall", "Martin",
    "Martinez", "Mason", "Matthews", "McDonald", "Meyer", "Miller", "Mitchell",
    "Moore", "Morgan", "Morris", "Morrison", "Murphy", "Murray", "Nelson",
    "Newman", "Nguyen", "Nichols", "Nielsen", "Nolan", "O'Brien", "Oliver",
    "Olsen", "O'Neill", "Ortiz", "Owen", "Palmer", "Park", "Parker", "Patel",
    "Patterson", "Perez", "Perry", "Peters", "Peterson", "Phillips", "Porter",
    "Powell", "Price", "Quinn", "Ramirez", "Reed", "Reid", "Reyes", "Reynolds",
    "Richardson", "Riley", "Rivera", "Roberts", "Robinson", "Rodriguez", "Rogers",
    "Ross", "Russell", "Ryan", "Sanchez", "Sanders", "Santos", "Schmidt",
    "Scott", "Shaw", "Silva", "Simpson", "Singh", "Smith", "Spencer", "Stewart",
    "Stone", "Sullivan", "Suzuki", "Taylor", "Thomas", "Thompson", "Torres",
    "Turner", "Walker", "Wallace", "Walsh", "Wang", "Ward", "Watson", "Webb",
    "Wells", "West", "White", "Williams", "Wilson", "Wood", "Wright", "Wu",
    "Yang", "Young", "Zhang",
]
```

- [ ] **Step 2: Verify the module is importable**

Run:
```bash
cd /Users/joehanse/Library/CloudStorage/OneDrive-Cisco/Documents/03_Funny_Projects/GIT-FAKE-DATA/fake-data
python3 -c "from data.names_sample import FIRST_NAMES, LAST_NAMES; print(f'{len(FIRST_NAMES)} first, {len(LAST_NAMES)} last')"
```
Expected: `197 first, 203 last` (approximate — exact count depends on the list above)

- [ ] **Step 3: Commit**

```bash
git add data/names_sample.py
git commit -m "feat: add bundled name lists for deterministic user generation"
```

---

### Task 2: Data — country_ip_ranges.py

**Files:**
- Create: `data/country_ip_ranges.py`
- Create: `data/__init__.py`

- [ ] **Step 1: Create `data/__init__.py` (empty)**

```python
```

- [ ] **Step 2: Create `data/country_ip_ranges.py`**

```python
"""Publicly allocated IP ranges per country for geo-aware external IP pools.

Used by the init skill to auto-populate EXTERNAL_IP_POOL and
EXTERNAL_IP_POOL_BY_COUNTRY based on the countries in LOCATIONS.
Sourced from public RIR data for major ISPs and cloud providers.
Not intended as threat intelligence — just plausible-looking source IPs.

Each country has 1-3 CIDR ranges. These are large allocations from
well-known providers, not specific organizations.
"""

COUNTRY_RANGES = {
    "US": ["52.0.0.0/11", "104.16.0.0/12", "34.0.0.0/9"],
    "GB": ["51.140.0.0/14", "86.128.0.0/11", "20.68.0.0/14"],
    "DE": ["52.28.0.0/15", "85.214.0.0/16", "46.4.0.0/14"],
    "FR": ["51.15.0.0/16", "62.210.0.0/16", "176.31.0.0/16"],
    "NO": ["77.40.0.0/16", "193.213.112.0/20", "84.208.0.0/13"],
    "SE": ["46.246.0.0/16", "83.233.0.0/16", "213.115.0.0/16"],
    "DK": ["87.54.0.0/15", "130.225.0.0/16", "185.240.0.0/14"],
    "NL": ["145.131.0.0/16", "185.17.0.0/16", "31.186.0.0/15"],
    "IT": ["151.0.0.0/12", "79.0.0.0/10", "213.144.0.0/14"],
    "ES": ["88.0.0.0/11", "213.194.0.0/15", "37.14.0.0/15"],
    "CA": ["99.224.0.0/11", "70.24.0.0/13", "142.160.0.0/12"],
    "AU": ["1.120.0.0/13", "103.24.0.0/14", "49.176.0.0/12"],
    "JP": ["126.0.0.0/8", "133.0.0.0/8", "210.128.0.0/11"],
    "BR": ["177.0.0.0/8", "200.128.0.0/9", "189.0.0.0/11"],
    "IN": ["49.32.0.0/11", "106.192.0.0/10", "223.176.0.0/12"],
    "CN": ["1.80.0.0/12", "36.0.0.0/10", "112.0.0.0/10"],
    "RU": ["5.136.0.0/13", "77.72.0.0/14", "188.32.0.0/11"],
    "PL": ["83.0.0.0/11", "185.156.0.0/14", "188.146.0.0/15"],
    "IE": ["86.40.0.0/13", "185.8.0.0/14", "79.140.0.0/14"],
    "CH": ["85.0.0.0/13", "178.196.0.0/14", "188.60.0.0/14"],
}

# RFC 5737 TEST-NET ranges — guaranteed non-routable, used as fallback
# when a country is not in COUNTRY_RANGES.
FALLBACK_RANGES = [
    "198.51.100.0/24",  # TEST-NET-2
    "203.0.113.0/24",   # TEST-NET-3
]
```

- [ ] **Step 3: Verify**

Run:
```bash
python3 -c "from data.country_ip_ranges import COUNTRY_RANGES, FALLBACK_RANGES; print(f'{len(COUNTRY_RANGES)} countries, {len(FALLBACK_RANGES)} fallbacks')"
```
Expected: `20 countries, 2 fallbacks`

- [ ] **Step 4: Commit**

```bash
git add data/__init__.py data/country_ip_ranges.py
git commit -m "feat: add geo-IP lookup data for 20 countries"
```

---

### Task 3: Template — config.py

**Files:**
- Create: `templates/runtime/config.py`

This file is copied as-is into the user's workspace by init. It must be a valid, runnable Python module with no TA-FAKE-TSHRT-specific references.

- [ ] **Step 1: Create `templates/runtime/config.py`**

```python
#!/usr/bin/env python3
"""
Configuration module for FAKE_DATA generators.
Contains shared constants, volume parameters, and output path management.

Ported from TA-FAKE-TSHRT shared/config.py — all organization-specific
references removed. This file is generic and works with any world.py.
"""

from datetime import date
from pathlib import Path
from dataclasses import dataclass
from typing import List

# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

DEFAULT_START_DATE = "2026-01-01"
DEFAULT_DAYS = 31
DEFAULT_SCALE = 1.0

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

OUTPUT_BASE = Path(__file__).resolve().parent / "output"

OUTPUT_DIRS = {
    "network": OUTPUT_BASE / "network",
    "cloud": OUTPUT_BASE / "cloud",
    "windows": OUTPUT_BASE / "windows",
    "linux": OUTPUT_BASE / "linux",
    "web": OUTPUT_BASE / "web",
    "retail": OUTPUT_BASE / "retail",
    "collaboration": OUTPUT_BASE / "collaboration",
    "itsm": OUTPUT_BASE / "itsm",
    "erp": OUTPUT_BASE / "erp",
    "ot": OUTPUT_BASE / "ot",
    "unknown": OUTPUT_BASE / "unknown",
}


def get_output_path(category: str, filename: str) -> Path:
    """Get the full output path for a given category and filename.

    Supports nested subdirectories in filename, e.g.:
        get_output_path("cloud", "webex/webex_events.json")
        -> output/cloud/webex/webex_events.json
    """
    base = OUTPUT_DIRS.get(category, OUTPUT_BASE)
    full_path = base / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


def set_output_base(new_base: Path):
    """Redirect all generator output to a different base directory.

    Reserved for future test/production staging. In X1, all output goes
    to fake_data/output/ directly.
    """
    global OUTPUT_BASE, OUTPUT_DIRS
    OUTPUT_BASE = new_base
    OUTPUT_DIRS = {
        "network": OUTPUT_BASE / "network",
        "cloud": OUTPUT_BASE / "cloud",
        "windows": OUTPUT_BASE / "windows",
        "linux": OUTPUT_BASE / "linux",
        "web": OUTPUT_BASE / "web",
        "retail": OUTPUT_BASE / "retail",
        "collaboration": OUTPUT_BASE / "collaboration",
        "itsm": OUTPUT_BASE / "itsm",
        "erp": OUTPUT_BASE / "erp",
        "ot": OUTPUT_BASE / "ot",
        "unknown": OUTPUT_BASE / "unknown",
    }


# =============================================================================
# VOLUME CONFIGURATION
# =============================================================================

# Weekend traffic factors by source type (percentage of weekday traffic)
VOLUME_WEEKEND_FACTORS = {
    "default": 25,
    "cloud": 30,
    "auth": 20,
    "firewall": 80,
    "email": 75,
    "web": 110,
    "windows": 25,
    "ot": 90,
}

# Monday multiplier (post-weekend catch-up)
VOLUME_MONDAY_BOOST = 115  # 115% = 15% more traffic on Mondays

# Day-to-day noise range (percentage variation)
VOLUME_DAILY_NOISE_MIN = -15
VOLUME_DAILY_NOISE_MAX = 15

# =============================================================================
# HOUR ACTIVITY LEVELS
# =============================================================================

# Activity level per hour (0-100) for weekdays
HOUR_ACTIVITY_WEEKDAY = {
    0: 10, 1: 10, 2: 10, 3: 10, 4: 10, 5: 10,
    6: 20,
    7: 40,
    8: 70,
    9: 100, 10: 100, 11: 100,
    12: 85,
    13: 90, 14: 90, 15: 90,
    16: 70,
    17: 50,
    18: 30,
    19: 20, 20: 20, 21: 20,
    22: 15, 23: 15,
}

# Enterprise/office weekend pattern
HOUR_ACTIVITY_WEEKEND = {
    0: 5, 1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5,
    7: 10, 8: 10, 9: 10,
    10: 15, 11: 15, 12: 15, 13: 15, 14: 15,
    15: 10, 16: 10, 17: 10, 18: 10,
    19: 5, 20: 5, 21: 5, 22: 5, 23: 5,
}

# E-commerce/consumer weekend pattern
HOUR_ACTIVITY_WEEKEND_ECOMMERCE = {
    0: 15, 1: 10, 2: 8, 3: 5, 4: 5, 5: 5, 6: 8,
    7: 15, 8: 25, 9: 40,
    10: 60, 11: 75, 12: 80,
    13: 85, 14: 90, 15: 95,
    16: 100, 17: 100, 18: 100,
    19: 95, 20: 90, 21: 80,
    22: 50, 23: 30,
}

# Firewall/perimeter weekend pattern (mix of e-commerce + enterprise)
HOUR_ACTIVITY_WEEKEND_FIREWALL = {
    0: 12, 1: 8, 2: 7, 3: 5, 4: 5, 5: 5, 6: 7,
    7: 13, 8: 20, 9: 30,
    10: 45, 11: 55, 12: 55,
    13: 60, 14: 65, 15: 65,
    16: 70, 17: 70, 18: 70,
    19: 65, 20: 60, 21: 50,
    22: 35, 23: 20,
}


# =============================================================================
# SCENARIO SUPPORT (placeholder for add-scenario skill)
# =============================================================================

def expand_scenarios(scenarios: str) -> List:
    """Expand a scenario specification string into active scenario instances.

    In X1 this is a no-op placeholder. The add-scenario skill (future plan)
    will replace this with real implementation that loads scenario classes
    from fake_data/scenarios/ and returns active instances.

    Args:
        scenarios: Comma-separated list of scenario names, "all", or "none".

    Returns:
        Empty list (always, in X1).
    """
    return []


# =============================================================================
# CONFIG CLASS
# =============================================================================

@dataclass
class Config:
    """Configuration container for generators."""
    start_date: str = DEFAULT_START_DATE
    days: int = DEFAULT_DAYS
    scale: float = DEFAULT_SCALE
    scenarios: str = "none"
```

- [ ] **Step 2: Verify**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'templates/runtime')
from config import DEFAULT_START_DATE, DEFAULT_DAYS, get_output_path, HOUR_ACTIVITY_WEEKDAY, Config
print(f'start={DEFAULT_START_DATE}, days={DEFAULT_DAYS}')
print(f'hours={len(HOUR_ACTIVITY_WEEKDAY)}')
print(f'config={Config()}')
print('OK')
"
```
Expected: Prints defaults and `OK` without errors.

- [ ] **Step 3: Commit**

```bash
git add templates/runtime/config.py
git commit -m "feat: add config.py template with volume params and output paths"
```

---

### Task 4: Template — time_utils.py

**Files:**
- Create: `templates/runtime/time_utils.py`

Ported from TA-FAKE-TSHRT `shared/time_utils.py`. All five timestamp formatters plus `calc_natural_events()` and `date_add()`. No org-specific references.

- [ ] **Step 1: Create `templates/runtime/time_utils.py`**

```python
#!/usr/bin/env python3
"""
Timestamp formatting and natural volume calculation utilities.

Provides consistent timestamp generation across all log formats and
realistic hourly/daily volume variation via calc_natural_events().

Ported from TA-FAKE-TSHRT shared/time_utils.py — generic, no org references.
"""

import random
from datetime import datetime, timedelta


def date_add(start_date: str, days: int) -> str:
    """Add days to a date string. Returns 'YYYY-MM-DD'."""
    dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)
    return dt.strftime("%Y-%m-%d")


def _base_datetime(start_date: str, day_offset: int, hour: int,
                   minute: int = 0, second: int = 0) -> datetime:
    """Build a datetime from generation parameters."""
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    return dt + timedelta(days=day_offset, hours=hour,
                          minutes=minute, seconds=second)


def ts_iso(start_date: str, day_offset: int, hour: int,
           minute: int = 0, second: int = 0) -> str:
    """ISO 8601 UTC timestamp: 2026-01-05T14:30:45Z

    Use for: JSON logs (AWS CloudTrail, GCP Audit, cloud APIs).
    """
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_iso_ms(start_date: str, day_offset: int, hour: int,
              minute: int = 0, second: int = 0, ms: int = 0) -> str:
    """ISO 8601 UTC with milliseconds: 2026-01-05T14:30:45.123Z

    Use for: JSON logs that include sub-second precision.
    """
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    dt = dt.replace(microsecond=ms * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def ts_syslog(start_date: str, day_offset: int, hour: int,
              minute: int = 0, second: int = 0) -> str:
    """Syslog timestamp: Jan 05 2026 14:30:45

    Use for: Syslog-format logs (Cisco ASA, Meraki, Catalyst).
    """
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%b %d %Y %H:%M:%S")


def ts_cef(start_date: str, day_offset: int, hour: int,
           minute: int = 0, second: int = 0) -> str:
    """CEF header timestamp: Jan 05 2026 14:30:45 UTC

    Use for: CEF-format syslog (Cyber Vision, generic CEF sources).
    """
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%b %d %Y %H:%M:%S") + " UTC"


def ts_perfmon(start_date: str, day_offset: int, hour: int,
               minute: int = 0, second: int = 0, ms: int = 0) -> str:
    """Windows Perfmon timestamp: 01/05/2026 14:30:45.123

    Use for: Windows performance monitor logs.
    """
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%m/%d/%Y %H:%M:%S") + f".{ms:03d}"


def calc_natural_events(base_count: int, start_date: str, day_offset: int,
                        hour: int, category: str) -> int:
    """Calculate a natural event count with realistic variation.

    Applies:
    - Hourly activity curve (different for weekday vs weekend)
    - Weekend traffic factor (by source category)
    - Monday boost (post-weekend catch-up)
    - Daily noise (random +-15%)

    Args:
        base_count: Base events per hour at peak (activity level 100).
        start_date: Generation start date (YYYY-MM-DD).
        day_offset: Day number (0-based) from start_date.
        hour: Hour of day (0-23).
        category: Volume category — one of 'firewall', 'cloud', 'auth',
                  'web', 'email', 'ot'. Controls weekend factors and
                  hourly curves.

    Returns:
        Integer event count for this hour, never less than 0.
    """
    # Import here to avoid circular import at module level
    from config import (
        VOLUME_WEEKEND_FACTORS, VOLUME_MONDAY_BOOST,
        VOLUME_DAILY_NOISE_MIN, VOLUME_DAILY_NOISE_MAX,
        HOUR_ACTIVITY_WEEKDAY, HOUR_ACTIVITY_WEEKEND,
        HOUR_ACTIVITY_WEEKEND_ECOMMERCE, HOUR_ACTIVITY_WEEKEND_FIREWALL,
    )

    dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day_offset)
    weekday = dt.weekday()  # 0=Monday, 6=Sunday
    is_weekend = weekday >= 5
    is_monday = weekday == 0

    # Pick hourly activity curve
    if is_weekend:
        if category == "web":
            activity = HOUR_ACTIVITY_WEEKEND_ECOMMERCE.get(hour, 10)
        elif category == "firewall":
            activity = HOUR_ACTIVITY_WEEKEND_FIREWALL.get(hour, 10)
        else:
            activity = HOUR_ACTIVITY_WEEKEND.get(hour, 10)
    else:
        activity = HOUR_ACTIVITY_WEEKDAY.get(hour, 10)

    # Base calculation: scale by activity level (0-100)
    count = base_count * (activity / 100.0)

    # Weekend factor
    if is_weekend:
        weekend_factor = VOLUME_WEEKEND_FACTORS.get(
            category, VOLUME_WEEKEND_FACTORS["default"]
        )
        count = count * (weekend_factor / 100.0)

    # Monday boost
    if is_monday:
        count = count * (VOLUME_MONDAY_BOOST / 100.0)

    # Daily noise
    noise = random.randint(VOLUME_DAILY_NOISE_MIN, VOLUME_DAILY_NOISE_MAX)
    count = count * (1 + noise / 100.0)

    return max(0, int(count))
```

- [ ] **Step 2: Verify all timestamp functions**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'templates/runtime')
from time_utils import ts_iso, ts_iso_ms, ts_syslog, ts_cef, ts_perfmon, date_add
print(ts_iso('2026-01-05', 0, 14, 30, 45))
print(ts_iso_ms('2026-01-05', 0, 14, 30, 45, 123))
print(ts_syslog('2026-01-05', 0, 14, 30, 45))
print(ts_cef('2026-01-05', 0, 14, 30, 45))
print(ts_perfmon('2026-01-05', 0, 14, 30, 45, 123))
print(date_add('2026-01-01', 14))
"
```
Expected:
```
2026-01-05T14:30:45Z
2026-01-05T14:30:45.123Z
Jan 05 2026 14:30:45
Jan 05 2026 14:30:45 UTC
01/05/2026 14:30:45.123
2026-01-15
```

- [ ] **Step 3: Verify calc_natural_events**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'templates/runtime')
from time_utils import calc_natural_events
# Wednesday at 10am (peak) should give roughly base_count
count = calc_natural_events(100, '2026-01-07', 0, 10, 'firewall')
print(f'Wed 10am: {count} (expect ~85-115)')
# Saturday at 3am should be much lower
count = calc_natural_events(100, '2026-01-10', 0, 3, 'cloud')
print(f'Sat 3am: {count} (expect ~0-5)')
print('OK')
"
```
Expected: Two numbers within rough ranges, then `OK`.

- [ ] **Step 4: Commit**

```bash
git add templates/runtime/time_utils.py
git commit -m "feat: add time_utils.py template with timestamp formatters and volume calc"
```

---

### Task 5: Template — main_generate.py

**Files:**
- Create: `templates/runtime/main_generate.py`

The orchestrator. Discovers generators via filesystem scan + `SOURCE_META`, runs them in topological order, shows progress. This is copied as-is to the user's workspace.

- [ ] **Step 1: Create `templates/runtime/main_generate.py`**

```python
#!/usr/bin/env python3
"""
FAKE_DATA log generator orchestrator.

Discovers generators in fake_data/generators/, sorts them by dependency
order, and runs them to produce log files in fake_data/output/.

Usage:
    python3 fake_data/main_generate.py [--sources=all] [--days=31] [--quiet]
    python3 fake_data/main_generate.py --list
    python3 fake_data/main_generate.py --show-files
    python3 fake_data/main_generate.py --help
"""

import argparse
import importlib
import pkgutil
import sys
import time as time_mod
from pathlib import Path
from typing import Dict, List, Any, Optional

# Bootstrap: ensure fake_data package is importable regardless of cwd
_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Version gate
if sys.version_info < (3, 9):
    print("ERROR: FAKE_DATA requires Python 3.9+. "
          f"You are running {sys.version_info.major}.{sys.version_info.minor}.",
          file=sys.stderr)
    sys.exit(1)

from fake_data.config import DEFAULT_START_DATE, DEFAULT_DAYS, DEFAULT_SCALE


def discover_generators() -> Dict[str, Any]:
    """Scan fake_data/generators/ for modules with SOURCE_META.

    Returns dict mapping source_id -> module object.
    Skips modules starting with '_' (e.g. _template_generator.py).
    """
    generators_dir = _script_dir / "generators"
    if not generators_dir.exists():
        return {}

    discovered = {}
    for finder, name, is_pkg in pkgutil.iter_modules([str(generators_dir)]):
        if name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"fake_data.generators.{name}")
        except (ImportError, SyntaxError) as e:
            print(f"WARNING: Could not import generators/{name}.py: {e}",
                  file=sys.stderr)
            continue

        meta = getattr(module, "SOURCE_META", None)
        if meta is None:
            print(f"WARNING: generators/{name}.py has no SOURCE_META, skipping.",
                  file=sys.stderr)
            continue

        source_id = meta.get("source_id", name.replace("generate_", ""))
        discovered[source_id] = module

    return discovered


def topological_sort(discovered: Dict[str, Any]) -> List[str]:
    """Sort source_ids by depends_on order. Raises ValueError on cycles."""
    graph = {}
    for sid, mod in discovered.items():
        deps = mod.SOURCE_META.get("depends_on", [])
        graph[sid] = [d for d in deps if d in discovered]

    visited = set()
    temp_mark = set()
    order = []

    def visit(node: str):
        if node in temp_mark:
            raise ValueError(f"Dependency cycle detected involving '{node}'")
        if node in visited:
            return
        temp_mark.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        temp_mark.remove(node)
        visited.add(node)
        order.append(node)

    for node in graph:
        visit(node)

    return order


def _progress_callback(source_id: str, day: int, total_days: int):
    """Print single-line progress update."""
    sys.stdout.write(f"\r  {source_id}: day {day + 1}/{total_days}   ")
    sys.stdout.flush()


def run_generators(discovered: Dict[str, Any], order: List[str],
                   args: argparse.Namespace) -> Dict[str, Any]:
    """Execute generators in order. Returns results dict."""
    results = {"success": {}, "errors": {}, "total_events": 0}
    total = len(order)

    for idx, source_id in enumerate(order, 1):
        module = discovered[source_id]
        meta = module.SOURCE_META
        func_name = f"generate_{source_id}_logs"
        func = getattr(module, func_name, None)

        if func is None:
            results["errors"][source_id] = f"Function {func_name}() not found"
            continue

        if not args.quiet:
            print(f"[{idx}/{total}] {source_id} ({meta.get('category', '?')})...")

        start_time = time_mod.time()
        try:
            result = func(
                start_date=args.start_date,
                days=args.days,
                scale=args.scale,
                scenarios=args.scenarios,
                progress_callback=None if args.quiet else _progress_callback,
                quiet=args.quiet,
            )
            elapsed = time_mod.time() - start_time

            if isinstance(result, dict):
                event_count = result.get("total", 0)
            else:
                event_count = result or 0

            results["success"][source_id] = {
                "events": event_count,
                "elapsed": elapsed,
            }
            results["total_events"] += event_count

            if not args.quiet:
                print(f"\r  {source_id}: {event_count:,} events "
                      f"in {elapsed:.1f}s")

        except Exception as e:
            elapsed = time_mod.time() - start_time
            results["errors"][source_id] = str(e)
            if not args.quiet:
                print(f"\r  {source_id}: ERROR after {elapsed:.1f}s — {e}",
                      file=sys.stderr)

    return results


def cmd_list(discovered: Dict[str, Any]):
    """Print a table of registered generators."""
    if not discovered:
        print("No generators registered. Run /fake-data:add-generator to create one.")
        return

    print(f"\n{'Source ID':<20} {'Category':<15} {'Depends On':<20} Description")
    print("-" * 80)
    for sid in sorted(discovered.keys()):
        meta = discovered[sid].SOURCE_META
        deps = ", ".join(meta.get("depends_on", [])) or "—"
        desc = meta.get("description", "")[:30]
        print(f"{sid:<20} {meta.get('category', '?'):<15} {deps:<20} {desc}")
    print(f"\n{len(discovered)} generator(s) registered.")


def cmd_show_files(discovered: Dict[str, Any]):
    """Print expected output files for all generators."""
    if not discovered:
        print("No generators registered.")
        return

    print("\nExpected output files:")
    for sid in sorted(discovered.keys()):
        meta = discovered[sid].SOURCE_META
        cat = meta.get("category", "unknown")
        print(f"  {sid}: output/{cat}/{sid}.log")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="FAKE_DATA log generator orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fake_data/main_generate.py --days=7 --quiet
  python3 fake_data/main_generate.py --sources=asa,aws --days=14
  python3 fake_data/main_generate.py --list
        """,
    )
    parser.add_argument("--sources", default="all",
                        help="Comma-separated source IDs, or 'all' (default: all)")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"Days to generate (default: {DEFAULT_DAYS})")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE,
                        help=f"Start date YYYY-MM-DD (default: {DEFAULT_START_DATE})")
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                        help=f"Volume scaling factor (default: {DEFAULT_SCALE})")
    parser.add_argument("--scenarios", default="none",
                        help="Scenario list (reserved for future use)")
    parser.add_argument("--list", action="store_true",
                        help="List registered generators and exit")
    parser.add_argument("--show-files", action="store_true",
                        help="Show expected output files and exit")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output")
    parser.add_argument("--test", action="store_true",
                        help="(Reserved for Splunk integration)")
    parser.add_argument("--no-test", action="store_true",
                        help="(Reserved for Splunk integration)")

    args = parser.parse_args()

    # Reserved flags
    if args.test or args.no_test:
        print("--test/--no-test flags are reserved for the upcoming "
              "Splunk integration plan.", file=sys.stderr)
        print("In the current version, all output goes to fake_data/output/.",
              file=sys.stderr)
        sys.exit(2)

    # Verify workspace
    try:
        from fake_data.manifest import FAKE_DATA_WORKSPACE_VERSION
        if FAKE_DATA_WORKSPACE_VERSION > 1:
            print(f"WARNING: This workspace uses schema version "
                  f"{FAKE_DATA_WORKSPACE_VERSION}, but this orchestrator "
                  f"only understands version 1. Some features may not work.",
                  file=sys.stderr)
    except ImportError:
        print("ERROR: fake_data/manifest.py not found. Is this a "
              "FAKE_DATA workspace?", file=sys.stderr)
        print("Run /fake-data:init to create one.", file=sys.stderr)
        sys.exit(1)

    # Discover
    discovered = discover_generators()

    # Info commands
    if args.list:
        cmd_list(discovered)
        return

    if args.show_files:
        cmd_show_files(discovered)
        return

    # Filter sources
    if args.sources != "all":
        requested = set(s.strip() for s in args.sources.split(","))
        missing = requested - set(discovered.keys())
        if missing:
            print(f"ERROR: Unknown source(s): {', '.join(sorted(missing))}",
                  file=sys.stderr)
            print(f"Available: {', '.join(sorted(discovered.keys()))}",
                  file=sys.stderr)
            sys.exit(1)
        # Include transitive dependencies
        to_run = set(requested)
        changed = True
        while changed:
            changed = False
            for sid in list(to_run):
                deps = discovered[sid].SOURCE_META.get("depends_on", [])
                for dep in deps:
                    if dep in discovered and dep not in to_run:
                        to_run.add(dep)
                        changed = True
        discovered = {k: v for k, v in discovered.items() if k in to_run}

    if not discovered:
        print("No generators to run. Use /fake-data:add-generator "
              "to create one.")
        return

    # Sort and run
    try:
        order = topological_sort(discovered)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"\nFAKE_DATA Generator — {len(order)} source(s), "
              f"{args.days} days, scale {args.scale}x\n")

    overall_start = time_mod.time()
    results = run_generators(discovered, order, args)
    overall_elapsed = time_mod.time() - overall_start

    # Summary
    if not args.quiet:
        print(f"\n{'=' * 50}")
        print(f"Total: {results['total_events']:,} events "
              f"in {overall_elapsed:.1f}s")
        if results["errors"]:
            print(f"Errors ({len(results['errors'])}):")
            for sid, err in results["errors"].items():
                print(f"  {sid}: {err}")
        print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify --help works**

Run:
```bash
python3 templates/runtime/main_generate.py --help
```
Expected: Prints usage info without errors. (Will warn about missing manifest.py — that is expected when running from templates/ directly.)

- [ ] **Step 3: Commit**

```bash
git add templates/runtime/main_generate.py
git commit -m "feat: add main_generate.py orchestrator with filesystem discovery"
```

---

### Task 6: Template — _template_generator.py

**Files:**
- Create: `templates/generators/_template_generator.py`

This is the skeleton that `add-generator` copies and fills in. It must be valid Python as-is (with placeholder values) so it can be imported and even run standalone for smoke testing.

- [ ] **Step 1: Create `templates/generators/_template_generator.py`**

```python
#!/usr/bin/env python3
"""
TEMPLATE generator — copy this file and customize for your data source.

Generated by fake-data:add-generator. This file is yours — edit freely.

Usage:
    Standalone:   python3 fake_data/generators/generate_TEMPLATE.py --days=1
    Orchestrator: python3 fake_data/main_generate.py --sources=TEMPLATE
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Bootstrap sys.path so this file runs standalone
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fake_data.world import USERS, LOCATIONS, NETWORK_CONFIG, EXTERNAL_IP_POOL
from fake_data.config import (
    DEFAULT_START_DATE, DEFAULT_DAYS, DEFAULT_SCALE,
    get_output_path, expand_scenarios,
)
from fake_data.time_utils import ts_iso, calc_natural_events, date_add

# =============================================================================
# SOURCE METADATA — read by main_generate.py for discovery and orchestration
# =============================================================================

SOURCE_META = {
    "source_id": "TEMPLATE",
    "category": "unknown",
    "source_groups": ["unknown"],
    "volume_category": "firewall",
    "multi_file": False,
    "depends_on": [],
    "description": "Template generator — replace with your source description",
}


# =============================================================================
# GENERATOR FUNCTION
# =============================================================================

def generate_TEMPLATE_logs(
    start_date: str = DEFAULT_START_DATE,
    days: int = DEFAULT_DAYS,
    scale: float = DEFAULT_SCALE,
    scenarios: str = "none",
    output_file: str = None,
    progress_callback=None,
    quiet: bool = False,
) -> int:
    """Generate TEMPLATE log events.

    Returns the number of events generated.
    """
    events = []
    active_scenarios = expand_scenarios(scenarios)

    for day in range(days):
        if progress_callback:
            progress_callback(SOURCE_META["source_id"], day, days)

        for hour in range(24):
            count = calc_natural_events(
                base_count=int(100 * scale),
                start_date=start_date,
                day_offset=day,
                hour=hour,
                category=SOURCE_META["volume_category"],
            )

            for _ in range(count):
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                events.append(_make_event(start_date, day, hour, minute, second))

            # Scenario events (future): active_scenarios would inject here
            # for scenario in active_scenarios:
            #     events.extend(scenario.source_hour(day, hour))

    # Sort by timestamp for realistic ordering
    events.sort(key=lambda e: e.get("timestamp", ""))

    # Write output
    output_path = Path(output_file) if output_file else get_output_path(
        SOURCE_META["category"],
        f"{SOURCE_META['source_id']}.log",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for event in events:
            f.write(_serialize(event) + "\n")

    if not quiet:
        print(f"  {SOURCE_META['source_id']}: {len(events):,} events "
              f"-> {output_path}")

    return len(events)


# =============================================================================
# EVENT CONSTRUCTION — customize these for your source
# =============================================================================

def _make_event(start_date: str, day: int, hour: int,
                minute: int, second: int) -> Dict:
    """Construct one log event. Customize fields for your source."""
    user = random.choice(USERS)
    return {
        "timestamp": ts_iso(start_date, day, hour, minute, second),
        "user": user["username"],
        "action": random.choice(["login", "logout", "access", "modify"]),
        "status": random.choice(["success", "failure"]),
        "source_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        # Scenario events (future) would set: "demo_id": <scenario_name>
        # Baseline events leave demo_id unset.
    }


def _serialize(event: Dict) -> str:
    """Serialize one event to a log line. Change for KV, syslog, CSV, etc."""
    return json.dumps(event)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=f"Generate {SOURCE_META['source_id']} logs")
    p.add_argument("--start-date", default=DEFAULT_START_DATE)
    p.add_argument("--days", type=int, default=DEFAULT_DAYS)
    p.add_argument("--scale", type=float, default=DEFAULT_SCALE)
    p.add_argument("--scenarios", default="none")
    p.add_argument("--output", default=None, help="Override output file path")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    count = generate_TEMPLATE_logs(
        start_date=args.start_date,
        days=args.days,
        scale=args.scale,
        scenarios=args.scenarios,
        output_file=args.output,
        quiet=args.quiet,
    )
    if not args.quiet:
        print(f"\nTotal: {count:,} events")
```

- [ ] **Step 2: Verify syntax is valid**

Run:
```bash
python3 -c "import ast; ast.parse(open('templates/generators/_template_generator.py').read()); print('Syntax OK')"
```
Expected: `Syntax OK`

Note: The file cannot be *run* from the templates directory because it imports `fake_data.world` which only exists in a user's workspace after init. Syntax check is sufficient here.

- [ ] **Step 3: Commit**

```bash
git add templates/generators/_template_generator.py
git commit -m "feat: add generator template skeleton with SOURCE_META convention"
```

---

### Task 7: Presets placeholder

**Files:**
- Create: `presets/README.md`
- Create: `presets/.gitkeep`

- [ ] **Step 1: Create `presets/README.md`**

```markdown
# Presets

This directory is reserved for pre-built source definitions for common log formats
(e.g. wineventlog, access_combined, cisco_asa, fortigate, aws_cloudtrail).

**Status:** Empty in X1. Will be populated starting with the discover-logformat plan (X2+).

**Future contribution model:** Each preset is a single Python file `<source_id>.py`
containing a `PRESET` dict with the same shape as a SPEC produced by discover-logformat.
Users can fork the plugin repo and add new presets via PR.
```

- [ ] **Step 2: Create `presets/.gitkeep`**

Empty file.

- [ ] **Step 3: Commit**

```bash
git add presets/README.md presets/.gitkeep
git commit -m "chore: reserve presets/ directory for future source format library"
```

---

### Task 8: Skill — init/SKILL.md

**Files:**
- Create: `.claude/skills/init/SKILL.md`

This is the longest single file. It contains all instructions for Claude to execute the init wizard. The skill reads template files from the plugin repo and writes generated files to the user's workspace.

- [ ] **Step 1: Create `.claude/skills/init/SKILL.md`**

Write the file with the following content. This is a Claude Code skill definition — it is markdown with embedded instructions that Claude follows when the user invokes `/fake-data:init`.

The SKILL.md must contain:
- YAML frontmatter with `name: init`, `description`, and `version: 0.1.0`
- Phase A: pre-flight checks (manifest.py collision, fake_data/ directory collision)
- Phase B: interactive wizard questions (ORG_NAME, is-real-company, INDUSTRY, employee count, locations, domain, IP plan)
- Phase B.1: optional research sub-phase for real companies (WebSearch + WebFetch, 60s budget, privacy guardrail)
- Phase C: in-memory content generation (load names_sample.py, seed from ORG_NAME hash, generate USERS, look up country IP ranges, build NETWORK_CONFIG, generate TENANT_ID via UUID5, compose all file contents)
- Phase D: review gate (show summary, yes/edit/cancel)
- Phase E: write all files (create fake_data/ tree, write manifest.py, world.py, config.py, time_utils.py, main_generate.py, README.md, __init__.py files, _template_generator.py, output/.gitkeep)
- Phase F: handoff message

Key implementation details for the skill author:
- The `find_workspace_root()` utility must be defined inline in the skill as a check function
- Template files are read from the plugin repo using relative paths from the skill location: `../../../templates/runtime/config.py`, `../../../data/names_sample.py`, etc.
- `world.py` is NOT a template copy — it is generated in-memory from wizard answers and the names list
- `manifest.py` is generated in-memory with the current UTC timestamp
- `config.py`, `time_utils.py`, `main_generate.py`, and `_template_generator.py` are copied byte-for-byte from `templates/`
- The skill must handle the `edit` response in the review gate by re-asking questions, not by re-running the entire skill
- Every file write uses the Write tool (not Bash echo/cat)
- After writing all files, the skill runs `python3 -c "from fake_data.world import USERS; print(len(USERS))"` via Bash to verify the workspace is importable

The full SKILL.md content is approximately 400-500 lines. The subagent executing this task should write it as a single Write tool call.

**Content structure of the SKILL.md:**

```markdown
---
name: init
description: Create a new FAKE_DATA workspace with a fictional organization. Generates world.py, config, runtime templates, and directory structure.
version: 0.1.0
metadata:
  argument-hint: "(no arguments — interactive wizard)"
---

# init — Create a FAKE_DATA workspace

[Phase A instructions...]
[Phase B instructions with question list...]
[Phase B.1 research sub-phase...]
[Phase C content generation with exact algorithms...]
[Phase D review gate with exact message format...]
[Phase E file writing with exact file list...]
[Phase F handoff message...]
```

The subagent must read the spec at `docs/superpowers/specs/2026-04-12-plan-x1-design.md` sections "Init skill design" and "world.py content shape" for the exact phase descriptions, question list, world.py shape, and manifest.py content to embed in the SKILL.md. The spec is the source of truth — do not invent new behaviors.

Additionally, the subagent must read these template files to understand what gets copied:
- `templates/runtime/config.py` (copied as-is)
- `templates/runtime/time_utils.py` (copied as-is)
- `templates/runtime/main_generate.py` (copied as-is)
- `templates/generators/_template_generator.py` (copied as-is)
- `data/names_sample.py` (read for FIRST_NAMES and LAST_NAMES lists, used to generate USERS)
- `data/country_ip_ranges.py` (read for COUNTRY_RANGES and FALLBACK_RANGES, used to populate EXTERNAL_IP_POOL)

- [ ] **Step 2: Verify the SKILL.md is valid markdown with correct frontmatter**

Run:
```bash
head -5 .claude/skills/init/SKILL.md
```
Expected: YAML frontmatter starting with `---`, containing `name: init`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/init/SKILL.md
git commit -m "feat: add init skill for workspace creation wizard"
```

---

### Task 9: Skill — add-generator/SKILL.md

**Files:**
- Create: `.claude/skills/add-generator/SKILL.md`

The add-generator skill. Supports two input modes (sample + wizard), includes the format detector, and scaffolds a generator file.

- [ ] **Step 1: Create `.claude/skills/add-generator/SKILL.md`**

Write the file with the following content. This is a Claude Code skill definition.

The SKILL.md must contain:
- YAML frontmatter with `name: add-generator`, `description`, `version: 0.1.0`, and `argument-hint`
- Phase A: pre-flight (find_workspace_root via manifest.py, check generator file collision, normalize source_id, decide mode)
- Phase B.sample: sample mode instructions (read file max 500 lines, format detection table with 8 patterns, field extraction per format type, field frequency calculation, category guessing from source_id tokens, volume category guessing, pick sample events)
- Phase B.wizard: wizard mode instructions (ask category, format, volume category, multi-file, field mode with three options, optional sample event paste)
- Phase C: review gate (display Findings summary, yes/edit/cancel)
- Phase D: scaffolding instructions (read _template_generator.py from plugin repo, substitute SOURCE_META values, generate field-specific _make_event body based on field types, generate format-specific _serialize body, write to fake_data/generators/generate_<source_id>.py)
- Phase E: handoff message with next steps

Key implementation details:
- `find_workspace_root()` is defined inline (same as in init skill)
- The format detection patterns from the spec must be reproduced exactly (8-row table)
- Field extraction rules per format (json: flatten + type infer, kv: split on = + type infer, csv: header detection, cef: 7-field header + extensions, syslog: KV on body or raw_line, xml: tag names, unknown: raw_line only)
- The `_make_event` body generation is the creative part: for each field in Findings, generate a Python line that produces a realistic value based on the field's type (ipv4 -> random from NETWORK_CONFIG or EXTERNAL_IP_POOL, int -> random.randint, enum -> random.choice, string/username -> random.choice(USERS), iso_timestamp -> ts_iso call, unknown -> "TODO_<name>")
- The `_serialize` body generation varies by format (json: json.dumps, kv: f-string join, csv: comma join, etc.)
- The generator file must include the sys.path bootstrap, all imports from fake_data.world/config/time_utils, SOURCE_META, the full function signature with progress_callback/scenarios/quiet, argparse standalone block
- The skill must use the Write tool to create the generator file, not Bash

The full SKILL.md is approximately 400-500 lines. The subagent must read the spec sections "Add-generator skill design" for exact phase descriptions, format detection table, field extraction rules, category guessing table, and volume category guessing table.

Additionally, the subagent must read `templates/generators/_template_generator.py` to understand the skeleton structure it will customize for each new generator.

**Content structure of the SKILL.md:**

```markdown
---
name: add-generator
description: Scaffold a new log generator from a sample file or interactive wizard. Creates a Python generator in fake_data/generators/.
version: 0.1.0
metadata:
  argument-hint: "<source_id> [--sample=<path>] [--category=<cat>] [--format=<fmt>]"
---

# add-generator — Scaffold a new log generator

[Phase A pre-flight...]
[Phase B.sample with format detection table and field extraction rules...]
[Phase B.wizard with question list...]
[Phase C review gate...]
[Phase D scaffolding with _make_event and _serialize generation...]
[Phase E handoff...]
```

- [ ] **Step 2: Verify the SKILL.md is valid markdown with correct frontmatter**

Run:
```bash
head -7 .claude/skills/add-generator/SKILL.md
```
Expected: YAML frontmatter with `name: add-generator`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/add-generator/SKILL.md
git commit -m "feat: add add-generator skill with sample and wizard modes"
```

---

### Task 10: Update CLAUDE.md + CHANGEHISTORY.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `CHANGEHISTORY.md`

- [ ] **Step 1: Update CLAUDE.md status**

Read the current `CLAUDE.md`. In the "Directory layout (planned)" section, update the status to reflect that init and add-generator skills now exist and templates are populated. The layout tree should match the actual files created in Tasks 1-9.

- [ ] **Step 2: Add CHANGEHISTORY.md entry**

Add a new entry at the top of `CHANGEHISTORY.md` (below the `# Change History` heading, above existing entries):

```markdown
## 2026-04-12 ~HH:MM UTC — Plan X1: Framework core + init + add-generator
Files: .claude/skills/init/SKILL.md, .claude/skills/add-generator/SKILL.md,
       templates/runtime/{config,time_utils,main_generate}.py,
       templates/generators/_template_generator.py,
       data/{names_sample,country_ip_ranges}.py, presets/

First functional version of the FAKE_DATA plugin. Users can run /fake-data:init
to create a workspace and /fake-data:add-generator to scaffold generators.
Includes working main_generate.py orchestrator with filesystem-based discovery,
topological dependency sorting, and progress display. All runtime code is
stdlib-only Python 3.9+.
```

Replace `HH:MM` with the actual UTC time at commit.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md CHANGEHISTORY.md
git commit -m "docs: update project docs for X1 completion"
```

---

### Task 11: End-to-end canary test

**Files:** None created — this is a verification task.

This task must be done by a human (or an interactive Claude session) because it requires invoking skills interactively. The subagent cannot run `/fake-data:init` — that is a Claude Code skill invocation, not a bash command.

- [ ] **Step 1: Create scratch directory**

```bash
mkdir -p /tmp/fake-data-canary
cd /tmp/fake-data-canary
```

- [ ] **Step 2: Run `/fake-data:init` interactively**

Start a Claude Code session in the scratch directory and run:
```
/fake-data:init
```

Answer with: "Acme Widgets", no on real company, "manufacturing", 50 employees, 2 locations (HQ in Oslo NO, branch in Stockholm SE), "acme-widgets.com", 10.0.0.0/8. Approve the review gate.

- [ ] **Step 3: Verify workspace structure**

```bash
ls fake_data/
python3 -c "from fake_data.world import USERS, LOCATIONS; print(len(USERS), len(LOCATIONS))"
# Expected: 50 2
python3 -c "from fake_data.world import EXTERNAL_IP_POOL_BY_COUNTRY; print(list(EXTERNAL_IP_POOL_BY_COUNTRY.keys()))"
# Expected: ['NO', 'SE']
python3 fake_data/main_generate.py --help
# Expected: prints usage without errors
python3 fake_data/main_generate.py --list
# Expected: "No generators registered"
```

- [ ] **Step 4: Run `/fake-data:add-generator` in sample mode**

Create a sample file:
```bash
cat > /tmp/sample.log << 'EOF'
date=2026-01-05 time=14:30:45 srcip=10.10.30.55 dstip=198.51.100.42 action=deny port=443
date=2026-01-05 time=14:30:46 srcip=10.10.30.56 dstip=198.51.100.17 action=accept port=80
date=2026-01-05 time=14:30:47 srcip=10.10.30.57 dstip=198.51.100.99 action=deny port=3389
EOF
```

Then in Claude Code:
```
/fake-data:add-generator acme_fw --sample=/tmp/sample.log
```

Verify format=kv detected, category=network guessed. Approve the review gate.

- [ ] **Step 5: Test standalone generator execution**

```bash
python3 fake_data/generators/generate_acme_fw.py --days=1 --quiet
ls fake_data/output/network/acme_fw.log
wc -l fake_data/output/network/acme_fw.log
# Expected: > 0 lines
head -3 fake_data/output/network/acme_fw.log
# Expected: KV-formatted log lines
```

- [ ] **Step 6: Run `/fake-data:add-generator` in wizard mode**

In Claude Code:
```
/fake-data:add-generator acme_web
```

Pick: format=json, category=web, volume_category=web, field mode="Minimal". Approve.

- [ ] **Step 7: Run orchestrator with both generators**

```bash
python3 fake_data/main_generate.py --list
# Expected: table showing acme_fw and acme_web

python3 fake_data/main_generate.py --days=2 --quiet
wc -l fake_data/output/network/acme_fw.log   # > 0
wc -l fake_data/output/web/acme_web.log      # > 0
```

- [ ] **Step 8: Idempotency checks**

In Claude Code:
```
/fake-data:init
# Expected: refuses (workspace exists)

/fake-data:add-generator acme_fw
# Expected: refuses (generator exists)
```

- [ ] **Step 9: Record results**

If all 8 steps pass, X1 is complete. Record pass/fail in CHANGEHISTORY.md as a note under the X1 entry.

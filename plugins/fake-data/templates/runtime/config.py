#!/usr/bin/env python3
"""
Configuration module for FAKE_DATA generators.
Contains shared constants, volume parameters, and output path management.

Generic and works with any world.py — no organization-specific references.
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

VALID_CATEGORIES = (
    "network",
    "cloud",
    "windows",
    "linux",
    "web",
    "retail",
    "collaboration",
    "itsm",
    "erp",
    "ot",
    "database",
)


def _build_output_dirs(base: Path) -> dict:
    return {cat: base / cat for cat in VALID_CATEGORIES}


OUTPUT_DIRS = _build_output_dirs(OUTPUT_BASE)


def get_output_path(category: str, filename: str) -> Path:
    """Get the full output path for a given category and filename.

    Supports nested subdirectories in filename, e.g.:
        get_output_path("cloud", "webex/webex_events.json")
        -> output/cloud/webex/webex_events.json

    Raises ValueError if category is not in VALID_CATEGORIES — generators
    must declare a real category, never "unknown".
    """
    if category not in OUTPUT_DIRS:
        raise ValueError(
            f"Unknown output category {category!r}. "
            f"Valid categories: {', '.join(VALID_CATEGORIES)}"
        )
    base = OUTPUT_DIRS[category]
    full_path = base / filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


def set_output_base(new_base: Path):
    """Redirect all generator output to a different base directory."""
    global OUTPUT_BASE, OUTPUT_DIRS
    OUTPUT_BASE = new_base
    OUTPUT_DIRS = _build_output_dirs(OUTPUT_BASE)


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
# SCENARIO SUPPORT
# =============================================================================

def discover_scenarios() -> dict:
    """Scan fake_data/scenarios/ for modules with SCENARIO_META.

    Returns dict mapping scenario_id -> {"meta": dict, "instance": BaseScenario}.
    """
    import importlib
    import pkgutil

    scenarios_dir = Path(__file__).resolve().parent / "scenarios"
    if not scenarios_dir.is_dir():
        return {}

    discovered = {}
    for finder, name, _ in pkgutil.iter_modules([str(scenarios_dir)]):
        if name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"fake_data.scenarios.{name}")
        except (ImportError, SyntaxError) as e:
            print(f"  Warning: could not import scenarios/{name}.py: {e}")
            continue

        meta = getattr(module, "SCENARIO_META", None)
        if meta is None:
            continue

        # Find the scenario class (convention: class ending in "Scenario")
        cls = None
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (isinstance(obj, type)
                    and attr_name.endswith("Scenario")
                    and attr_name != "BaseScenario"):
                cls = obj
                break

        if cls:
            try:
                discovered[meta["scenario_id"]] = {
                    "meta": meta,
                    "instance": cls(),
                }
            except Exception as e:
                print(f"  Warning: could not instantiate {attr_name}: {e}")

    return discovered


def expand_scenarios(scenarios: str) -> list:
    """Expand a scenario specification string into active scenario instances.

    Args:
        scenarios: Comma-separated list of scenario names, "all", or "none".

    Returns:
        List of scenario instances.
    """
    if scenarios == "none":
        return []

    discovered = discover_scenarios()

    if scenarios == "all":
        return [info["instance"] for info in discovered.values()]

    names = [n.strip() for n in scenarios.split(",")]
    active = []
    for name in names:
        if name in discovered:
            active.append(discovered[name]["instance"])
        else:
            print(f"  Warning: scenario '{name}' not found, skipping")
    return active


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

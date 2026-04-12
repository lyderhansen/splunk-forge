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

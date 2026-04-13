#!/usr/bin/env python3
"""
Timestamp formatting and natural volume calculation utilities.

Provides consistent timestamp generation across all log formats and
realistic hourly/daily volume variation via calc_natural_events().
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
    """ISO 8601 UTC timestamp: 2026-01-05T14:30:45Z"""
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_iso_ms(start_date: str, day_offset: int, hour: int,
              minute: int = 0, second: int = 0, ms: int = 0) -> str:
    """ISO 8601 UTC with milliseconds: 2026-01-05T14:30:45.123Z"""
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    dt = dt.replace(microsecond=ms * 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def ts_syslog(start_date: str, day_offset: int, hour: int,
              minute: int = 0, second: int = 0) -> str:
    """Syslog timestamp: Jan 05 2026 14:30:45"""
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%b %d %Y %H:%M:%S")


def ts_cef(start_date: str, day_offset: int, hour: int,
           minute: int = 0, second: int = 0) -> str:
    """CEF header timestamp: Jan 05 2026 14:30:45 UTC"""
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%b %d %Y %H:%M:%S") + " UTC"


def ts_perfmon(start_date: str, day_offset: int, hour: int,
               minute: int = 0, second: int = 0, ms: int = 0) -> str:
    """Windows Perfmon timestamp: 01/05/2026 14:30:45.123"""
    dt = _base_datetime(start_date, day_offset, hour, minute, second)
    return dt.strftime("%m/%d/%Y %H:%M:%S") + f".{ms:03d}"


def calc_natural_events(base_count: int, start_date: str, day_offset: int,
                        hour: int, category: str) -> int:
    """Calculate a natural event count with realistic variation.

    Applies hourly activity curve, weekend factor, Monday boost, daily noise.

    Args:
        base_count: Base events per hour at peak (activity level 100).
        start_date: Generation start date (YYYY-MM-DD).
        day_offset: Day number (0-based) from start_date.
        hour: Hour of day (0-23).
        category: Volume category — 'firewall', 'cloud', 'auth', 'web', 'email', 'ot'.

    Returns:
        Integer event count, never less than 0.
    """
    from fake_data.config import (
        VOLUME_WEEKEND_FACTORS, VOLUME_MONDAY_BOOST,
        VOLUME_DAILY_NOISE_MIN, VOLUME_DAILY_NOISE_MAX,
        HOUR_ACTIVITY_WEEKDAY, HOUR_ACTIVITY_WEEKEND,
        HOUR_ACTIVITY_WEEKEND_ECOMMERCE, HOUR_ACTIVITY_WEEKEND_FIREWALL,
    )

    dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day_offset)
    weekday = dt.weekday()
    is_weekend = weekday >= 5
    is_monday = weekday == 0

    if is_weekend:
        if category == "web":
            activity = HOUR_ACTIVITY_WEEKEND_ECOMMERCE.get(hour, 10)
        elif category == "firewall":
            activity = HOUR_ACTIVITY_WEEKEND_FIREWALL.get(hour, 10)
        else:
            activity = HOUR_ACTIVITY_WEEKEND.get(hour, 10)
    else:
        activity = HOUR_ACTIVITY_WEEKDAY.get(hour, 10)

    count = base_count * (activity / 100.0)

    if is_weekend:
        weekend_factor = VOLUME_WEEKEND_FACTORS.get(
            category, VOLUME_WEEKEND_FACTORS["default"]
        )
        count = count * (weekend_factor / 100.0)

    if is_monday:
        count = count * (VOLUME_MONDAY_BOOST / 100.0)

    noise = random.randint(VOLUME_DAILY_NOISE_MIN, VOLUME_DAILY_NOISE_MAX)
    count = count * (1 + noise / 100.0)

    return max(0, int(count))

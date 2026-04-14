"""Deterministic fallback pickers for baseline event correlation.

Used by generators when narrative.py is absent or when a generator's
source has no narrative role. Provides time-bucketed user and host
pickers that return the same value for the same inputs, so independent
generators pick the same "active" user/host in the same window.

This module is copied into the user workspace by fd-init. It has no
third-party dependencies.
"""
from __future__ import annotations

import hashlib
from typing import Optional


def _bucket_seed(day: int, hour: int, bucket_hours: int, salt: str) -> int:
    bucket = hour // max(1, bucket_hours)
    raw = f"{salt}:{day}:{bucket}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def active_user(
    day: int,
    hour: int,
    users: list,
    bucket_hours: int = 4,
) -> Optional[dict]:
    """Return a deterministic "currently active" user for this time bucket.

    Given the same (day, hour // bucket_hours) the function returns the
    same user. Different buckets return different users with high
    probability. Returns None if users is empty.
    """
    if not users:
        return None
    seed = _bucket_seed(day, hour, bucket_hours, salt="user")
    return users[seed % len(users)]

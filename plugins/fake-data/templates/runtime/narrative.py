"""Narrative spine for this demo workspace.

When populated, this module pins the actors, storyline, and join keys
that all generators reference. The shipped form is a STUB with empty
ACTORS / STORYLINE / JOIN_KEYS — generators fall through to
correlation.py shared pickers when ACTORS is empty.

fd-init replaces this file when the user opts into a demo narrative.

Field layout (when populated):
    ACTORS: dict keyed by role name (victim, attacker, pivot, ...).
        Each value is a dict with any of:
        user, email, host, host_ip, vpn_ip, mac, entra_object_id,
        aws_principal_id, bunit, department, src_ip, user_agent,
        c2_domain, country, category, protocol.

    STORYLINE: list of dicts, each with:
        days: tuple (lo, hi) inclusive
        phase: str phase name
        sources: list of source_ids that emit scenario events in this phase
"""
from __future__ import annotations

TITLE: str = ""
SECTOR: str = ""
DURATION_DAYS: int = 0
START_DATE: str = ""

ACTORS: dict = {}

JOIN_KEYS: list = []

SOURCES_NEEDED: list = []

STORYLINE: list = []


def get_actor(role: str) -> dict:
    """Return the actor dict for the given role, or empty dict if missing."""
    return ACTORS.get(role, {})


def get_phase(day: int) -> str:
    """Return the phase name for a given day number, or 'baseline' if unscoped."""
    for entry in STORYLINE:
        lo, hi = entry["days"]
        if lo <= day <= hi:
            return entry["phase"]
    return "baseline"


def has_scenario_events(source: str, day: int) -> bool:
    """Return True if source is listed in STORYLINE for this day."""
    for entry in STORYLINE:
        lo, hi = entry["days"]
        if lo <= day <= hi and source in entry["sources"]:
            return True
    return False

"""Unit tests for narrative.py (stub form as shipped by default).

The shipped template is a STUB: ACTORS is empty, STORYLINE is empty,
JOIN_KEYS is empty. fd-init replaces this file when the user opts
into a narrative during workspace creation. These tests cover the
stub form and the helper function contracts.
"""


def test_stub_has_module_level_constants():
    import narrative
    assert hasattr(narrative, "TITLE")
    assert hasattr(narrative, "SECTOR")
    assert hasattr(narrative, "DURATION_DAYS")
    assert hasattr(narrative, "ACTORS")
    assert hasattr(narrative, "STORYLINE")
    assert hasattr(narrative, "JOIN_KEYS")
    assert hasattr(narrative, "SOURCES_NEEDED")


def test_stub_actors_is_empty_dict():
    import narrative
    assert narrative.ACTORS == {}


def test_stub_storyline_is_empty_list():
    import narrative
    assert narrative.STORYLINE == []


def test_get_actor_returns_empty_dict_for_missing_role():
    import narrative
    assert narrative.get_actor("victim") == {}
    assert narrative.get_actor("nonexistent") == {}


def test_get_phase_returns_baseline_when_storyline_empty():
    import narrative
    assert narrative.get_phase(1) == "baseline"
    assert narrative.get_phase(99) == "baseline"


def test_has_scenario_events_returns_false_when_storyline_empty():
    import narrative
    assert narrative.has_scenario_events("wineventlog_security", 1) is False
    assert narrative.has_scenario_events("any_source", 99) is False


POPULATED_ACTORS = {
    "victim": {
        "role": "victim",
        "user": "maria.engineer",
        "host": "ENG-WS-MARIA01",
        "host_ip": "10.42.17.88",
        "vpn_ip": "172.20.3.54",
        "entra_object_id": "a7f3c921-4b8e-4d1a-9f2b-3e5c8a7d1f02",
    },
    "attacker": {
        "role": "attacker",
        "src_ip": "185.220.101.47",
        "c2_domain": "cdn-update-sync.xyz",
    },
}

POPULATED_STORYLINE = [
    {"days": (1, 3),   "phase": "recon",   "sources": ["fortigate", "cisco_ise"]},
    {"days": (4, 4),   "phase": "initial", "sources": ["wineventlog_security"]},
    {"days": (5, 9),   "phase": "lateral", "sources": ["sysmon", "fortigate"]},
    {"days": (10, 14), "phase": "impact",  "sources": ["ot_modbus"]},
]


def _populate(monkeypatch):
    import narrative
    monkeypatch.setattr(narrative, "ACTORS", POPULATED_ACTORS)
    monkeypatch.setattr(narrative, "STORYLINE", POPULATED_STORYLINE)
    return narrative


def test_get_actor_returns_pinned_dict_when_populated(monkeypatch):
    narrative = _populate(monkeypatch)
    victim = narrative.get_actor("victim")
    assert victim["user"] == "maria.engineer"
    assert victim["vpn_ip"] == "172.20.3.54"
    assert victim["entra_object_id"] == "a7f3c921-4b8e-4d1a-9f2b-3e5c8a7d1f02"


def test_get_actor_unknown_role_returns_empty_even_when_populated(monkeypatch):
    narrative = _populate(monkeypatch)
    assert narrative.get_actor("insider") == {}


def test_get_phase_returns_correct_phase_across_boundaries(monkeypatch):
    narrative = _populate(monkeypatch)
    assert narrative.get_phase(1) == "recon"
    assert narrative.get_phase(3) == "recon"    # inclusive upper
    assert narrative.get_phase(4) == "initial"
    assert narrative.get_phase(5) == "lateral"
    assert narrative.get_phase(9) == "lateral"
    assert narrative.get_phase(10) == "impact"
    assert narrative.get_phase(14) == "impact"
    assert narrative.get_phase(0) == "baseline"  # out of range
    assert narrative.get_phase(15) == "baseline"


def test_has_scenario_events_matches_source_and_day(monkeypatch):
    narrative = _populate(monkeypatch)
    assert narrative.has_scenario_events("fortigate", 1) is True  # recon
    assert narrative.has_scenario_events("fortigate", 4) is False  # initial, fortigate not listed
    assert narrative.has_scenario_events("fortigate", 7) is True  # lateral
    assert narrative.has_scenario_events("wineventlog_security", 4) is True
    assert narrative.has_scenario_events("ot_modbus", 12) is True
    assert narrative.has_scenario_events("sysmon", 1) is False  # not in recon


def test_has_scenario_events_returns_false_for_out_of_range_day(monkeypatch):
    narrative = _populate(monkeypatch)
    assert narrative.has_scenario_events("fortigate", 99) is False

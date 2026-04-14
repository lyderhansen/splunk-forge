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

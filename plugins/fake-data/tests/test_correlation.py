"""Unit tests for the correlation.py fallback pickers."""
import pytest


USERS = [
    {"username": "alice", "role": "admin"},
    {"username": "bob", "role": "user"},
    {"username": "carol", "role": "user"},
    {"username": "dave", "role": "power_user"},
    {"username": "eve", "role": "service_account"},
]


def test_active_user_returns_same_user_within_bucket():
    from correlation import active_user
    u1 = active_user(day=5, hour=9, users=USERS, bucket_hours=4)
    u2 = active_user(day=5, hour=10, users=USERS, bucket_hours=4)
    u3 = active_user(day=5, hour=11, users=USERS, bucket_hours=4)
    assert u1 == u2 == u3


def test_active_user_changes_across_buckets():
    from correlation import active_user
    found = set()
    for hour in range(0, 24, 4):
        u = active_user(day=1, hour=hour, users=USERS, bucket_hours=4)
        found.add(u["username"])
    assert len(found) >= 2  # at least two different users across 6 buckets


def test_active_user_deterministic_across_calls():
    from correlation import active_user
    u1 = active_user(day=3, hour=7, users=USERS, bucket_hours=4)
    u2 = active_user(day=3, hour=7, users=USERS, bucket_hours=4)
    assert u1 == u2
    assert u1["username"] == u2["username"]


def test_active_user_with_empty_list_returns_none():
    from correlation import active_user
    assert active_user(day=1, hour=1, users=[], bucket_hours=4) is None


INFRA = [
    {"hostname": "FW-HQ1-01", "role": "firewall", "category": "network"},
    {"hostname": "SW-HQ1-01", "role": "switch", "category": "network"},
    {"hostname": "SRV-HQ1-01", "role": "server", "category": "windows"},
    {"hostname": "SRV-HQ1-02", "role": "server", "category": "windows"},
    {"hostname": "WS-HQ1-01", "role": "workstation", "category": "endpoint"},
    {"hostname": "WS-HQ1-02", "role": "workstation", "category": "endpoint"},
]


def test_active_host_filters_by_category():
    from correlation import active_host
    h = active_host(day=2, hour=8, infra=INFRA, category="network")
    assert h is not None
    assert h["category"] == "network"


def test_active_host_deterministic():
    from correlation import active_host
    h1 = active_host(day=2, hour=8, infra=INFRA, category="windows")
    h2 = active_host(day=2, hour=8, infra=INFRA, category="windows")
    assert h1 == h2


def test_active_host_no_category_uses_full_pool():
    from correlation import active_host
    h = active_host(day=2, hour=8, infra=INFRA, category=None)
    assert h is not None
    assert h["hostname"] in {i["hostname"] for i in INFRA}


def test_active_host_returns_none_when_no_match():
    from correlation import active_host
    assert active_host(day=1, hour=1, infra=INFRA, category="ot") is None


def test_active_host_returns_none_for_empty_infra():
    from correlation import active_host
    assert active_host(day=1, hour=1, infra=[], category=None) is None

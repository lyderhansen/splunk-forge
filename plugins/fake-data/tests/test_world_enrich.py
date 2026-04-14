"""Unit tests for world_enrich.py — deterministic stable-ID generation."""


SAMPLE_USER = {
    "username": "alice.adams",
    "full_name": "Alice Adams",
    "email": "alice.adams@example.com",
    "location": "HQ1",
    "department": "it",
    "role": "admin",
    "workstation": "WS-HQ1-001",
    "workstation_ip": "10.10.10.1",
    "mac_address": "AA:BB:CC:0a:00:00",
    "user_id": "existing-user-id-value",
}


def test_enrich_user_adds_entra_object_id():
    from world_enrich import enrich_user
    out = enrich_user(SAMPLE_USER, workspace_name="ws1")
    assert "entra_object_id" in out
    # UUID v4-ish: 8-4-4-4-12 hex format
    parts = out["entra_object_id"].split("-")
    assert len(parts) == 5
    assert [len(p) for p in parts] == [8, 4, 4, 4, 12]


def test_entra_object_id_is_deterministic():
    from world_enrich import enrich_user
    a = enrich_user(SAMPLE_USER, workspace_name="ws1")
    b = enrich_user(SAMPLE_USER, workspace_name="ws1")
    assert a["entra_object_id"] == b["entra_object_id"]


def test_entra_object_id_differs_across_workspaces():
    from world_enrich import enrich_user
    a = enrich_user(SAMPLE_USER, workspace_name="ws1")
    b = enrich_user(SAMPLE_USER, workspace_name="ws2")
    assert a["entra_object_id"] != b["entra_object_id"]


def test_entra_object_id_differs_across_users():
    from world_enrich import enrich_user
    u2 = dict(SAMPLE_USER, username="bob.baker")
    a = enrich_user(SAMPLE_USER, workspace_name="ws1")
    b = enrich_user(u2, workspace_name="ws1")
    assert a["entra_object_id"] != b["entra_object_id"]


def test_enrich_user_preserves_existing_fields():
    from world_enrich import enrich_user
    out = enrich_user(SAMPLE_USER, workspace_name="ws1")
    assert out["username"] == "alice.adams"
    assert out["email"] == "alice.adams@example.com"
    assert out["workstation_ip"] == "10.10.10.1"
    assert out["user_id"] == "existing-user-id-value"  # not overwritten

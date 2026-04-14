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


def test_enrich_user_adds_aws_principal_id():
    from world_enrich import enrich_user
    out = enrich_user(SAMPLE_USER, workspace_name="ws1")
    assert out["aws_principal_id"].startswith("AROA")
    assert len(out["aws_principal_id"]) == 16  # AROA + 12 hex-ish chars


def test_enrich_user_adds_vpn_ip_in_172_20_range():
    from world_enrich import enrich_user
    out = enrich_user(SAMPLE_USER, workspace_name="ws1")
    ip = out["vpn_ip"]
    octets = ip.split(".")
    assert len(octets) == 4
    assert octets[0] == "172"
    assert octets[1] == "20"
    for octet in octets:
        n = int(octet)
        assert 0 <= n <= 255


def test_enrich_user_adds_employee_id_with_index():
    from world_enrich import enrich_user
    out = enrich_user(SAMPLE_USER, workspace_name="ws1", index=42)
    assert out["employee_id"] == "E10042"


def test_enrich_user_all_new_fields_deterministic():
    from world_enrich import enrich_user
    a = enrich_user(SAMPLE_USER, workspace_name="ws1", index=7)
    b = enrich_user(SAMPLE_USER, workspace_name="ws1", index=7)
    assert a["aws_principal_id"] == b["aws_principal_id"]
    assert a["vpn_ip"] == b["vpn_ip"]
    assert a["employee_id"] == b["employee_id"]


SAMPLE_INFRA = {
    "hostname": "SRV-HQ1-01",
    "ip": "10.10.0.10",
    "location": "HQ1",
    "role": "server",
    "description": "General purpose server",
}


def test_enrich_infra_adds_mac_address():
    from world_enrich import enrich_infra
    out = enrich_infra(SAMPLE_INFRA, workspace_name="ws1")
    assert "mac_address" in out
    parts = out["mac_address"].split(":")
    assert len(parts) == 6
    for p in parts:
        assert len(p) == 2
        int(p, 16)  # must be valid hex


def test_enrich_infra_adds_asset_tag():
    from world_enrich import enrich_infra
    out = enrich_infra(SAMPLE_INFRA, workspace_name="ws1", index=3)
    assert out["asset_tag"] == "AST-HQ1-0003"


def test_enrich_infra_deterministic():
    from world_enrich import enrich_infra
    a = enrich_infra(SAMPLE_INFRA, workspace_name="ws1", index=3)
    b = enrich_infra(SAMPLE_INFRA, workspace_name="ws1", index=3)
    assert a["mac_address"] == b["mac_address"]
    assert a["asset_tag"] == b["asset_tag"]


def test_enrich_infra_preserves_existing_fields():
    from world_enrich import enrich_infra
    out = enrich_infra(SAMPLE_INFRA, workspace_name="ws1")
    assert out["hostname"] == "SRV-HQ1-01"
    assert out["ip"] == "10.10.0.10"
    assert out["location"] == "HQ1"
    assert out["role"] == "server"


def test_enrich_users_list_applies_to_all():
    from world_enrich import enrich_users_list
    users = [
        dict(SAMPLE_USER, username="alice.a"),
        dict(SAMPLE_USER, username="bob.b"),
        dict(SAMPLE_USER, username="carol.c"),
    ]
    out = enrich_users_list(users, workspace_name="ws1")
    assert len(out) == 3
    for i, u in enumerate(out):
        assert "entra_object_id" in u
        assert "vpn_ip" in u
        assert u["employee_id"] == f"E{10000 + i}"


def test_enrich_users_list_produces_unique_ids():
    from world_enrich import enrich_users_list
    users = [dict(SAMPLE_USER, username=f"user{i}") for i in range(5)]
    out = enrich_users_list(users, workspace_name="ws1")
    ids = {u["entra_object_id"] for u in out}
    assert len(ids) == 5


def test_enrich_infra_list_applies_to_all():
    from world_enrich import enrich_infra_list
    infra = [
        dict(SAMPLE_INFRA, hostname=f"HOST-{i:02d}") for i in range(3)
    ]
    out = enrich_infra_list(infra, workspace_name="ws1")
    assert len(out) == 3
    for i, h in enumerate(out):
        assert h["asset_tag"] == f"AST-HQ1-{i:04d}"
        assert "mac_address" in h

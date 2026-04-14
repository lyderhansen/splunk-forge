"""Deterministic stable-ID enrichment for world.py users and infra.

Called by fd-init (at workspace creation time) to add stable identifiers
to every user and host in world.py. IDs are deterministic: the same
(workspace_name, username/hostname, field) always yields the same value,
so re-running fd-init does not drift.

This module lives in data/ rather than templates/runtime/ because it is
used at init time, not runtime — the enriched values are baked into
world.py and read as static data by generators.
"""
from __future__ import annotations

import hashlib


def _hex_hash(workspace_name: str, key: str, field: str, length: int) -> str:
    raw = f"{workspace_name}:{key}:{field}".encode()
    return hashlib.sha256(raw).hexdigest()[:length]


def _make_entra_object_id(workspace_name: str, username: str) -> str:
    """Return a deterministic UUID-v4-shaped string from (workspace, username)."""
    h = _hex_hash(workspace_name, username, "entra", 32)
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _make_aws_principal_id(workspace_name: str, username: str) -> str:
    """Return a deterministic AROA-prefixed principal ID (16 chars total)."""
    h = _hex_hash(workspace_name, username, "aws", 12).upper()
    return f"AROA{h}"


def _make_vpn_ip(workspace_name: str, username: str) -> str:
    """Return a deterministic IPv4 in 172.20.0.0/16 from (workspace, username)."""
    h = _hex_hash(workspace_name, username, "vpn", 8)
    n = int(h, 16)
    third = (n >> 8) & 0xFF
    fourth = n & 0xFF
    return f"172.20.{third}.{fourth}"


def _make_employee_id(index: int) -> str:
    """Return a zero-padded employee ID string of the form E10000 + index."""
    return f"E{10000 + index}"


def enrich_user(user: dict, workspace_name: str, index: int = 0) -> dict:
    """Return a copy of user with deterministic stable IDs added.

    Preserves all existing keys. Only adds fields that are absent or
    empty. Safe to call multiple times.

    index: positional index in the USERS list, used for employee_id.
    """
    out = dict(user)
    username = out["username"]
    if not out.get("entra_object_id"):
        out["entra_object_id"] = _make_entra_object_id(workspace_name, username)
    if not out.get("aws_principal_id"):
        out["aws_principal_id"] = _make_aws_principal_id(workspace_name, username)
    if not out.get("vpn_ip"):
        out["vpn_ip"] = _make_vpn_ip(workspace_name, username)
    if not out.get("employee_id"):
        out["employee_id"] = _make_employee_id(index)
    return out


def _make_infra_mac(workspace_name: str, hostname: str) -> str:
    """Return a deterministic MAC address with the locally-administered OUI 02:1A:2B."""
    h = _hex_hash(workspace_name, hostname, "mac", 6)
    return f"02:1A:2B:{h[0:2]}:{h[2:4]}:{h[4:6]}".upper()


def _make_asset_tag(location: str, index: int) -> str:
    """Return an asset tag of the form AST-<LOCATION>-<4-digit-index>."""
    return f"AST-{location}-{index:04d}"


def enrich_infra(infra: dict, workspace_name: str, index: int = 0) -> dict:
    """Return a copy of infra host with mac_address and asset_tag added.

    Preserves all existing keys. Only adds fields that are absent or empty.
    """
    out = dict(infra)
    hostname = out["hostname"]
    if not out.get("mac_address"):
        out["mac_address"] = _make_infra_mac(workspace_name, hostname)
    if not out.get("asset_tag"):
        out["asset_tag"] = _make_asset_tag(out["location"], index)
    return out


def enrich_users_list(users: list, workspace_name: str) -> list:
    """Enrich every user in the list with deterministic stable IDs.

    Returns a new list. The index of each user becomes its employee_id
    suffix. Safe to call on already-enriched lists.
    """
    return [
        enrich_user(u, workspace_name=workspace_name, index=i)
        for i, u in enumerate(users)
    ]


def enrich_infra_list(infra: list, workspace_name: str) -> list:
    """Enrich every infra host in the list with mac_address and asset_tag.

    Returns a new list. asset_tag uses the host's index within the list.
    """
    return [
        enrich_infra(h, workspace_name=workspace_name, index=i)
        for i, h in enumerate(infra)
    ]

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

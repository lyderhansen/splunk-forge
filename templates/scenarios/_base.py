"""
Base scenario class for FAKE_DATA.

Provides auto-resolution of 'auto' config sentinels from world.py,
phase tracking, and the interface contract for generator-specific methods.

Copied into user workspace by fd-init. Edit freely.
"""

import hashlib
import ipaddress
import random
from dataclasses import fields as dataclass_fields
from typing import Dict, List, Optional


class BaseScenario:
    """Base class for all scenarios."""

    def __init__(self, config=None):
        self.config = config or self.default_config()
        self._resolve_auto_values()

    def default_config(self):
        """Return the default config dataclass instance. Override in subclass."""
        raise NotImplementedError

    def meta(self) -> dict:
        """Return the SCENARIO_META dict. Override in subclass."""
        raise NotImplementedError

    # -----------------------------------------------------------------
    # Phase helpers
    # -----------------------------------------------------------------

    def get_phase(self, day: int) -> Optional[str]:
        """Return phase name for given day, or None if outside scenario window."""
        for phase in self.meta().get("phases", []):
            if phase["start_day"] <= day <= phase["end_day"]:
                return phase["name"]
        return None

    def is_active(self, day: int) -> bool:
        """Check if scenario is active on this day."""
        m = self.meta()
        return m["start_day"] <= day <= m["end_day"]

    # -----------------------------------------------------------------
    # Auto-resolver
    # -----------------------------------------------------------------

    def _resolve_auto_values(self):
        """Replace 'auto' sentinels with real values from world.py.

        Handles both enriched world.py (with role, INFRASTRUCTURE) and
        basic world.py (only username, email, location, department).
        Missing world.py exports are silently ignored.
        """
        try:
            from fake_data import world
        except ImportError:
            return

        users = getattr(world, "USERS", [])
        infrastructure = getattr(world, "INFRASTRUCTURE", [])
        external_pool = getattr(world, "EXTERNAL_IP_POOL", [])

        seed = self._stable_seed(self.meta().get("scenario_id", "default"))

        for field in dataclass_fields(self.config):
            value = getattr(self.config, field.name)
            if value != "auto":
                continue

            resolved = self._resolve_field(
                field.name, users, infrastructure, external_pool, seed
            )
            if resolved is not None:
                setattr(self.config, field.name, resolved)

    def _resolve_field(
        self,
        field_name: str,
        users: list,
        infrastructure: list,
        external_pool: list,
        seed: int,
    ) -> Optional[str]:
        """Resolve a single 'auto' field based on naming conventions."""
        fn = field_name.lower()

        # User fields
        if "user" in fn:
            user = self._pick_user(users, seed, field_name)
            return user["username"] if user else None

        # Host IP fields (must check before plain host)
        if "host_ip" in fn or ("host" in fn and "ip" in fn):
            host_field = fn.replace("_ip", "")
            host_val = getattr(self.config, host_field, None) if hasattr(self.config, host_field) else None
            if host_val and host_val != "auto" and infrastructure:
                match = self._find_infra_by_hostname(infrastructure, host_val)
                if match:
                    return match.get("ip", None)
            # Fallback: pick any infra IP
            if infrastructure:
                entry = self._pick_infra(infrastructure, seed, field_name)
                return entry.get("ip", None) if entry else None
            return None

        # Host fields (without ip)
        if "host" in fn:
            entry = self._pick_infra(infrastructure, seed, field_name)
            return entry.get("hostname", None) if entry else None

        # Attacker / external IP fields
        if "attacker" in fn or "external" in fn or fn.endswith("_ip"):
            return self._pick_external_ip(external_pool, seed, field_name)

        return None

    # -----------------------------------------------------------------
    # Deterministic pickers
    # -----------------------------------------------------------------

    def _pick_user(self, users: list, seed: int, field_name: str) -> Optional[dict]:
        """Pick a user deterministically. Prefers admin/IT for attack scenarios."""
        if not users:
            return None
        key = self._field_hash(seed, field_name)

        # Try role-based filtering for enriched world.py
        category = self.meta().get("category", "")
        if category == "attack":
            # Prefer IT/admin users if role field exists, else department=it
            filtered = [u for u in users if u.get("role") in ("admin", "it_admin")]
            if not filtered:
                filtered = [u for u in users if u.get("department") == "it"]
            if filtered:
                return filtered[key % len(filtered)]

        return users[key % len(users)]

    def _pick_infra(self, infrastructure: list, seed: int, field_name: str) -> Optional[dict]:
        """Pick an infrastructure entry deterministically."""
        if not infrastructure:
            return None
        key = self._field_hash(seed, field_name)
        return infrastructure[key % len(infrastructure)]

    def _find_infra_by_hostname(self, infrastructure: list, hostname: str) -> Optional[dict]:
        """Find an infrastructure entry by hostname."""
        for entry in infrastructure:
            if entry.get("hostname") == hostname:
                return entry
        return None

    def _pick_external_ip(self, pool: list, seed: int, field_name: str) -> str:
        """Pick a deterministic external IP from CIDR pool."""
        if not pool:
            return "198.51.100.1"
        key = self._field_hash(seed, field_name)
        cidr = pool[key % len(pool)]
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            # Pick a host address deterministically
            num_hosts = max(1, network.num_addresses - 2)
            offset = (key % num_hosts) + 1
            return str(network.network_address + offset)
        except (ValueError, TypeError):
            return "198.51.100.1"

    # -----------------------------------------------------------------
    # Hashing utilities
    # -----------------------------------------------------------------

    @staticmethod
    def _stable_seed(scenario_id: str) -> int:
        """Produce a stable integer seed from scenario_id."""
        return int(hashlib.sha256(scenario_id.encode()).hexdigest()[:8], 16)

    @staticmethod
    def _field_hash(seed: int, field_name: str) -> int:
        """Combine seed + field_name for per-field determinism."""
        combined = f"{seed}:{field_name}"
        return int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)

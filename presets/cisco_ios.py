"""Bundled preset for cisco_ios. Used by fd-discover when --preset is selected
or when no --sample/--doc is provided."""

PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "cisco_ios",
        "display_name": "Cisco Catalyst IOS-XE",
        "vendor": "Cisco",
        "product": "Catalyst IOS-XE",
        "description": "Cisco Catalyst IOS / IOS-XE switch and router syslog messages covering link state, authentication, spanning-tree, and configuration changes in BSD syslog format with facility-severity-mnemonic structure.",
    },

    "category": "network",
    "source_groups": ["network"],

    "format": {
        "type": "syslog_bsd",
        "confidence": 0.95,
        "message_prefix": "%<FACILITY>-<severity>-<MNEMONIC>",
        "timestamp_format": "MMM dd HH:mm:ss.SSS",
        "has_sequence_number": True,
        "has_host": True,
    },

    "sourcetype": {
        "name": "cisco:ios",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #7538) — Cisco Catalyst Add-on for Splunk",
    },

    "fields": [
        {"name": "timestamp", "type": "string", "required": True, "example": "Apr 12 10:23:45.123", "confidence": 1.0, "description": "BSD syslog timestamp with milliseconds"},
        {"name": "host", "type": "string", "required": True, "example": "cat9300-access-01", "confidence": 1.0, "description": "Hostname of the switch/router"},
        {"name": "sequence_number", "type": "int", "required": False, "example": "45231", "confidence": 0.7, "description": "Cisco log sequence number"},
        {"name": "facility", "type": "string", "required": True, "example": "LINK", "confidence": 1.0, "description": "Cisco facility name (LINK, LINEPROTO, SEC, SYS, CONFIG, DHCP, OSPF, BGP, SPANTREE)"},
        {"name": "severity", "type": "int", "required": True, "example": "5", "confidence": 1.0, "description": "Syslog severity 0-7 (0=emergency, 7=debug)"},
        {"name": "mnemonic", "type": "string", "required": True, "example": "UPDOWN", "confidence": 1.0, "description": "Cisco mnemonic identifying the specific event (UPDOWN, CHANGED, LOGIN_SUCCESS, CONFIG_I)"},
        {"name": "description", "type": "string", "required": True, "example": "Line protocol on Interface GigabitEthernet1/0/24, changed state to up", "confidence": 1.0, "description": "Human-readable message body"},

        # --- Interface fields ---
        {"name": "interface", "type": "string", "required": False, "example": "GigabitEthernet1/0/24", "confidence": 0.9, "description": "Interface name referenced in the message"},
        {"name": "interface_state", "type": "string", "required": False, "example": "up", "confidence": 0.8, "description": "Interface state: up, down, administratively down"},

        # --- Authentication / CLI ---
        {"name": "user", "type": "string", "required": False, "example": "netadmin", "confidence": 0.7, "description": "Username performing the action"},
        {"name": "source_ip", "type": "ipv4", "required": False, "example": "10.0.10.42", "confidence": 0.7, "description": "Source IP of management session"},
        {"name": "tty", "type": "string", "required": False, "example": "vty0", "confidence": 0.6, "description": "TTY / line identifier (console, vty0, aux)"},

        # --- Spanning tree / L2 ---
        {"name": "vlan", "type": "int", "required": False, "example": "100", "confidence": 0.7, "description": "VLAN ID referenced in the event"},
        {"name": "mac_address", "type": "string", "required": False, "example": "0050.56a1.2b3c", "confidence": 0.6, "description": "MAC address referenced (Cisco dotted format)"},
        {"name": "stp_state", "type": "string", "required": False, "example": "forwarding", "confidence": 0.5, "description": "Spanning-tree port state"},

        # --- Routing ---
        {"name": "neighbor_ip", "type": "ipv4", "required": False, "example": "10.0.0.2", "confidence": 0.5, "description": "Routing protocol neighbor IP (OSPF/BGP/EIGRP)"},
        {"name": "process_id", "type": "int", "required": False, "example": "100", "confidence": 0.5, "description": "Routing process ID (OSPF, EIGRP)"},

        # --- DHCP ---
        {"name": "dhcp_client_mac", "type": "string", "required": False, "example": "0050.56a1.aabb", "confidence": 0.5, "description": "DHCP client MAC address (DHCP messages)"},
    ],

    "sample_events": [
        {
            "raw": "Apr 12 10:23:45.123 cat9300-access-01 45231: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/24, changed state to up",
            "mnemonic": "UPDOWN",
        },
        {
            "raw": "Apr 12 10:23:46.456 cat9300-access-01 45232: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/24, changed state to up",
            "mnemonic": "UPDOWN",
        },
        {
            "raw": "Apr 12 10:25:11.789 cat9300-access-01 45233: %SEC_LOGIN-5-LOGIN_SUCCESS: Login Success [user: netadmin] [Source: 10.0.10.42] [localport: 22] at 10:25:11 UTC Sun Apr 12 2026",
            "mnemonic": "LOGIN_SUCCESS",
        },
    ],

    "generator_hints": {
        "module_name": "generate_cisco_ios",
        "function_name": "generate_cisco_ios_logs",
        "volume_category": "network_device",
        "baseline_events_per_day": 300,
        "facilities": ["LINK", "LINEPROTO", "SEC_LOGIN", "SYS", "CONFIG_I", "SPANTREE", "DHCP", "OSPF"],
        "mnemonics": ["UPDOWN", "CHANGED", "LOGIN_SUCCESS", "LOGIN_FAILED", "CONFIG_I", "RELOAD", "TOPOTRAP"],
        "facility_weights": {"LINK": 25, "LINEPROTO": 25, "SEC_LOGIN": 15, "SYS": 10, "CONFIG_I": 10, "SPANTREE": 5, "DHCP": 5, "OSPF": 5},
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-9/configuration_guide/sys_mgmt/b_179_sys_mgmt_9300_cg/configuring_system_message_logs.html", "kind": "vendor_doc", "trust": 0.95, "retrieved_at": "2026-04-12T00:00:00Z"},
            {"url": "https://splunkbase.splunk.com/app/7538", "kind": "splunkbase", "trust": 0.90, "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "total_samples_found": 3,
        "research_mode": "preset",
        "overall_confidence": 0.9,
    },
}

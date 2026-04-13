"""Bundled preset for cisco_asa. Used by fd-discover when --preset is selected
or when no --sample/--doc is provided."""

PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "cisco_asa",
        "display_name": "Cisco ASA Firewall",
        "vendor": "Cisco",
        "product": "ASA Firewall",
        "description": "Cisco ASA (Adaptive Security Appliance) firewall syslog messages covering connection builds/teardowns, ACL deny events, VPN activity, and threat detection, formatted as BSD syslog with %ASA- message IDs.",
    },

    "category": "network",
    "source_groups": ["network"],

    "format": {
        "type": "syslog_bsd",
        "confidence": 0.95,
        "message_prefix": "%ASA-<severity>-<message_id>",
        "timestamp_format": "MMM dd HH:mm:ss",
        "has_host": True,
        "has_message_id": True,
    },

    "sourcetype": {
        "name": "cisco:asa",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #1620) — Splunk Add-on for Cisco ASA",
    },

    "fields": [
        # --- Syslog header ---
        {"name": "timestamp", "type": "string", "required": True, "example": "Apr 12 10:23:45", "confidence": 1.0, "description": "BSD syslog timestamp (MMM dd HH:mm:ss)"},
        {"name": "host", "type": "string", "required": True, "example": "asa-fw-01", "confidence": 1.0, "description": "Hostname of the ASA device emitting the log"},
        {"name": "log_sequence_number", "type": "int", "required": False, "example": "123456", "confidence": 0.6, "description": "Sequential log message number (optional, if enabled)"},

        # --- ASA identifier ---
        {"name": "severity", "type": "int", "required": True, "example": "6", "confidence": 1.0, "description": "Syslog severity level (0-7, 0=emergency, 7=debug)"},
        {"name": "message_id", "type": "string", "required": True, "example": "302013", "confidence": 1.0, "description": "ASA message ID (e.g. 302013=TCP conn built, 106023=ACL deny)"},
        {"name": "log_level", "type": "string", "required": True, "example": "Information", "confidence": 0.9, "description": "Text severity: Emergency, Alert, Critical, Error, Warning, Notification, Information, Debug"},
        {"name": "description", "type": "string", "required": True, "example": "Built inbound TCP connection", "confidence": 1.0, "description": "Human-readable message body text"},

        # --- Connection fields ---
        {"name": "action", "type": "string", "required": True, "example": "Built", "confidence": 1.0, "description": "Action: Built, Teardown, Deny, permitted, denied"},
        {"name": "direction", "type": "string", "required": False, "example": "inbound", "confidence": 0.9, "description": "Traffic direction: inbound or outbound"},
        {"name": "protocol", "type": "string", "required": True, "example": "TCP", "confidence": 1.0, "description": "Network protocol: TCP, UDP, ICMP"},
        {"name": "connection_id", "type": "int", "required": False, "example": "5478921", "confidence": 0.8, "description": "ASA connection identifier"},

        # --- Source/destination ---
        {"name": "src_interface", "type": "string", "required": True, "example": "outside", "confidence": 1.0, "description": "Source interface name (e.g. outside, inside, dmz)"},
        {"name": "src_ip", "type": "ipv4", "required": True, "example": "198.51.100.42", "confidence": 1.0, "description": "Source IP address"},
        {"name": "src_port", "type": "int", "required": True, "example": "54321", "confidence": 1.0, "description": "Source TCP/UDP port"},
        {"name": "dest_interface", "type": "string", "required": True, "example": "inside", "confidence": 1.0, "description": "Destination interface name"},
        {"name": "dest_ip", "type": "ipv4", "required": True, "example": "10.1.1.25", "confidence": 1.0, "description": "Destination IP address"},
        {"name": "dest_port", "type": "int", "required": True, "example": "443", "confidence": 1.0, "description": "Destination TCP/UDP port"},

        # --- NAT translation ---
        {"name": "xlate_src_ip", "type": "ipv4", "required": False, "example": "203.0.113.5", "confidence": 0.7, "description": "Translated (NAT) source IP address"},
        {"name": "xlate_src_port", "type": "int", "required": False, "example": "51234", "confidence": 0.7, "description": "Translated (NAT) source port"},

        # --- Byte counters ---
        {"name": "bytes", "type": "int", "required": False, "example": "15482", "confidence": 0.8, "description": "Total bytes transferred in the connection"},
        {"name": "duration", "type": "string", "required": False, "example": "0:00:32", "confidence": 0.8, "description": "Connection duration (H:MM:SS)"},

        # --- ACL / policy ---
        {"name": "acl_name", "type": "string", "required": False, "example": "outside_access_in", "confidence": 0.8, "description": "Matched access control list name (deny/permit events)"},
        {"name": "acl_action", "type": "string", "required": False, "example": "denied", "confidence": 0.8, "description": "ACL action: permitted or denied"},

        # --- Authentication / user ---
        {"name": "user", "type": "string", "required": False, "example": "jdoe", "confidence": 0.7, "description": "Authenticated username (AAA, VPN)"},
        {"name": "auth_method", "type": "string", "required": False, "example": "LOCAL", "confidence": 0.6, "description": "Authentication method (LOCAL, RADIUS, LDAP)"},
        {"name": "group_policy", "type": "string", "required": False, "example": "GroupPolicy_VPN", "confidence": 0.6, "description": "VPN group policy name"},
        {"name": "tunnel_group", "type": "string", "required": False, "example": "DefaultRAGroup", "confidence": 0.6, "description": "VPN tunnel group name"},

        # --- Threat detection / misc ---
        {"name": "reason", "type": "string", "required": False, "example": "TCP Reset-O", "confidence": 0.7, "description": "Reason for action (teardown reason, deny reason)"},
        {"name": "icmp_type", "type": "int", "required": False, "example": "8", "confidence": 0.5, "description": "ICMP type (for ICMP connections)"},
        {"name": "icmp_code", "type": "int", "required": False, "example": "0", "confidence": 0.5, "description": "ICMP code"},
        {"name": "threat_category", "type": "string", "required": False, "example": "Scanning", "confidence": 0.5, "description": "Threat detection category"},
        {"name": "signature_id", "type": "string", "required": False, "example": "400025", "confidence": 0.5, "description": "IPS / threat detection signature ID"},
    ],

    "sample_events": [
        {
            "raw": "Apr 12 10:23:45 asa-fw-01 : %ASA-6-302013: Built inbound TCP connection 5478921 for outside:198.51.100.42/54321 (198.51.100.42/54321) to inside:10.1.1.25/443 (10.1.1.25/443)",
            "message_id": "302013",
        },
        {
            "raw": "Apr 12 10:24:12 asa-fw-01 : %ASA-6-302014: Teardown TCP connection 5478921 for outside:198.51.100.42/54321 to inside:10.1.1.25/443 duration 0:00:27 bytes 15482 TCP FINs",
            "message_id": "302014",
        },
        {
            "raw": "Apr 12 10:25:03 asa-fw-01 : %ASA-4-106023: Deny tcp src outside:203.0.113.77/49531 dst inside:10.1.1.50/22 by access-group \"outside_access_in\" [0x0, 0x0]",
            "message_id": "106023",
        },
    ],

    "generator_hints": {
        "module_name": "generate_cisco_asa",
        "function_name": "generate_cisco_asa_logs",
        "volume_category": "firewall",
        "baseline_events_per_day": 2000,
        "message_ids": ["302013", "302014", "302015", "302016", "106023", "106100", "113019", "602303", "722022", "733100"],
        "message_id_weights": {"302013": 30, "302014": 30, "302015": 10, "302016": 10, "106023": 10, "106100": 5, "113019": 2, "602303": 1, "722022": 1, "733100": 1},
        "actions": ["Built", "Teardown", "Deny", "permitted", "denied"],
        "protocols": ["TCP", "UDP", "ICMP"],
        "interfaces": ["outside", "inside", "dmz", "management"],
        "severities": [1, 2, 3, 4, 5, 6, 7],
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "https://www.cisco.com/c/en/us/td/docs/security/asa/syslog/b_syslog.html", "kind": "vendor_doc", "trust": 0.95, "retrieved_at": "2026-04-12T00:00:00Z"},
            {"url": "https://splunkbase.splunk.com/app/1620", "kind": "splunkbase", "trust": 0.90, "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "total_samples_found": 3,
        "research_mode": "preset",
        "overall_confidence": 0.9,
    },
}

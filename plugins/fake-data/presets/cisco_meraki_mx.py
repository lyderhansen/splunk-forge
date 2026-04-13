"""Bundled preset for cisco_meraki_mx. Used by fd-discover when --preset is selected
or when no --sample/--doc is provided."""

PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "cisco_meraki_mx",
        "display_name": "Cisco Meraki MX Security Appliance",
        "vendor": "Cisco",
        "product": "Meraki MX",
        "description": "Cisco Meraki MX security appliance syslog messages covering flows, URL activity, IDS alerts, and DHCP events. Flow logs use key=value pairs with org/network context and connection 5-tuple.",
    },

    "category": "network",
    "source_groups": ["network"],

    "format": {
        "type": "kv",
        "confidence": 0.9,
        "delimiter": " ",
        "kv_separator": "=",
        "syslog_wrapped": True,
        "message_tag": "flows",
        "timestamp_format": "epoch_float",
    },

    "sourcetype": {
        "name": "meraki:securityappliance",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #5580) — Cisco Meraki Add-on for Splunk",
    },

    "fields": [
        {"name": "timestamp", "type": "float", "required": True, "example": "1744453425.123456789", "confidence": 1.0, "description": "Epoch timestamp with nanosecond precision"},
        {"name": "host", "type": "string", "required": True, "example": "MX84-BranchOffice", "confidence": 1.0, "description": "Meraki appliance hostname or network name"},
        {"name": "org", "type": "string", "required": False, "example": "Example Corp", "confidence": 0.8, "description": "Meraki organization name"},
        {"name": "network", "type": "string", "required": True, "example": "Branch-NYC", "confidence": 0.9, "description": "Meraki network name"},
        {"name": "message_type", "type": "string", "required": True, "example": "flows", "confidence": 1.0, "description": "Meraki message tag: flows, urls, ids-alerts, events, airmarshal_events"},

        # --- Flow fields ---
        {"name": "src", "type": "ipv4", "required": True, "example": "10.0.10.42", "confidence": 1.0, "description": "Source IP address"},
        {"name": "dst", "type": "ipv4", "required": True, "example": "151.101.1.69", "confidence": 1.0, "description": "Destination IP address"},
        {"name": "protocol", "type": "string", "required": True, "example": "tcp", "confidence": 1.0, "description": "IP protocol (tcp, udp, icmp)"},
        {"name": "sport", "type": "int", "required": True, "example": "54321", "confidence": 1.0, "description": "Source port"},
        {"name": "dport", "type": "int", "required": True, "example": "443", "confidence": 1.0, "description": "Destination port"},
        {"name": "pattern", "type": "string", "required": True, "example": "allow all", "confidence": 1.0, "description": "Matched firewall rule pattern (allow/deny rule)"},

        # --- NAT ---
        {"name": "translated_src_ip", "type": "ipv4", "required": False, "example": "198.51.100.10", "confidence": 0.7, "description": "Post-NAT source IP"},
        {"name": "translated_port", "type": "int", "required": False, "example": "51234", "confidence": 0.7, "description": "Post-NAT source port"},

        # --- L2 / DHCP ---
        {"name": "mac", "type": "string", "required": False, "example": "aa:bb:cc:11:22:33", "confidence": 0.7, "description": "MAC address of client or device"},
        {"name": "dhcp_server", "type": "ipv4", "required": False, "example": "10.0.10.1", "confidence": 0.6, "description": "DHCP server IP address (DHCP events)"},
        {"name": "client_ip", "type": "ipv4", "required": False, "example": "10.0.10.85", "confidence": 0.6, "description": "DHCP client IP address"},
        {"name": "client_mac", "type": "string", "required": False, "example": "dd:ee:ff:44:55:66", "confidence": 0.6, "description": "DHCP client MAC"},
        {"name": "hostname", "type": "string", "required": False, "example": "laptop-jdoe", "confidence": 0.6, "description": "Client hostname"},

        # --- URL / IDS ---
        {"name": "url", "type": "string", "required": False, "example": "https://www.example.com/path", "confidence": 0.5, "description": "URL accessed (urls message type)"},
        {"name": "signature", "type": "string", "required": False, "example": "1:2019401:3", "confidence": 0.5, "description": "IDS signature ID (ids-alerts)"},
        {"name": "priority", "type": "string", "required": False, "example": "1", "confidence": 0.5, "description": "IDS alert priority"},
        {"name": "classification", "type": "string", "required": False, "example": "Attempted Information Leak", "confidence": 0.5, "description": "IDS classification text"},
    ],

    "sample_events": [
        {
            "raw": "<134>1 1744453425.123456789 MX84-BranchOffice flows src=10.0.10.42 dst=151.101.1.69 mac=aa:bb:cc:11:22:33 protocol=tcp sport=54321 dport=443 pattern: allow all",
            "message_type": "flows",
        },
        {
            "raw": "<134>1 1744453462.234567890 MX84-BranchOffice flows src=10.0.10.88 dst=203.0.113.77 mac=dd:ee:ff:44:55:66 protocol=tcp sport=49123 dport=23 pattern: deny all",
            "message_type": "flows",
        },
        {
            "raw": "<134>1 1744453510.345678901 MX84-BranchOffice urls src=10.0.10.42 dst=151.101.1.69 mac=aa:bb:cc:11:22:33 request: GET https://www.example.com/login",
            "message_type": "urls",
        },
    ],

    "generator_hints": {
        "module_name": "generate_cisco_meraki_mx",
        "function_name": "generate_cisco_meraki_mx_logs",
        "volume_category": "firewall",
        "baseline_events_per_day": 1500,
        "message_types": ["flows", "urls", "ids-alerts", "events", "airmarshal_events"],
        "message_type_weights": {"flows": 70, "urls": 20, "ids-alerts": 5, "events": 4, "airmarshal_events": 1},
        "protocols": ["tcp", "udp", "icmp"],
        "patterns": ["allow all", "deny all", "allow inbound", "deny inbound"],
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "https://documentation.meraki.com/General_Administration/Monitoring_and_Reporting/Syslog_Event_Types_and_Log_Samples", "kind": "vendor_doc", "trust": 0.95, "retrieved_at": "2026-04-12T00:00:00Z"},
            {"url": "https://splunkbase.splunk.com/app/5580", "kind": "splunkbase", "trust": 0.90, "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "total_samples_found": 3,
        "research_mode": "preset",
        "overall_confidence": 0.88,
    },
}

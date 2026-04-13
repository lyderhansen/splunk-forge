"""Bundled preset for checkpoint_traffic. Used by fd-discover when --preset is selected
or when no --sample/--doc is provided."""

PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "checkpoint_traffic",
        "display_name": "Check Point Firewall Traffic",
        "vendor": "Check Point",
        "product": "Check Point Firewall (Quantum / R81)",
        "description": "Check Point Security Gateway traffic log messages exported via LEA/Log Exporter in syslog key-value format. Includes connection 5-tuple, rule match, NAT, and blade enforcement fields.",
    },

    "category": "network",
    "source_groups": ["network"],

    "format": {
        "type": "kv",
        "confidence": 0.9,
        "delimiter": " ",
        "kv_separator": ":",
        "quoted_values": True,
        "syslog_wrapped": True,
        "timestamp_format": "epoch_seconds",
    },

    "sourcetype": {
        "name": "cp_log",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #4293) — Check Point App for Splunk",
    },

    "fields": [
        # --- Header ---
        {"name": "time", "type": "int", "required": True, "example": "1744453425", "confidence": 1.0, "description": "Epoch seconds when the event occurred"},
        {"name": "loc", "type": "int", "required": False, "example": "12345", "confidence": 0.7, "description": "Log file offset / location identifier"},
        {"name": "origin", "type": "string", "required": True, "example": "gw-hq-01", "confidence": 1.0, "description": "Security gateway hostname that generated the log"},
        {"name": "origin_ip", "type": "ipv4", "required": False, "example": "10.0.0.1", "confidence": 0.8, "description": "Security gateway management IP"},
        {"name": "product", "type": "string", "required": True, "example": "VPN-1 & FireWall-1", "confidence": 1.0, "description": "Check Point product / blade that produced the log"},
        {"name": "action", "type": "string", "required": True, "example": "accept", "confidence": 1.0, "description": "Action: accept, drop, reject, encrypt, decrypt, block"},
        {"name": "ifdir", "type": "string", "required": True, "example": "outbound", "confidence": 1.0, "description": "Interface direction: inbound or outbound"},
        {"name": "ifname", "type": "string", "required": True, "example": "eth1", "confidence": 1.0, "description": "Interface name"},
        {"name": "logid", "type": "int", "required": False, "example": "0", "confidence": 0.7, "description": "Log ID"},
        {"name": "loguid", "type": "string", "required": False, "example": "{0x661a2b3c,0x0,0x501a8c0,0x12345678}", "confidence": 0.6, "description": "Check Point log unique identifier"},

        # --- Connection 5-tuple ---
        {"name": "src", "type": "ipv4", "required": True, "example": "10.1.100.42", "confidence": 1.0, "description": "Source IP address"},
        {"name": "dst", "type": "ipv4", "required": True, "example": "203.0.113.25", "confidence": 1.0, "description": "Destination IP address"},
        {"name": "proto", "type": "string", "required": True, "example": "tcp", "confidence": 1.0, "description": "IP protocol: tcp, udp, icmp"},
        {"name": "s_port", "type": "int", "required": True, "example": "54321", "confidence": 1.0, "description": "Source port"},
        {"name": "service", "type": "int", "required": True, "example": "443", "confidence": 1.0, "description": "Destination port / service number"},
        {"name": "service_id", "type": "string", "required": False, "example": "https", "confidence": 0.9, "description": "Named service (http, https, ssh, dns)"},

        # --- Rule / policy ---
        {"name": "rule", "type": "int", "required": True, "example": "24", "confidence": 1.0, "description": "Numeric rule number that matched"},
        {"name": "rule_uid", "type": "string", "required": False, "example": "{3fa85f64-5717-4562-b3fc-2c963f66afa6}", "confidence": 0.7, "description": "Rule UID in the policy database"},
        {"name": "rule_name", "type": "string", "required": False, "example": "Outbound Web", "confidence": 0.8, "description": "Human-readable rule name"},
        {"name": "policy", "type": "string", "required": False, "example": "Standard", "confidence": 0.7, "description": "Security policy package name"},

        # --- NAT ---
        {"name": "xlatesrc", "type": "ipv4", "required": False, "example": "198.51.100.5", "confidence": 0.8, "description": "Translated (NAT) source IP"},
        {"name": "xlatedst", "type": "ipv4", "required": False, "example": "203.0.113.25", "confidence": 0.8, "description": "Translated (NAT) destination IP"},
        {"name": "xlatesport", "type": "int", "required": False, "example": "51234", "confidence": 0.8, "description": "Translated source port"},
        {"name": "xlatedport", "type": "int", "required": False, "example": "443", "confidence": 0.8, "description": "Translated destination port"},
        {"name": "nat_rule", "type": "int", "required": False, "example": "10", "confidence": 0.7, "description": "NAT rule number"},

        # --- Counters / session ---
        {"name": "bytes", "type": "int", "required": False, "example": "15482", "confidence": 0.8, "description": "Total bytes in the connection"},
        {"name": "packets", "type": "int", "required": False, "example": "42", "confidence": 0.7, "description": "Total packet count"},
        {"name": "elapsed", "type": "string", "required": False, "example": "0:00:05", "confidence": 0.6, "description": "Session elapsed time"},
        {"name": "conn_direction", "type": "string", "required": False, "example": "Outgoing", "confidence": 0.7, "description": "Connection direction classification"},

        # --- User / blade ---
        {"name": "user", "type": "string", "required": False, "example": "jdoe", "confidence": 0.6, "description": "Authenticated user (Identity Awareness)"},
        {"name": "src_user_name", "type": "string", "required": False, "example": "CORP\\jdoe", "confidence": 0.6, "description": "Source user name with domain"},
        {"name": "blade", "type": "string", "required": False, "example": "Firewall", "confidence": 0.7, "description": "Software blade producing the log (Firewall, URL Filtering, IPS, Application Control)"},
        {"name": "app_category", "type": "string", "required": False, "example": "Business / Economy", "confidence": 0.5, "description": "Application Control / URL Filtering category"},
    ],

    "sample_events": [
        {
            "raw": '<134>1 2026-04-12T10:23:45Z gw-hq-01 CheckPoint 12345 - [action:"accept"; conn_direction:"Outgoing"; ifdir:"outbound"; ifname:"eth1"; loguid:"{0x661a2b3c,0x0,0x501a8c0,0x12345678}"; origin:"gw-hq-01"; time:"1744453425"; version:"5"; product:"VPN-1 & FireWall-1"; src:"10.1.100.42"; dst:"203.0.113.25"; proto:"tcp"; s_port:"54321"; service:"443"; service_id:"https"; rule:"24"; rule_name:"Outbound Web"; rule_uid:"{3fa85f64-5717-4562-b3fc-2c963f66afa6}"; xlatesrc:"198.51.100.5"; xlatesport:"51234"; bytes:"15482"] accept',
            "action": "accept",
        },
        {
            "raw": '<134>1 2026-04-12T10:24:12Z gw-hq-01 CheckPoint 12346 - [action:"drop"; conn_direction:"Incoming"; ifdir:"inbound"; ifname:"eth0"; loguid:"{0x661a2b40,0x0,0x501a8c0,0x12345679}"; origin:"gw-hq-01"; time:"1744453452"; product:"VPN-1 & FireWall-1"; src:"203.0.113.77"; dst:"198.51.100.5"; proto:"tcp"; s_port:"49123"; service:"22"; service_id:"ssh"; rule:"99"; rule_name:"Cleanup Rule"] drop',
            "action": "drop",
        },
        {
            "raw": '<134>1 2026-04-12T10:25:11Z gw-hq-01 CheckPoint 12347 - [action:"accept"; conn_direction:"Outgoing"; ifdir:"outbound"; ifname:"eth1"; origin:"gw-hq-01"; time:"1744453511"; product:"Application Control"; src:"10.1.100.42"; dst:"8.8.8.8"; proto:"udp"; s_port:"53421"; service:"53"; service_id:"dns"; rule:"24"; rule_name:"Outbound Web"; blade:"Application Control"; app_category:"Network Protocols"; bytes:"182"] accept',
            "action": "accept",
        },
    ],

    "generator_hints": {
        "module_name": "generate_checkpoint_traffic",
        "function_name": "generate_checkpoint_traffic_logs",
        "volume_category": "firewall",
        "baseline_events_per_day": 3000,
        "actions": ["accept", "drop", "reject", "encrypt", "decrypt", "block"],
        "action_weights": {"accept": 80, "drop": 12, "reject": 4, "block": 3, "encrypt": 1},
        "protocols": ["tcp", "udp", "icmp"],
        "services": ["http", "https", "ssh", "dns", "smtp", "ftp", "rdp", "ntp", "snmp"],
        "blades": ["Firewall", "URL Filtering", "Application Control", "IPS", "Anti-Bot", "Anti-Virus"],
        "directions": ["inbound", "outbound"],
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "https://sc1.checkpoint.com/documents/SKP/CP_R81_LoggingAndMonitoring_AdminGuide/Topics-LMG/Log-Exporter.htm", "kind": "vendor_doc", "trust": 0.95, "retrieved_at": "2026-04-12T00:00:00Z"},
            {"url": "https://splunkbase.splunk.com/app/4293", "kind": "splunkbase", "trust": 0.90, "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "total_samples_found": 3,
        "research_mode": "preset",
        "overall_confidence": 0.88,
    },
}

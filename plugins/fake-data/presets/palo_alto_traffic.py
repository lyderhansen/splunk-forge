"""Bundled preset for palo_alto_traffic. Used by fd-discover when --preset is selected
or when no --sample/--doc is provided."""

PRESET = {
    "schema_version": 1,
    "generated_at": "2026-04-12T00:00:00Z",
    "generated_by": "manual bundled preset",

    "source": {
        "id": "palo_alto_traffic",
        "display_name": "Palo Alto Networks NGFW Traffic",
        "vendor": "Palo Alto Networks",
        "product": "NGFW / PAN-OS",
        "description": "Palo Alto Networks next-generation firewall traffic logs in PAN-OS comma-separated value (CSV) format, recording end-of-session flow records with App-ID, User-ID, zone, NAT, and byte/packet counters.",
    },

    "category": "network",
    "source_groups": ["network"],

    "format": {
        "type": "csv",
        "confidence": 0.95,
        "delimiter": ",",
        "quoted_values": False,
        "syslog_wrapped": True,
        "log_type_field_index": 3,
        "log_type_value": "TRAFFIC",
        "timestamp_format": "YYYY/MM/DD HH:mm:ss",
    },

    "sourcetype": {
        "name": "pan:traffic",
        "confidence": 0.95,
        "origin": "Splunkbase TA (app #491) — Palo Alto Networks Add-on for Splunk",
    },

    "fields": [
        # --- Header fields (positions 1-7) ---
        {"name": "future_use1", "type": "string", "required": False, "example": "", "confidence": 0.6, "description": "FUTURE_USE field (position 1)"},
        {"name": "receive_time", "type": "string", "required": True, "example": "2026/04/12 10:23:45", "confidence": 1.0, "description": "Time the log was received on the management plane"},
        {"name": "serial", "type": "string", "required": True, "example": "015351000012345", "confidence": 1.0, "description": "Serial number of the firewall that generated the log"},
        {"name": "type", "type": "string", "required": True, "example": "TRAFFIC", "confidence": 1.0, "description": "Log type — always TRAFFIC for traffic logs"},
        {"name": "subtype", "type": "string", "required": True, "example": "end", "confidence": 1.0, "description": "Subtype: start, end, drop, deny"},
        {"name": "future_use2", "type": "string", "required": False, "example": "", "confidence": 0.6, "description": "FUTURE_USE field (position 5)"},
        {"name": "time_generated", "type": "string", "required": True, "example": "2026/04/12 10:23:45", "confidence": 1.0, "description": "Time the log was generated on the dataplane"},

        # --- Session flow ---
        {"name": "src", "type": "ipv4", "required": True, "example": "10.1.100.42", "confidence": 1.0, "description": "Source IP address"},
        {"name": "dest", "type": "ipv4", "required": True, "example": "203.0.113.25", "confidence": 1.0, "description": "Destination IP address"},
        {"name": "natsrc", "type": "ipv4", "required": False, "example": "198.51.100.5", "confidence": 0.9, "description": "NAT source IP (post-translation)"},
        {"name": "natdst", "type": "ipv4", "required": False, "example": "203.0.113.25", "confidence": 0.9, "description": "NAT destination IP (post-translation)"},
        {"name": "rule", "type": "string", "required": True, "example": "allow-outbound-web", "confidence": 1.0, "description": "Name of the security rule that matched"},
        {"name": "src_user", "type": "string", "required": False, "example": "corp\\jdoe", "confidence": 0.7, "description": "User-ID mapped to source IP"},
        {"name": "dest_user", "type": "string", "required": False, "example": "", "confidence": 0.5, "description": "User-ID mapped to destination IP"},
        {"name": "app", "type": "string", "required": True, "example": "ssl", "confidence": 1.0, "description": "Application identified by App-ID"},
        {"name": "vsys", "type": "string", "required": True, "example": "vsys1", "confidence": 1.0, "description": "Virtual system name"},
        {"name": "from_zone", "type": "string", "required": True, "example": "trust", "confidence": 1.0, "description": "Source security zone"},
        {"name": "to_zone", "type": "string", "required": True, "example": "untrust", "confidence": 1.0, "description": "Destination security zone"},
        {"name": "inbound_interface", "type": "string", "required": True, "example": "ethernet1/2", "confidence": 1.0, "description": "Ingress interface"},
        {"name": "outbound_interface", "type": "string", "required": True, "example": "ethernet1/1", "confidence": 1.0, "description": "Egress interface"},
        {"name": "log_action", "type": "string", "required": True, "example": "default", "confidence": 1.0, "description": "Log forwarding action applied"},

        # --- Session detail ---
        {"name": "session_id", "type": "int", "required": True, "example": "178234", "confidence": 1.0, "description": "Unique session ID"},
        {"name": "repeat_count", "type": "int", "required": False, "example": "1", "confidence": 0.8, "description": "Repeat count for identical sessions"},
        {"name": "src_port", "type": "int", "required": True, "example": "54321", "confidence": 1.0, "description": "Source port"},
        {"name": "dest_port", "type": "int", "required": True, "example": "443", "confidence": 1.0, "description": "Destination port"},
        {"name": "natsport", "type": "int", "required": False, "example": "51234", "confidence": 0.9, "description": "Post-NAT source port"},
        {"name": "natdport", "type": "int", "required": False, "example": "443", "confidence": 0.9, "description": "Post-NAT destination port"},
        {"name": "flags", "type": "string", "required": False, "example": "0x19", "confidence": 0.8, "description": "Hex bitfield describing session flags"},
        {"name": "protocol", "type": "string", "required": True, "example": "tcp", "confidence": 1.0, "description": "IP protocol (tcp, udp, icmp)"},
        {"name": "action", "type": "string", "required": True, "example": "allow", "confidence": 1.0, "description": "Action: allow, deny, drop, reset-both, reset-client, reset-server"},

        # --- Counters ---
        {"name": "bytes", "type": "int", "required": True, "example": "15482", "confidence": 1.0, "description": "Total bytes (sent + received)"},
        {"name": "bytes_sent", "type": "int", "required": True, "example": "4823", "confidence": 1.0, "description": "Bytes sent from client to server"},
        {"name": "bytes_received", "type": "int", "required": True, "example": "10659", "confidence": 1.0, "description": "Bytes sent from server to client"},
        {"name": "packets", "type": "int", "required": True, "example": "42", "confidence": 1.0, "description": "Total packet count"},
        {"name": "start_time", "type": "string", "required": True, "example": "2026/04/12 10:23:42", "confidence": 1.0, "description": "Session start timestamp"},
        {"name": "elapsed", "type": "int", "required": True, "example": "3", "confidence": 1.0, "description": "Elapsed time in seconds"},
        {"name": "category", "type": "string", "required": False, "example": "computer-and-internet-info", "confidence": 0.8, "description": "URL / application category"},

        # --- Extended ---
        {"name": "seqno", "type": "int", "required": False, "example": "6543218", "confidence": 0.7, "description": "Log entry sequence number"},
        {"name": "action_flags", "type": "string", "required": False, "example": "0x8000000000000000", "confidence": 0.6, "description": "Bitfield of extended action flags"},
        {"name": "src_location", "type": "string", "required": False, "example": "10.0.0.0-10.255.255.255", "confidence": 0.6, "description": "Source GeoIP country/region"},
        {"name": "dest_location", "type": "string", "required": False, "example": "US", "confidence": 0.6, "description": "Destination GeoIP country/region"},
        {"name": "pkts_sent", "type": "int", "required": False, "example": "20", "confidence": 0.8, "description": "Packets sent client-to-server"},
        {"name": "pkts_received", "type": "int", "required": False, "example": "22", "confidence": 0.8, "description": "Packets sent server-to-client"},
        {"name": "session_end_reason", "type": "string", "required": False, "example": "tcp-fin", "confidence": 0.9, "description": "Reason session ended: tcp-fin, tcp-rst-from-client, aged-out, threat, policy-deny"},
        {"name": "device_name", "type": "string", "required": False, "example": "PA-5220-01", "confidence": 0.7, "description": "Firewall device name"},
    ],

    "sample_events": [
        {
            "raw": "1,2026/04/12 10:23:45,015351000012345,TRAFFIC,end,2049,2026/04/12 10:23:45,10.1.100.42,203.0.113.25,198.51.100.5,203.0.113.25,allow-outbound-web,corp\\jdoe,,ssl,vsys1,trust,untrust,ethernet1/2,ethernet1/1,default,2026/04/12 10:23:45,178234,1,54321,443,51234,443,0x19,tcp,allow,15482,4823,10659,42,2026/04/12 10:23:42,3,computer-and-internet-info,0,6543218,0x8000000000000000,10.0.0.0-10.255.255.255,US,0,20,22,tcp-fin,PA-5220-01",
            "subtype": "end",
        },
        {
            "raw": "1,2026/04/12 10:24:02,015351000012345,TRAFFIC,deny,2049,2026/04/12 10:24:02,10.1.100.88,203.0.113.77,198.51.100.5,203.0.113.77,block-telnet,corp\\asmith,,telnet,vsys1,trust,untrust,ethernet1/2,ethernet1/1,default,2026/04/12 10:24:02,178235,1,49123,23,0,0,0x0,tcp,deny,0,0,0,0,2026/04/12 10:24:02,0,any,0,6543219,0x0,10.0.0.0-10.255.255.255,US,0,0,0,policy-deny,PA-5220-01",
            "subtype": "deny",
        },
        {
            "raw": "1,2026/04/12 10:25:11,015351000012345,TRAFFIC,end,2049,2026/04/12 10:25:11,10.1.100.42,8.8.8.8,198.51.100.5,8.8.8.8,allow-dns,corp\\jdoe,,dns,vsys1,trust,untrust,ethernet1/2,ethernet1/1,default,2026/04/12 10:25:11,178236,1,53421,53,53421,53,0x19,udp,allow,182,62,120,2,2026/04/12 10:25:10,1,dns,0,6543220,0x0,10.0.0.0-10.255.255.255,US,0,1,1,aged-out,PA-5220-01",
            "subtype": "end",
        },
    ],

    "generator_hints": {
        "module_name": "generate_palo_alto_traffic",
        "function_name": "generate_palo_alto_traffic_logs",
        "volume_category": "firewall",
        "baseline_events_per_day": 5000,
        "subtypes": ["start", "end", "drop", "deny"],
        "subtype_weights": {"end": 80, "drop": 8, "deny": 10, "start": 2},
        "actions": ["allow", "deny", "drop", "reset-both", "reset-client", "reset-server"],
        "action_weights": {"allow": 85, "deny": 8, "drop": 5, "reset-both": 2},
        "apps": ["ssl", "web-browsing", "dns", "ssh", "ms-rdp", "smtp", "ntp", "icmp", "ftp", "office365", "salesforce", "slack"],
        "protocols": ["tcp", "udp", "icmp"],
        "zones": ["trust", "untrust", "dmz", "vpn"],
        "session_end_reasons": ["tcp-fin", "tcp-rst-from-client", "tcp-rst-from-server", "aged-out", "policy-deny", "threat"],
    },

    "research_metadata": {
        "sources_consulted": [
            {"url": "https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/traffic-log-fields", "kind": "vendor_doc", "trust": 0.95, "retrieved_at": "2026-04-12T00:00:00Z"},
            {"url": "https://splunkbase.splunk.com/app/491", "kind": "splunkbase", "trust": 0.90, "retrieved_at": "2026-04-12T00:00:00Z"},
        ],
        "total_samples_found": 3,
        "research_mode": "preset",
        "overall_confidence": 0.9,
    },
}

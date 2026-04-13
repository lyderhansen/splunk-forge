"""YOLO companion source map.

Maps a primary source (the one the user invoked /fd-init --yolo with) to
a short list of companion sources that tell a fuller story when
correlated via demo_id. fd-init's YOLO phase reads this to auto-scaffold
2-3 correlated generators instead of a single one — a one-source demo
feels thin in Splunk.

All referenced companion source IDs MUST match bundled preset filenames
in plugins/fake-data/presets/ so fd-add-generator hits the preset fast
path (no research subagent, no wizard).

Override with /fd-init <source> --yolo --single-source to disable
companion auto-scaffolding.
"""


# Exact-match companion map. Keys and values must match existing preset
# filenames (without .py). Each entry lists up to 2 companions in
# priority order — the first companion is scaffolded if opt-in is full,
# the second if the user asked for a richer demo.
YOLO_COMPANIONS = {
    # ─── Windows endpoint story ──────────────────────────────────────
    "wineventlog_security": ["sysmon", "entraid_signin"],
    "sysmon": ["wineventlog_security", "crowdstrike_falcon"],
    "crowdstrike_falcon": ["wineventlog_security", "sysmon"],

    # ─── Network perimeter story ─────────────────────────────────────
    "fortigate": ["wineventlog_security", "entraid_signin"],
    "palo_alto_traffic": ["wineventlog_security", "entraid_signin"],
    "cisco_asa": ["wineventlog_security", "entraid_signin"],
    "checkpoint_traffic": ["wineventlog_security", "entraid_signin"],
    "cisco_ios": ["fortigate", "wineventlog_security"],
    "cisco_meraki_mx": ["fortigate", "entraid_signin"],

    # ─── Cloud identity story ────────────────────────────────────────
    "entraid_signin": ["wineventlog_security", "o365_management"],
    "o365_management": ["entraid_signin", "wineventlog_security"],
    "aws_cloudtrail": ["aws_guardduty", "fortigate"],
    "aws_guardduty": ["aws_cloudtrail", "fortigate"],
    "gcp_audit": ["fortigate", "wineventlog_security"],

    # ─── Web / app story ─────────────────────────────────────────────
    "apache_access": ["fortigate", "linux_auth"],
    "nginx_access": ["fortigate", "linux_auth"],

    # ─── Linux ops ───────────────────────────────────────────────────
    "linux_auth": ["fortigate", "nginx_access"],

    # ─── Database ────────────────────────────────────────────────────
    "mssql_errorlog": ["wineventlog_security", "fortigate"],

    # ─── Collaboration ───────────────────────────────────────────────
    "cisco_webex": ["entraid_signin", "fortigate"],

    # ─── ERP ─────────────────────────────────────────────────────────
    "sap_audit": ["entraid_signin", "wineventlog_security"],

    # ─── ITSM ────────────────────────────────────────────────────────
    "servicenow_incident": ["wineventlog_security", "fortigate"],
}


# Category fallback when the primary source isn't in the exact-match
# map (e.g., the user ran /fd-init with a free-text description that
# fd-discover researched from scratch). Keys are SOURCE_META["category"]
# values from config.py's VALID_CATEGORIES.
YOLO_COMPANIONS_BY_CATEGORY = {
    "windows":       ["fortigate", "entraid_signin"],
    "linux":         ["fortigate", "entraid_signin"],
    "cloud":         ["fortigate", "wineventlog_security"],
    "network":       ["wineventlog_security", "entraid_signin"],
    "web":           ["fortigate", "linux_auth"],
    "database":      ["wineventlog_security", "fortigate"],
    "collaboration": ["entraid_signin", "fortigate"],
    "itsm":          ["wineventlog_security", "fortigate"],
    "erp":           ["wineventlog_security", "entraid_signin"],
    "retail":        ["fortigate", "nginx_access"],
    "ot":            ["fortigate", "wineventlog_security"],
}


def get_companions(primary_source_id: str, category: str = None) -> list:
    """Return up to 2 companion source IDs for a YOLO primary source.

    Args:
        primary_source_id: The source_id the user ran /fd-init --yolo with.
        category: The primary source's SOURCE_META category, used as a
            fallback when primary_source_id isn't in YOLO_COMPANIONS.

    Returns:
        List of 0-2 companion source_ids. Empty if no match.
    """
    if primary_source_id in YOLO_COMPANIONS:
        return YOLO_COMPANIONS[primary_source_id]
    if category and category in YOLO_COMPANIONS_BY_CATEGORY:
        return YOLO_COMPANIONS_BY_CATEGORY[category]
    return []

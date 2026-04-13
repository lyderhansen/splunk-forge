"""Publicly allocated IP ranges per country for geo-aware external IP pools.

Used by the init skill to auto-populate EXTERNAL_IP_POOL and
EXTERNAL_IP_POOL_BY_COUNTRY based on the countries in LOCATIONS.
Sourced from public RIR data for major ISPs and cloud providers.
Not intended as threat intelligence — just plausible-looking source IPs.

Each country has 1-3 CIDR ranges. These are large allocations from
well-known providers, not specific organizations.
"""

COUNTRY_RANGES = {
    "US": ["52.0.0.0/11", "104.16.0.0/12", "34.0.0.0/9"],
    "GB": ["51.140.0.0/14", "86.128.0.0/11", "20.68.0.0/14"],
    "DE": ["52.28.0.0/15", "85.214.0.0/16", "46.4.0.0/14"],
    "FR": ["51.15.0.0/16", "62.210.0.0/16", "176.31.0.0/16"],
    "NO": ["77.40.0.0/16", "193.213.112.0/20", "84.208.0.0/13"],
    "SE": ["46.246.0.0/16", "83.233.0.0/16", "213.115.0.0/16"],
    "DK": ["87.54.0.0/15", "130.225.0.0/16", "185.240.0.0/14"],
    "NL": ["145.131.0.0/16", "185.17.0.0/16", "31.186.0.0/15"],
    "IT": ["151.0.0.0/12", "79.0.0.0/10", "213.144.0.0/14"],
    "ES": ["88.0.0.0/11", "213.194.0.0/15", "37.14.0.0/15"],
    "CA": ["99.224.0.0/11", "70.24.0.0/13", "142.160.0.0/12"],
    "AU": ["1.120.0.0/13", "103.24.0.0/14", "49.176.0.0/12"],
    "JP": ["126.0.0.0/8", "133.0.0.0/8", "210.128.0.0/11"],
    "BR": ["177.0.0.0/8", "200.128.0.0/9", "189.0.0.0/11"],
    "IN": ["49.32.0.0/11", "106.192.0.0/10", "223.176.0.0/12"],
    "CN": ["1.80.0.0/12", "36.0.0.0/10", "112.0.0.0/10"],
    "RU": ["5.136.0.0/13", "77.72.0.0/14", "188.32.0.0/11"],
    "PL": ["83.0.0.0/11", "185.156.0.0/14", "188.146.0.0/15"],
    "IE": ["86.40.0.0/13", "185.8.0.0/14", "79.140.0.0/14"],
    "CH": ["85.0.0.0/13", "178.196.0.0/14", "188.60.0.0/14"],
}

# RFC 5737 TEST-NET ranges — guaranteed non-routable, used as fallback
# when a country is not in COUNTRY_RANGES.
FALLBACK_RANGES = [
    "198.51.100.0/24",  # TEST-NET-2
    "203.0.113.0/24",   # TEST-NET-3
]

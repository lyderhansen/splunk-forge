# Presets

This directory is reserved for pre-built source definitions for common log formats
(e.g. wineventlog, access_combined, cisco_asa, fortigate, aws_cloudtrail).

**Status:** Empty in X1. Will be populated starting with the discover-logformat plan (X2+).

**Future contribution model:** Each preset is a single Python file `<source_id>.py`
containing a `PRESET` dict with the same shape as a SPEC produced by discover-logformat.
Users can fork the plugin repo and add new presets via PR.

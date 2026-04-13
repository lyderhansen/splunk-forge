#!/usr/bin/env bash
# FAKE_DATA plugin SessionStart hook — announces plugin availability

# Output is injected into Claude's context at session start
cat <<'EOF'
🎯 FAKE_DATA plugin loaded — 8 skills available for synthetic Splunk log generation:

  /fd-init          Create a FAKE_DATA workspace (add --yolo for full auto-pipeline)
  /fd-discover      Research a log format from docs, samples, or free text
  /fd-add-generator Scaffold a Python log generator
  /fd-add-scenario  Create attack/ops/network scenarios with correlated events
  /fd-world         View and edit the organization world state (users, infra)
  /fd-generate      Guided log generation wizard (+ curses TUI)
  /fd-cim           Map generator fields to Splunk CIM data models
  /fd-build-app     Generate an installable Splunk Technology Add-on (TA)

Full pipeline: /fd-init → /fd-discover → /fd-add-generator → /fd-cim
             → /fd-add-scenario → /fd-generate → /fd-build-app

One-shot mode: /fd-init <log-file> --yolo
EOF

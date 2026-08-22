#!/bin/bash
# Monthly local data refresh for the OA competitive-intelligence project.
#
# Runs the three pull scripts that need real network access (ClinicalTrials.gov,
# openFDA, SEC EDGAR) - these can't run from the cloud weekly routine because
# that sandbox's network policy blocks those domains. This script is meant to
# run unattended via launchd (see com.wkalmans.oa-monthly-refresh.plist),
# not interactively.
set -euo pipefail

REPO_DIR="/Users/wkalmans/OA"
LOG_FILE="$REPO_DIR/scripts/monthly_refresh.log"

cd "$REPO_DIR"
{
  echo "===== Monthly refresh started: $(date) ====="

  git pull --ff-only origin main

  python3 scripts/pull_openfda_marketed.py
  python3 scripts/pull_clinicaltrials.py
  python3 scripts/pull_sec_filings.py

  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "Monthly local data refresh: $(date +%Y-%m-%d)

Re-pulls ClinicalTrials.gov, openFDA, and SEC EDGAR data from this machine
(the weekly cloud routine can't reach these domains - see README).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
    git push origin main
    echo "Changes committed and pushed."
  else
    echo "No changes - data was already current."
  fi

  echo "===== Monthly refresh finished: $(date) ====="
} >> "$LOG_FILE" 2>&1

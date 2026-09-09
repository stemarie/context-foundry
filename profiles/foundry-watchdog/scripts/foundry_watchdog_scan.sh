#!/usr/bin/env bash
# Scheduler-visible Watchdog entrypoint. Source sync installs this at
# ~/.hermes/profiles/foundry-watchdog/scripts/foundry_watchdog_scan.sh.
set -euo pipefail
PROFILE_ROOT="${HOME}/.hermes/profiles/foundry-watchdog"
SCANNER="${PROFILE_ROOT}/scripts/foundry_watchdog_scan.py"
STATE_DIR="${PROFILE_ROOT}/state"
DIGEST_FILE="${STATE_DIR}/foundry_watchdog_last_payload.sha256"

payload="$(/usr/bin/env python3 "${SCANNER}" --previous-digest-file "${DIGEST_FILE}")"
if [[ -z "${payload}" ]]; then
  exit 0
fi
printf '%s\n' "${payload}"
mkdir -p "${STATE_DIR}"
python3 -c 'import json,sys; print(json.load(sys.stdin)["digest"])' <<<"${payload}" > "${DIGEST_FILE}.tmp"
mv "${DIGEST_FILE}.tmp" "${DIGEST_FILE}"

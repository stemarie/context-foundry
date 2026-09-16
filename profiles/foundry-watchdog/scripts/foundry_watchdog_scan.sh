#!/usr/bin/env bash
# Scheduler-visible Watchdog entrypoint. Source sync installs this at
# ~/.hermes/profiles/foundry-watchdog/scripts/foundry_watchdog_scan.sh.
set -euo pipefail
PROFILE_ROOT="${HOME}/.hermes/profiles/foundry-watchdog"
SCANNER="${PROFILE_ROOT}/scripts/foundry_watchdog_scan.py"
FINALIZER="${PROFILE_ROOT}/scripts/foundry_draft_handoff.py"
INCIDENT_LOG="${PROFILE_ROOT}/scripts/foundry_incident_log.py"
STATE_DIR="${PROFILE_ROOT}/state"
DIGEST_FILE="${STATE_DIR}/foundry_watchdog_last_payload.sha256"

payload="$(/usr/bin/env python3 "${SCANNER}" --previous-digest-file "${DIGEST_FILE}")"
if [[ -z "${payload}" ]]; then
  exit 0
fi
# The finalizer consumes only explicit draft-handoff events, re-reads each
# cited card, and creates no external record. Any validation failure exits
# before the digest advances so the next scheduled run can retry safely.
printf '%s' "${payload}" | /usr/bin/env python3 "${FINALIZER}" --scan-payload >/dev/null
# A soft-nudge can be recorded by the Watchdog profile after live board
# read-back. Consume any durable pending incident here; the bridge itself
# passes only the database row's allowlisted structured fields to Brainiac.
/usr/bin/env python3 "${INCIDENT_LOG}" bridge-pending >/dev/null
printf '%s\n' "${payload}"
mkdir -p "${STATE_DIR}"
python3 -c 'import json,sys; print(json.load(sys.stdin)["digest"])' <<<"${payload}" > "${DIGEST_FILE}.tmp"
mv "${DIGEST_FILE}.tmp" "${DIGEST_FILE}"

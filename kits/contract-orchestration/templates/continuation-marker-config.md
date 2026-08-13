# Continuation adaptation marker

loop_job_id = "<LOOP_JOB_ID>"
project_scope = "<PROJECT_SCOPE>"
mode = "periodic-or-manual"

# Optional accelerator contract:
# - request only after a completed evidence receipt
# - coalesce duplicate requests by work record and revision
# - audit accepted and suppressed requests
# - reuse the existing loop; do not create a second scheduler/control plane
# - never create a concurrent writer for a shared checkout
# - preserve periodic/manual continuation as the fallback

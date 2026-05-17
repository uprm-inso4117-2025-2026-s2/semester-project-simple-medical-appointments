#!/usr/bin/env bash
# Creates two NEW scheduling LLTs (not in git history). Requires: gh auth login
set -euo pipefail

GH="${GH_CLI:-/opt/homebrew/bin/gh}"
REPO="${GITHUB_REPO:-uprm-inso4117-2025-2026-s2/semester-project-simple-medical-appointments}"

if ! "$GH" auth status &>/dev/null; then
  echo "Run: $GH auth login"
  exit 1
fi

echo "Using: $("$GH" --version | head -1)"

LTT1=$("$GH" issue create --repo "$REPO" \
  --title "[Lecture Topic Task]: Decision table tests for doctor slot availability (Lecture 2 & 3)" \
  --label "Task: Lecture Topic" --label "Scheduling" \
  --body "$(cat <<'EOF'
### Goal

Apply **decision table testing** from *Lecture 3 (Fit tables)* and *Lecture 2 Test Planning (input-space axes)* to **scheduling**: `GET /api/doctors/<id>/available-slots` and `generate_available_slots()`.

### Proposed Solution

- Build decision tables for API inputs (`date` missing/invalid/valid) and calendar rules (weekday vs Sunday, lunch break).
- Map each row to an automated pytest in `backend/tests/test_scheduling_decision_table.py`.
- Document tables in `documentation/Lecture Topic Task/Decision Table Testing for Doctor Slot Availability.adoc`.

### Success Criteria

- Every table row has a passing test named with its rule ID (e.g. `DT-API-03`).
- Rows cover **only scheduling** (availability/slots), not unrelated modules.
- Documentation cites Lecture 2 (input space) and Lecture 3 (Fit decision tables).

### Urgency

6 – Above Normal

### Difficulty

4 – Moderate

### Recommended Developer

@jachikasielu
EOF
)")

LTT2=$("$GH" issue create --repo "$REPO" \
  --title "[Lecture Topic Task]: State transition tests for slot booking capacity (Lecture 3 & Types)" \
  --label "Task: Lecture Topic" --label "Scheduling" \
  --body "$(cat <<'EOF'
### Goal

Model **slot capacity** as a state machine (AVAILABLE → PARTIAL → FULL → release) per *Lecture 3 defect life cycle* and *Types lecture state properties*, and verify scheduling never over-books or hides open seats incorrectly.

### Proposed Solution

- Implement in-memory per-slot counts and `try_reserve_slot` / capacity-aware available-slots list.
- Add `backend/tests/test_slot_capacity_state_transitions.py` for all valid and invalid transitions.
- Document the machine in `documentation/Lecture Topic Task/State Transition Testing for Slot Capacity.adoc`.

### Success Criteria

- Tests cover reserve-to-full, reject when full (409), decrement on cancel, and slot reappearing in the API list.
- Invalid times (e.g. lunch) never change state (400).
- Documentation ties transitions to Lecture 3 and scheduling risk from Lecture 2.

### Urgency

6 – Above Normal

### Difficulty

5 – Somewhat Hard

### Recommended Developer

@jachikasielu
EOF
)")

echo "Created: $LTT1"
echo "Created: $LTT2"

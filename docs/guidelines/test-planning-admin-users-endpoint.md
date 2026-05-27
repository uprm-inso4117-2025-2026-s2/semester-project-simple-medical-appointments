# Test Planning Applied to GET /api/admin/users

> Based on the *Test Planning* lecture by Professor Bienvenido Vélez, PhD, INSO 4117 Software Reliability Testing. Adapted for the User Management module of Simple Medical Appointments.

---

## 1. Why Test Planning Matters Here

The lecture opens with a constraint that applies directly to this route: resources are limited, you cannot test every possible situation, and you must invest those resources wisely. `GET /api/admin/users` is a single endpoint, but its input space is wider than it looks: authentication header, role filter, status filter, and page/limit parameters each multiply the number of possible inputs. Testing every combination is impossible. A test plan defines which tests to run and in what order, so the most important defects are found first.

The lecture's goal for test planning is to **deliver the right tests, in the right order, to discover as many issues as possible within the time, budget, and risk appetite available**.

---

## 2. Risk Assessment

The lecture defines the expected cost of a defect as:

> **Expected Cost(D) = P(D occurs) × Cost(D occurs)**

Prioritizing tests means finding where both factors are high.

### Probability of defect: P(D) >> 0

The lecture identifies four indicators. Two apply directly here:

- **Complex units:** The route combines JWT authentication, role verification, and query-parameter filtering in a single request handler. Each layer is an independent source of bugs.
- **Synchronization/timing issues:** The route reads from the database and must reflect current role and status values; stale reads or missing joins are a realistic failure mode.

### Cost of defect: Cost(D) >> 0

Two indicators from the lecture apply:

- **Sine qua non functionality:** The admin panel cannot function at all without a working user list. A broken `GET /api/admin/users` disables every administrative workflow downstream.
- **Damage to reputation/trust:** If a non-admin user can successfully call this route and retrieve the full user list, the system exposes personal health information to unauthorized parties. This is the highest-cost defect in the entire module.

**Conclusion:** This endpoint has both high probability and high cost indicators. It should be tested first and tested thoroughly relative to lower-risk routes.

---

## 3. Test Plan Axes

The lecture describes a test plan as unfolding along multiple axes. The ones relevant to this endpoint are:

| Axis | Decision for this plan |
|---|---|
| **Testing level** | Integration: tests hit a real (test) database and a running Flask app; unit tests alone cannot verify the auth middleware chain |
| **Testing type** | Functional (correctness of responses) + Security (authorization enforcement) |
| **Input space** | Equivalence partitions on auth header, `role` filter, `status` filter |
| **Functionality** | Each requirement maps to at least one test |
| **Level of automation** | Fully automated via pytest; no manual steps |

---

## 4. Input Space Partitioning

The lecture defines an **equivalence partition** as a subset of inputs that the system is expected to treat similarly. One representative per partition is sufficient to cover the class. Invalid partitions must also be represented.

### Auth header partitions

| Partition | Representative | Expected behavior |
|---|---|---|
| Valid admin JWT | Token for a user with `role = admin` | 200 OK, user list returned |
| Valid non-admin JWT | Token for a user with `role = doctor` or `patient` | 403 Forbidden |
| Missing header | No `Authorization` header | 401 Unauthorized |
| Malformed token | `Bearer not-a-real-token` | 401 Unauthorized |

### `role` filter partitions

| Partition | Representative | Expected behavior |
|---|---|---|
| Valid role | `?role=doctor` | 200, only doctor records returned |
| Another valid role | `?role=patient` | 200, only patient records returned |
| Invalid role value | `?role=wizard` | 400 Bad Request |
| Absent (no filter) | *(omit parameter)* | 200, all users returned |

### `status` filter partitions

| Partition | Representative | Expected behavior |
|---|---|---|
| Active | `?status=active` | 200, only active users |
| Deactivated | `?status=deactivated` | 200, only deactivated users |
| Invalid value | `?status=banned` | 400 Bad Request |
| Absent | *(omit parameter)* | 200, all statuses returned |

---

## 5. Prioritized Test Order

The lecture's test plan algorithm says: prioritize tests to uncover potential defects with the highest costs first, and remove lower-priority tests if the plan exceeds budget.

Applying the risk formula:

1. **Non-admin can call the route** (Cost(D) is highest: data exposure). Run this first.
2. **Unauthenticated request is rejected** (Cost(D) is high: any user could scrape the list). Run second.
3. **Admin gets the full user list** (core happy path; must pass before filter tests are meaningful).
4. **Invalid `role` filter returns 400** (prevents silent data corruption when a typo is in the filter).
5. **Invalid `status` filter returns 400** (same reason as above).
6. **Valid `role` filter returns correct subset** (verifies filtering logic works).
7. **Valid `status` filter returns correct subset** (verifies status filtering works).
8. **Malformed JWT is rejected** (covers a corner case in token parsing).

Tests 1–5 cover the highest-risk cases and should never be dropped. Tests 6–8 are lower risk but confirm the feature is complete.

---

## 6. Test Completion Criteria

The lecture identifies test completion criteria as a strategy axis. For this endpoint, testing is complete when:

- All eight partitions above have a passing test.
- No 403/401 test is skipped or marked expected-to-fail.
- The test suite runs cleanly in CI against a fresh test database.

---

## 7. Summary

| Test Planning Concept | Application to GET /api/admin/users |
|---|---|
| Limited resources → invest wisely | Only one representative per equivalence partition |
| P(D) indicators | Complex auth chain + DB reads = higher defect probability |
| Cost(D) indicators | Core functionality + potential data exposure = highest cost |
| Equivalence partitioning | Auth header, role filter, status filter each divided into valid/invalid/absent |
| Prioritization | Auth bypass tests run first; filter coverage runs last |
| Testing level | Integration (real DB + Flask app required) |
| Completion criteria | All partitions covered, no skipped security tests, CI green |

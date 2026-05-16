# Functional Testing Applied to the Doctor Profile Edit Flow

> Based on the *Functional Testing* lecture by Professor Marko Schütz-Schmuck, University of Puerto Rico at Mayagüez. Adapted for the User Management module of Simple Medical Appointments.

---

## 1. What Does "Functional" Mean?

A **functional test** verifies that the system behaves correctly from the user's perspective — that a given input produces the expected output or observable state change. It does not care *how* the code produces the result internally; it only checks *what* the system does.

In the context of `DoctorProfile.jsx`, the observable behaviors are:

- Clicking **Edit Profile** switches the page into edit mode (inputs appear for `phone_number`, `specialty`, and `bio`).
- Entering a phone number with fewer than 10 digits and clicking **Save Changes** blocks the save and shows an error message.
- Entering a valid change and clicking **Save Changes** calls the backend and updates the displayed values.

These are functional behaviors because they are derived directly from requirements and are verifiable without inspecting component internals.

---

## 2. Test Classification: Unit Tests with Test Doubles

The lecture distinguishes **unit**, **integration**, and **system** tests by the scope of what they exercise.

The `DoctorProfile` tests are **unit tests**: they render a single component in isolation and make assertions on what the user sees and how the component responds to interaction. No real network calls are made.

To isolate the component, the tests rely on **test doubles** — a concept from the lecture covering *stubs, mocks, scaffolding, and fixtures*:

| Test Double | Role in DoctorProfile Tests |
|---|---|
| **Mock** (`vi.mock`) | Replaces `getProfile` and `updateProfile` from `../services/api` so no real HTTP request is issued. |
| **Stub** | `supabase.auth.getSession` returns a canned session object, simulating an authenticated doctor without a real Supabase connection. |
| **Fixture** | A static profile object (name, phone, specialty, bio) serves as pre-test context, ensuring every test starts from the same known state. |

Using test doubles answers the lecture's question — *"how do we test A which relies on B, before B is ready?"* — by replacing B (the API layer and auth service) with controlled stand-ins.

---

## 3. Behavior Under Test and Functional Coverage

Each test maps to one of the acceptance criteria from the original feature requirement:

### 3.1 Entering Edit Mode

**Requirement:** Entering edit mode on the doctor profile page is covered in tests.

**Test scenario:**
```
Given  the doctor profile page is loaded with a valid session
When   the user clicks "Edit Profile"
Then   input fields appear for phone_number, specialty, and bio
```

The `isEditing` flag in the component controls whether `EditField` or `InfoField` renders. The functional test confirms the user-visible result: input elements become present in the DOM.

### 3.2 Invalid Phone Validation

**Requirement:** The invalid phone validation is covered in tests.

**Test scenario:**
```
Given  the page is in edit mode
When   the user changes the phone number to "123" (fewer than 10 digits)
 And   clicks "Save Changes"
Then   the save is blocked
 And   the error message "Phone number must be a valid 10-digit number." is displayed
 And   updateProfile is never called
```

This is a **negative functional test** — it verifies a requirement about what the system must *not* do (send invalid data). The lecture notes that we can test for *unnecessary parts of the implementation* (overly permissive sends) by asserting the mock was never called.

### 3.3 Valid Save with Changed Fields

**Requirement:** A valid save with changed doctor fields is covered in tests.

**Test scenario:**
```
Given  the page is in edit mode
 And   the user changes specialty to "Cardiology"
When   the user clicks "Save Changes"
Then   updateProfile is called with { specialty: "Cardiology" }
 And   the page exits edit mode
 And   the displayed specialty updates to "Cardiology"
```

Only changed fields are included in the payload — unchanged fields are not sent. The test asserts both the API call arguments (functional correctness of the diff logic) and the updated display (functional correctness of the UI).

---

## 4. Alpha vs. Beta Testing Alignment

The lecture distinguishes **alpha testing** (internal, by the development team, while the product is still maturing) from **beta testing** (external, by real users, after a release candidate is stable).

These Vitest tests are **alpha tests**: they run in CI against every pull request, before any user touches the feature. Their purpose is to confirm that the developer's implementation satisfies the requirements before the feature is promoted. A manual QA pass against a staging environment would be the beta equivalent for this feature.

---

## 5. Test Automation Trade-offs

The lecture lists both myths and real benefits of automated testing. For the DoctorProfile edit flow specifically:

**Benefit — regression testing:** Once the edit flow is automated, every future change to `DoctorProfile.jsx` re-runs these tests for free. If a refactor accidentally removes the phone validation, the test catches it without any human reviewer having to manually exercise the form.

**Benefit — setting up test data and pre-test context:** The fixture profile and stubbed session give every test a clean, deterministic starting state. Without automation, a tester would have to manually create a doctor account and log in before each check.

**Hidden cost — maintenance:** The lecture warns that *do the interfaces evolve?* is the key maintenance question. If `getProfile` or `updateProfile` change their signatures, or if the `DOCTOR_EDIT_FIELDS` constant expands, the mocks and fixture must be updated to match. Tests that mock the API layer are tightly coupled to that contract.

---

## 6. Acceptance Testing Connection

The lecture describes how acceptance tests are derived from the chain:

> user story → requirement → acceptance test → specification example

For the DoctorProfile edit flow:

| Layer | Content |
|---|---|
| **User story** | As a doctor, I want to edit my phone number, specialty, and bio so that my profile stays up to date. |
| **Requirement** | The system must validate that a phone number has at least 10 digits before saving. |
| **Acceptance test** | Entering a 3-digit phone number and clicking Save must display an error and not call the API. |
| **Specification example** | Phone input = `"123"` → error text = `"Phone number must be a valid 10-digit number."`, `updateProfile` call count = 0. |

The Vitest tests in `DoctorProfile.test.jsx` correspond directly to the **specification example** level — the most concrete, verifiable form of the requirement.

---

## 7. Summary

| Concept from Lecture | Application in DoctorProfile |
|---|---|
| Functional test | Verifies observable edit, validate, and save behaviors |
| Unit test | Single component rendered in isolation |
| Test doubles (mock/stub/fixture) | API and auth layers replaced with controlled stand-ins |
| Negative functional test | Confirms invalid phone blocks save and never calls API |
| Alpha testing | Automated Vitest suite run in CI before any user exposure |
| Acceptance test chain | User story → requirement → test → specification example |
| Automation benefit: regression | Future refactors re-run all edit-flow checks automatically |
| Automation cost: maintenance | Mocks must stay in sync with API contract changes |

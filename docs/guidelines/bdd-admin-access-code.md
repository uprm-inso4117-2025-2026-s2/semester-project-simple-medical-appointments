# Behavior-Driven Development Applied to the Admin Access-Code Flow

> Based on the *Behavior Driven Development* lecture by Professor Marko Schütz-Schmuck, University of Puerto Rico at Mayagüez. Adapted for the User Management module of Simple Medical Appointments.

---

## 1. Why BDD for This Flow

The admin access-code check sits at the boundary between the registration form and the backend. It involves three distinct outcomes (empty submission, rejected code, accepted code), each of which must be unambiguous to every stakeholder: the developer implementing the check, the team lead defining the rule, and the tester writing the assertions.

BDD targets exactly this problem. Its goal is not just to produce tests, but to produce an **unambiguous expression of requirements** that developers and non-developers can read and validate together. The three scenarios below are the result of the *discovery* phase: writing acceptance criteria while the user story is still being discussed, so the whole team contributes to what "correct behavior" means before any code is written.

---

## 2. The User Story

> As an admin, I want the signup form to verify my access code before creating my account, so that only authorized people can register as administrators.

From this story, the BDD process moves through three phases:

- **Discovery:** identify the acceptance criteria together (empty code, wrong code, valid code).
- **Formulation:** evolve those criteria into specific, clear, unambiguous scenarios.
- **Automation:** express the scenarios as runnable tests so that evidenced behavior remains.

---

## 3. The Three Perspectives (the "Triad")

The access-code feature involves three different viewpoints, each of which the scenarios must satisfy:

| Stakeholder | Focus |
|---|---|
| **Customer-centric** (team lead / admin user) | Is the right code accepted? Is an unauthorized person actually blocked? |
| **Developer-centric** | What does the component call? What state does it render after each response? |
| **Test-centric** | What are the edge cases: empty string, whitespace-only, wrong code vs. no code? |

Formulating scenarios with all three perspectives prevents gaps where a test passes for the wrong reason, or a real user case goes uncovered.

---

## 4. BDD Scenarios

Each scenario follows the **Given / When / Then** structure from the lecture: *Given* describes the software state before the test, *When* describes the action during the test, and *Then* describes the observable state after.

### Scenario 1: Empty access code

```
Feature: Admin access-code verification

  Scenario: Submitting an empty access code shows a page error
    Given  the admin is on the AdminDetails step of the signup flow
    When   the admin leaves the access-code field blank
     And   clicks the "Complete Signup" button
    Then   the form does not submit a request to the backend
     And   an error message is displayed on the page
```

**Why this scenario exists:** The frontend must guard against empty submissions before making a network call. Testing this without a backend response confirms that the validation is purely client-side and does not depend on network availability.

---

### Scenario 2: Access code rejected by the backend

```
  Scenario: A failed access-code check displays the backend error on the page
    Given  the admin is on the AdminDetails step of the signup flow
     And   the backend will reject the access code with a 401 error
    When   the admin enters an incorrect access code
     And   clicks the "Complete Signup" button
    Then   a POST request is sent to the access-code verification endpoint
     And   the backend error message is rendered on the page
     And   the signup flow does not advance
```

**Why this scenario exists:** The backend is the authoritative source of truth for whether a code is valid. This scenario confirms that the frontend correctly surfaces the server's rejection to the user and does not silently swallow the error.

---

### Scenario 3: Access code accepted by the backend

```
  Scenario: A successful access-code check continues the signup flow
    Given  the admin is on the AdminDetails step of the signup flow
     And   the backend will accept the access code with a 200 response
    When   the admin enters a valid access code
     And   clicks the "Complete Signup" button
    Then   a POST request is sent to the access-code verification endpoint
     And   the signup flow advances to the next step
     And   no error message is shown on the page
```

**Why this scenario exists:** The happy path must be explicitly verified. It is possible to write frontend logic that always shows an error (or never calls the backend) and still pass the first two scenarios. The third scenario closes that gap.

---

## 5. From Scenarios to Specification Examples

The lecture distinguishes between **scenarios** (general behavior) and **specification examples** (concrete, executable values). Translating Scenario 2 to a specification example:

```
Given  the admin is on the AdminDetails step
 And   the access-code input contains "WRONG-CODE-123"
 And   POST /api/auth/admin/verify-code returns { error: "Invalid access code" } with status 401
When   the admin clicks "Complete Signup"
Then   the text "Invalid access code" appears in the DOM
 And   the current route is still /register/admin-details
 And   the POST mock was called exactly once
```

This level of specificity (real input values, real endpoint paths, real DOM assertions) is what makes the test automatable and removes ambiguity about what "rejected" means.

---

## 6. Automation and Shared Understanding

The lecture notes that BDD is *possibly automated* and that automation ensures **evidenced behavior remains**: the test suite is living proof that each scenario still holds after every change to the codebase.

For the access-code flow, automated tests serve two purposes:

1. **Shared understanding:** Any team member can read a Given/When/Then scenario and understand exactly what the feature does, without reading the component source.
2. **Regression protection:** If a future refactor accidentally removes the empty-code guard, Scenario 1 will fail before the change is merged.

The scenarios above are written to be framework-agnostic, but they map directly to Vitest + React Testing Library assertions: `render`, `fireEvent`, `waitFor`, and `expect(screen.getByText(...))`.

---

## 7. Summary

| BDD Concept | Application in the Admin Access-Code Flow |
|---|---|
| User story | Admin wants signup gated by access code |
| Discovery phase | Three criteria identified: empty, rejected, accepted |
| Formulation phase | Each criterion expressed as a Given/When/Then scenario |
| Automation phase | Scenarios map to Vitest assertions on rendered component |
| The triad | Team lead (security), developer (API contract), tester (edge cases) |
| Specification example | Concrete values: input string, HTTP status, DOM text, call count |
| Shared understanding | Scenarios readable by any stakeholder without seeing the code |

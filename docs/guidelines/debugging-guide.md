# Debugging Guide

> Based on the debugging lecture by Professor Marko Schütz-Schmuck, University of Puerto Rico at Mayagüez. Adapted for this React project.

Welcome to the project. This guide introduces the core concepts and tools you'll need to debug effectively as you work on features like appointment booking, doctor search, and patient management.

---

## 1. What Is Debugging?

> "Fixing a buggy program is a process of confirming, one by one, that the many things you believe to be true about the code actually are true."

Debugging is a structured process of hypothesis testing. When something goes wrong (say, the doctor search list renders empty even though the API call succeeded), you likely have a mental model of how the code works. Debugging is how you systematically verify which part of that model is wrong.

This is closely related to testing: tests proactively confirm your assumptions before bugs surface; debugging confirms them after something has already gone wrong.

---

## 2. Breakpoints and Watchpoints: Why They Beat `console.log`

### The Problem with `console.log` Debugging

Scattering `console.log` calls through your components is slow and messy. You re-save the file for every new piece of information you need, logs pile up and become noisy, and it's easy to accidentally commit them. In React, a single state change can trigger multiple re-renders, logs can fire far more times than you expect, making the output hard to reason about.

### Breakpoints

A **breakpoint** is a marker you place on a line of code. When execution reaches that line, the browser pauses, giving you full visibility into the current state, props, and call stack at that exact moment.

**Setting a breakpoint in Chrome/Firefox DevTools:**

1. Open DevTools (`F12` or `Cmd+Option+I`)
2. Go to the **Sources** tab
3. Find your component file (for example: `AppointmentBooking.jsx`), use `Cmd+P` / `Ctrl+P` to search by filename
4. Click the line number to set a breakpoint

**Example:** Suppose `bookAppointment()` is silently failing. Set a breakpoint on the first line of that function. When it's hit, you can hover over variables to inspect their values, or explore them in the **Scope** panel on the right.

You can also trigger a breakpoint directly from code using the `debugger` statement:

```js
async function bookAppointment(patientId, doctorId, date) {
  debugger; // execution pauses here when DevTools is open
  const response = await api.post('/appointments', { patientId, doctorId, date });
  // ...
}
```

**Conditional breakpoints** only pause when a condition is met. Right-click a line number in DevTools, then **Add conditional breakpoint**:

```
doctorId === 1023
```

This is far more efficient than stepping through every call when you only care about one specific case.

### Watchpoints

A **watchpoint** monitors an expression and pauses execution whenever its value changes, regardless of where in the code that change happens.

**Setting a watchpoint in Chrome DevTools:**

1. In the **Sources** tab, find the **Watch** panel (right sidebar)
2. Click `+` and enter an expression, for example: `appointmentCount`

DevTools will evaluate that expression at every pause point and highlight when it changes.

For deeper state tracking in React, the **React DevTools** browser extension lets you inspect component state and props in real time, and highlights components that re-render, helping you spot unexpected state mutations.

**Summary of advantages over `console.log`:**

| | `console.log` | DevTools (breakpoints/watchpoints) |
|---|---|---|
| Requires file save & re-render | Yes | No |
| Risk of committing to repo | Yes | No |
| Can inspect any variable on the fly | No | Yes |
| Can pause on conditions | No | Yes |
| Can detect *where* a value changes | No | Yes (watchpoints) |
| Works with React component state/props | Partially | Yes (React DevTools) |

---

## 3. Preparing Your Code for Debugging

React apps built with Vite or Create React App are already configured to include **source maps** in development mode - the browser equivalent of compiling with debug symbols. Source maps let the browser translate minified/bundled JavaScript back into your original component files, so breakpoints and stack traces point to readable code instead of a compiled bundle.

**Always debug against the dev server, not a production build:**

```bash
npm run dev      # Vite
npm start        # Create React App
```

Never debug against `npm run build` output. That's equivalent to debugging optimized, minified code without symbols, the browser will show you `main.abc123.js:1` instead of `AppointmentBooking.jsx:47`.

**Source maps in Vite** are on by default in dev mode. For production debugging, you can opt in explicitly:

```js
// vite.config.js
export default {
  build: {
    sourcemap: true
  }
}
```

The analogy to the lecture concepts:

| C++ concept (from lecture) | React equivalent |
|---|---|
| Compile with `-g` (debug symbols) | Run dev server with source maps enabled |
| Compile with `-O0` (no optimization) | Use `npm run dev` (unminified, unoptimized) |
| GDB reads symbol table | Browser DevTools reads source maps |

---

## 4. Basic Browser DevTools Debugging Workflow

### The Debugging Cycle

The debugger workflow follows the same structure as the lecture's GDB flow, in the browser instead of the terminal.

| GDB command | DevTools / React equivalent |
|---|---|
| `start` | Open DevTools, reload the page to pause at first `debugger` or breakpoint |
| `run` | Resume (`F8` or the ▶ button) |
| `next` | Step over (`F10`) — executes the next line, skips over function calls |
| `step` | Step into (`F11`) — follows execution inside a called function |
| `cont` | Resume until the next breakpoint (`F8`) |
| `break <location>` | Click a line number in Sources, or write `debugger` in code |
| `watch <expr>` | Add expression to the **Watch** panel in Sources |
| `print <expr>` | Hover over variable, or evaluate in the Console while paused |
| `backtrace` | View the **Call Stack** panel in Sources |

### Example Walkthrough: Debugging an Appointment Booking Flow

Suppose submitting the booking form does nothing and you don't know why.

```jsx
// AppointmentBooking.jsx
async function handleSubmit(e) {
  e.preventDefault();
  debugger; // <-- add temporarily

  const result = await bookAppointment(patientId, selectedDoctor, selectedDate);
  setConfirmation(result);
}
```

1. Open DevTools (`F12`) and go to **Sources**
2. Trigger the form submit, execution pauses at `debugger`
3. In the **Scope** panel, inspect `patientId`, `selectedDoctor`, `selectedDate`
4. Press `F10` (step over) to advance line by line
5. Press `F11` (step into) to follow execution inside `bookAppointment()`
6. Check the **Call Stack** panel to see how you got here
7. Press `F8` to resume when done

### React DevTools

Install the **React Developer Tools** browser extension for React-specific inspection:

- **Components tab:** inspect props and state for any component in the tree in real time
- **Profiler tab:** record renders to identify unnecessary re-renders (for example: the doctor list re-rendering on every keystroke)

```
In Chrome Web Store, search "React Developer Tools" by Meta
```

---

## 5. Good Habits

- **Start small.** Reproduce the bug with the smallest possible input (one patient, one doctor, one date) before stepping through the full flow.
- **Form a hypothesis first.** Before adding a breakpoint, write down what you think is wrong. Use the debugger to confirm or disprove it.
- **Use conditional breakpoints** to avoid stepping through every item in a list when you only care about one specific case.
- **Check the call stack** when something crashes, it immediately shows the chain of component renders and function calls that led to the failure.
- **Remove `debugger` statements before committing.** Consider adding an ESLint `no-debugger` rule to catch them automatically.

---

*Based on: Schütz-Schmuck, M. (2023). Debugging [Lecture slides]. Department of Mathematical Sciences, University of Puerto Rico at Mayagüez.*
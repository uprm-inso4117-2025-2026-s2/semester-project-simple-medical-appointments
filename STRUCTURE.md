# Project Structure

This document describes how the project is organized and where new code should go.

---

## Current Structure

```
/
├── frontend/                        # React application (Vite)
│   ├── index.html                   # HTML shell — React mounts into <div id="root">
│   ├── vite.config.js               # Vite dev server config, proxy rules
│   ├── package.json                 # Frontend dependencies and npm scripts
│   └── src/
│       ├── main.jsx                 # App entry point — sets up routing and renders App
│       ├── App.jsx                  # Root component — defines all page routes
│       ├── index.css                # Global styles applied to the whole app
│       ├── pages/
│       │   └── Home.jsx             # Landing page rendered at "/"
│       ├── components/              # Empty — ready for shared UI components
│       └── services/
│           └── api.js               # Centralized fetch helper for Flask API calls
│
├── backend/                         # Flask API
│   ├── run.py                       # Entry point — starts the Flask dev server
│   ├── requirements.txt             # Python package dependencies
│   ├── .env                         # Local environment variables (gitignored)
│   ├── .env.example                 # Template showing which env vars are needed
│   └── app/
│       ├── __init__.py              # App factory — creates and configures Flask app
│       ├── config.py                # Loads .env values into a Config class
│       ├── routes/
│       │   ├── __init__.py          # Registers all blueprints with the app
│       │   └── main.py              # General routes (e.g. /api/health)
│       └── models/
│           └── __init__.py          # Placeholder for database models
│
├── requirements/
│   └── dependencies.md              # Full table of all packages with versions
│
├── documentation/                   # Project documentation (AsciiDoc)
│
├── .gitignore                       # Ignored files (node_modules, venv, .env, etc.)
├── README.md                        # Setup and usage instructions for new devs
└── STRUCTURE.md                     # This file
```

---

## Where to Put New Code

### Frontend

| What you're building | Where it goes |
|---|---|
| A new page ( Appointments, Login) | `frontend/src/pages/` |
| A reusable UI piece (button, card, modal) | `frontend/src/components/` |
| A new API call to the Flask backend | `frontend/src/services/api.js` |
| Global styles | `frontend/src/index.css` |
| A new page route | Add a `<Route>` in `frontend/src/App.jsx` |

### Backend

| What you're building | Where it goes |
|---|---|
| A new group of API endpoints | New file in `backend/app/routes/` + register it in `routes/__init__.py` |
| A database model (table) | New file in `backend/app/models/` |
| A new environment/config variable | Add to `backend/app/config.py` and `backend/.env.example` |
| Shared business logic | New folder `backend/app/services/` (create when needed) |

---

## Conventions

- **Frontend routes** use `/kebab-case` paths (e.g. `/my-appointments`).
- **API routes** are all prefixed with `/api` (e.g. `/api/appointments`).
- **Flask blueprints** group related routes — one file per feature (e.g. `appointments.py`, `users.py`).
- **React pages** are the top-level views tied to a URL. **Components** are smaller, reusable pieces used inside pages.
- Environment variables are never hardcoded — always use `config.py` on the backend and `import.meta.env` on the frontend.

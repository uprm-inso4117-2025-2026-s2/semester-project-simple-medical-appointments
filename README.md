# Simple Medical Appointments

A web application for managing medical appointments.

**Tech stack:** React (Vite) · Flask · Python

---

## Project Structure

```
├── frontend/       # React + Vite app (port 3000)
├── backend/        # Flask API (port 5000)
├── requirements/   # Dependency documentation
└── documentation/  # Project docs
```

---

## Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.10+
- [Git](https://git-scm.com/)

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd semester-project-simple-medical-appointments-1
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Run the server
python run.py
```

The Flask API will be available at `http://localhost:5000`.
Test it: `GET http://localhost:5000/api/health`

### 3. Frontend setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The React app will be available at `http://localhost:3000`.
API requests to `/api/*` are automatically proxied to Flask.

---

## Environment Variables

The backend uses a `.env` file inside the `backend/` folder. Copy `.env.example` to get started:

```bash
cp backend/.env.example backend/.env
```

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | Flask environment |
| `FLASK_DEBUG` | `1` | Enable debug mode (set to `0` in production) |
| `SECRET_KEY` | `dev-secret-key-...` | App secret key — **change this in production** |

> `.env` is gitignored and will never be committed. Never share or commit real secret keys.

---

## Available Scripts

### Frontend

| Command | Description |
|---|---|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |

### Backend

| Command | Description |
|---|---|
| `python run.py` | Start Flask development server |

---

## Dependencies

See [requirements/dependencies.md](requirements/dependencies.md) for a full list of packages and versions.

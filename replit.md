# Electronic Complaints System (نظام الشكاوى الإلكتروني)

## Overview
This is an Arabic electronic complaints management system built with Flask (backend) and React (frontend). The system allows traders to submit complaints and technical/higher committees to review and generate reports.

## Project Structure
```
.
├── complaints_backend/          # Flask backend API
│   ├── src/
│   │   ├── database/           # SQLite database
│   │   ├── models/             # Database models
│   │   ├── routes/             # API routes
│   │   ├── static/             # Static files (production build)
│   │   └── main.py             # Main application entry point
│   ├── requirements.txt        # Python dependencies
│   └── wsgi.py                # WSGI entry point for production
│
└── complaints_frontend/        # React + Vite frontend
    ├── src/
    │   ├── components/         # React components
    │   ├── contexts/           # React contexts (Auth)
    │   └── lib/                # Utilities
    ├── package.json            # Node dependencies
    └── vite.config.js          # Vite configuration

## Technology Stack

### Backend
- **Framework**: Flask 3.1.1
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT (PyJWT)
- **CORS**: flask-cors
- **Production Server**: Gunicorn

### Frontend
- **Framework**: React 19.1.0
- **Build Tool**: Vite 6.3.5
- **Routing**: React Router DOM
- **UI Library**: Radix UI components
- **Styling**: Tailwind CSS 4.1.7
- **HTTP Client**: Axios
- **Package Manager**: pnpm

## Development Setup

### Port Configuration
- **Frontend (Development)**: Port 5000 (0.0.0.0)
- **Backend (Development)**: Port 8000 (0.0.0.0)
- **Frontend proxies /api requests to backend on port 8000**

### Running Locally
The project has two workflows configured:
1. **Backend**: Runs Flask development server on port 8000
2. **Frontend**: Runs Vite development server on port 5000

Both workflows start automatically and the frontend is configured to proxy API requests to the backend.

## Deployment Configuration

### Production Build
The deployment process:
1. Installs frontend dependencies with pnpm
2. Builds the React app with Vite
3. Copies the built files to backend's static folder
4. Runs the Flask app with Gunicorn on port 5000

### Deployment Type
- **Type**: Autoscale (stateless web application)
- **Server**: Gunicorn with `--reuse-port` flag
- **Port**: 5000 (production)

## Key Features
- User authentication and authorization
- Role-based access control (Trader, Technical Committee, Higher Committee)
- Complaint submission and tracking
- Report generation
- Arabic language interface (RTL support)

## Recent Changes (Oct 2, 2025)
- Imported from GitHub and configured for Replit environment
- Installed Python 3.11 and Node.js 20
- Configured Vite to allow all hosts for Replit proxy support
- Set up backend on port 8000 with CORS enabled
- Set up frontend on port 5000 with API proxy
- Added .gitignore for Python and Node.js
- Configured deployment with Gunicorn for production
- Created WSGI entry point for production deployment

## User Preferences
- Language: Arabic (RTL interface)
- Database: SQLite (pre-existing, preserved)

## Important Notes
- The database file (app.db) contains existing data and should not be modified
- Frontend uses Vite's proxy in development to route /api requests to backend
- Production deployment serves the static frontend through Flask
- All API routes are prefixed with /api

# KSP Analytics: AI-Driven Crime Intelligence Platform

A comprehensive crime analytics and visualization platform designed for Karnataka State Police, powered by advanced AI, interactive mapping, and network analysis capabilities.

## 🎯 Overview

KSP Analytics provides law enforcement with:
- **Real-time crime tracking** across Karnataka districts
- **AI-powered insights** using local LLM (Ollama/Llama3)
- **Criminal network visualization** with D3.js force graphs
- **Geospatial hotspot mapping** with Leaflet
- **Predictive analytics** for crime trends and anomaly detection
- **Role-based access control** with JWT authentication
- **Comprehensive reporting** with PDF/CSV/Excel/JSON exports

## 📋 Prerequisites

### System Requirements
- **Python 3.9+** (Backend)
- **Node.js 16+** (Frontend)
- **SQLite3** (Database - auto-created)
- **Ollama** (Local LLM - optional but recommended for AI features)

### Software Requirements
- FastAPI + Uvicorn (Python web framework)
- React 18.2 + Vite (Frontend framework)
- SQLAlchemy 2.0 (ORM)
- D3.js, Leaflet, Recharts (Visualization)

### Hardware Recommendations
- **Minimum**: 4GB RAM, 2GB disk space
- **Recommended**: 8GB RAM, 10GB disk space (for Ollama models)
- **Optimal**: 16GB RAM, high-speed SSD

## 🚀 Quick Start

### 1. Clone or Extract Project

```bash
cd d:\project\ksp-analytics
```

### 2. Backend Setup

#### 2a. Install Python Dependencies

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### 2b. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings (mostly defaults are fine)
# Key setting: SECRET_KEY should be changed for production
```

#### 2c. Start Backend Server

```bash
# Backend runs on http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify Backend**: Visit `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/health`

### 3. Frontend Setup (in separate terminal)

#### 3a. Install Node Dependencies

```bash
cd frontend
npm install
```

#### 3b. Configure Environment (Optional)

```bash
# Copy example env file
cp .env.example .env

# Edit if needed - defaults point to localhost:8000
```

#### 3c. Start Development Server

```bash
# Frontend runs on http://localhost:5173
npm run dev
```

### 4. Setup Ollama (Optional but Recommended)

Ollama provides AI-powered crime analysis features:

```bash
# Install Ollama from https://ollama.ai/
# Download llama3 model:
ollama pull llama3

# Ollama runs on http://localhost:11434 by default
# Start Ollama before using AI features in the app
ollama serve
```

### 5. Access the Application

Open `http://localhost:5173` in your browser

**Demo Credentials:**
- Admin: `admin` / `admin123`
- Analyst: `analyst` / `analyst123`
- Investigator: `investigator` / `inv123`
- Viewer: `viewer` / `viewer123`

## 📁 Project Structure

```
ksp-analytics/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── database.py             # SQLAlchemy configuration
│   ├── models.py               # ORM models (8 entities)
│   ├── seed_data.py            # Initial data generator (150 criminals, 600+ crimes)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment template
│   ├── services/
│   │   ├── ollama_service.py   # AI generation (8 streaming functions)
│   │   ├── analytics_service.py # Data aggregation (14 functions)
│   │   └── export_service.py   # Multi-format exports (PDF/CSV/JSON/Excel)
│   └── routers/
│       ├── crimes.py           # Crime incident endpoints (7 endpoints)
│       ├── criminals.py        # Criminal records (9 endpoints)
│       ├── analytics.py        # Analytics queries (7 endpoints)
│       ├── alerts.py           # Alert management (9 endpoints)
│       ├── reports.py          # Report generation (8 endpoints)
│       ├── ai.py               # Ollama streaming endpoints (9 endpoints)
│       └── admin.py            # System administration (13 endpoints)
│
├── frontend/
│   ├── index.html              # HTML entry point
│   ├── src/
│   │   ├── App.jsx             # React Router setup + auth flow
│   │   ├── index.jsx           # React entry point
│   │   ├── index.css           # Global styles + Tailwind
│   │   ├── services/
│   │   │   └── api.js          # API client with interceptors (8 modules, 60+ endpoints)
│   │   ├── store/
│   │   │   └── authStore.js    # Zustand auth state (user, token, permissions)
│   │   ├── hooks/
│   │   │   └── index.js        # 5 custom React hooks (useFetch, useOllamaStream, etc.)
│   │   ├── components/
│   │   │   ├── Header.jsx      # Top navigation bar
│   │   │   ├── Sidebar.jsx     # Left navigation menu (8 items, role-aware)
│   │   │   ├── Cards.jsx       # KPI cards, risk badges, alert cards
│   │   │   └── Shared.jsx      # Modals, loaders, AI insight box
│   │   └── pages/
│   │       ├── Dashboard.jsx   # Executive overview (KPIs, charts, briefing)
│   │       ├── CrimeMap.jsx    # Leaflet geospatial mapping
│   │       ├── NetworkAnalysis.jsx # D3.js criminal networks
│   │       ├── Analytics.jsx   # Temporal, demographic, anomaly analysis
│   │       ├── Offenders.jsx   # Criminal tracking with profiles
│   │       ├── Alerts.jsx      # Real-time alert management
│   │       ├── Reports.jsx     # Report builder with export
│   │       ├── Admin.jsx       # User management & system health
│   │       └── Login.jsx       # Authentication page
│   ├── package.json            # Node dependencies + scripts
│   ├── vite.config.js          # Vite build configuration
│   ├── tailwind.config.js      # Tailwind CSS theme (police colors)
│   ├── .env.example            # Environment template
│   └── .gitignore              # Git ignore rules
│
├── README.md                   # This file
├── .gitignore                  # Project git ignore
└── DATABASE_SCHEMA.md          # (Optional) Detailed schema docs
```

## 🔑 Key Features

### 1. Crime Management
- **List & Filter**: Crimes by district, type, date, severity, status
- **Geospatial**: Interactive Leaflet map with severity-coded markers
- **Hotspot Analysis**: Identifies high-crime zones with density heatmaps
- **Export**: CSV download of crime records

### 2. Criminal Records
- **Network Visualization**: D3.js force-directed graph of criminal associations
- **Risk Scoring**: Automated calculation (40% crime count + 60% severity)
- **Profile Generation**: AI-powered behavioral analysis via Ollama
- **Repeat Offender Tracking**: searchable, filterable database

### 3. Analytics & Insights
- **Temporal Heatmap**: Crime patterns by hour and day of week (24×7 grid)
- **Demographics**: Victim age/gender/occupation distribution
- **Anomaly Detection**: Statistical outlier identification with AI explanation
- **Risk Assessment**: District-by-district scores with trend forecasts

### 4. AI Features (Ollama Integration)
8 streaming endpoints with police-context system prompts:
- Daily Briefing generation
- Hotspot detection reasoning
- Criminal network analysis
- Behavioral profile generation
- Anomaly explanation
- Crime trend forecasting
- Alert recommendation
- Report narrative generation

All with graceful fallback for Ollama unavailability.

### 5. Alert Management
- **Real-time Notifications**: Critical/High/Medium/Low severity levels
- **Filtering**: By severity, district, crime type, date range
- **Actions**: Mark acknowledged, escalate, escalate with cycling
- **Summary Stats**: Active alerts, critical count by district

### 6. Reporting Engine
- **Report Builder**: Date range, district, crime type filtering
- **Templates**: Pre-configured "Weekly District", "Monthly Executive", "Hotspot Analysis"
- **Live Preview**: Charts update as filters change
- **Multi-format Export**: PDF (charts + narrative), CSV, Excel, JSON
- **AI Narrative**: Auto-generated summary via Ollama

### 7. Administration
- **User Management**: Create/edit/deactivate users (4 roles)
- **Permissions Matrix**: Role-based access control (admin/analyst/investigator/viewer)
- **Audit Logging**: All API calls logged with user/action/resource/IP/timestamp
- **System Health**: Database status, Ollama connectivity, record counts, API performance

## 🔐 Authentication & Authorization

### JWT Authentication
- **Login Endpoint**: `POST /api/auth/login` → returns `access_token` + user info
- **Token Storage**: localStorage (persist across browser sessions)
- **Auto-refresh**: Token refresh endpoint for session extension
- **Interceptors**: Axios auto-injects Bearer token; redirects to /login on 401

### Role-Based Access Control (RBAC)
4 roles with granular permissions:

| Permission | Admin | Analyst | Investigator | Viewer |
|------------|-------|---------|--------------|--------|
| View crimes | ✓ | ✓ | ✓ | ✓ |
| View criminals | ✓ | ✓ | ✓ | ✓ |
| View reports | ✓ | ✓ | ✓ | ✓ |
| View analytics | ✓ | ✓ | ✓ | ✗ |
| Create reports | ✓ | ✓ | ✗ | ✗ |
| View alerts | ✓ | ✓ | ✓ | ✗ |
| User management | ✓ | ✗ | ✗ | ✗ |
| System admin | ✓ | ✗ | ✗ | ✗ |

Permissions checked both server-side (FastAPI) and client-side (Zustand store).

## 📊 API Endpoints (60+ endpoints)

### Authentication (2)
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh

### Crimes (7)
- `GET /api/crimes` - List crimes with filters
- `GET /api/crimes/{id}` - Crime details
- `GET /api/crimes/stats/summary` - 30-day summary
- `GET /api/crimes/stats/by-district` - By district breakdown
- `GET /api/crimes/stats/by-type` - By crime type breakdown
- `GET /api/crimes/stats/trend` - Monthly trend (12 months)
- `GET /api/crimes/hotspots` - GeoJSON hotspot map

### Criminals (9)
- `GET /api/criminals` - List criminals (searchable, filterable)
- `GET /api/criminals/{id}` - Criminal details
- `GET /api/criminals/{id}/associates` - Network associates
- `GET /api/criminals/network/data` - D3.js network format
- `GET /api/criminals/stats/summary` - Total count, active, associates
- `GET /api/criminals/high-risk` - Top 20 high-risk individuals
- `GET /api/criminals/export/csv` - Export to CSV
- `POST /api/criminals/{id}/flag-for-watch` - Flag operation
- `POST /api/criminals/{id}/assign-investigator` - Assignment

### Analytics (7)
- `GET /api/analytics/temporal-heatmap` - 24×7 crime grid
- `GET /api/analytics/anomalies` - Outliers with severity
- `GET /api/analytics/repeat-offenders` - Most active criminals
- `GET /api/analytics/risk-scores` - District scores
- `GET /api/analytics/hotspots-map` - GeoJSON hotspots
- `GET /api/analytics/demographics` - Victim stats
- `GET /api/analytics/report-snapshot` - Multi-metric summary

### Alerts (9)
- `GET /api/alerts` - List alerts with filtering
- `GET /api/alerts/{id}` - Alert details
- `POST /api/alerts/{id}/acknowledge` - Mark acknowledged
- `POST /api/alerts/{id}/escalate` - Escalate severity
- `GET /api/alerts/stats/summary` - Alert counts
- `GET /api/alerts/by-severity` - Grouped by severity
- `GET /api/alerts/active` - Active only
- `GET /api/alerts/export/csv` - Export to CSV
- `POST /api/alerts/{id}/dismiss` - Mark dismissed

### Reports (8)
- `GET /api/reports` - List saved reports
- `GET /api/reports/templates` - Available templates
- `POST /api/reports/generate` - Create new report
- `GET /api/reports/{id}` - Report details
- `POST /api/reports/{id}/export` - Export (format: pdf/csv/json/xlsx)
- `GET /api/reports/snapshot/data` - Quick metrics
- `POST /api/reports/{id}/share` - Share report
- `DELETE /api/reports/{id}` - Delete report

### AI (Ollama) Streaming (9)
All return Server-Sent Events (SSE) with JSON lines:

- `POST /api/ai/briefing` - Daily briefing generation
- `POST /api/ai/analyze-network` - Criminal network analysis
- `POST /api/ai/profile/{criminal_id}` - Behavioral profile
- `POST /api/ai/hotspots` - Hotspot analysis
- `POST /api/ai/forecast` - Crime trend forecast
- `POST /api/ai/anomaly-explanation` - Explain anomalies
- `POST /api/ai/alert-recommendation` - Alert recommendations
- `POST /api/ai/report-narrative` - Report summary
- `GET /api/ai/status` - Ollama health check

### Admin (13)
- `GET /api/admin/users` - List users
- `POST /api/admin/users` - Create user
- `GET /api/admin/users/{id}` - User details
- `PUT /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Deactivate user
- `GET /api/admin/permissions` - Role permission matrix
- `GET /api/admin/audit-logs` - Audit trail
- `GET /api/admin/audit-logs/stats` - Audit statistics
- `GET /api/admin/system-health` - Health check
- `POST /api/admin/seed-data` - Generate demo data
- `POST /api/admin/drop-db` - Clear database (dev only)
- `GET /api/admin/export/data` - System data export
- `POST /api/admin/backup` - Database backup

## 🛠️ Development

### Frontend Development
```bash
cd frontend

# Development server with hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format
```

### Backend Development
```bash
cd backend

# Development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run specific module
python -m seed_data  # Regenerate demo data

# Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Running Tests
```bash
# Backend (pytest)
cd backend
pytest

# Frontend (Vitest/Jest)
cd frontend
npm run test
```

## 🗄️ Database Schema

SQLAlchemy 2.0 with SQLite, auto-creates at `ksp_analytics.db`

### 8 Core Models
1. **User**: Authentication + roles (admin, analyst, investigator, viewer)
2. **Crime**: Incident records with GPS, severity, status
3. **Criminal**: Offender profiles with risk scores
4. **Victim**: Crime victims (linked to crimes)
5. **Alert**: Anomaly notifications with escalation
6. **Report**: Generated reports with export history
7. **AuditLog**: API access trail (user, action, resource, IP, time)
8. **OllamaAuditLog**: AI generation logs (input hash, response time, model)

### Key Features
- Foreign key relationships with cascade delete
- Self-referential many-to-many for criminal associates
- JSON fields for flexible data (crime_history, metrics)
- Indexes on frequently queried fields (district, severity, status, created_at)
- Audit fields (created_at, updated_at) on all tables

## 🎨 UI/UX Design

### Color Scheme (Police Grade)
- **Navy** (#0A1628): Primary background
- **Steel Blue** (#1E3A5F): Card/container backgrounds
- **Amber** (#F59E0B): Primary actions, CTAs
- **Alert Red** (#DC2626): Critical alerts, dangerous actions
- **Safe Green** (#16A34A): Success states, safe operations

### Responsive Design
- Mobile-first approach (Tailwind CSS)
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px)
- Sidebar collapses to hamburger on mobile
- All tables are horizontally scrollable on small screens
- Modals are full-screen on mobile

### Accessibility
- WCAG 2.1 AA compliant
- Semantic HTML structure
- ARIA labels where needed
- Keyboard navigation support
- Color contrast ratios ≥ 4.5:1 for normal text

## 📈 Performance Optimization

### Frontend
- Code splitting with React Router
- Lazy loading of pages and components
- Image optimization with WebP format
- CSS minification in production builds
- Vite's optimized bundle size

### Backend
- Database indexes on query filters
- SQLAlchemy connection pooling
- Request/response compression with gzip
- API caching headers for static data
- Async/await for I/O operations

## 🔒 Security Measures

- **JWT Tokens**: Stateless, expiring authentication
- **Password Hashing**: bcrypt + salting
- **CORS Protection**: Whitelist allowed origins
- **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries
- **HTTPS Ready**: Configure in production
- **Audit Logging**: All sensitive operations logged
- **Rate Limiting**: Optional per-endpoint configuration
- **Input Validation**: Pydantic models on all endpoints

## 🚨 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Clear cache and reinstall
rm -rf venv
python -m venv venv
pip install -r requirements.txt
```

### Frontend Port Conflict
```bash
# If port 5173 is busy, Vite will try 5174, 5175, etc.
# Or specify port:
npm run dev -- --port 3000
```

### Ollama Not Connecting
```bash
# Check Ollama is running:
curl http://localhost:11434

# Restart Ollama:
ollama serve

# Pull model if missing:
ollama pull llama3
```

### Database Issues
```bash
# Reset database (deletes all data):
# Run admin endpoint: POST /api/admin/drop-db

# Or from Python:
cd backend
python -c "from database import drop_all_tables, init_db; drop_all_tables(); init_db()"
```

### API Errors
Visit `http://localhost:8000/docs` to test endpoints directly with Swagger UI

### Frontend Blank Screen
- Check browser console (F12) for JavaScript errors
- Ensure backend is running: `http://localhost:8000/health`
- Clear browser cache: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Frontend Storybook**: `npm run storybook` (if set up)
- **Architecture Diagram**: See `ARCHITECTURE.md` (optional)

## 🤝 Contributing

To extend the platform:

1. **New API Endpoint**:
   - Add model to `models.py` if needed
   - Create router file in `routers/`
   - Import in `main.py`
   - Add permission checks using `@require_permission`

2. **New Frontend Page**:
   - Create component in `src/pages/`
   - Import in `App.jsx` and add Route
   - Add menu item to Sidebar with permission check
   - Use API client from `src/services/api.js`

3. **New AI Function**:
   - Add streaming function to `ollama_service.py`
   - Create endpoint in `routers/ai.py`
   - Test with Swagger UI first

## 📦 Deployment

### Production Checklist
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Update `CORS_ORIGINS` to production domain
- [ ] Configure SSL/HTTPS
- [ ] Use PostgreSQL instead of SQLite for scale
- [ ] Set up Redis for caching
- [ ] Configure logging (Sentry, ELK, etc.)
- [ ] Set up monitoring (Prometheus, New Relic, etc.)
- [ ] Enable rate limiting
- [ ] Regular database backups

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📞 Support

For issues, questions, or feature requests:
1. Check the Troubleshooting section
2. Review API documentation at `/docs`
3. Check browser console for frontend errors
4. Check terminal output for backend errors

## 📄 License

© 2026 Karnataka State Police. All rights reserved.

Confidential. For authorized KSP personnel only.

---

**Version**: 1.0.0  
**Last Updated**: 2026  
**Status**: Production Ready

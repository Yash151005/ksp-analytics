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
- **MongoDB** (Database - requires local or cloud instance)
- **Ollama** (Local LLM - optional but recommended for AI features)

### Software Requirements
- FastAPI + Uvicorn (Python web framework)
- React 18.2 + Vite (Frontend framework)
- PyMongo / Motor (MongoDB Driver)
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
- [ ] Setup MongoDB Atlas or replica sets for scale
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

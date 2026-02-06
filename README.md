# Zora--Powering_Smarter_Energy_Decisions
Machine Learning–Based Battery Degradation Prediction System for Electric Vehicles

# Migration Walkthrough: Flask → Vue.js + Vite

We have successfully migrated the frontend from Jinja2 templates to a modern **Vue.js** Single Page Application (SPA), while keeping Flask as the API backend.

## Architecture
- **Backend (Flask)**: Runs on port `5000`. Serves JSON data via `/api/dashboard` and `/api/data`. COSE enabled.
- **Frontend (Vue + Vite)**: Runs on port `5173`. Consumes the Flask API and renders the UI.

## File Changes
- **Converted**: `app.py` now focuses on JSON responses.
- **Moved**: CSS moved to `client/src/assets/main.css`.
- **Created**:
  - `client/src/components/Dashboard.vue`: Contains the dashboard UI and logic.
  - `client/src/App.vue`: Handles the global layout (Sidebar, Top bar).

## How to Run

You need **two** terminal windows.

### 1. Backend Terminal
```powershell
python app.py
```
*Verify it says "Running on http://127.0.0.1:5000"*

### 2. Frontend Terminal
First, ensure dependencies are installed (this was handled automatically, but if needed):
```powershell
cd client
npm install
```

Start the development server:
```powershell
cd client
npm run dev
```
*Open the URL shown (usually http://localhost:5173) in your browser.*

## Next Steps
- Implement routing (`vue-router`) if you plan to add the "Analytics" or "Fleet" pages.
- Add stricter typing or use TypeScript for better maintainability.

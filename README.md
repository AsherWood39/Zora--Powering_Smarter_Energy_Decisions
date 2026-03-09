# Zora — Powering Smarter Energy Decisions
Machine Learning–Based Battery Degradation Prediction System for Electric Vehicles

## Architecture

This is a monorepo with two separate parts:

- **`backend/`** — Flask API server (Python). Serves JSON data on port `5000`.
- **`client/`** — Vue.js + Vite frontend (JavaScript). Consumes the Flask API on port `5173`.

## Project Structure

```
Zora--Powering_Smarter_Energy_Decisions/
├── backend/
│   ├── app.py              ← Flask API entry point
│   ├── mock_data.py        ← Data generation / model logic
│   ├── requirements.txt    ← Python dependencies
│   ├── templates/          ← Jinja2 HTML templates (legacy)
│   ├── static/             ← Static assets served by Flask (legacy)
│   └── dataset/            ← Raw / cleaned dataset files
├── client/
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   └── assets/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── README.md
└── .gitignore
```

## How to Run

You need **two** terminal windows.

### 1. Backend

```powershell
cd backend
pip install -r requirements.txt
python app.py
```

*Verify it says "Running on http://127.0.0.1:5000"*

API endpoints:
- `GET /api/dashboard` — battery stats & recommendations
- `GET /api/data` — chart payload

### 2. Frontend

```powershell
cd client
npm install   # first time only
npm run dev
```

*Open the URL shown (usually http://localhost:5173) in your browser.*

## Next Steps
- Implement routing (`vue-router`) for Analytics / Fleet pages.
- Replace `mock_data.py` with a real ML model once training is complete.
- Add TypeScript for better maintainability.

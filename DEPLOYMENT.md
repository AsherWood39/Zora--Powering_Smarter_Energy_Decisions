# Zora Deployment Guide 🚀

The project is now fully verified locally and ready for production deployment. Since the deployment configurations (`render.yaml` for Render and `vercel.json` for Vercel) are already in place, the process is streamlined.

## 1. Backend Deployment (Render)

Render will host your Flask API.

### Steps:
1. **GitHub Connection**: Go to [Render Dashboard](https://dashboard.render.com/) and create a **New » Blueprint**.
2. **Select Repository**: Pick your `Zora--Powering_Smarter_Energy_Decisions` repo.
3. **Configuration**: Render will automatically detect the `render.yaml` file.
4. **Environment Variables**:
   - In the Render dashboard for your `zora-backend` service, go to **Environment**.
   - Add `GROQ_API_KEY`: `YOUR_GROQ_API_KEY_HERE` (Copy from your local .env).
   - Add `PYTHON_VERSION`: `3.11.0`.
5. **Deploy**: Click **Apply**. 

> [!NOTE]
> The `render.yaml` is configured to look in the `/backend` directory and run `gunicorn app:app`.

---

## 2. Frontend Deployment (Vercel)

Vercel will build and host your Vue.js dashboard as a Single Page Application (SPA).

### Steps:
1. **GitHub Connection**: Go to [Vercel Dashboard](https://vercel.com/new) and import your repository.
2. **Framework Preset**: Vercel should auto-detect **Vite**.
3. **Build Settings**:
   - Vercel will follow `vercel.json` instructions:
     - **Build Command**: `cd client && npm install && npm run build`
     - **Output Directory**: `client/dist`
4. **Environment Variables**:
   - Add `VITE_API_URL`: Set this to your **Render Backend URL** (e.g., `https://zora-backend.onrender.com`).
5. **Deploy**: Click **Deploy**.

---

## 3. Verification Checklist

- [ ] **API Connectivity**: Open the Vercel URL and check if the dashboard loads data (it might take a minute for Render to wake up on the free plan).
- [ ] **AI Recommendations**: Ensure the "Deep-Dive" view shows recommendations (verifies Groq integration).
- [ ] **PDF Export**: Test the "Export Report" button to ensure `matplotlib` is rendering correctly on the server.

> [!IMPORTANT]
> Because you are on a Render Free Plan, the backend will "spin down" after inactivity. The first request after a break may take 30-60 seconds to respond.

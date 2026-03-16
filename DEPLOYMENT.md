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
3. **CRITICAL: Root Directory**: 
   - In the "Build and Output Settings" during import, find the **Root Directory** setting.
   - Click **Edit** and select the **`client`** folder.
4. **Build Settings**:
   - Vercel will follow `client/vercel.json` instructions:
     - **Build Command**: `npm install && npm run build`
     - **Output Directory**: `dist`
5. **Environment Variables**:
   - Add `VITE_API_URL`: Set this to your **Render Backend URL** (e.g., `https://zora-backend.onrender.com`).
6. **Deploy**: Click **Deploy**.

---

## 3. Verification Checklist

- [ ] **API Connectivity**: Open the Vercel URL and check if the dashboard loads data (it might take a minute for Render to wake up on the free plan).
- [ ] **AI Recommendations**: Ensure the "Deep-Dive" view shows recommendations (verifies Groq integration).
- [ ] **PDF Export**: Test the "Export Report" button to ensure `matplotlib` is rendering correctly on the server.

---

## 🛠️ Troubleshooting: No Data Loading

If the dashboard loads but "Fleet Triage" or "Analytics" is empty:

1. **Verify Backend Health**: 
   - Open your Render URL in a browser (e.g., `https://zora-backend.onrender.com`).
   - You should see: `{"status": "online", "service": "Zora Energy Intelligence API"}`.
   - If not, check your **Render Logs** for errors.

2. **Check Vercel Environment Variables**:
   - Go to **Vercel Dashboard -> Settings -> Environment Variables**.
   - Ensure `VITE_API_URL` is set to your **Render URL** (with NO trailing slash).
   - If you just added it, you MUST **Redeploy** (Deployments -> Redploy) for it to take effect.

3. **Check Browser Console**:
   - Press `F12` in your browser and go to the **Network** tab.
   - Look for red failed requests (e.g., `/api/fleet/triage`).
   - If the request URL starts with `https://...vercel.app/api/`, it means **`VITE_API_URL` is missing** in Vercel.

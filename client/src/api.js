// src/api.js
// Dynamic API base URL — uses env var in production, local proxy in dev
const BASE = import.meta.env.VITE_API_URL || '';

export default {
  dashboard:  `${BASE}/api/dashboard`,
  chartData:  `${BASE}/api/data`,
  fleetTriage:`${BASE}/api/fleet/triage`,
  analytics:  `${BASE}/api/analytics/summary`,
  battery:    (id) => `${BASE}/api/battery/${id}/health`,
  simulate:   (id) => `${BASE}/api/battery/${id}/simulate`,
  report:     (id) => `${BASE}/api/export/report?battery_id=${id}`,
};

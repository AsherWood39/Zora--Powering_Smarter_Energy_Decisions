# 📓 Zora — Project Notes
> Shared team log. Both members add findings here daily.
> Format: `[Date] [Member] — Note`

---

## 🗂️ Current API Structure (Understood by Person B)

### Existing Routes in `app.py`
| Route | Method | Returns |
|---|---|---|
| `/api/dashboard` | GET | `{ stats: {...}, recommendations: [...] }` |
| `/api/data` | GET | `{ labels: [...], datasets: [{...}, {...}] }` |

### New Routes to Build (Day 2 — Person B stubs these)
| Route | Method | Returns (agreed shape) |
|---|---|---|
| `/api/battery/<battery_id>/health` | GET | `{ battery_id, soh, rul, regime }` |
| `/api/fleet/triage` | GET | `[ { battery_id, soh, rul, regime, status_color }, ... ]` |
| `/api/battery/<battery_id>/simulate?temp=X` | GET | `{ battery_id, temperature, adjusted_rul }` |

---

## 🤝 Data Contracts (Agreed with Person A)

> Fill this in after your Day 1 sync with Person A!

### What format will `regime` be?
- [ ] String: `"Normal"` / `"Accelerated"` / `"Anomalous"`
- [ ] Number: `0` / `1` / `2`
- **Agreed**: _______________

### What is the `rated_capacity` value used for SoH calculation?
- **Agreed**: _______________ Ahr

### What battery IDs are in the dataset?
- Room temp batteries: B0005, B0006, B0007, B0018
- Cold temp batteries: B0045–B0048
- **Total batteries Person B needs to display in Fleet Triage**: ___

### Features Person A will put in `ml/features.csv`
| Column | Type | Description |
|---|---|---|
| `battery_id` | string | e.g., "B0005" |
| `cycle_number` | int | cycle index |
| `capacity` | float | measured Ahr |
| `SoH` | float | 0–100 % |
| `RUL` | int | cycles remaining |
| `regime` | string/int | health regime label |
| `ambient_temperature` | float | °C |

---

## 🎨 Dashboard Wireframe (Person B)

### Screen 1 — Fleet Triage Panel
```
┌──────────────────────────────────────────┐
│  Fleet Overview — All Batteries          │
│                                          │
│  🔴 B0018  SoH: 68%   RUL: 12 cycles    │
│  🟡 B0005  SoH: 79%   RUL: 34 cycles    │
│  🟢 B0006  SoH: 91%   RUL: 67 cycles    │
│  🟢 B0007  SoH: 94%   RUL: 80 cycles    │
│  ...                                     │
│                                          │
│  🔴 = SoH < 75%  🟡 = 75–85%  🟢 = >85% │
└──────────────────────────────────────────┘
```

### Screen 2 — Individual Battery Deep Dive
```
┌──────────────────────────────────────────┐
│  Battery B0005 — Deep Dive               │
│  [SoH Curve — line chart]                │
│                                          │
│  Regime Timeline:                        │
│  [🟢🟢🟢🟡🟡🔴] ← colored bar segments  │
│                                          │
│  RUL: 34 cycles / ~2.8 months remaining  │
│                                          │
│  ── Temperature Scenario ──              │
│  -10°C [──────●──────────] 45°C          │
│  At current setting: RUL = 34 cycles     │
└──────────────────────────────────────────┘
```

---

## 🐛 Bugs & Blockers

| Date | Member | Issue | Status |
|---|---|---|---|
| 2026-03-10 | Person B | Flask `ModuleNotFoundError` — fixed by using `venv/bin/python app.py` | ✅ Fixed |
|  |  |  |  |

---

## 💡 Interesting Findings

| Date | Member | Finding |
|---|---|---|
| 2026-03-10 | Person B | Current dashboard calls `/api/data` for chart and `/api/dashboard` for KPI cards — keep both working during refactor |
|  |  |  |

---

## ✅ Daily Sync Log

### Day 1 — 2026-03-10
**Person A completed:**
- [ ] _Fill after sync_

**Person B completed:**
- [x] Mapped existing `app.py` and `mock_data.py`
- [x] Understood `App.vue` and `Dashboard.vue`
- [x] Sketched wireframe for Fleet Triage + Individual Battery + Temp Slider
- [x] Fixed Flask environment issue (venv setup)
- [ ] Agreed data contracts with Person A

**Blockers / Questions for tomorrow:**
- _Write here_

---

## 🚀 How to Run the Project

```bash
# Backend (always use venv!)
cd backend
source venv/bin/activate     # activate once per terminal
python app.py                # runs on http://127.0.0.1:5000

# Frontend (separate terminal)
cd client
npm run dev                  # runs on http://localhost:5173
```

> Open **http://localhost:5173** to see the dashboard.

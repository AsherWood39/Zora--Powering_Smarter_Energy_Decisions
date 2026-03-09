# Zora — 5-Day Execution Plan
## 2-Person Team Roadmap | Deadline: Day 5

> **Core principle**: Person A owns the *intelligence* (data + ML). Person B owns the *interface* (API + dashboard). Both lanes run in parallel from Day 2 onwards, merging on Day 4.

---

## Team Role Split

| | **Person A — "The Data Scientist"** | **Person B — "The Engineer"** |
|---|---|---|
| **Primary focus** | Dataset, feature engineering, ML models | Flask API, Vue.js dashboard, integration |
| **Key output** | Trained models + validation results | Live, beautiful dashboard consuming real model data |
| **Languages** | Python (pandas, scikit-learn, XGBoost) | Python (Flask) + JavaScript (Vue.js) |
| **Overlaps with other person on** | Day 1 (setup), Day 3 (regime labels), Day 4 (integration) | Day 1 (setup), Day 4 (integration), Day 5 (demo) |

---

## Day 1 — Foundation & Exploration
**Theme: Understand the battlefield. Both people do this together.**

### ✅ Both (Together, ~3 hrs)
- [ ] Set up shared Python environment: `pip install pandas numpy matplotlib scikit-learn xgboost`
- [ ] Run the assignment from Lesson 1: Load `metadata.csv`, filter for `discharge`, plot B0005 degradation curve
- [ ] Discuss what you see in the plot — where does it start, where does it end, is it linear?
- [ ] Read through the `extra_infos/` README files together to understand battery groups and conditions

### 🔵 Person A — Data Exploration
- [ ] Write a script to print: total cycle count per battery, min/max capacity per battery, number of NaN values per column
- [ ] Answer: Which battery degrades fastest? Which slowest? Which has the most cycles?

### 🟠 Person B — Project Architecture
- [ ] Map out the current `app.py` and `mock_data.py` — understand what the Flask API currently serves
- [ ] Explore the `client/` Vue.js folder. Understand `Dashboard.vue` and `App.vue`
- [ ] Draw (on paper or Figma) what the new dashboard should look like: Fleet Triage panel, individual battery view, temperature slider

**End of Day 1 checkpoint**: Both people can independently load the data and have a shared understanding of the project structure.

---

## Day 2 — Feature Engineering (A) | API Scaffolding (B)
**Theme: Build your lanes in parallel.**

### 🔵 Person A — Feature Engineering
- [ ] Create `ml/feature_engineering.py`
- [ ] **Step 1**: From `metadata.csv`, extract per-cycle tabular features for every discharge cycle:
  - `battery_id`, `cycle_number`, `capacity`, `ambient_temperature`, `Re`, `Rct`
- [ ] **Step 2**: From the raw `data/` CSVs, extract these features for each discharge cycle:
  - `ohmic_drop` — voltage at t=0 minus voltage at t=1s
  - `avg_discharge_temp` — mean temperature during the discharge
  - `discharge_duration` — total time of the cycle in seconds
- [ ] **Step 3**: Calculate `SoH` and label it (capacity / rated_capacity * 100)
- [ ] **Step 4**: Calculate `RUL` label — cycles remaining until capacity < 1.4 Ahr
- [ ] Save the final combined DataFrame as `ml/features.csv`

### 🟠 Person B — API Scaffolding
- [ ] Create new Flask routes (stub them out with placeholder data for now):
  - `GET /api/battery/<battery_id>/health` — returns SoH + RUL + regime
  - `GET /api/fleet/triage` — returns all batteries ranked by urgency
  - `GET /api/battery/<battery_id>/simulate?temp=4` — temperature-adjusted RUL
- [ ] Update `Dashboard.vue` to call these new endpoints instead of `/api/data`
- [ ] Add a **Fleet Triage Panel** component (list of batteries with color-coded status: 🟢/🟡/🔴)

**End of Day 2 checkpoint**: Person A has `features.csv` with clean, engineered features. Person B has live (stubbed) API routes the dashboard can call.

---

## Day 3 — Model Training (A) | Dashboard UI (B)
**Theme: Build the core intelligence and the core visual.**

### 🔵 Person A — Model Training
- [ ] Create `ml/train_models.py`
- [ ] **Model 1 — SoH Regressor**: `XGBoostRegressor` on features → target: `SoH`
  - Split: Train on B0005+B0006+B0007, test on B0018 (LOBO validation)
  - Print R² and MAE
- [ ] **Model 2 — RUL Regressor**: `XGBoostRegressor` on features → target: `RUL`
  - Same LOBO split. Print R² and MAE.
- [ ] **Model 3 — Regime Classifier**: Create labels (Normal / Accelerated / Anomalous) using a rolling average rule, then train a `RandomForestClassifier`
- [ ] **Cross-temperature test**: Train on all room-temp batteries, test on 4°C batteries (B0045–B0048). Record R² — this is your headline result.
- [ ] Save trained models using `joblib`: `soh_model.pkl`, `rul_model.pkl`, `regime_model.pkl`

### 🟠 Person B — Dashboard Polish
- [ ] Build the **Individual Battery Deep Dive** view:
  - Real-time SoH curve (powered by stub data for now)
  - Regime timeline bar under the chart (🟢🟡🔴 colored segments)
  - RUL displayed as "X cycles / ~Y months remaining"
- [ ] Build the **Temperature Scenario Slider** UI: a slider from -10°C to 45°C that updates the displayed RUL estimate
- [ ] Add loading/skeleton states so the UI looks polished even with slow API responses

**End of Day 3 checkpoint**: Person A has 3 trained models with quantified scores. Person B has a beautiful dashboard ready to receive real data.

---

## Day 4 — Integration Day 🔗
**Theme: Connect the two lanes. This is the most critical day.**

### ✅ Both (Together, full day)

**Morning: Wire models into the API**
- [ ] Update `app.py` to load `soh_model.pkl`, `rul_model.pkl`, `regime_model.pkl` on startup
- [ ] `/api/battery/<id>/health` — load battery's features from `features.csv`, run predictions, return real values
- [ ] `/api/fleet/triage` — loop all batteries, get predictions, sort by urgency (lowest SoH first)
- [ ] `/api/battery/<id>/simulate?temp=X` — adjust the `thermal_factor` feature and re-run the RUL model

**Afternoon: End-to-End Testing**
- [ ] Load the full dashboard in the browser — confirm every chart shows real data, not mocks
- [ ] Run the LOBO experiment results and add them to a "Model Performance" section in the dashboard
- [ ] Fix any bugs from integration (expect 2-3 small issues — this is normal)

**End of Day 4 checkpoint**: Fully working end-to-end product. Real models, real data, live dashboard.

---

## Day 5 — Polish, Documentation & Demo Prep
**Theme: Make it undeniable.**

### 🔵 Person A — Results & Science Story
- [ ] Create a `results/` folder with comparison charts:
  - Within-battery accuracy (B0005) vs. cross-battery accuracy (trained on others, tested on B0005)
  - Room-temp vs. cold-temp generalization R² comparison
- [ ] Write a 1-page `model_card.md` that explains: features used, model type, validation approach, key results
- [ ] Prepare the "killer stat" for judges: *"Our model achieves R²=X.XX on a battery it has NEVER seen, operating at 4°C with training data from 24°C"*

### 🟠 Person B — UI Polish & Demo Script
- [ ] Final visual pass on the dashboard — consistency, colors, fonts, spacing
- [ ] Add an "About This Model" info panel in the UI linking to the model card
- [ ] Prepare a 2-minute live demo script:
  1. Show the Fleet Triage view — *"Here are 12 batteries ranked by urgency"*
  2. Click on a degraded battery — *"This battery has SoH 71%, 34 cycles to EOL"*
  3. Drag the temperature slider to 4°C — *"In winter conditions, that drops to just 22 cycles"*
  4. Call out the science — *"Every number here comes from a model validated on batteries it has never seen"*

### ✅ Both (Final 2 hrs)
- [ ] Rehearse the demo together twice
- [ ] Update `README.md` with the three-pillar breakthrough story, tech stack, and how to run locally
- [ ] Final commit and push

---

## At-a-Glance Timeline

```
         Person A (Data/ML)              Person B (Backend/Frontend)
Day 1  │ Explore data + plot            │ Understand app structure + wireframe
Day 2  │ Feature engineering → features.csv │ API scaffolding + Fleet Triage UI
Day 3  │ Train 3 models → .pkl files    │ Dashboard polish + Temp slider UI
Day 4  │ ◄──────── INTEGRATION DAY (Together) ──────────►
Day 5  │ Results charts + model card    │ UI polish + demo script
```

---

## Shared Rules for the 5 Days

1. **Daily 15-min sync**: Every morning, share what you completed yesterday and what you're building today.
2. **One shared notebook**: Keep a `notes.md` in the repo. Any finding (a bug, a surprising result, a cool stat) goes in there. This becomes your competition narrative.
3. **Commit often**: Both people commit to the same repo daily. Use branches: `feature/ml-pipeline` for Person A, `feature/dashboard-v2` for Person B.
4. **Fail fast on Day 2**: If the feature engineering or the API scaffolding is blocked, raise it at the Day 2 checkpoint — not Day 4.

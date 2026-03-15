import os
import json
import io
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import pickle
import matplotlib.pyplot as plt
from fpdf import FPDF

# --- REAL ML INTEGRATION ---
# Use absolute paths that work in both local development and Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_RESULTS_DIR = os.path.join(BASE_DIR, "ml", "results")

FEATS_PATH = os.path.join(ML_RESULTS_DIR, "final_features.csv")
TRIAGE_RULES_PATH = os.path.join(ML_RESULTS_DIR, "fleet_triage_rules.json")
SOH_MODEL_PATH = os.path.join(ML_RESULTS_DIR, "soh_model_bundle.pkl")
RUL_MODEL_PATH = os.path.join(ML_RESULTS_DIR, "rul_model_bundle.pkl")

class ZoraPredictor:
    def __init__(self):
        self.soh_bundle = None
        self.rul_bundle = None
        self.triage_rules = None
        
        if os.path.exists(SOH_MODEL_PATH):
            with open(SOH_MODEL_PATH, 'rb') as f:
                self.soh_bundle = pickle.load(f)
        if os.path.exists(RUL_MODEL_PATH):
            with open(RUL_MODEL_PATH, 'rb') as f:
                self.rul_bundle = pickle.load(f)
        if os.path.exists(TRIAGE_RULES_PATH):
            with open(TRIAGE_RULES_PATH, 'r') as f:
                self.triage_rules = json.load(f)

    def _apply_bundle(self, bundle, features_dict, is_rul=False):
        if not bundle:
            return None
            
        group_id = features_dict.get('meta_group_id', 0)
        cycle = features_dict.get('cycle_number', 1)
        
        group_baselines = bundle.get('group_baselines', {})
        if group_id in group_baselines:
            poly_coeff = group_baselines[group_id]
            poly_func = np.poly1d(poly_coeff)
            baseline_pred = poly_func(cycle)
        else:
            poly_func = np.poly1d(bundle['global_baseline'])
            baseline_pred = poly_func(cycle)
            
        feature_cols = bundle['features']
        x_input = pd.DataFrame([{col: features_dict.get(col, 0) for col in feature_cols}])
        residual_pred = bundle['ml_model'].predict(x_input)[0]
        
        final_pred = baseline_pred + residual_pred
        
        if is_rul:
            return max(0.0, float(final_pred))
        else:
            return max(0.0, min(100.0, float(final_pred)))

    def predict(self, features_dict):
        # Initialize result structure
        response = {
            "status": "success",
            "predictions": {}
        }
        
        predictions = {} # Dict for results
        
        # Stage 1: Triage
        cap = features_dict.get('Capacity', 2.0)
        rated = features_dict.get('meta_rated_cap', 2.0)
        soh_raw = (cap / rated) * 100
        
        triage_stage = "healthy"
        if soh_raw < 60: 
            triage_stage = "eol"
        elif soh_raw < 75:
            triage_stage = "aging"

        # Stage 2: Model Selection & Prediction
        soh_pred = self._apply_bundle(self.soh_bundle, features_dict, is_rul=False)
        soh_std = self.soh_bundle.get('model_std', 1.5) if (self.soh_bundle and 'model_std' in self.soh_bundle) else 1.5
        
        if soh_pred is not None:
            predictions["soh"] = {
                "value_percent": round(soh_pred, 2),
                "confidence_interval": [max(0, round(soh_pred - 2*soh_std, 2)), min(100, round(soh_pred + 2*soh_std, 2))]
            }
            
        # RUL Logic
        rul_std = self.rul_bundle.get('model_std', 5.0) if (self.rul_bundle and 'model_std' in self.rul_bundle) else 5.0
        
        if triage_stage == "eol":
            rul_pred = max(0.0, float(soh_raw - 50.0) * 0.5) 
            predictions["rul_method"] = "rule-based (stable eol)"
        else:
            rul_pred = self._apply_bundle(self.rul_bundle, features_dict, is_rul=True)
            predictions["rul_method"] = "machine-learning"

        if rul_pred is not None:
            predictions["rul"] = {
                "value_cycles": round(rul_pred, 1),
                "confidence_interval": [max(0, round(rul_pred - 2*rul_std, 1)), round(rul_pred + 2*rul_std, 1)]
            }
            
        # Degradation Regime
        regime = "Normal 🟢"
        if self.triage_rules:
            curr_fade = features_dict.get('fade_rate_last_10_cycles', 0)
            thresh = self.triage_rules.get("degradation_regime", {})
            if curr_fade < thresh.get("threshold_critical", -0.01):
                regime = "Critical 🔴"
            elif curr_fade < thresh.get("threshold_accelerated", -0.005):
                regime = "Warning 🟡"
            
            if soh_pred is not None:
                if soh_pred < 75 and "Critical" not in regime:
                    regime = "Critical 🔴"
                elif soh_pred < 86 and "Normal" in regime:
                    regime = "Warning 🟡"
        
        predictions["degradation_regime"] = regime
            
        # Stage 3: Explainable Risk Score & Action Items
        risk_level = "LOW"
        action_item = "Continue Monitoring"
        risk_reason = "Normal degradation signatures."
        
        re_val = features_dict.get('Re', 0)
        slope_5 = features_dict.get('cap_slope_5', 0)
        
        if triage_stage == "eol" or (rul_pred is not None and rul_pred < 10):
            risk_level = "CRITICAL"
            action_item = "REPLACE NOW"
            risk_reason = "Battery has reached the 'aging cliff'. Chemical breakdown imminent."
        elif re_val > 0.08:
            risk_level = "HIGH"
            action_item = "Immediate Inspection"
            risk_reason = "Severe impedance growth detected (Electrolyte decomposition)."
        elif slope_5 < -0.005:
            risk_level = "HIGH"
            action_item = "Operational Limit Required"
            risk_reason = "Accelerated capacity fade trajectory detected."
        elif (soh_pred is not None and soh_pred < 80) or (rul_pred is not None and rul_pred < 40):
            risk_level = "MEDIUM"
            action_item = "Schedule Maintenance"
            risk_reason = "Entering secondary aging phase."
            
        predictions["risk_report"] = {
            "level": risk_level,
            "action": action_item,
            "reason": risk_reason,
            "triage_stage": triage_stage
        }

        # Second Life eligibility
        if self.triage_rules:
            curr_re = features_dict.get('Re', 0)
            if soh_pred is not None and soh_pred <= 80.0:
                is_safe = curr_re < self.triage_rules.get("second_life", {}).get("re_safety_cutoff", 0.1)
                predictions["second_life_eligible"] = "Yes ✅" if is_safe else "Unsafe (High Re) ❌"
            else:
                predictions["second_life_eligible"] = "N/A (Battery still in Primary Life)"
                
        response["predictions"] = predictions
        return response

# Initialize components
_predictor = ZoraPredictor()
_cached_df = None
_valid_battery_ids = None

def _identify_valid_batteries(df):
    global _valid_battery_ids
    if df.empty:
        _valid_battery_ids = set()
        return
    research_grade_bids = {'B0005', 'B0006', 'B0018', 'B0033', 'B0034', 'B0039', 'B0040', 'B0042', 'B0043', 'B0044', 'B0046', 'B0047', 'B0048', 'B0053', 'B0054', 'B0055', 'B0056'}
    available = set(df['battery_id'].unique())
    _valid_battery_ids = research_grade_bids.intersection(available)

def _get_data():
    global _cached_df
    if _cached_df is None or _cached_df.empty:
        if os.path.exists(FEATS_PATH):
            try:
                _cached_df = pd.read_csv(FEATS_PATH)
                _identify_valid_batteries(_cached_df)
            except:
                _cached_df = pd.DataFrame()
        else:
            _cached_df = pd.DataFrame()
    return _cached_df

load_dotenv()
_groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_dashboard_stats(battery_id="B0005"):
    df = _get_data()
    if df.empty or battery_id not in df['battery_id'].unique():
        return {"health_score": 87, "health_status": "Healthy", "remaining_useful_life": "45 Cycles", "current_capacity": 1.74, "original_capacity": 2.0, "total_cycles": 100, "efficiency": 87}

    battery_df = df[df['battery_id'] == battery_id].sort_values('cycle_number')
    latest = battery_df.iloc[-1]
    pred = _predictor.predict(latest.to_dict())
    
    soh_rel = min(100.0, float(latest['capacity_rel'] * 100))
    rul = pred["predictions"].get("rul", {}).get("value_cycles")
    
    status = "healthy"
    if (rul is not None and rul == 0) or soh_rel < 60:
        status = "critical"
    elif soh_rel < 75:
        status = "warning"
        
    return {
        "battery_id": battery_id,
        "health_score": round(soh_rel, 1),
        "health_status": status.capitalize(),
        "remaining_useful_life": f"{round(rul / 14, 1)} Months" if (rul and rul > 0) else ("End of Life" if rul == 0 else "N/A"),
        "current_capacity": float(round(latest['Capacity'], 2)),
        "original_capacity": float(round(latest['meta_rated_cap'], 2)),
        "total_cycles": int(latest['cycle_number']),
        "efficiency": int(latest['capacity_rel'] * 100),
        "temperature": float(latest.get('ambient_temperature', 24.0)),
        "action_item": pred["predictions"].get("risk_report", {}).get("action", "Monitor")
    }

def get_fleet_triage():
    df = _get_data()
    if df.empty: return []
    fleet = []
    global _valid_battery_ids
    if _valid_battery_ids is None: _get_data()
    for bid in df['battery_id'].unique():
        if _valid_battery_ids and bid not in _valid_battery_ids: continue
        latest = df[df['battery_id'] == bid].sort_values('cycle_number').iloc[-1]
        pred = _predictor.predict(latest.to_dict())
        soh_rel = min(100.0, float(latest['capacity_rel'] * 100))
        rul = pred["predictions"].get("rul", {}).get("value_cycles", 0)
        status = "healthy"
        if rul == 0 or soh_rel < 60: status = "critical"
        elif soh_rel < 75: status = "warning"
        fleet.append({
            "battery_id": bid,
            "soh": round(soh_rel, 1),
            "rul": int(rul),
            "status": status,
            "total_cycles": int(latest['cycle_number']),
            "temperature": float(latest.get('ambient_temperature', 24.0)),
            "action_item": pred["predictions"].get("risk_report", {}).get("action", "Monitor")
        })
    return sorted(fleet, key=lambda x: x['soh'])

def get_fleet_analytics():
    df = _get_data()
    if df.empty: return {}
    latest = df.sort_values('cycle_number').groupby('battery_id').tail(1)
    return {
        "avg_resistance_ohm": round(latest['Re'].mean(), 4),
        "total_fleet_cycles": int(latest['cycle_number'].sum()),
        "active_batteries": len(df['battery_id'].unique())
    }

def get_most_critical_battery_id():
    fleet = get_fleet_triage()
    return fleet[0]["battery_id"] if fleet else "B0005"

def get_battery_health_details(battery_id):
    df = _get_data()
    if df.empty or battery_id not in df['battery_id'].unique(): return None
    batt_df = df[df['battery_id'] == battery_id].sort_values('cycle_number')
    latest = batt_df.iloc[-1]
    pred = _predictor.predict(latest.to_dict())
    
    soh = round(min(100.0, float(latest['capacity_rel'] * 100)), 1)
    rul = pred["predictions"].get("rul", {}).get("value_cycles", 0)
    
    # Historical Data for Charts
    chart_data = get_historical_data(battery_id)
    
    # Regime History (Legacy logic based on SoH thresholds)
    regimes = []
    labels = []
    for _, row in batt_df.tail(50).iterrows():
        s = row['capacity_rel'] * 100
        r = "Normal" if s >= 86 else ("Warning" if s >= 75 else "Critical")
        regimes.append(r)
        labels.append(int(row['cycle_number']))

    return {
        "battery_id": battery_id,
        "soh": soh,
        "rul": int(rul),
        "rul_months": round(float(rul) / 14, 1),
        "total_cycles": int(latest['cycle_number']),
        "temperature": float(latest.get('ambient_temperature', 24.0)),
        "status": "eol" if (rul == 0 or soh < 60) else ("critical" if soh < 70 else ("warning" if soh < 80 else "healthy")),
        "action": pred["predictions"].get("risk_report", {}).get("action", "Monitor"),
        "reason": pred["predictions"].get("risk_report", {}).get("reason", "Normal aging"),
        "chart_data": chart_data,
        "regime_history": regimes,
        "cycle_labels": labels,
        "recommendations": get_recommendations({"battery_id": battery_id, "soh": soh}),
        "dataset_threshold": 70.0
    }

def get_historical_data(battery_id):
    df = _get_data()
    if df.empty: return {"labels": [], "datasets": []}
    batt_df = df[df['battery_id'] == battery_id].sort_values('cycle_number').tail(50)
    labels = list(batt_df['cycle_number'])
    actual = list(batt_df['capacity_rel'] * 100)
    
    # Predicted curve (simple projection for UI)
    last_soh = actual[-1]
    slope = (actual[-1] - actual[0]) / len(actual) if len(actual) > 1 else -0.1
    predicted = [None] * len(actual)
    predicted[-1] = last_soh
    for i in range(1, 21):
        predicted.append(max(0, last_soh + slope * i))
        labels.append(labels[-1] + 1)
        actual.append(None)
        
    return {
        "labels": labels,
        "datasets": [
            {"label": "Actual", "data": actual},
            {"label": "Predicted", "data": predicted}
        ]
    }

def simulate_temperature(battery_id, temp_c, load_current=2.0, usage_intensity=1.0):
    """Scenario Simulator: Multi-factor stress adjustment."""
    df = _get_data()
    if df.empty or battery_id not in df['battery_id'].unique(): return None
    latest = df[df['battery_id'] == battery_id].sort_values('cycle_number').iloc[-1]
    pred = _predictor.predict(latest.to_dict())
    base_rul = pred["predictions"].get("rul", {}).get("value_cycles", 0)
    
    # Physics factors
    t_stress = 1.0 + (temp_c - 24) * 0.04 if temp_c > 24 else (1.0 + (24 - temp_c) * 0.01)
    l_stress = 1.0 + (load_current - 2.0) * 0.25
    total_stress = t_stress * l_stress * usage_intensity
    
    adj_rul = max(0, float(base_rul) / total_stress)
    
    # Create a predicted curve for the chart
    last_soh = latest['capacity_rel'] * 100
    slope = -0.1 * total_stress
    curve = [last_soh + slope * i for i in range(20)]
    
    return {
        "base_rul": int(base_rul),
        "adjusted_rul": int(adj_rul),
        "adjusted_rul_months": round(adj_rul / 14, 1),
        "impact_pct": round((adj_rul/base_rul - 1) * 100, 1) if base_rul > 0 else 0,
        "predicted_curve": curve
    }

def get_recommendations(battery_data=None):
    if not battery_data: return []
    try:
        prompt = f"3 tech recommendations for battery {battery_data.get('battery_id')} with SoH {battery_data.get('soh')}%."
        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return [{"id": 1, "title": "Check Thermal Management", "description": "Ensure cooling is active.", "severity": "medium"}]
    except:
        return [{"id": 1, "title": "Scheduled Inspection", "description": "Regular maintenance check.", "severity": "low"}]

def generate_pdf_report(battery_id):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Zora Report: {battery_id}", ln=True, align='C')
    return bytes(pdf.output())

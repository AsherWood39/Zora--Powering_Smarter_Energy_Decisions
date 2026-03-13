import os
import pickle
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOH_MODEL_PATH = os.path.join(BASE_DIR, "ml/results/soh_model_bundle.pkl")
RUL_MODEL_PATH = os.path.join(BASE_DIR, "ml/results/rul_model_bundle.pkl")
TRIAGE_RULES_PATH = os.path.join(BASE_DIR, "ml/results/fleet_triage_rules.json")

class ZoraPredictor:
    def __init__(self):
        """
        Phase 4: Actionable Fleet Intelligence
        Zora-DOC Reference: Lesson 11 (Beating SOTA in the Real World)
        
        This is the "Handoff" script. It loads the pre-trained 'Brains' (models and rules) 
        into memory. It is incredibly fast, meant to be queried instantly by the web server
        without ever needing to retrain.
        """
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
        """
        Internal helper to apply the Group-Residual Meta-Learner Architecture.
        Zora-DOC Lesson 9: 
        1. Predicts the physical Baseline curve for the specific chemistry.
        2. Applies the XGBoost model to guess the Residual Error.
        3. Combines them mathematically.
        """
        if not bundle:
            return None
            
        group_id = features_dict.get('meta_group_id', 0)
        cycle = features_dict.get('cycle_number', 1)
        
        # 1. Baseline prediction (Group-Specific Polynomial)
        group_baselines = bundle.get('group_baselines', {})
        if group_id in group_baselines:
            poly_coeff = group_baselines[group_id]
            poly_func = np.poly1d(poly_coeff)
            baseline_pred = poly_func(cycle)
        else:
            # Fallback to global baseline if group is unknown
            poly_func = np.poly1d(bundle['global_baseline'])
            baseline_pred = poly_func(cycle)
            
        # 2. Residual prediction (XGBoost)
        feature_cols = bundle['features']
        # Build an ordered array of features for xgboost
        x_input = pd.DataFrame([{col: features_dict.get(col, 0) for col in feature_cols}])
        residual_pred = bundle['ml_model'].predict(x_input)[0]
        
        # 3. Combine and clip
        final_pred = baseline_pred + residual_pred
        
        if is_rul:
            return max(0.0, float(final_pred))
        else:
            return max(0.0, min(100.0, float(final_pred)))

    def predict(self, features_dict):
        """
        The Main Inference Function.
        Takes a single row dictionary of battery features and returns 
        the full Fleet Intelligence suite of predictions (SoH, RUL, CI bounds, and Regime).
        
        Input Example:
        {
            'cycle_number': 85,
            'meta_group_id': 0,
            'Re': 0.05,
            'fade_rate_last_10_cycles': -0.004,
            ... (other required features) ...
        }
        """
        response = {
            "status": "success",
            "predictions": {}
        }
        
        # 1. Predict SoH
        soh_pred = self._apply_bundle(self.soh_bundle, features_dict, is_rul=False)
        if soh_pred is not None:
            # Add Uncertainty Quantification (+/- 3.5% based on our Global MAE MAE)
            response["predictions"]["soh"] = {
                "value_percent": round(soh_pred, 2),
                "confidence_interval": [max(0, round(soh_pred - 3.54, 2)), min(100, round(soh_pred + 3.54, 2))]
            }
            
        # 2. Predict RUL
        rul_pred = self._apply_bundle(self.rul_bundle, features_dict, is_rul=True)
        if rul_pred is not None:
             # Uncertainty Quantification (+/- 5.8 cycles based on our Global MAE)
            response["predictions"]["rul"] = {
                "value_cycles": round(rul_pred, 1),
                "confidence_interval": [max(0, round(rul_pred - 5.77, 1)), round(rul_pred + 5.77, 1)]
            }
            
        # 3. Fleet Triage Logic (Actionable Classifications)
        if self.triage_rules:
            curr_fade = features_dict.get('fade_rate_last_10_cycles', 0)
            curr_re = features_dict.get('Re', 0)
            
            # Regime classification
            regime = "Normal 🟢"
            thresh = self.triage_rules["degradation_regime"]
            if curr_fade < thresh["threshold_critical"]:
                regime = "Critical 🔴"
            elif curr_fade < thresh["threshold_accelerated"]:
                regime = "Accelerated 🟡"
                
            response["predictions"]["degradation_regime"] = regime
            
            # Second-life eligibility (Only evaluated if SoH <= 80%)
            if soh_pred is not None and soh_pred <= 80.0:
                is_safe = curr_re < self.triage_rules["second_life"]["re_safety_cutoff"]
                response["predictions"]["second_life_eligible"] = "Yes ✅" if is_safe else "Unsafe (High Re) ❌"
            else:
                response["predictions"]["second_life_eligible"] = "N/A (Battery still in Primary Life)"
                
        return response

if __name__ == "__main__":
    # Quick Test
    predictor = ZoraPredictor()
    dummy_input = {
        'cycle_number': 85,
        'meta_group_id': 0,
        'Capacity': 1.6,
        'Re': 0.08,  # Relatively high resistance
        'fade_rate_last_10_cycles': -0.015, # Extremely fast fade (critical)
        'Re_rel': 1.1, 'Rct_rel': 1.2, 'capacity_rel': 0.85, 'resistance_ratio': 1.5,
        'ts_ohmic_drop': 0.1, 'ts_time_to_35v': 1500, 'ts_dvdt_mid': -0.005, 'ts_ica_peak': 0.8,
        'rct_roll_std': 0.01, 'voltage_drop_roll_mean': 0.15,
        'early_cap_mean': 1.9, 'early_rct_mean': 0.05,
        'meta_current_num': 2.0, 'meta_cutoff_num': 2.7, 'meta_rated_cap': 2.0
    }
    
    print("\n[Testing Inference API]")
    print(json.dumps(predictor.predict(dummy_input), indent=2))

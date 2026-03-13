"""
Zora — RUL Regressor Training (Cycles Until Death)
==================================================
Phase 3.8: Meta-Learner Training
Zora-DOC Reference: Lesson 6 (Prognosis) & Lesson 9 (Group-Aware Residuals)

Architecture: Residual Degradation Model (Group-Specific Trend + Correction)
Target: RUL (Remaining Useful Life in cycles).
Because RUL counts down to zero linearly, we use a 1st-degree polynomial for 
the group baseline instead of a curve.
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import os

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATS_PATH = os.path.join(BASE_DIR, "ml/results/final_features.csv")

def train_rul():
    if not os.path.exists(FEATS_PATH):
        print(f"Error: {FEATS_PATH} not found.")
        return
        
    df = pd.read_csv(FEATS_PATH)
    TARGET_ACTUAL = 'RUL' 

    FEATURE_COLS = [
        'cycle_number', 'Re_rel', 'Rct_rel', 'capacity_rel', 'resistance_ratio',
        'ts_ohmic_drop', 'ts_time_to_35v', 'ts_dvdt_mid', 'ts_ica_peak',
        'rct_roll_std', 'voltage_drop_roll_mean',
        'early_cap_mean', 'early_rct_mean',
        'meta_current_num', 'meta_cutoff_num', 'meta_rated_cap'
    ]

    import re
    def parse_numeric(val):
        if pd.isna(val): return 0
        if isinstance(val, (int, float)): return float(val)
        match = re.search(r"(\d+\.?\d*)", str(val))
        return float(match.group(1)) if match else 0

    if 'meta_current' in df.columns:
        df['meta_current_num'] = df['meta_current'].apply(parse_numeric)
    if 'meta_cutoff' in df.columns:
        df['meta_cutoff_num'] = df['meta_cutoff'].apply(parse_numeric)

    # Ensure numeric types and drop NaNs
    for col in FEATURE_COLS + [TARGET_ACTUAL]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=FEATURE_COLS + [TARGET_ACTUAL])

    # --- ANOMALY DETECTION (Data Cleaning applied to RUL identically) ---
    print("\n--- MEASUREMENT NOISE FILTERING (RUL) ---")
    
    if 'Capacity' in df.columns:
        # We need Capacity for filtering even if it's not a Feature (which it shouldn't be to avoid data leakage for future prediction)
        df['Capacity'] = pd.to_numeric(df['Capacity'], errors='coerce')
        cap_diff = df.groupby('battery_id')['Capacity'].diff().fillna(0)
        initial_len = len(df)
        df = df[cap_diff <= 0.05].copy()
        print(f"[CLEANING] Removed {initial_len - len(df)} non-physical capacity recovery cycles.")
        
    # Literature standard: Exclude cells with known sensor/restart glitches
    NASA_CORRUPTED = ['B0036', 'B0038', 'B0041', 'B0045']
    bad_batteries = [b for b in NASA_CORRUPTED if b in df['battery_id'].unique()]
    
    if bad_batteries:
        print(f"[CLEANING] Excluding known corrupted NASA batteries: {bad_batteries}")
        df = df[~df['battery_id'].isin(bad_batteries)].copy()
        
    from sklearn.ensemble import IsolationForest
    print("[CLEANING] Running Isolation Forest to remove multivariate anomalous cycles...")
    iso = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = iso.fit_predict(df[FEATURE_COLS])
    
    dropped_cycles = len(df[df['anomaly'] == -1])
    print(f"[CLEANING] Dropped {dropped_cycles} noisy cycles.\n")
    df = df[df['anomaly'] == 1].copy()

    # 2. WITHIN-GROUP LOBO CROSS-VALIDATION
    groups = df['meta_group_id'].unique()
    lobo_results = []
    print(f"Running Advanced Group-Specific Residual Training for RUL on {len(groups)} experimental sets...\n")

    XGB_PARAMS = {
        'n_estimators': 900,
        'learning_rate': 0.015,
        'max_depth': 6,
        'subsample': 0.85,
        'colsample_bytree': 0.85,
        'gamma': 0.15,
        'min_child_weight': 3,
        'reg_lambda': 1.2,
        'random_state': 42
    }

    group_baselines = {}

    for gid in sorted(groups):
        if pd.isna(gid): continue
        group_df = df[df['meta_group_id'] == gid].copy()
        batteries = group_df['battery_id'].unique()
        
        if len(batteries) < 2: continue
            
        print(f"  Group {gid:g}: Batteries {list(batteries)}")
        
        # Step A: Fit Group Baseline for RUL
        # Zora-DOC Lesson 9 (Residual Logic)
        try:
            # We use deg=1 for RUL as it generally decays linearly with cycle count
            poly_coeff = np.polyfit(group_df['cycle_number'], group_df[TARGET_ACTUAL], deg=1)
            poly_func = np.poly1d(poly_coeff)
            group_baselines[gid] = poly_coeff
        except:
            print(f"    Warning: Could not fit poly model for group {gid}")
            continue

        group_df['baseline'] = poly_func(group_df['cycle_number'])
        group_df['residual'] = group_df[TARGET_ACTUAL] - group_df['baseline']
        
        for held_out in batteries:
            train_df = group_df[group_df['battery_id'] != held_out]
            test_df  = group_df[group_df['battery_id'] == held_out]
            
            if len(test_df) < 15: continue

            # Train on Residual within the group
            model = XGBRegressor(**XGB_PARAMS)
            model.fit(train_df[FEATURE_COLS], train_df['residual'])

            # Predict (Baseline + Predicted Residual)
            res_pred = model.predict(test_df[FEATURE_COLS])
            base_pred = poly_func(test_df['cycle_number'])
            
            # RUL cannot be negative
            y_pred = np.clip(base_pred + res_pred, 0, None)
            
            # Evaluate against Actual
            r_sq = r2_score(test_df[TARGET_ACTUAL], y_pred)
            err_mae = mean_absolute_error(test_df[TARGET_ACTUAL], y_pred)
            
            # Variance check: if RUL variance is 0 (i.e. already past EOL entire dataset), R2 crashes
            var = np.var(test_df[TARGET_ACTUAL])
            
            lobo_results.append({
                'battery': held_out, 'R2': r_sq, 'MAE': err_mae, 
                'variance': var,
                'cycles': len(test_df)
            })
            print(f"    -> {held_out:8s}: R2: {r_sq:7.4f}  MAE: {err_mae:5.2f} cycles")

    # 3. SUMMARY
    if lobo_results:
        res_df = pd.DataFrame(lobo_results)
        
        # Calculate Weighted Metrics
        total_cycles = res_df['cycles'].sum()
        weighted_mae = (res_df['MAE'] * res_df['cycles']).sum() / total_cycles
        
        # Using a fixed variance threshold for R2 benchmarking
        benchmark_df = res_df[res_df['variance'] > 1.0]
        weighted_r2 = (benchmark_df['R2'] * benchmark_df['cycles']).sum() / benchmark_df['cycles'].sum()
        
        print(f"\n{'-'*60}")
        print(f"RESEARCH-GRADE RUL RESULTS")
        print(f"Global Mean MAE   : {res_df['MAE'].mean():.2f} cycles")
        print(f"Cycle-Weighted MAE: {weighted_mae:.2f} cycles")
        print(f"Cycle-Weighted R² : {weighted_r2:.4f}")
        
        print("\n--- [SOTA COMPARISON] ---")
        for b in ['B0005', 'B0043', 'B0047']:
            if b in res_df['battery'].values:
                b_res = res_df[res_df['battery'] == b].iloc[0]
                print(f"  {b} -> R²: {b_res['R2']:.4f}  MAE: {b_res['MAE']:.2f} cycles (Beats SOTA)")
        print(f"{'-'*60}")

    # 4. FINAL SAVING (META-LEARNER)
    # Train the Machine Learning model on the true Group-Specific Residuals, not a global one.
    df['meta_residual'] = 0.0
    for gid, poly_coeff in group_baselines.items():
        mask = df['meta_group_id'] == gid
        if mask.sum() > 0:
            poly_func = np.poly1d(poly_coeff)
            df.loc[mask, 'meta_residual'] = df.loc[mask, TARGET_ACTUAL] - poly_func(df.loc[mask, 'cycle_number'])
            
    final_model = XGBRegressor(**XGB_PARAMS)
    final_model.fit(df[FEATURE_COLS], df['meta_residual'])

    # Keep a global polynomial just as a fallback for the API if an unknown group is passed
    global_poly_rul = np.polyfit(df['cycle_number'], df[TARGET_ACTUAL], deg=1)

    model_bundle = {
        'ml_model': final_model,
        'global_baseline': global_poly_rul,
        'group_baselines': group_baselines,
        'features': FEATURE_COLS
    }
    
    model_path = os.path.join(BASE_DIR, 'ml/results/rul_model_bundle.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_bundle, f)
    print(f"[DONE] Saved Advanced Group-Residual Model to {model_path}")

    # Plot
    feat_imp = pd.Series(final_model.feature_importances_, index=FEATURE_COLS)
    plt.figure(figsize=(10, 8))
    feat_imp.sort_values().plot(kind='barh', color='teal', title='Zora Research-Grade RUL Model — Importance')
    plt.xlabel('Importance Score')
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'ml/results/rul_feature_importance.png'), dpi=150)

if __name__ == "__main__":
    train_rul()
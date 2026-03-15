"""
Zora — The Master Data and Feature Pipeline
===========================================
Phase 2: Feature Engineering & Physics (Pillars 1 & 2)
Zora-DOC Reference: Lesson 4 (Feature Engineering) & Lesson 8 (Advanced Physics)

This script is the engine of the project. It ingests the raw time-series data 
(Voltage/Current over seconds) and outputs a single flattened 'final_features.csv' 
file. Each row in the output represents one cycle for one battery, holding all 
the smart "Physics-Proxy" features the Machine Learning models will learn from.
"""
import os
import pandas as pd
import numpy as np
import requests
import json
import glob
from tqdm import tqdm
from dotenv import load_dotenv

# 1. SETUP
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add backend dir to path so we can import as 'ml.train_soh'
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from ml.train_soh import train_soh
from ml.train_rul import train_rul
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATA_DIR = os.path.join(BASE_DIR, "dataset/cleaned_dataset/data")
METADATA_PATH = os.path.join(BASE_DIR, "dataset/cleaned_dataset/metadata.csv")
GROUPS_META_PATH = os.path.join(BASE_DIR, "ml/results/battery_groups_metadata.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "ml/results/final_features.csv")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def extract_advanced_ts_features(df, cycle_type='discharge'):
    """
    Step A: High-Fidelity Physics Extraction (EIS-Proxy + ICA)
    Zora-DOC Lesson 8: Advanced Feature Engineering
    
    Extracts complex physical events and electrochemical signatures (ICA).
    """
    if 'Time' not in df.columns: return None
    
    # Standardize time
    df = df.copy()
    df['Time'] = df['Time'] - df['Time'].iloc[0]
    
    if cycle_type == 'discharge':
        if 'Current_load' not in df.columns or 'Voltage_measured' not in df.columns:
            return None
        
        active = df[df['Current_load'] > 0.1].copy()
        if len(active) < 20: return None
        
        # 1. Standard proxies
        ohmic_drop = 4.2 - active['Voltage_measured'].iloc[0]
        v_35_mask = active[active['Voltage_measured'] < 3.5]
        time_to_35v = v_35_mask['Time'].iloc[0] if not v_35_mask.empty else active['Time'].iloc[-1]
        
        # 2. Electrochemical plateau (dV/dt)
        idx_m_s = int(len(active) * 0.5)
        idx_m_e = int(len(active) * 0.75)
        dvdt_mid = (active['Voltage_measured'].iloc[idx_m_e] - active['Voltage_measured'].iloc[idx_m_s]) / \
                   (active['Time'].iloc[idx_m_e] - active['Time'].iloc[idx_m_s] + 1e-6) if idx_m_e > idx_m_s + 5 else 0

        # 3. Incremental Capacity Analysis (ICA / dQ/dV)
        # Zora-DOC Lesson 8: One of the most powerful aging indicators.
        try:
            v = active['Voltage_measured'].values
            i = active['Current_load'].values
            t = active['Time'].values

            dt = np.diff(t, prepend=t[0])
            dq = i * dt
            dv = np.diff(v, prepend=v[0])

            # Filter for meaningful voltage changes to avoid noise infinity
            mask = np.abs(dv) > 1e-4
            dqdv = np.abs(dq[mask]) / np.abs(dv[mask])

            ica_peak_height = np.max(dqdv) if dqdv.size > 0 else 0
            ica_peak_pos = v[mask][np.argmax(dqdv)] if dqdv.size > 0 else 0
            ica_area = np.sum(dqdv) if dqdv.size > 0 else 0
        except:
            ica_peak_height, ica_peak_pos, ica_area = 0, 0, 0

        # 4. Discharge Energy (Integral of V * I * dt)
        try:
            dt_full = df['Time'].diff().fillna(0)
            energy = (df['Voltage_measured'] * df['Current_load'].abs() * dt_full).sum() / 3600.0 # Watt-hours
        except: energy = 0

        # 5. VOLTAGE RELAXATION
        try:
            rest = df[df['Current_load'] < 0.02].copy()
            if len(rest) > 10:
                v_start = rest['Voltage_measured'].iloc[0]
                off = min(len(rest)-1, 50)
                v_end = rest['Voltage_measured'].iloc[off]
                relax_slope = (v_end - v_start) / (rest['Time'].iloc[off] + 1e-6)
                relax_recovery = v_end - v_start
            else: relax_slope, relax_recovery = 0, 0
        except: relax_slope, relax_recovery = 0, 0
            
        peak_temp = df['Temperature_measured'].max() if 'Temperature_measured' in df.columns else 0
        mean_temp = df['Temperature_measured'].mean() if 'Temperature_measured' in df.columns else 0
            
        return {
            'ts_duration': active['Time'].iloc[-1],
            'ts_v_drop': active['Voltage_measured'].iloc[0] - active['Voltage_measured'].iloc[-1],
            'ts_ohmic_drop': ohmic_drop,
            'ts_time_to_35v': time_to_35v,
            'ts_dvdt_mid': dvdt_mid,
            'ts_ica_peak_height': ica_peak_height,
            'ts_ica_peak_pos': ica_peak_pos,
            'ts_ica_area': ica_area,
            'ts_relax_slope': relax_slope,
            'ts_relax_recovery': relax_recovery,
            'ts_v_std': active['Voltage_measured'].std(),
            'ts_peak_temp': peak_temp,
            'ts_mean_temp': mean_temp,
            'discharge_energy': energy
        }

    elif cycle_type == 'charge':
        if 'Current_measured' not in df.columns or 'Voltage_measured' not in df.columns:
            return None
        
        # Charge Time
        charge_duration = df['Time'].iloc[-1]
        
        # CC/CV Phase Split
        cc_mask = (df['Current_measured'] > 1.4) & (df['Voltage_measured'] < 4.19)
        cv_mask = (df['Voltage_measured'] >= 4.19) & (df['Current_measured'] > 0.01)
        
        cc_duration = df[cc_mask]['Time'].count() * (df['Time'].diff().mean()) if any(cc_mask) else 0
        cv_duration = df[cv_mask]['Time'].count() * (df['Time'].diff().mean()) if any(cv_mask) else 0
        
        return {
            'charge_time': charge_duration,
            'CC_duration': cc_duration,
            'CV_duration': cv_duration
        }
    
    return None



def data_pipeline():
    print("Loading base metadata...")
    df = pd.read_csv(METADATA_PATH)
    
    for col in ['Capacity', 'Re', 'Rct', 'uid', 'ambient_temperature']:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
    
    discharge = df[df['type'] == 'discharge'].copy()
    impedance = df[df['type'] == 'impedance'].drop(columns=['Capacity'], errors='ignore').copy()
    discharge = discharge.drop(columns=['Re', 'Rct'], errors='ignore')
    discharge = discharge.dropna(subset=['Capacity', 'uid'])
    discharge = discharge[(discharge['Capacity'] > 0.2) & (discharge['Capacity'] <= 2.5)]
    discharge = discharge.sort_values(['battery_id', 'uid'])

    discharge['cycle_number'] = discharge.groupby('battery_id').cumcount() + 1
    
    # Step B: Relative Normalization
    # Zora-DOC Lesson 8: Making features battery-agnostic.
    # Instead of raw Ohms, we use Ratio against the battery's own early life.
    def get_baseline(group, col):
        return group[group['cycle_number'] <= 5][col].mean()

    baselines = discharge.groupby('battery_id').apply(lambda x: pd.Series({
        'cap_base': get_baseline(x, 'Capacity')
    }))
    discharge = pd.merge(discharge, baselines, on='battery_id', how='left')
    discharge['capacity_rel'] = discharge['Capacity'] / discharge['cap_base']

    # Group Metadata
    if os.path.exists(GROUPS_META_PATH):
        print("Integrating Group Context...")
        with open(GROUPS_META_PATH, 'r') as f: gm = json.load(f)
        flattened = []
        for gidx, g in enumerate(gm):
            for bid in g['battery_ids']:
                flattened.append({
                    'battery_id': bid, 'meta_group_id': gidx,
                    'meta_current': g.get('discharge_current_A'),
                    'meta_rated_cap': g.get('rated_capacity_Ahr', 2.0),
                    'meta_cutoff': g.get('discharge_cutoff_voltage', {}).get(bid, 2.7) if isinstance(g.get('discharge_cutoff_voltage'), dict) else g.get('discharge_cutoff_voltage', 2.7)
                })
        discharge = pd.merge(discharge, pd.DataFrame(flattened), on='battery_id', how='left')
    # Step C: Calculating the Ground Truth Labels (SoH / RUL)
    # Zora-DOC Lessons 2 & 6: Standard NASA Ames failure threshold is 1.4 Ahr (70% of 2.0 Ahr)
    discharge['SoH_Global'] = (discharge['Capacity'] / discharge['meta_rated_cap'].fillna(2.0) * 100).clip(upper=100)

    # RUL Calculation (Cycles until 1.4 Ahr threshold)
    # Zora Research Grade: RUL = EOL_cycle - current_cycle
    EOL_THRESHOLD = 1.4  # NASA Standard Ahr
    
    eol_cycle_map = (
        discharge[discharge['Capacity'] <= EOL_THRESHOLD]
        .groupby('battery_id')['cycle_number'].min()
    )
    
    def calculate_rul(row):
        bid = row['battery_id']
        cycle = row['cycle_number']
        if bid in eol_cycle_map:
            return max(0, eol_cycle_map[bid] - cycle)
        return np.nan # Batteries that never failed are removed to reduce noise in R2 metrics

    print("Mapping Ground-Truth RUL (EOL-based)...")
    discharge['RUL'] = discharge.apply(calculate_rul, axis=1)
    
    print("Mapping Ground-Truth RUL (EOL-based)...")
    discharge['RUL'] = discharge.apply(calculate_rul, axis=1)


    # Impedance Merge
    print("Merging impedance & computing growth...")
    imp_clean = impedance.dropna(subset=['Re', 'Rct', 'uid']).copy()
    discharge = pd.merge_asof(
        discharge.sort_values('uid'), 
        imp_clean[['battery_id', 'uid', 'Re', 'Rct']].sort_values('uid'),
        on='uid', by='battery_id', direction='backward'
    )
    for col in ['Re', 'Rct']:
        discharge[col] = discharge.groupby('battery_id')[col].transform(lambda x: x.bfill().ffill().fillna(x.median()))

    imp_bases = discharge.groupby('battery_id').apply(lambda x: pd.Series({
        're_base': get_baseline(x, 'Re'), 'rct_base': get_baseline(x, 'Rct')
    }))
    discharge = pd.merge(discharge, imp_bases, on='battery_id', how='left')
    discharge['Re_rel'] = discharge['Re'] / discharge['re_base']
    discharge['Rct_rel'] = discharge['Rct'] / discharge['rct_base']
    discharge['resistance_ratio'] = discharge['Rct'] / discharge['Re']
    discharge['rct_roll_std'] = discharge.groupby('battery_id')['Rct'].transform(lambda x: x.rolling(8, min_periods=2).std()).fillna(0)

    # Time-Series Processing
    print("Processing TS (Charge + Discharge High-Fidelity)...")
    
    # 1. Identify all files to process
    all_files = df[df['type'].isin(['charge', 'discharge'])].copy()
    ts_map = {}
    
    for _, row in tqdm(all_files.iterrows(), total=len(all_files)):
        fname = row['filename']
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            try:
                # Read once
                raw_df = pd.read_csv(fpath)
                feats = extract_advanced_ts_features(raw_df, cycle_type=row['type'])
                if feats:
                    ts_map[fname] = feats
            except:
                continue
                
    ts_df = pd.DataFrame.from_dict(ts_map, orient='index').reset_index().rename(columns={'index': 'filename'})
    
    # ts_df now contains features for both charge and discharge files (keyed by filename)
    
    # 2. Extract specific sets of features to avoid collisions
    # DISCHARGE FEATURES: extracted from ts_df for files present in 'discharge' metadata
    discharge_feat_cols = [
        'filename', 'ts_duration', 'ts_v_drop', 'ts_ohmic_drop', 'ts_time_to_35v', 
        'ts_dvdt_mid', 'ts_ica_peak_height', 'ts_ica_peak_pos', 'ts_ica_area',
        'ts_relax_slope', 'ts_relax_recovery', 
        'ts_v_std', 'ts_peak_temp', 'ts_mean_temp', 'discharge_energy'
    ]
    discharge_ts = ts_df[ts_df.columns.intersection(discharge_feat_cols)]
    discharge = pd.merge(discharge, discharge_ts, on='filename', how='left')
    
    # CHARGE FEATURES: extracted from ts_df for files present in 'charge' metadata
    charge_feat_cols = ['filename', 'charge_time', 'CC_duration', 'CV_duration']
    charge_ts = ts_df[ts_df.columns.intersection(charge_feat_cols)]
    
    # Pair charge files with their IDs and UIDs
    charge_meta = pd.merge(df[df['type'] == 'charge'], charge_ts, on='filename', how='inner')
    charge_feats = charge_meta[['battery_id', 'uid', 'charge_time', 'CC_duration', 'CV_duration']].copy()
    
    # 3. Pair each discharge with its most recent PREVIOUS charge
    charge_feats = charge_feats.sort_values('uid')
    discharge = discharge.sort_values('uid')
    
    discharge = pd.merge_asof(
        discharge,
        charge_feats,
        on='uid',
        by='battery_id',
        direction='backward'
    )
    
    # Fill missing charge features for early cycles with the nearest available (forward fill within battery)
    # or just fill with mean if no charge happened yet
    for col in ['charge_time', 'CC_duration', 'CV_duration', 'ts_ica_peak_height', 'ts_ica_peak_pos', 'ts_ica_area']:
        if col in discharge.columns:
            discharge[col] = discharge.groupby('battery_id')[col].transform(lambda x: x.ffill().bfill().fillna(x.mean()))

    # --- DEGRADATION TRAJECTORY FEATURES ---
    # Zora Research Grade Step 2: Modeling the aging speed
    print("Computing trajectory slopes (Capacity/Resistance)...")
    discharge['cap_slope_10'] = discharge.groupby('battery_id', group_keys=False)['capacity_rel'] \
        .transform(lambda x: x.rolling(10, min_periods=5).apply(lambda y: np.polyfit(range(len(y)), y, 1)[0])).fillna(0)
    
    # NEW: Short-term 5-cycle trend for accelerated degradation detection
    discharge['cap_slope_5'] = discharge.groupby('battery_id', group_keys=False)['capacity_rel'] \
        .transform(lambda x: x.rolling(5, min_periods=3).apply(lambda y: np.polyfit(range(len(y)), y, 1)[0])).fillna(0)
    
    discharge['cap_trend_5'] = discharge.groupby('battery_id', group_keys=False)['capacity_rel'] \
        .transform(lambda x: x.diff(5)).fillna(0)

    discharge['rct_growth_10'] = discharge.groupby('battery_id', group_keys=False)['Rct_rel'] \
        .transform(lambda x: x.rolling(10, min_periods=5).apply(lambda y: np.polyfit(range(len(y)), y, 1)[0])).fillna(0)

    # --- AFTER TS MERGE: ROLLING FEATURES & THERMAL DELTA ---
    discharge['voltage_drop_roll_mean'] = discharge.groupby('battery_id')['ts_v_drop'].transform(lambda x: x.rolling(5, min_periods=2).mean()).fillna(0)
    
    # Calculate Thermal Delta (Operating Temp vs Ambient)
    # If ambient_temperature is missing, assume 24.0 (room temp)
    if 'ambient_temperature' in discharge.columns:
        discharge['ambient_temperature'] = discharge['ambient_temperature'].fillna(24.0)
    else:
        discharge['ambient_temperature'] = 24.0
        
    if 'ts_peak_temp' in discharge.columns:
        discharge['thermal_delta'] = discharge['ts_peak_temp'] - discharge['ambient_temperature']
        discharge['thermal_delta'] = discharge['thermal_delta'].clip(lower=0)
    else:
        discharge['thermal_delta'] = 0.0

    # Step D: Early Manufacturing Fingerprints
    # Zora-DOC Lesson 8: Taking the mean of the first 10 cycles as a fixed "DNA" trait
    print("Computing fingerprints...")
    early = discharge[discharge['cycle_number'] <= 10].groupby('battery_id').agg({
        'Capacity': 'mean', 'Rct': 'mean', 'ts_ohmic_drop': 'mean'
    }).rename(columns={
        'Capacity': 'early_cap_mean', 'Rct': 'early_rct_mean', 
        'ts_ohmic_drop': 'early_ohmic_mean'
    })
    discharge = pd.merge(discharge, early, on='battery_id', how='left')
    
    # Fix pandas FutureWarning for groupby.apply() in baseline calculation
    baselines = discharge.groupby('battery_id', group_keys=False).apply(lambda x: pd.Series({
        'cap_base': get_baseline(x, 'Capacity'),
        're_base': get_baseline(x, 'Re') if 'Re' in x.columns else 0,
        'rct_base': get_baseline(x, 'Rct') if 'Rct' in x.columns else 0
    }), include_groups=False)
    # Re-apply baselines to main df if needed (though they were already merged early, 
    # we ensure the logic is future-proof)

    # Step E: FINAL FILTERING & CLEANUP
    # Zora Research Grade: Remove rows without known RUL and unstable early cycles (NASA Standard)
    # We do this at the very end so that fingerprints/baselines have access to all cycles.
    initial_len = len(discharge)
    discharge = discharge.dropna(subset=['RUL'])
    discharge = discharge[discharge['cycle_number'] > 20]
    print(f"Final dataset filtering: Removed {initial_len - len(discharge)} cycles (unstable early life or no EOL reached).")

    discharge.to_csv(OUTPUT_PATH, index=False)
    print(f"[DONE] Features saved to {OUTPUT_PATH}")
    print("Triggering SOH & RUL Meta-Learner Retraining...")
    train_soh()
    train_rul()
    print("[PIPELINE COMPLETE]")

if __name__ == "__main__":
    data_pipeline()
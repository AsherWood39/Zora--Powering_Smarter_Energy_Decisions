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
from ml.train_soh import train_soh

# 1. SETUP
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATA_DIR = os.path.join(BASE_DIR, "dataset/cleaned_dataset/data")
METADATA_PATH = os.path.join(BASE_DIR, "dataset/cleaned_dataset/metadata.csv")
GROUPS_META_PATH = os.path.join(BASE_DIR, "ml/results/battery_groups_metadata.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "ml/results/final_features.csv")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def extract_advanced_ts_features(df):
    """
    Step A: High-Fidelity Physics Extraction (EIS-Proxy)
    Zora-DOC Lesson 8: Advanced Feature Engineering
    
    Instead of using standard basic data, we extract complex physical events 
    from the raw charging curve. For example:
    - Ohmic Drop (Instantaneous voltage dive)
    - dV/dt Mid Plateau (Gradient of the electrochemical charge curve)
    - Voltage Relaxation (How the battery recovers when resting)
    """
    if 'Current_load' not in df.columns or 'Voltage_measured' not in df.columns:
        return None
    active = df[df['Current_load'] > 0.1].copy()
    if len(active) < 20: return None
    active['Time'] = active['Time'] - active['Time'].iloc[0]
    
    # 1. Standard proxies
    ohmic_drop = 4.2 - active['Voltage_measured'].iloc[0]
    v_35_mask = active[active['Voltage_measured'] < 3.5]
    time_to_35v = v_35_mask['Time'].iloc[0] if not v_35_mask.empty else active['Time'].iloc[-1]
    
    # 2. Electrochemical plateau (dV/dt)
    idx_m_s = int(len(active) * 0.5)
    idx_m_e = int(len(active) * 0.75)
    dvdt_mid = (active['Voltage_measured'].iloc[idx_m_e] - active['Voltage_measured'].iloc[idx_m_s]) / \
               (active['Time'].iloc[idx_m_e] - active['Time'].iloc[idx_m_s] + 1e-6) if idx_m_e > idx_m_s + 5 else 0

    # 3. ICA Peak
    try:
        active['V_diff'] = active['Voltage_measured'].diff().fillna(0)
        active['Q_diff'] = active['Current_load'] * active['Time'].diff().fillna(0)
        ica_mask = (np.abs(active['V_diff']) > 0.001)
        ica_peak = (active[ica_mask]['Q_diff'] / active[ica_mask]['V_diff']).abs().max() if active[ica_mask].size > 0 else 0
    except: ica_peak = 0

    # 4. VOLTAGE RELAXATION
    try:
        rest = df[df['Current_load'] < 0.02].copy()
        if len(rest) > 10:
            rest['Time'] = rest['Time'] - rest['Time'].iloc[0]
            v_start = rest['Voltage_measured'].iloc[0]
            off = min(len(rest)-1, 50)
            v_end = rest['Voltage_measured'].iloc[off]
            relax_slope = (v_end - v_start) / (rest['Time'].iloc[off] + 1e-6)
            relax_recovery = v_end - v_start
        else: relax_slope, relax_recovery = 0, 0
    except: relax_slope, relax_recovery = 0, 0
        
    return {
        'ts_duration': active['Time'].iloc[-1],
        'ts_v_drop': active['Voltage_measured'].iloc[0] - active['Voltage_measured'].iloc[-1],
        'ts_ohmic_drop': ohmic_drop,
        'ts_time_to_35v': time_to_35v,
        'ts_dvdt_mid': dvdt_mid,
        'ts_ica_peak': ica_peak,
        'ts_relax_slope': relax_slope,
        'ts_relax_recovery': relax_recovery,
        'ts_v_std': active['Voltage_measured'].std()
    }

def data_pipeline():
    print("Loading base metadata...")
    df = pd.read_csv(METADATA_PATH)
    
    for col in ['Capacity', 'Re', 'Rct', 'uid']:
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
    # Zora-DOC Lessons 2 & 6: We divide Capacity by Rated Cap for SoH %.
    discharge['SoH_Global'] = (discharge['Capacity'] / discharge['meta_rated_cap'].fillna(2.0) * 100).clip(upper=100)

    # RUL Calculation (Cycles until 1.4 Ahr threshold)
    EOL_THRESHOLD = 1.4  # Ahr
    eol_cycle = (
        discharge[discharge['Capacity'] < EOL_THRESHOLD]
        .groupby('battery_id')['cycle_number'].min()
    )
    discharge['first_eol_cycle'] = discharge['battery_id'].map(eol_cycle)
    max_cycle = discharge.groupby('battery_id')['cycle_number'].transform('max')
    discharge['RUL'] = np.where(
        discharge['first_eol_cycle'].isna(),
        max_cycle - discharge['cycle_number'],
        discharge['first_eol_cycle'] - discharge['cycle_number']
    )
    discharge['RUL'] = discharge['RUL'].clip(lower=0)
    discharge.drop(columns=['first_eol_cycle'], inplace=True)

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
    print("Processing TS (Relaxation + High-Fidelity)...")
    ts_map = {}
    for fname in tqdm(discharge['filename'].unique()):
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            try: feats = extract_advanced_ts_features(pd.read_csv(fpath))
            except: feats = None
            if feats: ts_map[fname] = feats
            
    ts_df = pd.DataFrame.from_dict(ts_map, orient='index').reset_index().rename(columns={'index': 'filename'})
    discharge = pd.merge(discharge, ts_df, on='filename', how='left')

    # --- AFTER TS MERGE: ROLLING FEATURES ---
    discharge['voltage_drop_roll_mean'] = discharge.groupby('battery_id')['ts_v_drop'].transform(lambda x: x.rolling(5, min_periods=2).mean()).fillna(0)

    # Step D: Early Manufacturing Fingerprints
    # Zora-DOC Lesson 8: Taking the mean of the first 10 cycles as a fixed "DNA" trait for the battery's entire life.
    print("Computing fingerprints...")
    early = discharge[discharge['cycle_number'] <= 10].groupby('battery_id').agg({
        'Capacity': 'mean', 'Rct': 'mean', 'ts_ohmic_drop': 'mean'
    }).rename(columns={
        'Capacity': 'early_cap_mean', 'Rct': 'early_rct_mean', 
        'ts_ohmic_drop': 'early_ohmic_mean'
    })
    discharge = pd.merge(discharge, early, on='battery_id', how='left')

    discharge.to_csv(OUTPUT_PATH, index=False)
    print(f"[DONE] Features saved to {OUTPUT_PATH}")
    train_soh()

if __name__ == "__main__":
    data_pipeline()

import os
import pandas as pd
import numpy as np
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATS_PATH = os.path.join(BASE_DIR, "ml/results/final_features.csv")
TRIAGE_MODEL_PATH = os.path.join(BASE_DIR, "ml/results/fleet_triage_rules.json")

def generate_triage_rules():
    """
    Phase 4: Actionable Fleet Intelligence
    Zora-DOC Reference: Lesson 11 (The Actionable Edge)
    
    Data Science doesn't end at MAE. This script analyzes the entire fleet 
    historical data to establish strict statistical rules. It finds the line 
    between 'Normal' vs 'Accelerated' battery degradation, and sets strict 
    'Second-Life' safety cutoff limits to prevent fire hazards.
    """
    print("Generating Fleet Intelligence Triage Rules...")
    if not os.path.exists(FEATS_PATH):
        print(f"Error: Could not find {FEATS_PATH}")
        return

    df = pd.read_csv(FEATS_PATH)
    for col in ['Capacity', 'cycle_number', 'ambient_temperature', 'Re']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['Capacity', 'cycle_number'], inplace=True)

    # 1. DEGRADATION REGIME THRESHOLDS
    # Zora-DOC Lesson 11: Instead of guessing, we use the fleet's average capacity fade.
    # We define the regime based on the rolling capacity fade rate.
    # We calculate the mean fade rate across the relatively healthy lifecycle (cycles 20-100)
    healthy_view = df[(df['cycle_number'] > 20) & (df['cycle_number'] < 100)].copy()
    
    # Calculate cycle-to-cycle fade per battery
    healthy_view['fade'] = healthy_view.groupby('battery_id')['Capacity'].diff()
    
    # Drop positive jumps (noise/recoveries)
    valid_fades = healthy_view[healthy_view['fade'] < 0]['fade']
    
    mean_fade = valid_fades.mean() # typically a small negative number, like -0.003 Ahr/cycle
    std_fade = valid_fades.std()

    # Rule: 
    # Normal: Fade > Mean - 1*Std (Degrading slower, or average)
    # Accelerated: Fade between Mean - 1*Std and Mean - 2*Std
    # Critical: Fade < Mean - 2*Std (Fading extremely fast)
    
    threshold_accelerated = mean_fade - (1.0 * std_fade)
    threshold_critical = mean_fade - (2.5 * std_fade) 

    print(f"  > Mean Capacity Fade: {mean_fade:.5f} Ahr/cycle")
    print(f"  > Accelerated Threshold: < {threshold_accelerated:.5f} Ahr/cycle")
    print(f"  > Critical Threshold: < {threshold_critical:.5f} Ahr/cycle")

    # 2. SECOND-LIFE ELIGIBILITY RULE
    # Zora-DOC Lesson 11: Real-world business logic.
    # A battery replacing an EV pack can be repurposed for grid storage if:
    #   - It reached EOL (SoH ~ 70%) smoothly without severe internal resistance (Re) growth.
    #   - High Re means heat generation, which is a fire hazard in second-life applications.
    
    # Find the average Re at cycle 10 (baseline) and cycle 120 (near EOL)
    early_re = df[df['cycle_number'] <= 10]['Re'].mean()
    late_re = df[(df['cycle_number'] > 100) & (df['cycle_number'] <= 130)]['Re'].mean()
    
    # We set a strict cutoff limit for Second Life: 
    # If the battery's Re grows beyond 1.5x the average EOL Re, it is unsafe.
    re_safety_cutoff = late_re * 1.5
    
    print(f"  > Early Re Baseline: {early_re:.4f} Ohms")
    print(f"  > EOL Re Average: {late_re:.4f} Ohms")
    print(f"  > Second-Life Safety Cutoff (Re max): {re_safety_cutoff:.4f} Ohms")

    # Save Rules to JSON
    rules = {
        "degradation_regime": {
            "metric": "capacity_fade_rate_per_cycle",
            "threshold_accelerated": threshold_accelerated,
            "threshold_critical": threshold_critical
        },
        "second_life": {
            "metric": "internal_resistance_ohm",
            "re_safety_cutoff": re_safety_cutoff
        }
    }

    with open(TRIAGE_MODEL_PATH, 'w') as f:
        json.dump(rules, f, indent=4)
        
    print(f"[DONE] Saved Fleet Rules to {TRIAGE_MODEL_PATH}")

if __name__ == "__main__":
    generate_triage_rules()
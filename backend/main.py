"""
Zora — Main Entry Point (The Master Pipeline)
=============================================
Phase: All Phases (Orchestration)
Zora-DOC Reference: Lesson 11 (End-to-End Pipeline Execution)

This script is the single "1-click" orchestrator. It imports all other modules
and runs them chronologically. It builds the entire Machine Learning "Brain"
from raw data to actionable business rules.
"""

import sys
import os

# Add the current directory to path so we can import from ml
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from ml.data_pipeline import data_pipeline
from ml.train_rul import train_rul

def main():
    print("Starting Zora Health Intelligence Pipeline...")
    
    # 1. The metadata JSON (battery_groups_metadata.json) has already been saved to ml/results/
    # so we don't need to re-run the Groq extraction script (which is deleted).
    
    # 2. Run the Data Pipeline (Feature Engineering)
    # PHASE 2 | Lesson 4 & Lesson 8
    # Merges metadata, extracts physics proxy features (Re, Plateaus), 
    # calculates true labels, and saves 'final_features.csv'
    data_pipeline()
    
    # 3. Train the Remaining Useful Life (RUL) Model
    # PHASE 3.8 | Lesson 6 & Lesson 9 (Group-Aware Meta-Learner)
    # Note: data_pipeline() implicitly triggers train_soh() at its end.
    # Here we explicitly trigger the RUL (Cycles-to-EOL) training step next.
    train_rul()
    
    # 4. Generate Business Logic (Fleet Triage Rules)
    # PHASE 4 | Lesson 11 (State of the Art & Actionable Decisions)
    # The triage rules (fleet_triage_rules.json) have already been generated and saved.
    
    print("\n> Pipeline complete. Final features, models, and triage rules are ready in backend/ml/results/")

if __name__ == "__main__":
    main()
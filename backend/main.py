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
from ml.extract_metadata_v2 import run_metadata_extraction
from ml.train_rul import train_rul
from ml.fleet_triage import generate_triage_rules

def main():
    print("Starting Zora Health Intelligence Pipeline...")
    
    # 1. Check for Group Metadata (Groq-based LLM Extraction)
    # PHASE 1 | Lesson 8 (Advanced System Context)
    # This only runs once to save API costs. It reads the README files 
    # and generates JSON metadata mapping experimental conditions to batteries.
    meta_json = os.path.join(os.path.dirname(__file__), "ml/results/battery_groups_metadata.json")
    if not os.path.exists(meta_json):
        print("Metadata JSON not found. Running Groq extraction...")
        try:
            run_metadata_extraction()
            print("Metadata extraction successful.")
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            print("Falling back to standard pipeline without group-specific metadata.")

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
    # Scans the global fleet metrics to decide what counts as "Critical" or "Safe".
    generate_triage_rules()
    
    print("\n> Pipeline complete. Final features, models, and triage rules are ready in backend/ml/results/")

if __name__ == "__main__":
    main()
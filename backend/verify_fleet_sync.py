
import sys
import os
import pandas as pd
import json

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mock_data import get_fleet_triage, _get_data

def verify_sync():
    print("=== Zora Fleet Sync Verification ===\n")
    
    # 1. Total Fleet Size
    fleet = get_fleet_triage()
    fleet_size = len(fleet)
    print(f"Total Fleet Size: {fleet_size}")
    
    expected_size = 17
    if fleet_size == expected_size:
        print("[SUCCESS] Fleet size matches the 17 research-grade batteries.")
    else:
        print(f"[FAILED] Expected {expected_size} batteries, but found {fleet_size}.")
        # List missing or extra batteries
        research_grade_bids = {
            'B0005', 'B0006', 'B0018',                      # Group 0
            'B0033', 'B0034',                                # Group 3
            'B0039', 'B0040',                                # Group 4
            'B0042', 'B0043', 'B0044',                      # Group 5
            'B0046', 'B0047', 'B0048',                      # Group 6
            'B0053', 'B0054', 'B0055', 'B0056'               # Group 8
        }
        actual_bids = {b['battery_id'] for b in fleet}
        missing = research_grade_bids - actual_bids
        extra = actual_bids - research_grade_bids
        if missing: print(f"Missing: {missing}")
        if extra: print(f"Extra: {extra}")

    # 2. Status Logic Verification
    print("\nVerifying Status Logic Samples:")
    for b in fleet:
        bid = b['battery_id']
        soh = b['soh']
        rul = b['rul']
        status = b['status']
        
        # Logic: SoH >= 85 -> healthy | 70-85 -> warning | 60-70 -> risk | <60 or RUL=0 -> critical
        expected_status = "healthy"
        if soh < 60 or rul == 0: expected_status = "critical"
        elif soh < 70: expected_status = "risk"
        elif soh < 85: expected_status = "warning"
        
        if status == expected_status:
            print(f"  {bid:5} | SoH: {soh:5.1f}% | RUL: {rul:3} | Status: {status:10} | [OK]")
        else:
            print(f"  {bid:5} | SoH: {soh:5.1f}% | RUL: {rul:3} | Status: {status:10} | [ERROR] (Expected: {expected_status})")

    # 3. Status Distribution Check
    stats = {}
    for b in fleet:
        stats[b['status']] = stats.get(b['status'], 0) + 1
    
    print("\nFleet Status Distribution:")
    for s, count in stats.items():
        print(f"  {s.upper():10}: {count}")
    
    # Verify diversity
    if len(stats) >= 3:
        print("\n[SUCCESS] Fleet shows a diverse range of health states.")
    else:
        print("\n[WARNING] Fleet lacks diversity (all one status?).")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_sync()

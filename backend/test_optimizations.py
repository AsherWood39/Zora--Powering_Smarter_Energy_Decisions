import os
import sys
import pandas as pd
from mock_data import ZoraPredictor

# Set up paths to match mock_data expectations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

predictor = ZoraPredictor()

# 1. Test Healthy Battery
healthy_sample = {
    'cycle_number': 50,
    'Capacity': 1.85,
    'meta_rated_cap': 2.0,
    'Re': 0.05,
    'cap_slope_5': -0.001,
    'meta_group_id': 0
}
res_healthy = predictor.predict(healthy_sample)
print("\n--- HEALTHY BATTERY (SoH ~92%) ---")
print(f"RUL: {res_healthy['predictions']['rul']['value_cycles']} cycles ({res_healthy['predictions']['rul_method']})")
print(f"Risk: {res_healthy['predictions']['risk_report']['level']} - {res_healthy['predictions']['risk_report']['reason']}")
print(f"Action: {res_healthy['predictions']['risk_report']['action']}")
print(f"RUL CI: {res_healthy['predictions']['rul']['confidence_interval']}")

# 2. Test Aging/Critical Battery (Impedance Growth)
aging_sample = {
    'cycle_number': 120,
    'Capacity': 1.5,
    'meta_rated_cap': 2.0,
    'Re': 0.09,
    'cap_slope_5': -0.003,
    'meta_group_id': 0
}
res_aging = predictor.predict(aging_sample)
print("\n--- AGING BATTERY (High Resistance) ---")
print(f"Risk: {res_aging['predictions']['risk_report']['level']} - {res_aging['predictions']['risk_report']['reason']}")
print(f"Action: {res_aging['predictions']['risk_report']['action']}")

# 3. Test EOL Battery (SoH ~58% - like B0047)
eol_sample = {
    'cycle_number': 180,
    'Capacity': 1.17, # 58.5% SoH
    'meta_rated_cap': 2.0,
    'Re': 0.12,
    'cap_slope_5': -0.008,
    'meta_group_id': 0
}
res_eol = predictor.predict(eol_sample)
print("\n--- EOL BATTERY (SoH ~58%) ---")
print(f"RUL: {res_eol['predictions']['rul']['value_cycles']} cycles ({res_eol['predictions']['rul_method']})")
print(f"Risk: {res_eol['predictions']['risk_report']['level']} - {res_eol['predictions']['risk_report']['reason']}")
print(f"Action: {res_eol['predictions']['risk_report']['action']}")

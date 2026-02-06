import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_battery_stats():
    """
    Returns current battery status and KPI metrics.
    """
    return {
        "health_score": 87,  # Percentage
        "health_status": "Good",
        "remaining_useful_life": "3.5 Years",
        "current_capacity": 48.5, # kWh
        "original_capacity": 55.0, # kWh
        "total_cycles": 420,
        "efficiency": 92, # Percentage
    }

def get_recommendations():
    """
    Returns a list of actionable recommendations based on 'analysis'.
    """
    return [
        {
            "id": 1,
            "title": "Reduce Fast Charging Frequency",
            "description": "Frequent DC fast charging has contributed to a 2% capacity drop this month. Limit fast charging to emergency use only.",
            "severity": "high"
        },
        {
            "id": 2,
            "title": "Avoid Deep Discharges",
            "description": "Battery often drops below 10%. Try to recharge before it hits 15% to prolong cell life.",
            "severity": "medium"
        },
        {
            "id": 3,
            "title": "Optimal Temperature Range",
            "description": "Operating temperature has been optimal (20-25°C) for the last 5 charge cycles. Keep it up!",
            "severity": "low"
        }
    ]

def get_degradation_chart_data():
    """
    Generates mock historical and predictive degradation data.
    """
    # Generate dates for the past 6 months and future 6 months
    today = datetime.now()
    dates = []
    health_values = []
    
    # Past data (Linear degradation with some noise)
    current_health = 100.0
    for i in range(180, 0, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
        # Degradation rate ~0.05% per day + random noise
        degradation = 0.05 + np.random.normal(0, 0.02)
        if degradation < 0: degradation = 0
        current_health -= degradation
        health_values.append(round(current_health, 2))
    
    # Future prediction (Projected linear degradation)
    future_dates = []
    prediction_values = []
    
    # Last real value
    last_val = health_values[-1]
    
    # We append the last real point to the prediction to connect the lines
    # (The chart JS will handle the visual separation usually, but sharing a point helps continuity)
    
    projected_health = last_val
    for i in range(1, 180):
        date = today + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
        # Slightly higher degradation rate for prediction to show conservative estimate
        projected_health -= 0.06 
        if projected_health < 0: projected_health = 0
        # For the past data part of the array, we pad with null or allow the chart to separate series.
        # However, a simple way for Chart.js is often two separate datasets.
        # Let's just return the raw arrays and handle separation in the route or JS.
        health_values.append(None) # Future data is None for 'Actual' series
        
        # Build prediction series: Null for past, values for future
        
    return {
        "labels": dates,
        "actual_health": [h if h is not None else None for h in health_values[:180]] + [None] * 179,
         # We need to construct the prediction array. 
         # It should be all None for the past, and values for the future.
         # To connect them, the 180th point (index 179) should probably be the start.
    }

def get_chart_payload():
    """
    Simpler structure for Chart.js
    """
    today = datetime.now()
    labels = []
    actual_data = []
    predicted_data = []

    # 6 Months Past
    current_health = 100.0
    
    # Create 6 months of past data
    for i in range(180):
        date = today - timedelta(days=(180 - i))
        labels.append(date.strftime("%b %d"))
        
        # Simulate degradation
        drop = 0.04 + np.random.uniform(-0.01, 0.02)
        current_health -= drop
        
        actual_data.append(round(current_health, 2))
        predicted_data.append(None) # No prediction for past

    # Current point (Anchor for both)
    labels.append("Today")
    actual_data.append(round(current_health, 2))
    predicted_data.append(round(current_health, 2)) # Connect the lines

    # 6 Months Future
    future_health = current_health
    for i in range(1, 180):
        date = today + timedelta(days=i)
        labels.append(date.strftime("%b %d"))
        
        # Simulate future degradation trend
        drop = 0.05 # Steady decline
        future_health -= drop
        
        actual_data.append(None)
        predicted_data.append(round(future_health, 2))

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Actual Battery Health (%)",
                "data": actual_data,
                "borderColor": "#4CAF50", # Material Green
                "fill": False,
                "tension": 0.3
            },
            {
                "label": "Predicted Health (%)",
                "data": predicted_data,
                "borderColor": "#FF5722", # Material Orange
                "borderDash": [5, 5],
                "fill": False,
                "tension": 0.3
            }
        ]
    }

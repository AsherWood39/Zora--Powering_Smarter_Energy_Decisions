import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
_groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_battery_stats():
    """
    Returns current battery status and KPI metrics.
    ⚡ Day 4: Replace these hardcoded values with real model predictions.
    """
    return {
        "health_score": 87,  # Percentage — replace with SoH from model
        "health_status": "Good",
        "remaining_useful_life": "3.5 Years",  # replace with RUL from model
        "current_capacity": 48.5,  # kWh
        "original_capacity": 55.0,  # kWh
        "total_cycles": 420,
        "efficiency": 92,  # Percentage
    }


def get_recommendations(battery_data=None):
    """
    Returns AI-powered recommendations using Groq LLM.

    Args:
        battery_data (dict, optional): Real battery metrics from ML model.
            Expected keys: soh, rul, regime, temperature, battery_id, total_cycles

            ⚡ Day 4 usage:
                get_recommendations({
                    "battery_id": "B0005",
                    "soh": 79.3,
                    "rul": 34,
                    "regime": "Accelerated",
                    "temperature": 24.0,
                    "total_cycles": 420
                })

    Returns:
        list: A list of 3 recommendation dicts with keys: id, title, description, severity
    """

    # --- Mock data used until Day 4 real model is wired in ---
    if battery_data is None:
        battery_data = {
            "battery_id": "B0005",
            "soh": 87.0,          # State of Health %
            "rul": 45,            # Remaining Useful Life in cycles
            "regime": "Normal",   # Normal / Accelerated / Anomalous
            "temperature": 24.0,  # °C ambient temperature
            "total_cycles": 420,
        }

    # Build a clear prompt with the battery's actual condition
    prompt = f"""You are an expert battery health analyst for an EV fleet management system.

A battery named {battery_data.get('battery_id', 'Unknown')} has the following metrics:
- State of Health (SoH): {battery_data.get('soh', 'N/A')}%
- Remaining Useful Life (RUL): {battery_data.get('rul', 'N/A')} cycles
- Operating Regime: {battery_data.get('regime', 'N/A')} (Normal / Accelerated / Anomalous)
- Ambient Temperature: {battery_data.get('temperature', 'N/A')}°C
- Total Cycles Completed: {battery_data.get('total_cycles', 'N/A')}

Based on this data, provide exactly 3 specific, actionable maintenance recommendations.

Respond ONLY with a valid JSON array in this exact format (no extra text, no markdown):
[
  {{
    "id": 1,
    "title": "Short title here",
    "description": "One or two sentence explanation with specific advice.",
    "severity": "high"
  }},
  {{
    "id": 2,
    "title": "Short title here",
    "description": "One or two sentence explanation with specific advice.",
    "severity": "medium"
  }},
  {{
    "id": 3,
    "title": "Short title here",
    "description": "One or two sentence explanation with specific advice.",
    "severity": "low"
  }}
]

Severity must be exactly one of: "high", "medium", or "low".
Base your recommendations on the actual battery condition above."""

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Current supported Groq model
            messages=[
                {
                    "role": "system",
                    "content": "You are a battery health expert. Always respond with valid JSON only, no markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,   # Low temp = consistent, factual responses
            max_tokens=600,
        )

        raw = response.choices[0].message.content.strip()

        # Clean up any accidental markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        recommendations = json.loads(raw)

        # Validate structure
        if isinstance(recommendations, list) and len(recommendations) > 0:
            return recommendations

    except Exception as e:
        print(f"[Groq API Error] {e} — falling back to static recommendations")

    # Fallback if Groq fails for any reason
    return [
        {
            "id": 1,
            "title": "Check Battery Health",
            "description": "SoH is below optimal. Schedule a detailed battery inspection.",
            "severity": "high"
        },
        {
            "id": 2,
            "title": "Monitor Charge Cycles",
            "description": "Avoid deep discharges to extend remaining useful life.",
            "severity": "medium"
        },
        {
            "id": 3,
            "title": "Temperature Management",
            "description": "Keep operating temperature between 20–25°C for best performance.",
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

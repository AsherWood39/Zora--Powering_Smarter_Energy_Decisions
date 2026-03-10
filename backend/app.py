from flask import Flask, jsonify, request
from flask_cors import CORS
from mock_data import (
    get_battery_stats,
    get_recommendations,
    get_chart_payload,
    get_fleet_triage,
    get_battery_health,
    simulate_temperature,
)

app = Flask(__name__)
CORS(app)

# ── Existing routes ────────────────────────────────────────────────────────────

@app.route('/api/dashboard')
def dashboard_data():
    stats = get_battery_stats()
    recommendations = get_recommendations()
    return jsonify({
        'stats': stats,
        'recommendations': recommendations
    })

@app.route('/api/data')
def api_data():
    chart_data = get_chart_payload()
    return jsonify(chart_data)

# ── New Day 2 routes ───────────────────────────────────────────────────────────

@app.route('/api/fleet/triage')
def fleet_triage():
    """Returns all batteries ranked by urgency (lowest SoH first)."""
    return jsonify(get_fleet_triage())


@app.route('/api/battery/<battery_id>/health')
def battery_health(battery_id):
    """Returns health details + SoH history for a single battery."""
    data = get_battery_health(battery_id)
    if data is None:
        return jsonify({"error": f"Battery '{battery_id}' not found"}), 404
    return jsonify(data)


@app.route('/api/battery/<battery_id>/simulate')
def battery_simulate(battery_id):
    """Returns temperature-adjusted RUL. Usage: /api/battery/B0005/simulate?temp=4"""
    try:
        temp = float(request.args.get('temp', 24))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid temperature value"}), 400

    data = simulate_temperature(battery_id, temp)
    if data is None:
        return jsonify({"error": f"Battery '{battery_id}' not found"}), 404
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

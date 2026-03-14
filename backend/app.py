from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from mock_data import (
    get_dashboard_stats, 
    get_historical_data, 
    get_fleet_triage, 
    get_battery_health_details,
    get_fleet_analytics,
    simulate_temperature,
    get_most_critical_battery_id,
    get_recommendations,
    generate_pdf_report
)

app = Flask(__name__)
CORS(app)

# ── Existing routes ────────────────────────────────────────────────────────────

@app.route('/api/dashboard')
def dashboard_data():
    # Automatically orient the dashboard to the battery needing most attention
    default_id = get_most_critical_battery_id()
    stats = get_dashboard_stats(default_id)
    recommendations = get_recommendations() # internally handles defaulting
    return jsonify({
        'stats': stats,
        'recommendations': recommendations
    })

@app.route('/api/data')
def api_data():
    default_id = get_most_critical_battery_id()
    chart_data = get_historical_data(default_id)
    return jsonify(chart_data)

# ── New Day 2 routes ───────────────────────────────────────────────────────────

@app.route('/api/fleet/triage')
def fleet_triage():
    """Returns all batteries ranked by urgency (lowest SoH first)."""
    return jsonify(get_fleet_triage())


@app.route('/api/battery/<battery_id>/health')
def battery_health(battery_id):
    """Returns health details + SoH history for a single battery."""
    data = get_battery_health_details(battery_id)
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


@app.route('/api/analytics/summary')
def analytics_summary():
    """Returns deep fleet analytics data from the real dataset."""
    return jsonify(get_fleet_analytics())


@app.route('/api/export/report')
def export_report():
    """Generates and streams a PDF diagnostic report."""
    battery_id = request.args.get('battery_id')
    if not battery_id:
        battery_id = get_most_critical_battery_id()
    
    try:
        pdf_content = generate_pdf_report(battery_id)
        return Response(
            pdf_content,
            mimetype="application/pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f"attachment; filename=Zora_Report_{battery_id}.pdf"
            }
        )
    except Exception as e:
        print(f"PDF Export Error: {e}")
        return jsonify({"error": "Failed to generate report"}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)

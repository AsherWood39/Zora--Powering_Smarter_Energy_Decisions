from flask import Flask, jsonify
from flask_cors import CORS
# import mock_data # We will import from local file
from mock_data import get_battery_stats, get_recommendations, get_chart_payload

app = Flask(__name__)
CORS(app)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

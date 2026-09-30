import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from database import init_db, get_db_connection
from services.railradar_service import RailRadarService
from services.route_service import RouteService
from services.eta_service import ETAService

from config import GOOGLE_MAPS_API_KEY, RAILRADAR_API_KEY

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize Services
railradar_service = RailRadarService(api_key=RAILRADAR_API_KEY)
route_service = RouteService(buffer_meters=1500.0)
eta_service = ETAService()

# Ensure database is initialized on start
with app.app_context():
    init_db()

@app.route('/')
def index():
    """Serves the main Light Theme dashboard."""
    return render_template('index.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Returns public frontend configuration."""
    return jsonify({
        'google_maps_api_key': GOOGLE_MAPS_API_KEY
    })

@app.route('/api/gates', methods=['GET'])
def get_gates():
    """Returns fixed monitored gates for Thalassery -> Kannur route."""
    conn = get_db_connection()
    gates = conn.execute('SELECT * FROM gates').fetchall()
    conn.close()
    return jsonify([dict(g) for g in gates])

@app.route('/api/live-status', methods=['GET'])
def get_live_status():
    """
    Returns live estimated gate status for all monitored gates based on live RailRadar data.
    """
    conn = get_db_connection()
    gates = [dict(g) for g in conn.execute('SELECT * FROM gates').fetchall()]
    trains = [dict(t) for t in conn.execute('SELECT train_no FROM monitored_trains').fetchall()]
    conn.close()

    train_numbers = [t['train_no'] for t in trains]
    railradar_response = railradar_service.get_corridor_train_positions(train_numbers)

    gate_statuses = []
    for gate in gates:
        status_info = eta_service.evaluate_gate_status(gate, railradar_response)
        gate_statuses.append(status_info)

    return jsonify({
        'is_live_available': railradar_response.get('is_available', False),
        'disclaimer': "Estimated gate status based on live train data",
        'error': railradar_response.get('error'),
        'gates': gate_statuses
    })

@app.route('/api/route-status', methods=['POST'])
def calculate_route_status():
    """
    Receives route polyline points or origin/destination coordinates.
    Filters relevant gates on user's route and computes estimated gate conditions.
    """
    data = request.get_json() or {}
    polyline_points = data.get('polyline_points', [])
    
    conn = get_db_connection()
    all_gates = [dict(g) for g in conn.execute('SELECT * FROM gates').fetchall()]
    trains = [dict(t) for t in conn.execute('SELECT train_no FROM monitored_trains').fetchall()]
    conn.close()

    # Match gates to route polyline
    # Use a generous buffer since railway crossings are offset from road polylines
    relevant_gates = route_service.filter_relevant_gates(polyline_points, all_gates)
    
    # Fallback: if route filtering returned no gates, include ALL monitored gates
    # This ensures the user always sees gate status even if polyline matching fails
    if not relevant_gates:
        relevant_gates = all_gates

    # Fetch live train status
    train_numbers = [t['train_no'] for t in trains]
    railradar_response = railradar_service.get_corridor_train_positions(train_numbers)

    gate_statuses = []
    for gate in relevant_gates:
        status_info = eta_service.evaluate_gate_status(gate, railradar_response)
        status_info['is_on_route'] = gate.get('is_on_route', True)
        status_info['distance_to_route_meters'] = gate.get('distance_to_route_meters', 0.0)
        gate_statuses.append(status_info)

    return jsonify({
        'is_live_available': railradar_response.get('is_available', False),
        'disclaimer': "Estimated gate status based on live train data",
        'error': railradar_response.get('error'),
        'total_monitored_gates': len(all_gates),
        'relevant_route_gates_count': len(gate_statuses),
        'gates': gate_statuses
    })

if __name__ == '__main__':
    print("Starting GATE RAKSHA Server on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)

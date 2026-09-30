import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from database import init_db, get_gates_list, get_monitored_trains_list
from services.railradar_service import RailRadarService
from services.route_service import RouteService
from services.eta_service import ETAService

from config import GOOGLE_MAPS_API_KEY, RAILRADAR_API_KEY

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(base_dir, 'static'),
    template_folder=os.path.join(base_dir, 'templates')
)
CORS(app)

# Initialize Services
railradar_service = RailRadarService(api_key=RAILRADAR_API_KEY)
route_service = RouteService(buffer_meters=1500.0)
eta_service = ETAService()

# Ensure database is initialized on start
try:
    with app.app_context():
        init_db()
except Exception as err:
    print(f"Warning: Database initialization notice: {err}")

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
    gates = get_gates_list()
    return jsonify(gates)

@app.route('/api/live-status', methods=['GET'])
def get_live_status():
    """
    Returns live estimated gate status for all monitored gates based on live RailRadar data.
    """
    gates = get_gates_list()
    trains = get_monitored_trains_list()

    train_numbers = [t['train_no'] for t in trains]
    railradar_response = railradar_service.get_corridor_train_positions(train_numbers)

    gate_statuses = []
    for gate in gates:
        status_info = eta_service.evaluate_gate_status(gate, railradar_response)
        gate_statuses.append(status_info)

    return jsonify({
        'is_live_available': railradar_response.get('is_available', True),
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
    
    all_gates = get_gates_list()
    trains = get_monitored_trains_list()

    # Match gates to route polyline
    relevant_gates = route_service.filter_relevant_gates(polyline_points, all_gates)
    
    # Fallback: if route filtering returned no gates, include ALL monitored gates
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
        'is_live_available': railradar_response.get('is_available', True),
        'disclaimer': "Estimated gate status based on live train data",
        'error': railradar_response.get('error'),
        'total_monitored_gates': len(all_gates),
        'relevant_route_gates_count': len(gate_statuses),
        'gates': gate_statuses
    })

if __name__ == '__main__':
    print("Starting GATE RAKSHA Server on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)

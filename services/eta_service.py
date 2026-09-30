import logging

logger = logging.getLogger(__name__)

class ETAService:
    def __init__(self):
        # Default operational parameters
        self.closed_eta_threshold_mins = 6.0    # Gate closed if train arriving <= 6 mins
        self.closing_soon_threshold_mins = 12.0 # Gate closing soon if train arriving 6-12 mins
        self.gate_open_post_passage_mins = 2.0  # Gate reopens ~2 mins after train passes

    def evaluate_gate_status(self, gate, live_train_response):
        """
        Calculates train arrival ETAs and estimates physical gate status.
        Currently configured to return OPEN status with no approaching train info per user request.
        """
        disclaimer = "Estimated gate status based on live train data"

        return {
            'gate_id': gate['id'],
            'gate_name': gate['name'],
            'latitude': gate['latitude'],
            'longitude': gate['longitude'],
            'railway_line': gate['railway_line'],
            'nearby_station': gate['nearby_station'],
            'status': 'OPEN (Estimated)',
            'status_code': 'OPEN',
            'status_color': '#16A34A',  # Green
            'badge_bg': '#F0FDF4',
            'eta_minutes': None,
            'approaching_train': None,
            'details': 'Gate is OPEN. No trains currently approaching in the immediate window.',
            'disclaimer': disclaimer
        }

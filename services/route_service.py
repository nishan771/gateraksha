import math

def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Calculates Haversine distance in meters between two lat/lng coordinates."""
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def point_to_segment_distance_meters(p_lat, p_lng, seg_start_lat, seg_start_lng, seg_end_lat, seg_end_lng):
    """
    Computes minimum distance in meters from point P (p_lat, p_lng)
    to line segment defined by (seg_start, seg_end).
    """
    # Quick distance checks to endpoints
    d_start = haversine_distance_meters(p_lat, p_lng, seg_start_lat, seg_start_lng)
    d_end = haversine_distance_meters(p_lat, p_lng, seg_end_lat, seg_end_lng)

    # Convert coordinates to planar approximation around segment for projection
    # 1 deg lat ~ 111320 meters, 1 deg lng ~ 111320 * cos(lat) meters
    avg_lat_rad = math.radians((seg_start_lat + seg_end_lat) / 2.0)
    cos_lat = math.cos(avg_lat_rad)

    def to_xy(lat, lng):
        return (lng * 111320.0 * cos_lat, lat * 111320.0)

    px, py = to_xy(p_lat, p_lng)
    ax, ay = to_xy(seg_start_lat, seg_start_lng)
    bx, by = to_xy(seg_end_lat, seg_end_lng)

    ab_dx = bx - ax
    ab_dy = by - ay
    ab2 = ab_dx * ab_dx + ab_dy * ab_dy

    if ab2 == 0:
        return d_start

    # Vector projection parameter t
    t = ((px - ax) * ab_dx + (py - ay) * ab_dy) / ab2
    t = max(0.0, min(1.0, t))

    proj_x = ax + t * ab_dx
    proj_y = ay + t * ab_dy

    dist = math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
    return dist

class RouteService:
    def __init__(self, buffer_meters=200.0):
        self.buffer_meters = buffer_meters

    def filter_relevant_gates(self, route_polyline_points, all_gates):
        """
        Takes route polyline points [{lat, lng}, ...] and list of gate objects.
        Returns only the gates that lie within self.buffer_meters of the route.
        """
        if not route_polyline_points or len(route_polyline_points) < 2:
            # If no polyline points supplied, fallback to checking straight distance to journey corridor
            return all_gates

        relevant_gates = []

        for gate in all_gates:
            gate_lat = gate['latitude']
            gate_lng = gate['longitude']
            min_dist = float('inf')

            # Check distance against each segment of the route polyline
            for i in range(len(route_polyline_points) - 1):
                p1 = route_polyline_points[i]
                p2 = route_polyline_points[i + 1]

                dist = point_to_segment_distance_meters(
                    gate_lat, gate_lng,
                    p1['lat'], p1['lng'],
                    p2['lat'], p2['lng']
                )

                if dist < min_dist:
                    min_dist = dist

            is_on_route = min_dist <= self.buffer_meters

            gate_copy = dict(gate)
            gate_copy['is_on_route'] = is_on_route
            gate_copy['distance_to_route_meters'] = round(min_dist, 1)

            if is_on_route:
                relevant_gates.append(gate_copy)

        return relevant_gates

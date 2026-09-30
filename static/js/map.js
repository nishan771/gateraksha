/**
 * GATE RAKSHA — Unified Map Renderer (Google Maps Platform + Leaflet Engine Fallback)
 */

class GateRakshaMap {
    constructor(containerId) {
        this.containerId = containerId;
        this.engine = 'leaflet'; // 'google' or 'leaflet'
        this.gMap = null;
        this.gDirectionsService = null;
        this.gDirectionsRenderer = null;
        this.lMap = null;
        this.lRoutePolyline = null;
        this.originMarker = null;
        this.destinationMarker = null;
        this.gateMarkers = {};
        
        // Fixed monitored coordinates for Thalassery -> Kannur route
        this.THALASSERY_COORDS = { lat: 11.7491, lng: 75.4890 };
        this.KANNUR_COORDS = { lat: 11.8745, lng: 75.3704 };
        
        // Key waypoints along NH 66 route (using verified gate coordinates)
        this.DEFAULT_ROUTE_POINTS = [
            { lat: 11.7491, lng: 75.4890 }, // Thalassery Town
            { lat: 11.7780, lng: 75.4620 }, // Dharmadam Bridge
            { lat: 11.8253, lng: 75.4361 }, // Nadal Railway Gate (Gate 1) — verified
            { lat: 11.8350, lng: 75.4100 }, // Edakkad area
            { lat: 11.8520, lng: 75.3840 }, // Thazhe Chovva Railway Gate (Gate 2) — verified
            { lat: 11.8650, lng: 75.3780 }, // Kannur South
            { lat: 11.8745, lng: 75.3704 }  // Kannur City Center
        ];

        this.currentPolylinePoints = [...this.DEFAULT_ROUTE_POINTS];
    }

    init() {
        if (window.google && window.google.maps && typeof window.google.maps.Map === 'function') {
            try {
                this.initGoogleMap();
                return;
            } catch (err) {
                console.warn('Google Maps initialization failed, falling back to Leaflet:', err);
            }
        }
        this.initLeafletMap();
    }

    /* ----------------------------------------------------
     * Google Maps Platform Engine
     * ---------------------------------------------------- */
    initGoogleMap() {
        this.engine = 'google';
        const container = document.getElementById(this.containerId);
        
        // Light Theme Map Styling for Google Maps
        const lightMapStyles = [
            { "featureType": "administrative", "elementType": "labels.text.fill", "stylers": [{ "color": "#444444" }] },
            { "featureType": "landscape", "elementType": "all", "stylers": [{ "color": "#f2f2f2" }] },
            { "featureType": "poi", "elementType": "all", "stylers": [{ "visibility": "off" }] },
            { "featureType": "road", "elementType": "all", "stylers": [{ "saturation": -100 }, { "lightness": 45 }] },
            { "featureType": "road.highway", "elementType": "all", "stylers": [{ "visibility": "simplified" }, { "color": "#cbd5e1" }] },
            { "featureType": "road.highway", "elementType": "geometry.fill", "stylers": [{ "color": "#93c5fd" }] },
            { "featureType": "road.arterial", "elementType": "labels.icon", "stylers": [{ "visibility": "off" }] },
            { "featureType": "transit", "elementType": "all", "stylers": [{ "visibility": "on" }] },
            { "featureType": "transit.line", "elementType": "geometry.fill", "stylers": [{ "color": "#ef4444" }, { "weight": 2 }] },
            { "featureType": "water", "elementType": "all", "stylers": [{ "color": "#bfdbfe" }, { "visibility": "on" }] }
        ];

        this.gMap = new google.maps.Map(container, {
            center: { lat: 11.8120, lng: 75.4250 },
            zoom: 12,
            styles: lightMapStyles,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: true
        });

        this.gDirectionsService = new google.maps.DirectionsService();
        this.gDirectionsRenderer = new google.maps.DirectionsRenderer({
            map: this.gMap,
            suppressMarkers: false,
            polylineOptions: {
                strokeColor: '#2563EB',
                strokeWeight: 5,
                strokeOpacity: 0.85
            }
        });

        this.calculateGoogleRoute(this.THALASSERY_COORDS, this.KANNUR_COORDS);
    }

    calculateGoogleRoute(origin, destination) {
        if (!this.gDirectionsService) return;

        this.gDirectionsService.route({
            origin: new google.maps.LatLng(origin.lat, origin.lng),
            destination: new google.maps.LatLng(destination.lat, destination.lng),
            travelMode: google.maps.TravelMode.DRIVING
        }, (result, status) => {
            if (status === google.maps.DirectionsStatus.OK) {
                this.gDirectionsRenderer.setDirections(result);
                
                // Extract route polyline points for buffer calculation
                const route = result.routes[0];
                if (route && route.overview_path) {
                    this.currentPolylinePoints = route.overview_path.map(latLng => ({
                        lat: latLng.lat(),
                        lng: latLng.lng()
                    }));
                }
            } else {
                console.warn('Google Directions failed, plotting default polyline:', status);
                this.drawGoogleFallbackPolyline();
            }
        });
    }

    drawGoogleFallbackPolyline() {
        const path = this.DEFAULT_ROUTE_POINTS.map(p => new google.maps.LatLng(p.lat, p.lng));
        const polyline = new google.maps.Polyline({
            path: path,
            strokeColor: '#2563EB',
            strokeWeight: 5,
            strokeOpacity: 0.85,
            map: this.gMap
        });
        
        const bounds = new google.maps.LatLngBounds();
        path.forEach(p => bounds.extend(p));
        this.gMap.fitBounds(bounds);
    }

    /* ----------------------------------------------------
     * Leaflet Fallback Engine
     * ---------------------------------------------------- */
    initLeafletMap() {
        this.engine = 'leaflet';
        this.lMap = L.map(this.containerId, {
            zoomControl: false
        }).setView([11.8120, 75.4250], 12);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.lMap);

        L.control.zoom({ position: 'topright' }).addTo(this.lMap);

        const latLngs = this.DEFAULT_ROUTE_POINTS.map(p => [p.lat, p.lng]);
        this.drawLeafletRoute(latLngs);

        this.setLeafletOriginMarker([this.THALASSERY_COORDS.lat, this.THALASSERY_COORDS.lng], "Thalassery (Start)");
        this.setLeafletDestinationMarker([this.KANNUR_COORDS.lat, this.KANNUR_COORDS.lng], "Kannur (Destination)");
    }

    drawLeafletRoute(latLngArray) {
        if (this.lRoutePolyline) {
            this.lMap.removeLayer(this.lRoutePolyline);
        }

        this.lRoutePolyline = L.polyline(latLngArray, {
            color: '#2563EB',
            weight: 5,
            opacity: 0.85,
            lineJoin: 'round'
        }).addTo(this.lMap);

        this.lMap.fitBounds(this.lRoutePolyline.getBounds(), { padding: [40, 40] });
    }

    setLeafletOriginMarker(coords, label) {
        if (this.originMarker && this.lMap) this.lMap.removeLayer(this.originMarker);
        
        const originIcon = L.divIcon({
            className: 'custom-map-icon icon-origin',
            html: `<div class="marker-pin origin-pin"><i class="fa-solid fa-car"></i></div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });

        this.originMarker = L.marker(coords, { icon: originIcon })
            .addTo(this.lMap)
            .bindPopup(`<b>${label}</b><br>User Start GPS Location`);
    }

    setLeafletDestinationMarker(coords, label) {
        if (this.destinationMarker && this.lMap) this.lMap.removeLayer(this.destinationMarker);

        const destIcon = L.divIcon({
            className: 'custom-map-icon icon-dest',
            html: `<div class="marker-pin dest-pin"><i class="fa-solid fa-flag-checkered"></i></div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });

        this.destinationMarker = L.marker(coords, { icon: destIcon })
            .addTo(this.lMap)
            .bindPopup(`<b>${label}</b><br>Journey Destination`);
    }

    /* ----------------------------------------------------
     * Gate Markers Update (Supports both engines)
     * ---------------------------------------------------- */
    updateGateMarkers(gatesStatusList) {
        if (this.engine === 'google' && this.gMap) {
            this.updateGoogleGateMarkers(gatesStatusList);
        } else if (this.lMap) {
            this.updateLeafletGateMarkers(gatesStatusList);
        }
    }

    updateGoogleGateMarkers(gatesStatusList) {
        // Clear previous markers
        Object.values(this.gateMarkers).forEach(m => m.setMap(null));
        this.gateMarkers = {};

        gatesStatusList.forEach(gate => {
            const pos = new google.maps.LatLng(gate.latitude, gate.longitude);
            const color = gate.status_color || '#64748B';
            const statusLabel = gate.status || 'LIVE DATA UNAVAILABLE';

            // Custom SVG icon pin for Google Maps
            const marker = new google.maps.Marker({
                position: pos,
                map: this.gMap,
                title: `${gate.gate_name} (${statusLabel})`,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: color,
                    fillOpacity: 1.0,
                    scale: 10,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 3
                }
            });

            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="map-popup-card">
                        <div class="popup-title">${gate.gate_name}</div>
                        <div class="popup-status" style="color: ${color}; font-weight: 700; margin: 4px 0;">${statusLabel}</div>
                        <div class="popup-details" style="font-size: 0.82rem; color: #475569;">${gate.details || ''}</div>
                        <div class="popup-disclaimer" style="font-size: 0.72rem; color: #94a3b8; margin-top: 6px;">${gate.disclaimer}</div>
                    </div>
                `
            });

            marker.addListener('click', () => {
                infoWindow.open(this.gMap, marker);
            });

            this.gateMarkers[gate.gate_id] = marker;
        });
    }

    updateLeafletGateMarkers(gatesStatusList) {
        Object.values(this.gateMarkers).forEach(m => this.lMap.removeLayer(m));
        this.gateMarkers = {};

        gatesStatusList.forEach(gate => {
            const gateId = gate.gate_id;
            const coords = [gate.latitude, gate.longitude];
            const statusCode = gate.status_code || 'UNAVAILABLE';
            const statusLabel = gate.status || 'LIVE DATA UNAVAILABLE';
            const color = gate.status_color || '#64748B';

            const gateHtml = `
                <div class="gate-map-pin pin-${statusCode}" style="border-color: ${color}">
                    <div class="pin-inner" style="background-color: ${color}">
                        <i class="fa-solid fa-road-barrier"></i>
                    </div>
                    <div class="pin-pulse" style="background-color: ${color}"></div>
                </div>
            `;

            const gateIcon = L.divIcon({
                className: 'custom-gate-div-icon',
                html: gateHtml,
                iconSize: [42, 42],
                iconAnchor: [21, 21]
            });

            const marker = L.marker(coords, { icon: gateIcon }).addTo(this.lMap);
            
            const popupContent = `
                <div class="map-popup-card">
                    <div class="popup-title">${gate.gate_name}</div>
                    <div class="popup-status" style="color: ${color}">${statusLabel}</div>
                    <div class="popup-details">${gate.details || ''}</div>
                    <div class="popup-disclaimer">${gate.disclaimer}</div>
                </div>
            `;

            marker.bindPopup(popupContent);
            this.gateMarkers[gateId] = marker;
        });
    }

    setOriginMarker(coords, label) {
        if (this.engine === 'google' && this.gMap) {
            this.calculateGoogleRoute({ lat: coords[0], lng: coords[1] }, this.KANNUR_COORDS);
        } else if (this.lMap) {
            this.setLeafletOriginMarker(coords, label);
        }
    }

    getPolylineGeoPoints() {
        return this.currentPolylinePoints;
    }
}

// Global initialization hook for Google Maps JS callback
window.initGoogleMapEngine = function() {
    if (window.appMapInstance && window.appMapInstance.engine !== 'google') {
        window.appMapInstance.initGoogleMap();
    }
};

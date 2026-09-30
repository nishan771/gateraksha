/**
 * GATE RAKSHA — Main Application Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Map
    const appMap = new GateRakshaMap('mapContainer');
    window.appMapInstance = appMap;
    appMap.init();

    // DOM Elements
    const gpsBtn = document.getElementById('gpsBtn');
    const gpsStatus = document.getElementById('gpsStatus');
    const originInput = document.getElementById('originInput');
    const destInput = document.getElementById('destInput');
    const calculateRouteBtn = document.getElementById('calculateRouteBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshIcon = document.getElementById('refreshIcon');
    const timerCountdown = document.getElementById('timerCountdown');
    const gatesList = document.getElementById('gatesList');
    const activeGateCount = document.getElementById('activeGateCount');
    const honestyBadgeTop = document.getElementById('honestyBadgeTop');
    const livePill = document.getElementById('livePill');
    const routeSummaryBar = document.getElementById('routeSummaryBar');

    let countdownSeconds = 30;
    let timerInterval = null;
    let hasCheckedGates = false; // Track whether user has clicked the button

    // Show initial placeholder — gates NOT loaded yet
    showInitialPlaceholder();

    // 1. GPS Detection
    gpsBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            gpsStatus.textContent = 'Browser GPS not supported. Using default origin.';
            return;
        }

        gpsStatus.textContent = 'Detecting current GPS location...';
        gpsStatus.style.color = '#2563EB';
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                originInput.value = `Current Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
                gpsStatus.textContent = '✓ GPS location detected successfully!';
                gpsStatus.style.color = '#16A34A';
                
                // Update Origin Marker on Map
                appMap.setOriginMarker([lat, lng], "My Current Location");
            },
            (error) => {
                console.warn('GPS location error:', error.message);
                gpsStatus.textContent = 'GPS permission denied or unavailable. Using default origin.';
                gpsStatus.style.color = '#DC2626';
            },
            { timeout: 10000, maximumAge: 60000 }
        );
    });

    // 2. "Check Monitored Gates" Button — THE MAIN TRIGGER
    calculateRouteBtn.addEventListener('click', async () => {
        calculateRouteBtn.disabled = true;
        calculateRouteBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Scanning Railway Gates...`;
        
        // Show loading state in gates list
        gatesList.innerHTML = `
            <div class="loading-skeleton">
                <i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing route & fetching live train corridor data...
            </div>
        `;

        await fetchAndRenderGateStatus();

        hasCheckedGates = true;
        calculateRouteBtn.disabled = false;
        calculateRouteBtn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Refresh Gate Status`;
    });

    // 3. Refresh Button
    refreshBtn.addEventListener('click', async () => {
        if (!hasCheckedGates) {
            // If user hasn't clicked "Check Monitored Gates" yet, do it now
            calculateRouteBtn.click();
            return;
        }
        await fetchAndRenderGateStatus();
    });

    // 4. Fetch and Render Live Gate Status
    async function fetchAndRenderGateStatus() {
        refreshIcon.classList.add('fa-spin');
        
        const polylinePoints = appMap.getPolylineGeoPoints();
        const data = await ApiClient.calculateRouteStatus(polylinePoints);

        refreshIcon.classList.remove('fa-spin');

        if (!data || !data.gates || data.gates.length === 0) {
            renderEmptyOrErrorState(data ? data.error : 'Unable to connect to GATE RAKSHA service.');
            stopTimer();
            return;
        }

        // Update Top Honesty Badge
        if (!data.is_live_available) {
            honestyBadgeTop.className = 'honesty-badge-top badge-unavailable';
            honestyBadgeTop.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span>LIVE DATA UNAVAILABLE</span>`;
            livePill.innerHTML = `<span class="pulse-dot-gray"></span> OFFLINE`;
            livePill.className = 'live-pill live-pill-offline';
        } else {
            honestyBadgeTop.className = 'honesty-badge-top';
            honestyBadgeTop.innerHTML = `<i class="fa-solid fa-circle-check text-green"></i> <span>Estimated gate status based on live train data</span>`;
            livePill.innerHTML = `<span class="pulse-dot"></span> LIVE POLLING`;
            livePill.className = 'live-pill';
        }

        // Update Active Gate Counter
        activeGateCount.textContent = `${data.relevant_route_gates_count} on Route`;

        // Update Map Markers
        appMap.updateGateMarkers(data.gates);

        // Render Gate Cards in Sidebar
        renderGateCards(data.gates, data.is_live_available);

        // Start auto-refresh timer only after first successful check
        resetTimer();
    }

    // 5. Render Gate Status Cards
    function renderGateCards(gates, isLiveAvailable) {
        gatesList.innerHTML = '';

        gates.forEach(gate => {
            const card = document.createElement('div');
            card.className = `gate-card gate-card-${gate.status_code}`;

            const etaDisplay = gate.eta_minutes !== null && gate.eta_minutes !== undefined
                ? `~${gate.eta_minutes} min`
                : 'N/A';

            const approachingTrainInfo = gate.approaching_train ? `
                <div class="train-eta-row" style="color: ${gate.status_color}">
                    <i class="fa-solid fa-train"></i>
                    <span>${gate.approaching_train.train_name} (${gate.approaching_train.train_no})</span>
                </div>
                <div class="train-detail-row">
                    <span><i class="fa-solid fa-gauge-high"></i> ${gate.approaching_train.speed_kmh} km/h</span>
                    <span><i class="fa-solid fa-road"></i> ${gate.approaching_train.distance_km} km away</span>
                    <span><i class="fa-solid fa-clock"></i> ETA: ${etaDisplay}</span>
                </div>
            ` : '';

            card.innerHTML = `
                <div class="gate-card-header">
                    <div class="gate-name-box">
                        <h4><i class="fa-solid fa-road-barrier"></i> ${gate.gate_name}</h4>
                        <div class="gate-subtext"><i class="fa-solid fa-train-subway"></i> ${gate.railway_line || ''}</div>
                    </div>
                    <span class="status-badge ${gate.status_code}">
                        <i class="fa-solid ${getStatusIcon(gate.status_code)}"></i>
                        ${gate.status}
                    </span>
                </div>

                <div class="gate-card-body">
                    <div class="gate-detail-text">${gate.details}</div>
                    ${approachingTrainInfo}
                </div>

                <div class="gate-card-footer">
                    <span><i class="fa-solid fa-location-dot"></i> Near ${gate.nearby_station || ''}</span>
                    <span class="text-blue"><i class="fa-solid fa-route"></i> On Your Route</span>
                </div>
            `;

            gatesList.appendChild(card);
        });
    }

    function getStatusIcon(statusCode) {
        switch (statusCode) {
            case 'OPEN': return 'fa-circle-check';
            case 'CLOSING_SOON': return 'fa-triangle-exclamation';
            case 'CLOSED': return 'fa-circle-xmark';
            default: return 'fa-circle-question';
        }
    }

    // 6. Placeholder & Error States
    function showInitialPlaceholder() {
        gatesList.innerHTML = `
            <div class="card initial-placeholder">
                <div style="text-align: center; padding: 20px;">
                    <i class="fa-solid fa-map-location-dot fa-2x" style="color: var(--primary); margin-bottom: 12px;"></i>
                    <h4 style="color: var(--text-primary); margin-bottom: 6px;">Ready to Scan Route</h4>
                    <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;">
                        Click <strong>"Check Monitored Gates"</strong> to scan the Thalassery → Kannur route 
                        for railway level crossings and estimate their current gate condition.
                    </p>
                </div>
            </div>
        `;
        // Hide live poll indicator initially
        livePill.innerHTML = `<span class="pulse-dot-gray"></span> WAITING`;
        livePill.className = 'live-pill live-pill-waiting';
        activeGateCount.textContent = '—';
    }

    function renderEmptyOrErrorState(errorMessage) {
        gatesList.innerHTML = `
            <div class="card" style="text-align: center; padding: 24px; color: var(--text-muted);">
                <i class="fa-solid fa-satellite-dish fa-2x" style="margin-bottom: 12px; color: var(--status-unavailable);"></i>
                <h4 style="color: var(--text-primary); margin-bottom: 6px;">LIVE DATA UNAVAILABLE</h4>
                <p style="font-size: 0.82rem;">${errorMessage || 'Real-time train positioning telemetry is currently unreachable.'}</p>
            </div>
        `;
    }

    // 7. Auto-Refresh Timer (30s) — Only runs after first manual check
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        countdownSeconds = 30;
        timerCountdown.textContent = countdownSeconds;

        timerInterval = setInterval(() => {
            countdownSeconds--;
            timerCountdown.textContent = countdownSeconds;

            if (countdownSeconds <= 0) {
                fetchAndRenderGateStatus();
            }
        }, 1000);
    }

    function resetTimer() {
        startTimer();
    }

    function stopTimer() {
        if (timerInterval) clearInterval(timerInterval);
        timerCountdown.textContent = '—';
    }

    // NO auto-fetch on page load.
    // User must click "Check Monitored Gates" to trigger the first scan.
});

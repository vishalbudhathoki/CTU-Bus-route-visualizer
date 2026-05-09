const API = '/api';
let map, allRoutes = [], currentLayers = [];

function initMap() {
    map = L.map('map').setView([30.7333, 76.7794], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    loadRoutes();
}

function loadRoutes() {
    var list = document.getElementById('route-list');
    list.innerHTML = '<div class="loading">Loading routes...</div>';

    fetch(API + '/routes')
        .then(function(r) { return r.json(); })
        .then(function(routes) {
            allRoutes = routes;
            renderRouteList(routes);
        })
        .catch(function(err) {
            list.innerHTML = '<div class="no-results">Failed to load routes. Make sure the server is running.</div>';
        });
}

function renderRouteList(routes) {
    var list = document.getElementById('route-list');
    if (routes.length === 0) {
        list.innerHTML = '<div class="no-results">No routes found</div>';
        return;
    }

    var html = '';
    for (var i = 0; i < routes.length; i++) {
        var r = routes[i];
        html += '<div class="route-item" data-id="' + r.route_id + '">';
        html += '<div class="route-color" style="background:' + r.color + '"></div>';
        html += '<div class="route-info">';
        html += '<div class="route-id">Route ' + r.route_id + '</div>';
        html += '<div class="route-name">' + r.name + '</div>';
        html += '<div class="route-meta">' + r.schedule.frequency + ' · ' + r.stop_count + ' stops · ' + r.schedule.length_km + ' km</div>';
        html += '</div></div>';
    }
    list.innerHTML = html;

    var items = list.querySelectorAll('.route-item');
    for (var j = 0; j < items.length; j++) {
        items[j].addEventListener('click', function() {
            selectRoute(this.getAttribute('data-id'));
        });
    }
}

function selectRoute(routeId, highlightFrom, highlightTo) {
    var now = new Date();
    var nowStr = ('0' + now.getHours()).slice(-2) + ':' + ('0' + now.getMinutes()).slice(-2);
    
    fetch(API + '/routes/' + routeId + '?now=' + nowStr)
        .then(function(r) { return r.json(); })
        .then(function(route) {
            var rightPanel = document.getElementById('right-panel');
            if (rightPanel.classList.contains('collapsed')) {
                rightPanel.classList.remove('collapsed');
            }
            showRouteOnMap(route, highlightFrom, highlightTo);
            showRouteDetail(route, highlightFrom, highlightTo);
        });
}

function showRouteOnMap(route, highlightFrom, highlightTo) {
    clearMap();

    if (!route.stops || route.stops.length < 1) return;

    var bounds = L.latLngBounds();

    for (var i = 0; i < route.stops.length; i++) {
        var s = route.stops[i];
        var pos = [s.lat, s.lng];
        bounds.extend(pos);

        var isTerminal = (i === 0 || i === route.stops.length - 1);
        var isHighlight = (s.name === highlightFrom || s.name === highlightTo);

        var mColor = isHighlight ? '#FF9500' : route.color;
        var mRadius = isHighlight ? 10 : (isTerminal ? 8 : 5);

        var marker = L.circleMarker(pos, {
            radius: mRadius,
            fillColor: mColor,
            fillOpacity: 1,
            color: '#ffffff',
            weight: isHighlight ? 3 : 2
        }).addTo(map);

        var label = '';
        if (i === 0) label = ' (Start)';
        else if (i === route.stops.length - 1) label = ' (End)';

        var arrivalText = s.arrival ? '<br><span style="color:#0066cc">Arrival: ' + s.arrival + '</span>' : '';
        marker.bindPopup(
            '<strong>' + s.name + '</strong>' + label +
            '<br><span style="color:#7a7a7a">Stop ' + (i + 1) + ' of ' + route.stops.length + '</span>' +
            arrivalText
        );

        currentLayers.push(marker);
    }

    map.fitBounds(bounds, { padding: [40, 40] });
}

function showRouteDetail(route, highlightFrom, highlightTo) {
    document.getElementById('route-list').style.display = 'none';
    var detail = document.getElementById('route-detail');
    detail.classList.remove('hidden');

    var sched = route.schedule;
    var html = '<div class="detail-header">';
    html += '<div class="detail-route-id" style="color:' + route.color + '">Route ' + route.route_id + '</div>';
    html += '<div class="detail-route-name">' + route.name + '</div>';
    html += '<div class="detail-desc">' + route.description + '</div>';
    html += '</div>';

    html += '<table class="schedule-table">';
    html += '<tr><th>Timing</th><td>' + sched.time_range + '</td></tr>';
    html += '<tr><th>Frequency</th><td>' + sched.frequency + '</td></tr>';
    html += '<tr><th>Route Length</th><td>' + sched.length_km + ' km</td></tr>';
    html += '<tr><th>Buses</th><td>' + sched.num_buses + '</td></tr>';
    html += '<tr><th>Stops</th><td>' + route.stops.length + '</td></tr>';
    html += '</table>';

    html += '<div class="stops-heading">Route Stops</div>';
    html += '<ul class="stop-list">';
    for (var i = 0; i < route.stops.length; i++) {
        var arrTime = route.stops[i].arrival ? ' <span class="stop-time">' + route.stops[i].arrival + '</span>' : '';
        var isHighlight = (route.stops[i].name === highlightFrom || route.stops[i].name === highlightTo);
        var liClass = isHighlight ? ' class="highlight-stop"' : '';
        html += '<li' + liClass + '>' + route.stops[i].name + arrTime + '</li>';
    }
    html += '</ul>';

    document.getElementById('detail-content').innerHTML = html;
}

function clearMap() {
    for (var i = 0; i < currentLayers.length; i++) {
        map.removeLayer(currentLayers[i]);
    }
    currentLayers = [];
}

function backToList() {
    document.getElementById('route-list').style.display = '';
    document.getElementById('route-detail').classList.add('hidden');
    clearMap();
    map.setView([30.7333, 76.7794], 12);
}

// Search
var searchTimer = null;
document.getElementById('search-input').addEventListener('input', function() {
    var q = this.value.trim();
    clearTimeout(searchTimer);

    if (!q) {
        renderRouteList(allRoutes);
        return;
    }

    searchTimer = setTimeout(function() {
        fetch(API + '/search?q=' + encodeURIComponent(q))
            .then(function(r) { return r.json(); })
            .then(function(results) {
                backToList();
                renderRouteList(results);
            });
    }, 300);
});

document.getElementById('clear-btn').addEventListener('click', function() {
    document.getElementById('search-input').value = '';
    backToList();
    renderRouteList(allRoutes);
});

document.getElementById('back-btn').addEventListener('click', backToList);

// ===== Trip Planner =====

function setupAutocomplete(inputId, suggestionsId) {
    var input = document.getElementById(inputId);
    var box = document.getElementById(suggestionsId);
    var timer = null;

    input.addEventListener('input', function() {
        var q = this.value.trim();
        clearTimeout(timer);
        if (q.length < 2) {
            box.classList.add('hidden');
            box.innerHTML = '';
            return;
        }
        timer = setTimeout(function() {
            fetch(API + '/suggest?q=' + encodeURIComponent(q))
                .then(function(r) { return r.json(); })
                .then(function(stops) {
                    if (stops.length === 0) {
                        box.classList.add('hidden');
                        return;
                    }
                    var html = '';
                    for (var i = 0; i < stops.length; i++) {
                        html += '<div class="suggestion-item" data-name="' + stops[i].name + '">' + stops[i].name + '</div>';
                    }
                    box.innerHTML = html;
                    box.classList.remove('hidden');

                    var items = box.querySelectorAll('.suggestion-item');
                    for (var j = 0; j < items.length; j++) {
                        items[j].addEventListener('click', function() {
                            input.value = this.getAttribute('data-name');
                            box.classList.add('hidden');
                        });
                    }
                });
        }, 250);
    });

    input.addEventListener('blur', function() {
        setTimeout(function() { box.classList.add('hidden'); }, 200);
    });
}

setupAutocomplete('from-input', 'from-suggestions');
setupAutocomplete('to-input', 'to-suggestions');

document.getElementById('plan-btn').addEventListener('click', function() {
    var fromVal = document.getElementById('from-input').value.trim();
    var toVal = document.getElementById('to-input').value.trim();
    var resultsDiv = document.getElementById('plan-results');

    if (!fromVal || !toVal) {
        resultsDiv.innerHTML = '<div class="no-results">Please enter both stops.</div>';
        resultsDiv.classList.remove('hidden');
        return;
    }

    var now = new Date();
    var nowStr = ('0' + now.getHours()).slice(-2) + ':' + ('0' + now.getMinutes()).slice(-2);

    resultsDiv.innerHTML = '<div class="loading">Finding buses...</div>';
    resultsDiv.classList.remove('hidden');

    fetch(API + '/plan?from=' + encodeURIComponent(fromVal) + '&to=' + encodeURIComponent(toVal) + '&now=' + nowStr)
        .then(function(r) { return r.json(); })
        .then(function(results) {
            if (results.length === 0) {
                resultsDiv.innerHTML = '<div class="no-results">No buses found for this route right now.</div>';
                return;
            }
            var html = '';
            for (var i = 0; i < results.length; i++) {
                var r = results[i];
                html += '<div class="plan-card" style="cursor:pointer" data-route-id="' + r.route_id + '" data-from="' + r.from_stop + '" data-to="' + r.to_stop + '">';
                html += '<div class="plan-route-header">';
                html += '<div class="route-color" style="background:' + r.color + '"></div>';
                html += '<div class="plan-route-info">';
                html += '<span class="route-id">Route ' + r.route_id + '</span>';
                html += '<span class="plan-travel-time">' + r.travel_min + ' min</span>';
                html += '</div></div>';
                html += '<div class="plan-stops">' + r.from_stop + ' → ' + r.to_stop + '</div>';
                var waitText = r.next_bus.wait_min <= 1 ? 'Now' : r.next_bus.wait_min + ' min';
                html += '<div class="plan-bus plan-bus-next">';
                html += '<span class="plan-bus-time">🚌 ' + r.next_bus.time + '</span>';
                html += '<span class="plan-bus-wait">' + waitText + '</span>';
                html += '</div>';
                html += '</div>';
            }
            resultsDiv.innerHTML = html;
            
            var cards = resultsDiv.querySelectorAll('.plan-card');
            for (var c = 0; c < cards.length; c++) {
                cards[c].addEventListener('click', function() {
                    var rId = this.getAttribute('data-route-id');
                    var fStop = this.getAttribute('data-from');
                    var tStop = this.getAttribute('data-to');
                    selectRoute(rId, fStop, tStop);
                });
            }
        })
        .catch(function() {
            resultsDiv.innerHTML = '<div class="no-results">Error finding buses.</div>';
        });
});

document.getElementById('panel-toggle').addEventListener('click', function() {
    var panel = document.getElementById('right-panel');
    panel.classList.toggle('collapsed');
});

document.addEventListener('DOMContentLoaded', initMap);

const API = '/api';
let map, allRoutes = [], currentLayers = [], currentBounds = null;

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

function selectRoute(routeId, highlightFrom, highlightTo, tripInfo) {
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
            showRouteDetail(route, highlightFrom, highlightTo, tripInfo);
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

    currentBounds = bounds;
    map.fitBounds(bounds, { padding: [40, 40] });
}

function showRouteDetail(route, highlightFrom, highlightTo, tripInfo) {
    document.getElementById('route-list').style.display = 'none';
    var detail = document.getElementById('route-detail');
    detail.classList.remove('hidden');

    var sched = route.schedule;
    var html = '<div class="detail-header">';
    html += '<div class="detail-route-id" style="color:' + route.color + '">Route ' + route.route_id + '</div>';
    html += '<div class="detail-route-name">' + route.name + '</div>';
    html += '<div class="detail-desc">' + route.description + '</div>';
    html += '</div>';

    // Trip info section (only when coming from trip planner)
    if (tripInfo) {
        var waitLabel = tripInfo.wait === 'Now' ? 'Now' : 'in ' + tripInfo.wait.replace('Wait: ', '');
        html += '<table class="schedule-table">';
        html += '<tr><th>Next Bus</th><td style="color:#D4A843;font-weight:700">' + tripInfo.depart + ' <span style="opacity:0.8">(' + waitLabel + ')</span></td></tr>';
        html += '<tr><th>Travel Time</th><td>' + tripInfo.travel + ' min</td></tr>';
        if (tripInfo.fare && tripInfo.fare !== 'undefined') {
            html += '<tr><th>Est. Fare</th><td>' + tripInfo.fare + '</td></tr>';
        }
        html += '</table>';
    }

    html += '<table class="schedule-table">';
    if (!tripInfo) {
        html += '<tr><th>Timing</th><td>' + sched.time_range + '</td></tr>';
    }
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
                var waitText = r.next_bus.wait_min <= 1 ? 'Now' : 'Wait: ' + r.next_bus.wait_min + ' min';
                html += '<div class="plan-card" style="cursor:pointer" data-route-id="' + r.route_id + '" data-from="' + r.from_stop + '" data-to="' + r.to_stop + '" data-depart="' + r.next_bus.time + '" data-travel="' + r.travel_min + '" data-wait="' + waitText + '" data-fare="' + r.fare + '">';
                html += '<div class="plan-route-header">';
                html += '<div class="route-color" style="background:' + r.color + '"></div>';
                html += '<div class="plan-route-info">';
                html += '<span class="route-id">Route ' + r.route_id + '</span>';
                html += '<span class="plan-travel-time">Travel: ' + r.travel_min + ' min</span>';
                html += '</div></div>';
                html += '<div class="plan-stops">' + r.from_stop + ' → ' + r.to_stop + '</div>';
                html += '<div class="plan-bus plan-bus-next">';
                html += '<span class="plan-bus-time"><svg class="bus-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM18 11H6V6h12v5z"/></svg> ' + r.next_bus.time + '</span>';
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
                    var info = {
                        depart: this.getAttribute('data-depart'),
                        travel: this.getAttribute('data-travel'),
                        wait: this.getAttribute('data-wait'),
                        fare: this.getAttribute('data-fare')
                    };
                    selectRoute(rId, fStop, tStop, info);
                });
            }
        })
        .catch(function() {
            resultsDiv.innerHTML = '<div class="no-results">Error finding buses.</div>';
        });
});

// ===== Panel Toggle (Desktop) =====
document.getElementById('panel-toggle').addEventListener('click', function() {
    var panel = document.getElementById('right-panel');
    panel.classList.toggle('collapsed');
});

// ===== Mobile Bottom Sheet =====
function isMobile() {
    return window.matchMedia('(max-width: 834px)').matches;
}

function openSheet() {
    var panel = document.getElementById('right-panel');
    var overlay = document.getElementById('sheet-overlay');
    var fab = document.getElementById('mobile-fab');
    panel.classList.add('sheet-open');
    panel.classList.remove('collapsed');
    panel.classList.remove('sheet-full');
    overlay.classList.add('active');
    fab.classList.add('hidden');
}

function expandSheet() {
    var panel = document.getElementById('right-panel');
    panel.classList.add('sheet-open');
    panel.classList.add('sheet-full');
}

function collapseSheet() {
    var panel = document.getElementById('right-panel');
    panel.classList.remove('sheet-full');
}

function closeSheet() {
    var panel = document.getElementById('right-panel');
    var overlay = document.getElementById('sheet-overlay');
    var fab = document.getElementById('mobile-fab');
    panel.classList.remove('sheet-open');
    panel.classList.remove('sheet-full');
    overlay.classList.remove('active');
    fab.classList.remove('hidden');
}

// Enter route-viewing mode on mobile: hide sidebar, full-screen map, peek sheet with route details
function enterRouteViewing() {
    var app = document.getElementById('app');
    var panel = document.getElementById('right-panel');
    var overlay = document.getElementById('sheet-overlay');
    var fab = document.getElementById('mobile-fab');
    app.classList.add('route-viewing');
    // Show sheet in peek mode (small, showing route detail header)
    panel.classList.add('sheet-open', 'sheet-peek');
    panel.classList.remove('collapsed', 'sheet-full');
    overlay.classList.remove('active');
    fab.classList.add('hidden');
    setTimeout(function() {
        map.invalidateSize();
    }, 100);
}

function exitRouteViewing() {
    var app = document.getElementById('app');
    var panel = document.getElementById('right-panel');
    var fab = document.getElementById('mobile-fab');
    app.classList.remove('route-viewing');
    panel.classList.remove('sheet-open', 'sheet-peek', 'sheet-full');
    fab.classList.remove('hidden');
    clearMap();
    backToList();
    setTimeout(function() {
        map.invalidateSize();
        map.setView([30.7333, 76.7794], 12);
    }, 100);
}

document.getElementById('mobile-fab').addEventListener('click', openSheet);
document.getElementById('sheet-overlay').addEventListener('click', closeSheet);
document.getElementById('mobile-back').addEventListener('click', exitRouteViewing);

// Recenter map to fit route bounds
document.getElementById('mobile-recenter').addEventListener('click', function() {
    if (currentBounds && currentBounds.isValid()) {
        map.fitBounds(currentBounds, { padding: [40, 40] });
    }
});

// Clicking search input in the bottom sheet expands to full screen
document.getElementById('search-input').addEventListener('focus', function() {
    if (isMobile()) {
        expandSheet();
    }
});

// When a route is selected on mobile: enter route-viewing mode
var _origSelectRoute = selectRoute;
selectRoute = function(routeId, highlightFrom, highlightTo, tripInfo) {
    _origSelectRoute(routeId, highlightFrom, highlightTo, tripInfo);
    if (isMobile()) {
        enterRouteViewing();
    }
};

// Tap on the peek sheet to expand it
document.getElementById('panel-content').addEventListener('click', function() {
    if (!isMobile()) return;
    var panel = document.getElementById('right-panel');
    if (panel.classList.contains('sheet-peek')) {
        panel.classList.remove('sheet-peek');
        panel.classList.add('sheet-full');
    }
});

// Tap on the drag handle to toggle minimize/maximize
document.getElementById('panel-drag-handle').addEventListener('click', function() {
    if (!isMobile()) return;
    var panel = document.getElementById('right-panel');
    var isRouteView = document.getElementById('app').classList.contains('route-viewing');
    
    if (panel.classList.contains('sheet-full')) {
        // Minimize
        if (isRouteView) {
            panel.classList.remove('sheet-full');
            panel.classList.add('sheet-peek');
        } else {
            collapseSheet();
        }
    } else {
        // Maximize
        panel.classList.remove('sheet-peek');
        expandSheet();
    }
});

// Swipe gestures — touch anywhere on the sheet, threshold-based commit
(function() {
    var panel = document.getElementById('right-panel');
    var content = document.getElementById('panel-content');
    var startY = 0, currentY = 0;
    var dragging = false, pending = false;
    var sheetBaseHeight = 0;

    function getBaseHeight() {
        if (panel.classList.contains('sheet-full')) return window.innerHeight;
        if (panel.classList.contains('sheet-peek')) return window.innerHeight * 0.4;
        return window.innerHeight * 0.65;
    }

    function lockScroll() {
        content.style.overflow = 'hidden';
        content.style.touchAction = 'none';
        panel.style.overflow = 'hidden';
    }

    function unlockScroll() {
        content.style.overflow = '';
        content.style.touchAction = '';
        panel.style.overflow = '';
    }

    panel.addEventListener('touchstart', function(e) {
        if (!isMobile()) return;
        if (!panel.classList.contains('sheet-open')) return;

        var isFull = panel.classList.contains('sheet-full');

        // It won't move the sheet down unless the content is at the very top (scrollTop <= 1)
        if (isFull && content.scrollTop > 1) return;

        // If half open, ALWAYS lock scroll so any upward swipe drags the sheet
        if (!isFull) {
            lockScroll();
        }

        pending = true;
        dragging = false;
        startY = e.touches[0].clientY;
        currentY = startY;
        sheetBaseHeight = getBaseHeight();
    });

    document.addEventListener('touchmove', function(e) {
        if (!pending && !dragging) return;

        currentY = e.touches[0].clientY;
        var diff = currentY - startY;

        if (pending) {
            var isFull = panel.classList.contains('sheet-full');

            // If full sheet and swiping UP, abort drag and let native scroll take over
            if (isFull && diff < 0) {
                pending = false;
                return;
            }

            if (Math.abs(diff) > 15) {
                // Commit to dragging the sheet
                pending = false;
                dragging = true;
                lockScroll(); // Ensure locked if it wasn't already
                panel.style.transition = 'none';
            } else {
                // Not enough movement — block scroll only if half-open
                if (!isFull) {
                    e.preventDefault();
                }
                return;
            }
        }

        if (!dragging) return;

        var newHeight = sheetBaseHeight - diff;
        newHeight = Math.max(0, Math.min(window.innerHeight, newHeight));
        panel.style.height = newHeight + 'px';
        panel.style.maxHeight = newHeight + 'px';
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('touchend', function() {
        if (pending) {
            pending = false;
            unlockScroll();
            return;
        }
        if (!dragging) return;
        dragging = false;
        unlockScroll();
        panel.style.transition = '';
        panel.style.height = '';
        panel.style.maxHeight = '';

        var isRouteView = document.getElementById('app').classList.contains('route-viewing');
        var vh = window.innerHeight;
        var diff = currentY - startY;
        var finalHeight = sheetBaseHeight - diff;
        var finalHeightPercent = finalHeight / vh;

        // Threshold based on the actual visual height of the sheet when you let go
        // 0.60 means if you drag it down by 40% from the top, it snaps down
        if (finalHeightPercent <= 0.60) {
            if (isRouteView) {
                panel.classList.remove('sheet-full');
                panel.classList.add('sheet-peek');
            } else if (panel.classList.contains('sheet-full')) {
                collapseSheet();
            } else {
                closeSheet();
            }
        } else if (finalHeightPercent >= 0.75) {
            // If the sheet is pulled above 75% of the screen, expand to full
            panel.classList.remove('sheet-peek');
            expandSheet();
        } else {
            // Not dragged past a threshold, snap back to wherever it started
            if (panel.classList.contains('sheet-full')) {
                expandSheet();
            } else if (panel.classList.contains('sheet-peek')) {
                panel.classList.add('sheet-peek');
            } else {
                collapseSheet();
            }
        }
    });
})();

document.addEventListener('DOMContentLoaded', initMap);

import json, os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Load data once at startup
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..')

with open(os.path.join(ROOT, 'data.json'), 'r', encoding='utf-8') as f:
    raw = json.load(f)
    STATIONS = json.loads(raw['data'])

with open(os.path.join(ROOT, 'routes.json'), 'r', encoding='utf-8') as f:
    ROUTES = json.load(f)

# Index for search
station_lookup = {s['stationid']: s for s in STATIONS}

def fuzzy_match(query, text):
    """Return a score 0-1 for how well query matches text.
    Uses word-level matching so partial/closest words still score."""
    query = query.lower().strip()
    text = text.lower().strip()

    # Exact substring is the strongest signal
    if query in text:
        return 1.0

    # Check if any word in the text starts with the query
    words = text.split()
    for w in words:
        if w.startswith(query):
            return 0.95

    # Check word-by-word similarity
    best = 0.0
    for w in words:
        ratio = SequenceMatcher(None, query, w).ratio()
        if ratio > best:
            best = ratio

    # Also check the full string similarity
    full_ratio = SequenceMatcher(None, query, text).ratio()
    if full_ratio > best:
        best = full_ratio

    return best

FUZZY_THRESHOLD = 0.5

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/stations')
def get_stations():
    return jsonify(STATIONS)

@app.route('/api/routes')
def get_routes():
    summary = []
    for r in ROUTES:
        summary.append({
            'route_id': r['route_id'],
            'name': r['name'],
            'color': r['color'],
            'schedule': r['schedule'],
            'stop_count': len(r['stops'])
        })
    return jsonify(summary)

import re, copy

def get_stop_offsets(stops, length_km, freq_min, num_buses):
    """Calculate cumulative time offsets (in minutes) for each stop on the route, factoring in local speed limits."""
    num_stops = len(stops)
    offsets = [0.0] * num_stops
    if num_stops <= 1:
        return offsets

    if length_km and length_km > 0:
        avg_dist_km = length_km / (num_stops - 1)
        
        for i in range(num_stops - 1):
            # Flat average speed of 40 km/h for all segments
            eff_speed = 40.0

            seg_min = (avg_dist_km / eff_speed) * 60
            seg_min += 0.5  # Boarding/alighting penalty

            if seg_min < 1.0:
                seg_min = 1.0

            offsets[i+1] = offsets[i] + seg_min
    else:
        # Fallback: use cycle time estimation
        cycle_time = freq_min * num_buses
        is_circular = len(stops) > 1 and stops[0]['name'].lower() == stops[-1]['name'].lower()
        total_trip_min = (cycle_time * 0.9) if is_circular else (cycle_time * 0.45)
        interval = total_trip_min / (num_stops - 1)
        if interval < 2:
            interval = 2
        for i in range(1, num_stops):
            offsets[i] = offsets[i-1] + interval

    return offsets

def estimate_arrival_times(route, now_minutes):
    """Add estimated next arrival time to each stop based on the schedule and current time.
    
    The algorithm finds the next bus departing from stop 0 after 'now',
    then tracks that SINGLE bus through all subsequent stops so times
    are always monotonically increasing.
    """
    route = copy.deepcopy(route)
    sched = route.get('schedule', {})
    time_range = sched.get('time_range', '')
    frequency_str = sched.get('frequency', '')
    num_buses = sched.get('num_buses', 1)
    stops = route.get('stops', [])

    if not stops or not time_range:
        return route

    parts = time_range.split('-')
    if len(parts) < 2:
        return route
    start_parts = parts[0].strip().split(':')
    end_parts = parts[1].strip().split(':')
    if len(start_parts) < 2 or len(end_parts) < 2:
        return route

    first_dep = int(start_parts[0]) * 60 + int(start_parts[1])
    last_dep = int(end_parts[0]) * 60 + int(end_parts[1])

    freq_match = re.search(r'(\d+)', frequency_str)
    freq_min = int(freq_match.group(1)) if freq_match else 20

    length_km = sched.get('length_km', 0)
    num_stops = len(stops)
    if num_stops <= 1:
        return route

    offsets = get_stop_offsets(stops, length_km, freq_min, num_buses)

    # Find the next bus departure from stop 0 after now
    next_dep = -1
    dep = first_dep
    while dep <= last_dep:
        if dep >= now_minutes:
            next_dep = dep
            break
        dep += freq_min

    if next_dep == -1:
        # No more buses today
        for i in range(num_stops):
            stops[i]['arrival'] = 'Finished'
        route['stops'] = stops
        return route

    # Track this single bus through all stops
    for i in range(num_stops):
        arr = next_dep + int(round(offsets[i]))
        h = (arr // 60) % 24
        m = arr % 60
        stops[i]['arrival'] = '{:02d}:{:02d}'.format(h, m)

    route['stops'] = stops
    return route

@app.route('/api/routes/<route_id>')
def get_route(route_id):
    now_str = request.args.get('now', '')
    if now_str and ':' in now_str:
        now_parts = now_str.split(':')
        now_minutes = int(now_parts[0]) * 60 + int(now_parts[1])
    else:
        from datetime import datetime
        n = datetime.now()
        now_minutes = n.hour * 60 + n.minute

    for r in ROUTES:
        if r['route_id'] == route_id:
            return jsonify(estimate_arrival_times(r, now_minutes))
    return jsonify({'error': 'Route not found'}), 404

@app.route('/api/search')
def search():
    q = request.args.get('q', '').lower().strip()
    if not q:
        return jsonify([])

    # Strip 'route' or 'route no' prefix if the user types it so that searching 'route 4C' matches '4C' perfectly
    if q.startswith('route'):
        q = q.replace('route no', '').replace('route', '').strip()

    # If the query is empty after stripping, return early
    if not q:
        return jsonify([])

    scored = []
    for r in ROUTES:
        best_score = 0.0

        # Match route ID
        s = fuzzy_match(q, r['route_id'])
        if s > best_score:
            best_score = s

        # Match route name
        s = fuzzy_match(q, r['name'])
        if s > best_score:
            best_score = s

        # Match description
        s = fuzzy_match(q, r['description'])
        if s > best_score:
            best_score = s

        # Match stop names
        for stop in r['stops']:
            s = fuzzy_match(q, stop['name'])
            if s > best_score:
                best_score = s

        if best_score >= FUZZY_THRESHOLD:
            scored.append((best_score, {
                'route_id': r['route_id'],
                'name': r['name'],
                'color': r['color'],
                'schedule': r['schedule'],
                'stop_count': len(r['stops'])
            }))

    # Sort by score descending so best matches come first
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored]
    return jsonify(results)

@app.route('/api/suggest')
def suggest_stops():
    """Return stop names that fuzzy-match the query for autocomplete."""
    q = request.args.get('q', '').lower().strip()
    if not q or len(q) < 2:
        return jsonify([])

    seen = set()
    scored = []
    # Check all stops across all routes (these are the stops that actually have service)
    for r in ROUTES:
        for stop in r['stops']:
            name = stop['name']
            if name in seen:
                continue
            score = fuzzy_match(q, name)
            if score >= FUZZY_THRESHOLD:
                seen.add(name)
                scored.append((score, {
                    'name': name,
                    'lat': stop['lat'],
                    'lng': stop['lng']
                }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return jsonify([s[1] for s in scored[:15]])

@app.route('/api/plan')
def plan_trip():
    """Find routes that go from 'from' stop to 'to' stop.
    Returns routes with next upcoming bus times."""
    from_q = request.args.get('from', '').lower().strip()
    to_q = request.args.get('to', '').lower().strip()
    now_str = request.args.get('now', '')  # HH:MM from client

    if not from_q or not to_q:
        return jsonify([])

    # Parse current time
    if now_str and ':' in now_str:
        now_parts = now_str.split(':')
        now_minutes = int(now_parts[0]) * 60 + int(now_parts[1])
    else:
        from datetime import datetime
        n = datetime.now()
        now_minutes = n.hour * 60 + n.minute

    results = []

    for r in ROUTES:
        stops = r['stops']
        sched = r['schedule']

        # Find best matching from-stop index
        from_idx = -1
        for i, stop in enumerate(stops):
            if from_q in stop['name'].lower().strip():
                from_idx = i
                break

        # Find best matching to-stop index (must be AFTER from)
        to_idx = -1
        for i, stop in enumerate(stops):
            if i <= from_idx:
                continue
            if to_q in stop['name'].lower().strip():
                to_idx = i
                break

        if from_idx < 0 or to_idx < 0:
            continue

        # Calculate timing
        time_range = sched.get('time_range', '')
        frequency_str = sched.get('frequency', '')
        num_buses = sched.get('num_buses', 1)

        parts = time_range.split('-')
        if len(parts) < 2:
            continue
        start_parts = parts[0].strip().split(':')
        end_parts = parts[1].strip().split(':')
        if len(start_parts) < 2 or len(end_parts) < 2:
            continue

        first_dep = int(start_parts[0]) * 60 + int(start_parts[1])
        last_dep = int(end_parts[0]) * 60 + int(end_parts[1])

        freq_match_obj = re.search(r'(\d+)', frequency_str)
        freq_min = int(freq_match_obj.group(1)) if freq_match_obj else 20

        length_km = sched.get('length_km', 0)
        num_stops = len(stops)
        if num_stops <= 1:
            continue
            
        offsets = get_stop_offsets(stops, length_km, freq_min, num_buses)

        # Time offset for the from-stop from the route start
        from_offset = int(round(offsets[from_idx]))
        to_offset = int(round(offsets[to_idx]))
        travel_time = to_offset - from_offset

        # Find next 3 buses arriving at the from-stop
        next_buses = []
        dep = first_dep
        while dep <= last_dep and len(next_buses) < 3:
            arrival_at_from = dep + from_offset
            if arrival_at_from >= now_minutes:
                h = (arrival_at_from // 60) % 24
                m = arrival_at_from % 60
                wait = arrival_at_from - now_minutes
                next_buses.append({
                    'time': '{:02d}:{:02d}'.format(h, m),
                    'wait_min': wait
                })
            dep += freq_min

        if not next_buses:
            continue

        # Calculate estimated distance and fare (CTU slabs)
        fraction = float(to_idx - from_idx) / max(1, num_stops - 1)
        travel_km = length_km * fraction
        
        if travel_km <= 5.0:
            fare_range = "₹10 (Non-AC) - ₹15 (AC)"
        elif travel_km <= 10.0:
            fare_range = "₹20 (Non-AC) - ₹25 (AC)"
        else:
            fare_range = "₹25 (Non-AC) - ₹30 (AC)"

        results.append({
            'route_id': r['route_id'],
            'name': r['name'],
            'color': r['color'],
            'from_stop': stops[from_idx]['name'],
            'to_stop': stops[to_idx]['name'],
            'travel_min': travel_time,
            'fare': fare_range,
            'next_bus': next_buses[0],  # only the very next bus
            'frequency': sched.get('frequency', '')
        })

    # Sort by soonest arrival and limit to top 5
    results.sort(key=lambda x: x['next_bus']['time'])
    return jsonify(results[:5])

if __name__ == '__main__':
    print(f"Loaded {len(STATIONS)} stations and {len(ROUTES)} routes")
    app.run(debug=True, port=5000)

# Complete Line-by-Line Code Explanation

This document contains the exact code from your backend Python server (`app.py`) and frontend JavaScript (`app.js`), but with a plain-English explanation written as a comment `#` (or `//`) above almost every single line. 

You can use this to understand exactly what the code is doing if the teacher points to any specific part of the screen.

---

## Part 1: The Python Backend (`app.py`)

### 1. Setup and Loading Data
```python
import json, os 
# Import 'json' to read our data files, and 'os' to interact with the computer's folder system

from flask import Flask, jsonify, request, send_from_directory 
# Import 'Flask', which is the framework that runs our web server. 'jsonify' turns Python data into web data.

from flask_cors import CORS 
# 'CORS' is a security tool that allows our frontend website to talk to our backend server safely.

from dotenv import load_dotenv 
# Loads secret variables (like passwords) from a hidden .env file (if we had any)

from difflib import SequenceMatcher 
# Imports a math tool that compares two words to see how similar they are (used for typo matching)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env')) 
# Tells the server to actually load the hidden .env file from the root directory

app = Flask(__name__, static_folder='../frontend') 
# Creates our web server and tells it that all our HTML/CSS/JS files live in the 'frontend' folder

CORS(app) 
# Applies the CORS security rules to our new web server

BASE = os.path.dirname(os.path.abspath(__file__)) 
# Figures out the exact folder path where this app.py file lives on your computer

ROOT = os.path.join(BASE, '..') 
# Figures out the path to the main project folder (one level up)

with open(os.path.join(ROOT, 'data.json'), 'r', encoding='utf-8') as f: 
# Opens the data.json file in 'read' mode
    raw = json.load(f) 
    # Reads the file into memory
    STATIONS = json.loads(raw['data']) 
    # Extracts the specific list of bus stations from the JSON and saves it to a variable called STATIONS

with open(os.path.join(ROOT, 'routes.json'), 'r', encoding='utf-8') as f: 
# Opens the routes.json file
    ROUTES = json.load(f) 
    # Reads all 52 routes into memory and saves it to a variable called ROUTES
```

### 2. The Fuzzy Search (Handling Typos)
```python
def fuzzy_match(query, text):
# Creates a function that takes two words: what the user typed (query), and the actual word (text)

    query = query.lower().strip() 
    # Converts the user's text to lowercase and removes accidental spaces at the end

    text = text.lower().strip() 
    # Converts the actual text to lowercase and removes spaces

    if query in text: 
    # If what the user typed is exactly inside the actual word...
        return 1.0 
        # Return a perfect score of 100% (1.0)

    words = text.split() 
    # Splits a long phrase like "Sector 17 Bus Stand" into individual words

    for w in words: 
    # Loops through every single word in the phrase
        if w.startswith(query): 
        # If any word starts with what the user typed (e.g. they typed "Sec" and the word is "Sector")
            return 0.95 
            # Return a nearly perfect score of 95%

    best = 0.0 
    # Create a variable to keep track of the highest score we find

    for w in words: 
    # Loop through the words again
        ratio = SequenceMatcher(None, query, w).ratio() 
        # Ask the SequenceMatcher math tool: "How mathematically similar are these two words?"
        if ratio > best: 
        # If this score is higher than our previous best...
            best = ratio 
            # Save it as the new best score

    full_ratio = SequenceMatcher(None, query, text).ratio() 
    # Check the mathematical similarity of the entire phrase, not just individual words
    if full_ratio > best: 
        best = full_ratio 

    return best 
    # Give the final score back to whatever asked for it

FUZZY_THRESHOLD = 0.5 
# Set a rule: if the score is lower than 50% (0.5), it's a bad match, ignore it.
```

### 3. The Core Timing Algorithm
```python
def get_stop_offsets(stops, length_km, freq_min, num_buses):
# Creates a function to calculate exactly how many minutes it takes to reach each stop

    num_stops = len(stops) 
    # Counts how many stops are on this route

    offsets = [0.0] * num_stops 
    # Creates an empty list of zeros, one for each stop. Example: [0, 0, 0, 0]

    if num_stops <= 1: 
    # If the route only has 1 stop (which makes no sense)...
        return offsets 
        # Just return the zeros and give up

    if length_km and length_km > 0: 
    # If we know the total distance of the route in kilometers...
        avg_dist_km = length_km / (num_stops - 1) 
        # Divide the total distance by the number of stops to find the distance between each stop
        
        for i in range(num_stops - 1): 
        # Loop through every single stop segment (from Stop A to Stop B, then B to C, etc)
            eff_speed = 40.0 
            # Assume the bus drives at an average speed of 40 km/h in the city

            seg_min = (avg_dist_km / eff_speed) * 60 
            # Math: Time = Distance / Speed. Multiply by 60 to turn hours into minutes.

            seg_min += 0.5  
            # Add 30 seconds (0.5 minutes) to account for passengers getting on/off

            if seg_min < 1.0: 
            # If the stops are so close that the math says it takes less than 1 minute...
                seg_min = 1.0 
                # Force it to take at least 1 minute (safety check)

            offsets[i+1] = offsets[i] + seg_min 
            # Take the time of the previous stop, add this segment's time, and save it for the next stop. 
            # This creates a cumulative running total.

    return offsets 
    # Return the final list of running totals (e.g. [0 mins, 4 mins, 9 mins, 13 mins])
```

### 4. Assigning Times to the Bus
```python
def estimate_arrival_times(route, now_minutes):
# Creates a function to figure out what time the bus will physically be at the stops

    route = copy.deepcopy(route) 
    # Makes a safe copy of the route data so we don't accidentally corrupt our master database

    sched = route.get('schedule', {}) 
    time_range = sched.get('time_range', '') 
    frequency_str = sched.get('frequency', '') 
    stops = route.get('stops', []) 
    # Extract the necessary variables from the route dictionary

    parts = time_range.split('-') 
    # Splits "06:00-22:00" into two pieces: "06:00" and "22:00"

    start_parts = parts[0].strip().split(':') 
    end_parts = parts[1].strip().split(':') 
    # Splits the times into hours and minutes

    first_dep = int(start_parts[0]) * 60 + int(start_parts[1]) 
    # Converts the start time into pure minutes since midnight (e.g. 6am = 360 minutes)

    last_dep = int(end_parts[0]) * 60 + int(end_parts[1]) 
    # Converts the end time into pure minutes since midnight (e.g. 10pm = 1320 minutes)

    offsets = get_stop_offsets(stops, length_km, freq_min, num_buses) 
    # Calls our math function from earlier to get the cumulative time for each stop

    next_dep = -1 
    dep = first_dep 
    # Sets our starting point to the very first bus of the day (e.g. 6am)

    while dep <= last_dep: 
    # Starts a loop: keep going as long as the current bus is earlier than the last bus of the night
        if dep >= now_minutes: 
        # If this bus's departure time is AFTER right now...
            next_dep = dep 
            # We found the next bus! Save this time.
            break 
            # Stop searching

        dep += freq_min 
        # If that bus already left, add 20 minutes (the frequency) to check the next bus

    if next_dep == -1: 
    # If the loop finished and we never found a bus...
        for i in range(num_stops): 
            stops[i]['arrival'] = 'Finished' 
        return route 
        # Tell the user the bus is done running for the day and exit

    for i in range(num_stops): 
    # Loop through all the stops
        arr = next_dep + int(round(offsets[i])) 
        # Take the time the bus leaves Stop 1, and add the cumulative travel time for this specific stop

        h = (arr // 60) % 24 
        # Math: divide total minutes by 60 to get the Hour (e.g. 18). "% 24" ensures it loops past midnight correctly.

        m = arr % 60 
        # Math: find the remainder of minutes to get the Minutes (e.g. 45)

        stops[i]['arrival'] = '{:02d}:{:02d}'.format(h, m) 
        # Format the numbers nicely like "18:45" and save it to the stop data

    route['stops'] = stops 
    return route 
    # Update the route with our calculated arrival times and send it back
```

### 5. Serving Web Pages & Basic APIs
```python
@app.route('/api/routes')
def get_routes():
# When the javascript asks for the list of routes to build the sidebar...
    summary = [] 
    for r in ROUTES: 
    # Loop through all 52 routes
        summary.append({ 
        # Add a simplified version of the route (no coordinates, just names/colors) to save internet bandwidth
            'route_id': r['route_id'],
            'name': r['name'],
            'color': r['color'],
            'schedule': r['schedule'],
            'stop_count': len(r['stops'])
        })
    return jsonify(summary) 
    # Send the list back to Javascript as JSON format

@app.route('/api/suggest')
def suggest_stops():
# This API powers the dropdown when typing in the search box
    q = request.args.get('q', '').lower().strip() 
    # Get what the user typed in the search box
    
    if not q or len(q) < 2: 
    # If they typed nothing or only 1 letter, don't waste time searching
        return jsonify([])

    seen = set() 
    # Create an empty 'Set' (like a list, but automatically prevents duplicates)
    
    scored = [] 
    # Create an empty list to hold the matching stops
    
    for r in ROUTES: 
    # Loop through every single route
        for stop in r['stops']: 
        # Loop through every stop on that route
            name = stop['name'] 
            # Grab the name of the stop
            
            if name in seen: 
            # If we've already searched this exact stop name before...
                continue 
                # Skip it to save time

            score = fuzzy_match(q, name) 
            # Call our math tool to see how similar the typed text is to the stop name
            
            if score >= FUZZY_THRESHOLD: 
            # If it's a good match (above 50%)...
                seen.add(name) 
                # Add it to our 'seen' list so we don't check it again
                
                scored.append((score, { 
                # Add it to our results list along with its score and coordinates
                    'name': name,
                    'lat': stop['lat'],
                    'lng': stop['lng']
                }))

    scored.sort(key=lambda x: x[0], reverse=True) 
    # Sort the results so the highest score is at the top of the list
    
    return jsonify([s[1] for s in scored[:15]]) 
    # Send only the top 15 results back to the frontend
```

### 6. The Trip Planner Logic
```python
@app.route('/api/plan')
def plan_trip():
    from_q = request.args.get('from', '').lower().strip() 
    # Get the starting stop
    
    to_q = request.args.get('to', '').lower().strip() 
    # Get the destination stop

    results = [] 

    for r in ROUTES: 
    # Loop through all 52 routes
        stops = r['stops'] 

        from_idx = -1 
        # Set starting stop index to "not found"
        for i, stop in enumerate(stops): 
        # Loop through stops to find the origin
            if from_q in stop['name'].lower().strip():
                from_idx = i 
                # Save the position of the starting stop
                break

        to_idx = -1 
        # Set destination stop index to "not found"
        for i, stop in enumerate(stops): 
        # Loop through stops again
            if i <= from_idx: 
            # If this stop comes BEFORE the origin stop...
                continue 
                # Skip it! The bus can't go backwards.
                
            if to_q in stop['name'].lower().strip():
                to_idx = i 
                # Save the position of the destination stop
                break

        if from_idx < 0 or to_idx < 0: 
        # If we didn't find BOTH stops on this route...
            continue 
            # Skip this route, it's not a valid path!

        # ... (The math logic calculates offsets here, exactly like estimate_arrival_times) ...
        offsets = get_stop_offsets(stops, length_km, freq_min, num_buses)

        from_offset = int(round(offsets[from_idx])) 
        # Get the cumulative travel time for the starting stop
        
        to_offset = int(round(offsets[to_idx])) 
        # Get the cumulative travel time for the destination stop
        
        travel_time = to_offset - from_offset 
        # Math: Destination time minus Start time = Total Travel Time!

        # ... (Finds the next bus in the schedule and returns the times) ...
```

---

## Part 2: The JavaScript Frontend (`frontend/app.js`)

This file controls the map and the buttons on your screen.

### 1. Variables and Map Setup
```javascript
const API = '/api'; 
// Save the URL path to our Python server in a constant variable

let map, allRoutes = [], currentLayers = []; 
// Create empty variables to hold the Map object, the list of routes, and the active map markers

function initMap() { 
// This function runs the moment the page loads
    map = L.map('map').setView([30.7333, 76.7794], 12); 
    // Tells Leaflet to find the <div id="map"> and center it on Chandigarh (Latitude 30.73, Longitude 76.77) at Zoom level 12

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
    // Adds the actual visual street map tiles from OpenStreetMap
        attribution: '&copy; OpenStreetMap contributors' 
        // Gives legal credit to OpenStreetMap
    }).addTo(map); 
    // Attaches the tiles to the map

    loadRoutes(); 
    // Calls our function to fetch the route data from the server
}
```

### 2. Fetching and Listing Routes
```javascript
function loadRoutes() {
    var list = document.getElementById('route-list'); 
    // Finds the empty HTML box where the routes will go
    
    list.innerHTML = '<div class="loading">Loading routes...</div>'; 
    // Shows a temporary loading message

    fetch(API + '/routes') 
    // Makes a network request to the Python server asking for '/api/routes'
        .then(function(r) { return r.json(); }) 
        // When the server answers, convert the raw text into a Javascript Object (JSON)
        .then(function(routes) { 
        // When the conversion is done...
            allRoutes = routes; 
            // Save the routes to our global variable
            renderRouteList(routes); 
            // Call a function to draw the routes on the screen
        })
}

function renderRouteList(routes) {
    var list = document.getElementById('route-list'); 
    var html = ''; 
    // Create an empty text variable

    for (var i = 0; i < routes.length; i++) { 
    // Start a loop that runs once for every single route in the list
        var r = routes[i]; 
        // Grab the current route
        
        // Build the HTML for the route card by combining text and variables using the + operator
        html += '<div class="route-item" data-id="' + r.route_id + '">';
        html += '<div class="route-color" style="background:' + r.color + '"></div>';
        html += '<div class="route-info">';
        html += '<div class="route-id">Route ' + r.route_id + '</div>';
        html += '<div class="route-name">' + r.name + '</div>';
        html += '<div class="route-meta">' + r.schedule.frequency + ' · ' + r.stop_count + ' stops</div>';
        html += '</div></div>';
    }
    
    list.innerHTML = html; 
    // Inject all that HTML text into the actual webpage at once (much faster than doing it one by one)

    var items = list.querySelectorAll('.route-item'); 
    // Find all the newly created route cards
    
    for (var j = 0; j < items.length; j++) { 
    // Loop through them
        items[j].addEventListener('click', function() { 
        // Add a "click" listener to each one
            selectRoute(this.getAttribute('data-id')); 
            // If clicked, trigger the selectRoute function and pass it the ID
        });
    }
}
```

### 3. Drawing the Map Markers
```javascript
function showRouteOnMap(route, highlightFrom, highlightTo) {
    clearMap(); 
    // Calls a function to delete any old circles off the map

    var bounds = L.latLngBounds(); 
    // Creates a mathematical boundary box. We will expand this box to fit all our stops.

    for (var i = 0; i < route.stops.length; i++) { 
    // Loop through every stop on the selected route
        var s = route.stops[i]; 
        
        var pos = [s.lat, s.lng]; 
        // Grab the GPS coordinates
        
        bounds.extend(pos); 
        // Stretch our mathematical boundary box so it encompasses this coordinate

        var isTerminal = (i === 0 || i === route.stops.length - 1); 
        // Check if this is the very first or very last stop
        
        var isHighlight = (s.name === highlightFrom || s.name === highlightTo); 
        // Check if this stop is the origin or destination the user searched for

        var mColor = isHighlight ? '#FF9500' : route.color; 
        // If highlighted, use Orange. Otherwise, use the route's specific color.
        
        var mRadius = isHighlight ? 10 : (isTerminal ? 8 : 5); 
        // If highlighted, make the circle huge (10). If it's a terminal, make it big (8). Otherwise normal (5).

        var marker = L.circleMarker(pos, { 
        // Create the circle object in Leaflet using our rules
            radius: mRadius,
            fillColor: mColor,
            fillOpacity: 1,
            color: '#ffffff',
            weight: isHighlight ? 3 : 2
        }).addTo(map); 
        // Attach the circle to the map

        currentLayers.push(marker); 
        // Save the circle to our global list so we can delete it later
    }

    map.fitBounds(bounds, { padding: [40, 40] }); 
    // Tell the map to physically zoom and pan so that our boundary box perfectly fits on the screen, leaving a 40px margin
}
```

### 4. The Autocomplete Debouncer
```javascript
function setupAutocomplete(inputId, suggestionsId) {
// This function sets up the search boxes
    var input = document.getElementById(inputId); 
    var box = document.getElementById(suggestionsId); 
    var timer = null; 
    // Create an empty timer

    input.addEventListener('input', function() { 
    // Listen for any typing inside the box
        var q = this.value.trim(); 
        // Get the text they typed
        
        clearTimeout(timer); 
        // INSTANTLY destroy the old timer. If they type quickly, this prevents the old timer from executing.
        
        if (q.length < 2) { 
        // If they only typed 1 letter, don't search.
            box.classList.add('hidden'); 
            return;
        }
        
        timer = setTimeout(function() { 
        // Create a new timer that will wait exactly 250 milliseconds
            fetch(API + '/suggest?q=' + encodeURIComponent(q)) 
            // Once the timer ends, FINALLY send the text to the Python server to search
                .then(function(r) { return r.json(); })
                .then(function(stops) {
                    // ... (Build the HTML dropdown menu using the results) ...
                });
        }, 250); // This is the length of the timer!
    });
}
```

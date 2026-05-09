# CTU Bus Route Visualizer - Detailed Code Explanation

This document provides an in-depth, function-by-function explanation of the entire codebase. Use this guide during your presentation to explain exactly how the data flows, how the math is calculated, and how the user interface reacts.

---

## 1. Frontend (`frontend/app.js`)
This is the core JavaScript file that runs in the user's browser. It handles user interactions, renders the map, and communicates with the backend API.

### Global Variables
- `map`: Stores the Leaflet map instance.
- `currentLayers`: An array tracking all currently drawn map markers. This is used to delete the old markers before drawing new ones.
- `API`: A string pointing to the backend URL (`http://localhost:5000/api`).

### Map & Route Functions
- **`initMap()`**: Called when the page loads. It creates the interactive map centered on Chandigarh (`[30.7333, 76.7794]`), sets the zoom level, loads the OpenStreetMap visual tiles, and triggers `loadRoutes()`.
- **`loadRoutes()`**: Makes a `fetch()` request to `/api/routes` to get a list of all bus routes. It generates HTML `div` elements for each route and inserts them into the right-side panel's route list.
- **`selectRoute(routeId, highlightFrom, highlightTo)`**: Triggered when a user clicks a route. 
  - It generates the current local time (`nowStr` like "14:30") and passes it to the backend.
  - It automatically forces the right panel to open by removing the `.collapsed` CSS class.
  - It passes the detailed route data to `showRouteOnMap` and `showRouteDetail`.
- **`showRouteOnMap(route, highlightFrom, highlightTo)`**: 
  - Calls `clearMap()` to erase old markers.
  - Loops through every stop in `route.stops` and creates a circular marker (`L.circleMarker`) at the stop's latitude and longitude.
  - **Highlight Logic:** If a stop's name exactly matches `highlightFrom` or `highlightTo`, it overrides the marker's default color with bright orange (`#FF9500`) and increases its radius so it stands out.
  - Binds an HTML popup to the marker displaying the stop name and the estimated arrival time.
- **`showRouteDetail(route, highlightFrom, highlightTo)`**: Hides the main list of routes and shows the specific details (Frequency, Distance, Total Buses). It dynamically builds an HTML list (`<ul>`) of all stops. If a stop matches the highlighted stops, it adds a `.highlight-stop` CSS class to it.
- **`clearMap()`**: Loops through the `currentLayers` array and removes each item from the Leaflet map to prevent overlapping drawings.

### Autocomplete & Trip Planner Functions
- **`setupAutocomplete(inputId, suggestionsId)`**: Attaches an event listener to the search boxes. As the user types, it sends their text to `/api/suggest`. It takes the backend's suggestions and creates clickable dropdown items. When an item is clicked, it fills the input field with the exact stop name.
- **`document.getElementById('plan-btn').addEventListener('click')`**: The core Trip Planner trigger.
  - Grabs the text from the "Current Location" and "Destination" fields.
  - Calculates the current time and sends a request to `/api/plan`.
  - Loops through the backend's results and generates HTML `.plan-card` elements. These cards show the route number, total travel time, and exactly how many minutes away the next bus is.
  - Attaches a click listener to the cards so that clicking one triggers `selectRoute()` to show it on the map.
- **Panel Toggle Listener**: Attaches to the `panel-toggle` button. It simply toggles the `.collapsed` CSS class on the right panel to slide it in and out of view.

---

## 2. Backend (`backend/app.py`)
This is the Python Flask server. It processes requests from the frontend, does heavy mathematical calculations for timing, and serves JSON data.

### Initialization & Data Loading
- **`load_data()`**: Runs immediately when the script starts. It opens `data.json` and `routes.json`, parsing them into Python dictionaries (`STATIONS` and `ROUTES`) so they stay in the computer's fast memory (RAM) for quick access.

### Core Mathematical Algorithm
- **`estimate_arrival_times(route, now_minutes)`**: This is the most complex function in the app. It calculates exactly when the next bus will arrive at any given stop.
  - **Step 1 (Cycle Time):** It multiplies the route's `frequency` by `num_buses` to figure out the total cycle time (how long it takes for all buses to complete a full loop).
  - **Step 2 (One-Way Factor):** It checks if the route is circular (starts and ends at the exact same stop). If circular, the time to traverse the stops is 90% of the cycle time. If it is a linear (one-way) route, it applies a 45% factor (because the cycle time includes the return trip).
  - **Step 3 (Stop Intervals):** It divides that travel time evenly across the number of stops to find out how many minutes it takes to drive between two adjacent stops.
  - **Step 4 (Next Bus Calculation):** For a specific stop, it looks at the daily schedule (e.g., buses departing every 20 mins from 06:00 to 18:00). It calculates the arrival time of *every single bus* for the day at that stop, and finds the very first one that arrives *after* the user's current time (`now_minutes`).

### API Endpoints
- **`@app.route('/api/routes')`**: Returns a lightweight summary list of all routes to populate the sidebar menu.
- **`@app.route('/api/routes/<route_id>')`**: Fetches the full data for a single route. It reads the `?now=` parameter from the URL, processes the route through `estimate_arrival_times`, and sends the completed data back to the frontend.
- **`@app.route('/api/suggest')`**: The Autocomplete engine. Takes a partial string from the user, scans through all `STATIONS`, and uses the `in` keyword to find exact substring matches (e.g., typing "sec" returns "Sector 15", "Sector 17").
- **`@app.route('/api/plan')`**: The Trip Planner engine.
  - **Direction Check:** For every route, it searches the stops array for the user's `from` stop. Once found, it searches for the `to` stop, but *strictly only starting after the index of the from stop*. This guarantees the bus is traveling in the correct direction.
  - **Timing Calculation:** If a valid route is found, it calculates the wait time by finding the next bus departing from the origin stop, and calculates the total travel time by multiplying the number of stops between them by the calculated stop interval.
  - **Sorting:** It gathers all valid routes, sorts them so the bus arriving soonest is at the very top, and returns the top 5 results to the frontend.

---

## 3. Styling & Layout (`frontend/style.css` & `frontend/index.html`)

### `index.html`
- **Structure:** Uses semantic HTML. The `#app` `div` takes up the entire screen. Inside it are three main siblings: `#sidebar` (left), `#map` (center background), and `#right-panel` (right). 
- **Forms:** The search inputs utilize `autocomplete="off"` to prevent the browser's default autocomplete from interfering with our custom JS autocomplete dropdowns.

### `style.css`
- **CSS Variables (`:root`)**: Centralizes the color scheme. Changing `--primary` from blue to green here would instantly change the accent color across the entire application.
- **Flexbox Layout**: Heavy use of `display: flex;`. The sidebar uses `flex-direction: column` to cleanly stack the title, trip planner, and results without complex math.
- **Animations (`transition`)**: The right panel slides in and out using `transform: translateX(360px)` and a `.3s cubic-bezier` easing function, which gives it that smooth, Apple-like snappy feel.
- **Highlighting (`.highlight-stop`)**: Custom styling applied dynamically by JavaScript. It forces the text to become bold and overrides the standard blue colors with a vibrant orange (`#FF9500`) to draw the user's eye immediately to their specific search results.
- **Mobile Responsiveness (`@media`)**: Detects if the screen is smaller than 834px (like an iPad or iPhone). It overrides the Flexbox layout to stack the sidebar on top of the map instead of side-by-side, and moves the right panel to slide up from the bottom of the screen to accommodate touch interfaces.

---

## 4. Data Configuration (`data.json` & `routes.json`)

- **`data.json`**: A static JSON array serving as the primary database of physical coordinates. It prevents us from needing to call external Geocoding APIs, ensuring the app runs extremely fast.
- **`routes.json`**: Acts as the operational rulebook. By keeping `time_range`, `frequency`, and `num_buses` entirely in JSON, administrators can update bus schedules without needing to touch or rewrite a single line of Python or JavaScript code. The backend algorithm mathematically adapts to whatever is in this file.

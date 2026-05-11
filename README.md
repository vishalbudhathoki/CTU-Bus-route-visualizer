# CTU Bus Route Visualizer

A web app that helps you figure out which CTU bus to take and when it'll show up. You type in where you are and where you want to go, and it tells you the best routes along with estimated arrival times based on the actual CTU timetable.

Built this as an end-term project. The whole thing runs on Flask + vanilla JS with Leaflet for the map.

![Backend](https://img.shields.io/badge/Backend-Flask-lightgrey?style=for-the-badge&logo=flask)
![Frontend](https://img.shields.io/badge/Frontend-Vanilla_JS-yellow?style=for-the-badge&logo=javascript)
![Maps](https://img.shields.io/badge/Maps-Leaflet.js-green?style=for-the-badge&logo=leaflet)

---

## What it does

- **Trip planner** — type your starting stop and destination, and it finds which buses go that way and when the next one leaves
- **Arrival time estimates** — uses the route distance and bus frequency to calculate when a bus will reach each stop
- **Browse all routes** — collapsible side panel where you can scroll through every CTU route and see its stops on the map
- **Map view** — stops show up as markers on a Leaflet map, origin/destination get highlighted when you search

---

## Tech used

- **Frontend**: Plain JavaScript, HTML, CSS (dark theme)
- **Map**: Leaflet.js + OpenStreetMap tiles
- **Backend**: Python Flask serving a REST API
- **Data**: Two JSON files — `data.json` has the stop coordinates, `routes.json` has all the schedules and route info
- **No database** — everything loads from JSON at startup, keeps it simple and fast

---

## How to run locally

```bash
# clone it
git clone https://github.com/vishalbudhathoki/CTU-Bus-route-visualizer.git
cd CTU-Bus-route-visualizer

# install python deps
pip install -r backend/requirements.txt

# start the server
python backend/app.py
```

Then open `http://localhost:5000` in your browser.

---

## Project structure

```
backend/
  app.py              — flask server + timing/routing logic
  requirements.txt    — python dependencies
frontend/
  index.html          — main page
  style.css           — dark theme styles
  app.js              — map rendering + UI logic
data.json             — coordinates for 888 bus stops
routes.json           — 52 routes with schedules
explanation.md        — detailed writeup of how everything works
```

---

## How the timing works (short version)

The app takes a route's total distance (km), assumes city bus speed of ~18 km/h, and divides the travel time evenly across the stops. Then it finds the next bus departure from the first stop and tracks that single bus through every stop — so the times always go up as you'd expect.

More details in [explanation.md](explanation.md).

---

Built by [Vishal Budhathoki](https://github.com/vishalbudhathoki), [Aryan Sharma](https://github.com/aryansharma0730-cloud), and [Raghav Tayal](https://github.com/raghavtayal0903)

Data from CTU official timetables.
# CTU Bus Route Visualizer

A high-performance, Modern Dark web application for visualizing and planning bus routes for the Chandigarh Transport Undertaking (CTU). This project features a precision timing engine that estimates bus arrivals based on real-world schedules and total route cycle times.

![Design Preview](https://img.shields.io/badge/Design-Modern_Dark-black?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-Flask-lightgrey?style=for-the-badge&logo=flask)
![Frontend](https://img.shields.io/badge/Frontend-Vanilla_JS-yellow?style=for-the-badge&logo=javascript)
![Maps](https://img.shields.io/badge/Maps-Leaflet.js-green?style=for-the-badge&logo=leaflet)

---

## 🏎️ Key Features

- **Intelligent Trip Planner**: Enter your current location and destination to find the best upcoming bus routes.
- **Real-Time Arrival Estimates**: Dynamically calculates when the next bus will arrive at any given stop based on frequency, number of buses, and current system time.
- **Premium Dark Aesthetic**: A premium, dark-mode interface featuring absolute black surfaces, Signature Gold accents, and sharp aerodynamic lines.
- **Directional Accuracy**: The routing engine ensures buses are suggested in the correct direction of travel.
- **Interactive Maps**: Powered by Leaflet.js with custom-styled stop markers and highlighted origin/destination points.
- **Zero-Database Architecture**: Powered by static JSON data for extreme speed and easy deployment.

---

## 🛠️ Tech Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3 (Custom Dark System).
- **Mapping**: Leaflet.js for interactive markers and popups.
- **Backend**: Python Flask REST API.
- **Data**: Static JSON files (`data.json` for coordinates, `routes.json` for schedules).
- **Deployment**: Optimized for Render/Gunicorn.

---

## 🚀 Local Setup

To run this project on your local machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vishalbudhathoki/CTU-Bus-route-visualizer.git
   cd CTU-Bus-route-visualizer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Start the Flask server**:
   ```bash
   python backend/app.py
   ```

4. **View the app**:
   Open your browser and navigate to `http://localhost:5000`.

---

## 📁 Project Structure

```text
├── backend/
│   ├── app.py              # Main Flask application & Timing Engine
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main UI structure
│   ├── style.css           # Custom dark styling system
│   └── app.js              # Map & UI logic
├── data.json               # Physical coordinates for all stops
├── routes.json             # Bus schedules & route sequences
└── explanation.md          # Deep technical dive into the code logic
```

---

## 🌐 Deployment

This project is ready for deployment on **Render**. 
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `gunicorn backend.app:app`

---

## 📜 Credits

- **Design**: Inspired by Modern High-Performance aesthetics.
- **Data Source**: CTU Official Timetables.
- **Developer**: [Vishal Budhathoki](https://github.com/vishalbudhathoki)
# 🌊 EnviroPulse 3D: Real-Time Multi-Tier GPU Environmental & DBMS Grid

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![Deck.gl](https://img.shields.io/badge/Deck.gl-WebGL_GPU-brightgreen?style=for-the-badge)](https://deck.gl)
[![WebSockets](https://img.shields.io/badge/WebSockets-Real--Time_Streaming-blue?style=for-the-badge)](https://websockets.readthedocs.io)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

A high-performance, 60 FPS GPU-accelerated spatial intelligence platform visualizing real-time environmental telemetry (BOD, COD, DO, pH, AQI, PM2.5, PM10, natural resources) across an **84-node hierarchical spatial database** covering India, states, cities, and micro-industrial clusters.

---

## 🌟 Key Features

* **3-Tier Normalized Spatial Hierarchy (84 Nodes):**
  * **Tier 1 (States):** 11 Major States & Union Territories (Maharashtra, Delhi NCT, Karnataka, Gujarat, Tamil Nadu, Telangana, West Bengal, UP, MP, Rajasthan, Kerala).
  * **Tier 2 (Cities):** 27 Major Municipal Cities & Industrial Districts.
  * **Tier 3 (Micro-Areas):** 46 High-Priority Wards, Industrial CETP Belts & Wetland Basins (e.g., Mahape MIDC, Vashi Creek, BKC, Hinjewadi, Whitefield, Okhla).
* **60 FPS Hardware-Accelerated WebGL Rendering:**
  * Multi-layer composite visualization using **Deck.gl** and **MapLibre GL JS**.
  * **3D Volumetric Extrusions (`ColumnLayer`):** Proportional COD/BOD/AQI height scaling with minimum pixel clamping (`radiusMinPixels`) ensuring persistent visibility at all zoom altitudes.
  * **Territorial Polygons (`GeoJsonLayer`):** State and district boundary highlighting with dynamic elevation and opacity transitions.
  * **Dynamic GPU Floating Labels (`TextLayer`):** Crisp, billboard-oriented location badges rendered directly on the GPU without external API key dependencies.
* **Real-Time Asynchronous Telemetry Pipeline:**
  * Python **FastAPI** backend streaming simulated CPCB/MoEFCC calibrated sensor pulses every 2 seconds via persistent **WebSockets**.
* **Topological Neighbor Comparative Analytics:**
  * Real-time spatial adjacency joins comparing active regions against geographical neighbors via interactive **Recharts Radar & Bar Charts** with sub-50ms query response times.
* **Resilient Dual-Tier Architecture:**
  * Embedded synchronous client-side fallback catalog (`ENTITY_CATALOGUE`) guaranteeing zero UI lockups or click freezes during temporary network disruptions.

---

## 🏗️ System Architecture

```
                             [ Nationwide Root ]
                                      │
         ┌────────────────────────────┼───────────────────────────┐
      [Tier 1]                     [Tier 1]                    [Tier 1]
    Maharashtra                   Delhi NCT                    Karnataka
     (IN-MH)                       (IN-DL)                      (IN-KA)
    (11 States Total)                 │                            │
         │                            │                            │
   ┌─────┴──────────────┐      ┌──────┴──────┐              ┌──────┴──────┐
 [Tier 2]            [Tier 2] [Tier 2]    [Tier 2]        [Tier 2]    [Tier 2]
Navi Mumbai           Pune   New Delhi   South Delhi      Bengaluru   Mysuru
 (MH-NM)            (MH-PU)   (DL-ND)     (DL-SO)          (KA-BLR)   (KA-MYS)
(27 Cities Total)                     │                        │
   │                                  │                        │
 ┌─┴─────────────┐              ┌─────┴─────┐            ┌─────┴─────┐
[Tier 3]       [Tier 3]       [Tier 3]   [Tier 3]      [Tier 3]   [Tier 3]
 Mahape         Vashi          Okhla    Connaught     Whitefield  Peenya
  MIDC          Creek           CETP      Place        Tech Hub  Industrial
(46 Micro-Areas Total)
```

---

## 🛠️ Technology Stack

| Domain | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | React 18, Vite, Deck.gl (`@deck.gl/core`, `@deck.gl/layers`, `@deck.gl/react`), MapLibre GL JS, Tailwind CSS, Recharts, Framer Motion, Lucide React |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, WebSockets, Pydantic |
| **Spatial & Basemap** | GeoJSON, OpenStreetMap Humanitarian (HOT) CDN (Zero API Key required), In-Memory Adjacency Relational Schema |
| **Telemetry Standards** | CPCB (Central Pollution Control Board) & MoEFCC Calibration Limits |

---

## 📊 Standardized Environmental Parameters Monitored

* **Water Quality Metrics:**
  * **BOD (Biochemical Oxygen Demand):** mg/L (Safe limit: $< 3$ mg/L)
  * **COD (Chemical Oxygen Demand):** mg/L (Safe limit: $< 50$ mg/L)
  * **DO (Dissolved Oxygen):** mg/L (Aquatic minimum: $> 5$ mg/L)
  * **pH:** Normal range: $6.5 - 8.5$
  * **Effluent Flow Rate:** MLD (Million Litres per Day)
* **Air Quality Metrics:**
  * **AQI (Air Quality Index):** Continuous 0–500 index
  * **PM2.5 & PM10:** $\mu\text{g/m}^3$ particulate matter concentrations
* **Natural Resource Accounting:**
  * Forest Canopy Coverage (%), Monitored Lake Counts, Groundwater Table Depth (m bgl)

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+ (for frontend dev server)

### Option 1: One-Click Launch (Recommended)
Clone the repository and start the integrated engine:

```bash
git clone https://github.com/vedant21006-byte/enviro-pulse-webgl.git
cd enviro-pulse-webgl

# Install backend dependencies
cd backend
python -m pip install -r requirements.txt
cd ..

# Run the unified platform
python run_dashboard.py
```
* **Dashboard:** [http://localhost:8000](http://localhost:8000)
* **WebSocket Stream:** `ws://localhost:8000/ws/environmental-data`

---

### Option 2: Running Frontend & Backend Separately

#### 1. Backend (FastAPI WebSocket Server)
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 📜 API Endpoints

* `GET /api/hierarchy` - Complete 84-node hierarchical topology snapshot.
* `GET /api/entity/{tier}/{entity_id}` - Real-time telemetry for a specific State, City, or Micro-Area.
* `WS /ws/environmental-data` - High-frequency 2-second streaming socket pushing nationwide sensor pulses.

---

## 👨‍💻 Author
**Vedant Patil**  
* Artificial Intelligence & Machine Learning, RAIT (D.Y. Patil University)  
* [LinkedIn](https://linkedin.com/in/vedant-patil-358a69298) • [GitHub](https://github.com/vedant21006-byte)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

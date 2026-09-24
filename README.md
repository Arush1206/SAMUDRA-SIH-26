# SAMUDRA
### Synthetic Aperture Monitoring for Unified Detection and Rapid Assessment

> **SIH 2026** · Maritime Oil-Spill Forensics Platform · Python 3.10+ · FastAPI · DuckDB · Uber H3

---

## The Problem

Every day, ships crossing the world's oceans quietly commit one of the most widespread and least prosecuted environmental crimes: the deliberate discharge of oily bilge water, slop tanks, and cargo residues directly into the sea.

### Scale of the Crisis

The ocean is vast, enforcement vessels are few, and the crime is almost entirely invisible to the naked eye. Satellite surveillance has begun to change that — but detection alone is not enough. The central challenge is **attribution**: connecting a detected oil slick back to the ship that caused it.

Global studies by SkyTruth, Global Fishing Watch, and the European Maritime Safety Agency reveal the scale of the problem:

- **25% to 45%** of all detected operational oil slicks cannot be immediately matched to an active, broadcasting vessel transponder.
- A landmark 2024 study found that **21% to 30%** of global cargo and tanker vessel activity is entirely absent from public tracking systems.
- An estimated **800 to 1,400+ tankers** — roughly 10–15% of the world's large tanker capacity — operate outside international oversight, routinely disabling their transponders to execute unmonitored discharges.
- In automated satellite radar pipelines, **nearly one-third** of detected slicks require cross-matching against non-cooperative vessel signatures because no active transponder exists at the slick's origin.

### Why Attribution Fails

Ships exploit three physical facts to evade forensic accountability:

**1. The Transponder Kill Switch (Dark Vessels)**
A ship's crew manually cuts power to its Class-A AIS transponder — in direct violation of SOLAS Regulation V/19.2.4.7 — between 1 and 3 hours before flushing bilge or slop tanks. By the time a satellite passes overhead and detects the oil slick, the ship has steamed 100+ kilometres away with no broadcast record of ever being there.

**2. The Open Ocean Assumption**
The majority of illegal discharges (~60–70%) actually happen with the transponder *on*. Crews rely on the sheer scale of the ocean: dilution, nocturnal dispersion, and the assumption that no one is watching in real time. These ships are visible in AIS data — but connecting their track to a specific slick requires sub-kilometre precision at a specific timestamp, which raw telemetry cannot provide.

**3. Temporal Dispersion**
Oil slicks drift with surface currents and wind for 6 to 12 hours before a satellite overpass. A slick detected at 04:15 UTC may have been discharged at 02:00 UTC, when the culprit was 50 kilometres away and its track looked entirely innocent. Naive point-in-time mapping is useless.

### The Legal & Regulatory Gap

Two landmark international conventions exist precisely to prevent this:

| Convention | Full Name | Relevance |
|---|---|---|
| **MARPOL** | International Convention for the Prevention of Pollution from Ships | Prohibits discharge of oily mixtures; mandates the Oily Water Separator (OWS) |
| **SOLAS** | International Convention for the Safety of Life at Sea | Reg. V/19.2.4.7 requires continuous AIS transponder operation for all commercial vessels |

Both are routinely violated. The bottleneck is not law — it is **forensic evidence**. Without a system that can reconstruct exactly where a vessel was at the moment of discharge and quantify that vessel's culpability with a defensible, multi-factor score, prosecutions rarely succeed.

---

## The Solution — SAMUDRA

SAMUDRA is a three-engine forensic pipeline that bridges the gap between satellite detection and legal attribution. It ingests SAR imagery of oil slicks and outputs a ranked, scored dossier of suspect vessels — including unbroadcasting "dark" vessels identified through radar cross-matching — suitable for submission to port state authorities and maritime tribunals.

### Core Principle

> *A vessel is a suspect if and only if its physical path intersected the hydrodynamic origin of the spill at the moment of discharge — not at the moment the satellite passed.*

SAMUDRA works backwards from the satellite image to the crime scene, and forwards from each vessel's telemetry to the same point in space and time, then asks: **did these two paths meet?**

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SAMUDRA PIPELINE                                  │
│                                                                            │
│  Sentinel-1 SAR Scene                                                     │
│         │                                                                  │
│         ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  ENGINE 1 — SAR Slick Detection                                      │  │
│  │  Input : Raw SAR backscatter scene metadata                          │  │
│  │  Output: Slick polygon (WGS84), centroid, major axis, Bonn class,   │  │
│  │          confidence score, T_sat, t0_window         [Contract A]     │  │
│  └────────────────────────┬────────────────────────────────────────────┘  │
│                           │ Contract A                                     │
│                           ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  ENGINE 2 — Lagrangian Backward Drift Hindcast                       │  │
│  │  Input : Slick centroid + MetOcean surface currents & wind fields    │  │
│  │  Output: Spill origin (X₀, Y₀), release time T₀, uncertainty        │  │
│  │          radius σ_d                               [Contract B]       │  │
│  └────────────────────────┬────────────────────────────────────────────┘  │
│                           │ Contract A + Contract B                        │
│                           ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  ENGINE 3 — AIS Forensic Attribution & Dark Vessel Detection         │  │
│  │                                                                      │  │
│  │  ├─ Part 1: Coordinate normalisation & temporal window extraction    │  │
│  │  ├─ Part 2: Kinematic search envelope (R_search = σ_d + V_max·Δt)  │  │
│  │  ├─ Part 3: Uber H3 spatial pre-filtering (two-tier disk query)     │  │
│  │  ├─ Part 4: Trajectory reconstruction (PCHIP / dead-reckoning)      │  │
│  │  ├─ Part 5: Multi-factor AHP culprit scoring                        │  │
│  │  └─ Part 6: SAR-to-AIS KD-Tree dark vessel interception             │  │
│  │                                                                      │  │
│  │  Output: Ranked suspect dossier + dark vessel alerts  [Contract C]  │  │
│  └────────────────────────┬────────────────────────────────────────────┘  │
│                           │ Contract C                                     │
│                           ▼                                                │
│              POST /api/v1/attribution → AttributionResponse               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Engine Breakdown

### Engine 1 — SAR Slick Detection

Sentinel-1 SAR satellites image the ocean surface using synthetic aperture radar. Oil slicks suppress natural sea surface roughness (Bragg scattering), appearing as dark, low-backscatter patches against a brighter ocean background.

Engine 1 extracts the following from each detected slick:

| Output Field | Description |
|---|---|
| `polygon_wgs84` | GeoJSON polygon of the slick boundary |
| `centroid` | [lon, lat] slick centre of mass |
| `major_axis_deg` | Principal orientation angle — the direction the source vessel was travelling |
| `t0_window` | Estimated discharge window `[start_ISO, end_ISO]` based on scene acquisition time |
| `heading_ambiguous` | True when the slick axis represents an undirected line (θ or θ+180°) |
| `bonn_class` | Bonn Agreement pollution category (1–5) |
| `confidence` | Model confidence score [0.0–1.0] |

---

### Engine 2 — Lagrangian Backward Drift Hindcast

A slick detected at 04:15 UTC did not originate at the satellite-observed centroid. Surface currents and wind have advected it for hours since discharge. Engine 2 runs a backward Lagrangian particle simulation to trace the slick to its point and time of origin.

**Key Outputs:**

| Output | Symbol | Meaning |
|---|---|---|
| Origin latitude | X₀ | Where the oil entered the water |
| Origin longitude | Y₀ | Where the oil entered the water |
| Release timestamp | T₀ | When the discharge occurred |
| Uncertainty radius | σ_d ≈ 2.5 km | Hydrodynamic spread of origin estimate |

This hindcasted origin — not the satellite-observed centroid — is the forensic crime scene that Engine 3 queries against.

---

### Engine 3 — AIS Forensic Attribution & Dark Vessel Detection

Engine 3 is the forensic core of SAMUDRA. It works across six stages:

#### Stage 1 · Temporal Slicing
Before any spatial work, the global AIS database is filtered to a narrow time window around T₀. Any vessel that was not in the region during the discharge window is physically incapable of culpability and is discarded immediately.

```
Temporal window: [T₀ − Δt, T₀ + Δt]
```

#### Stage 2 · Kinematic Search Envelope
A ship transmitting an AIS ping at 12:30 and another at 13:00 may have been anywhere within a 15 km radius of each ping between those two times. Querying only pings within the 2.5 km attribution buffer would miss the culprit entirely if its pings bracketed the discharge.

SAMUDRA computes a wide ingestion radius that accounts for maximum commercial vessel speed:

```
R_search = σ_d + (V_max × Δt)
         = 2.5 km + (18 knots × Δt hours)
```

This retrieves all vessels that *could* have reached the spill origin — even if their recorded pings were kilometres away.

#### Stage 3 · Uber H3 Spatial Pre-Filtering
SAMUDRA uses [Uber H3](https://h3geo.org/) at **Resolution 8** (~460 m hexagon edge length) to replace expensive floating-point distance calculations with O(1) integer hash lookups.

Every AIS ping in the database is pre-tagged with its 64-bit H3 cell ID at ingestion. The spill origin is snapped to its Resolution 8 cell and expanded into a flat set of hexagons using `h3.grid_disk()`:

| Purpose | Ring Count | Hex Count | Radius Covered |
|---|---|---|---|
| Wide ingestion disk (Stage 2) | k ≈ 20–22 | ~1,400 cells | ~17.5 km |
| Attribution scoring disk (Stage 5) | k = 3 | 37 cells | ~2.5 km |
| Radar Doppler tolerance (Stage 6) | k = 2 | 19 cells | ~2.0 km |

```sql
-- O(1) candidate retrieval from DuckDB
SELECT DISTINCT mmsi FROM ais_pings
WHERE h3_res8 IN (search_set)
  AND timestamp BETWEEN (T0 - INTERVAL '30' MINUTE)
                    AND (T0 + INTERVAL '30' MINUTE);
```

#### Stage 4 · Trajectory Reconstruction

Raw AIS pings are broadcast asynchronously — a ship does not transmit at the exact second the spill occurred. SAMUDRA reconstructs every candidate vessel's exact position, speed, and heading at T₀ using two methods:

**For Cooperative Vessels (AIS On):**
PCHIP interpolation (Piecewise Cubic Hermite Interpolating Polynomial) fits a smooth, non-overshooting spline through the vessel's pings and evaluates it at the precise spill timestamp. Unlike linear interpolation (which ignores ship momentum through turns) or standard cubic splines (which can produce fictitious velocity spikes), PCHIP preserves monotonicity of speed across manoeuvres.

**For Dark Vessels (AIS Off — Vanishing Act):**
When a vessel's signal terminates unexpectedly while heading toward the spill zone, SAMUDRA projects its trajectory forward via constant-velocity dead reckoning constrained to navigable shipping fairways:

```
X(T₀) = X(t_last) + SOG · cos(COG) · δt / 111.0
Y(T₀) = Y(t_last) + SOG · sin(COG) · δt / (111.0 · cos(X_last))
```

#### Stage 5 · Multi-Factor AHP Culprit Scoring

Each candidate vessel is scored across four normalised factors using an Analytic Hierarchy Process (AHP) weighted composite:

```
S_culprit = 100 × (0.56·F_dist + 0.23·F_heading + 0.13·F_anomaly + 0.08·F_type)
```

| Factor | Weight | Formula | What it Measures |
|---|---|---|---|
| **F_dist** (Spatial Proximity) | 0.56 | `exp(−d²_min / 2σ²_d)` | Gaussian proximity of reconstructed T₀ position to spill origin |
| **F_heading** (Wake Alignment) | 0.23 | `cos(COG_T₀ − θ_slick)` | Parallelism between vessel heading and slick principal axis |
| **F_anomaly** (MARPOL Speed Window) | 0.13 | `1.0 if 6 ≤ SOG ≤ 14 kts` | Whether vessel speed matches the illegal discharge operating envelope |
| **F_type** (Vessel Risk Prior) | 0.08 | Categorical weight | Baseline risk by vessel class (tanker > bulk > cargo > tug) |

**Suspicion Tiers:**

| Score | Tier |
|---|---|
| ≥ 80.0 | 🔴 High Culpability |
| 50.0 – 79.9 | 🟡 Medium Suspicion |
| < 50.0 | 🟢 Cleared |

#### Stage 6 · SAR-to-AIS Dark Vessel Interception (Radar Fusion)

When a ship operates with its transponder completely off during the satellite overpass, it appears as a metallic radar reflection in the SAR scene with no matching AIS beacon.

SAMUDRA isolates these "ghost" vessels via sensor subtraction:

1. Interpolate all *broadcasting* vessels to their exact positions at T_sat.
2. Build a `scipy.spatial.cKDTree` over the broadcasting fleet's coordinates.
3. Query each SAR radar detection against the tree.
4. Any radar target with **no AIS match within 2.0 km** is classified as a confirmed `UNIDENTIFIED_DARK_VESSEL` — a SOLAS violation logged with exact coordinates, nearest transponder distance, and heading correlation to the slick.

---

## API Reference

| Endpoint | Method | Engine | Description |
|---|---|---|---|
| `/api/v1/detection` | `POST` | E1 | Submit SAR scene metadata, receive slick detections |
| `/api/v1/hindcast` | `POST` | E2 | Submit slick detections, receive hindcasted origin |
| `/api/v1/attribution` | `POST` | E3 | Submit Contract A + B, receive ranked suspect dossier |
| `/health` | `GET` | — | Service health check |

Interactive docs available at `/docs` (Swagger UI) after server start.

---

## Output — Attribution Dossier

```json
{
  "incident_id": "SAM-2026-09-24-CANONICAL",
  "evaluated_at_utc": "2026-09-25T01:00:00Z",
  "suspect_vessels": [
    {
      "rank": 1,
      "mmsi": 413219000,
      "vessel_name": "PACIFIC PIONEER",
      "vessel_type": "Crude Oil Tanker",
      "culprit_score": 94.6,
      "metrics": {
        "f_dist": 0.98,
        "f_heading": 0.99,
        "f_anomaly": 1.0,
        "f_type": 1.0
      },
      "closest_point_of_approach_km": 0.12,
      "reconstructed_sog_knots": 10.8,
      "reconstructed_cog_deg": 104.5,
      "anomaly_flags": ["WITHIN_DISCHARGE_SPEED_WINDOW", "DIRECT_WAKE_ALIGNMENT"]
    }
  ],
  "dark_vessel_alerts": [
    {
      "alert_id": "DV-20260922-01",
      "radar_target_location": [19.115, 72.9],
      "nearest_ais_transponder_km": 4.82,
      "threat_level": "CRITICAL",
      "statutory_violation": "IMO SOLAS Regulation V/19.2.4.7"
    }
  ]
}
```

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| API | FastAPI + Uvicorn | REST endpoints and async request handling |
| Schema Validation | Pydantic v2 | Inter-engine data contract enforcement |
| Analytical DB | DuckDB | In-process SQL over AIS CSV/Parquet — no server required |
| Data Processing | Pandas + NumPy | In-memory telemetry frames and vectorised operations |
| Interpolation | SciPy (`PchipInterpolator`) | Monotone cubic spline trajectory reconstruction |
| Radar Fusion | SciPy (`cKDTree`) | O(log N) nearest-neighbour SAR-to-AIS cross-matching |
| Spatial Index | Uber H3 (`h3-py`, Res 8) | O(1) hexagonal candidate retrieval, ~460 m precision |
| Geometry | Shapely | Polygon containment and coordinate utilities |
| Terminal Output | Rich | Suspect leaderboard tables and dark vessel alert panels |
| Containerisation | Docker + Docker Compose | Reproducible deployment |

---

## Project Structure

```
samudra/
├── backend/
│   ├── app/
│   │   ├── engines/
│   │   │   ├── engine1/          ← SAR detection
│   │   │   ├── engine2/          ← Lagrangian hindcast
│   │   │   └── engine3/          ← AIS attribution + dark vessel fusion
│   │   ├── schemas/              ← Pydantic data contracts (A, B, C)
│   │   ├── utils/                ← Geo math, H3 helpers, DuckDB, Rich
│   │   ├── api/v1/               ← FastAPI route handlers
│   │   └── core/                 ← Config and constants
│   ├── data/
│   │   ├── canonical_example.json  ← hardcoded test payload (committed)
│   │   ├── sample_ais/             ← AIS telemetry slices (gitignored)
│   │   └── sample_sar/             ← SAR scene JSONs (gitignored)
│   ├── prototypes/
│   │   └── engine3_prototype.py    ← standalone zero-database PoC
│   └── tests/
│       ├── unit/
│       └── integration/
└── frontend/
```

---

## Quick Start

```bash
# Clone and enter
git clone https://github.com/<your-org>/samudra.git
cd samudra/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify all engines load
python -c "import numpy, scipy, duckdb, h3, shapely, pydantic, pandas, rich; print('All dependencies OK')"

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000` · Swagger UI at `http://localhost:8000/docs`

### Run the Standalone Prototype (no server needed)

```bash
python prototypes/engine3_prototype.py
```

Runs the complete Engine 3 forensic pipeline on the hardcoded Mumbai offshore scenario and renders the suspect leaderboard and dark vessel alert directly in the terminal.

### Docker

```bash
docker compose up --build
```

---

## Glossary

| Term | Expansion |
|---|---|
| AIS | Automatic Identification System |
| MMSI | Maritime Mobile Service Identity |
| IMO | International Maritime Organization |
| SOG | Speed Over Ground |
| COG | Course Over Ground |
| CPA | Closest Point of Approach |
| VLCC | Very Large Crude Carrier |
| MARPOL | International Convention for the Prevention of Pollution from Ships |
| SOLAS | International Convention for the Safety of Life at Sea |
| SAR | Synthetic Aperture Radar |
| GIS | Geographic Information System |
| H3 | Hexagonal Hierarchical Spatial Index (Uber H3) |
| WGS84 | World Geodetic System 1984 |
| PCHIP | Piecewise Cubic Hermite Interpolating Polynomial |
| AHP | Analytic Hierarchy Process |
| DBSCAN | Density-Based Spatial Clustering of Applications with Noise |
| NTRO | National Technical Research Organisation |
| SIH | Smart India Hackathon |
| MVP | Minimum Viable Product |

---

## Regulatory Framework

SAMUDRA generates attribution evidence under two binding international conventions:

**MARPOL Annex I — Prevention of Oil Pollution**
- Prohibits discharge of oily water mixtures exceeding 15 ppm within 12 nautical miles of land
- Mandates the use of an Oily Water Separator (OWS) and Oil Record Book
- SAMUDRA's MARPOL speed anomaly factor (`F_anomaly`) directly models the 6–14 knot discharge operating window

**SOLAS Regulation V/19.2.4.7 — AIS Transponder Requirements**
- Requires all vessels ≥ 300 GT on international voyages to maintain continuous AIS broadcast
- Intentional transponder silencing is a flag-state and port-state enforceable violation
- SAMUDRA's dark vessel interception module generates statutory violation records citing this regulation by name

---

## Acknowledgements

Built for **Smart India Hackathon 2026**.  
Maritime telemetry data formats: [MarineCadastre](https://marinecadastre.gov/), [Spire Maritime](https://spire.com/maritime/).  
Spatial indexing: [Uber H3](https://h3geo.org/).  
SAR research references: [SkyTruth Cerulean](https://cerulean.skytruth.org/), [Global Fishing Watch](https://globalfishingwatch.org/), [EMSA CleanSeaNet](https://www.emsa.europa.eu/csn-menu.html).

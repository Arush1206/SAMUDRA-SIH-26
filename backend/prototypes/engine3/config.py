from datetime import datetime

# ==============================================================================
# ─── USER SCENARIO INPUTS (VALIDATED) ─────────────────────────────────────────
# ==============================================================================

# 1. Slick Location (Spill Origin centroid [Latitude, Longitude] in WGS84 decimal degrees)
SLICK_LOCATION_LAT: float = 19.11019
SLICK_LOCATION_LON: float = 72.88979

# 2. Slick Major Axis Orientation (Degrees [0.0, 180.0) or [0.0, 360.0) from True North)
SLICK_ANGLE_DEG: float = 104.5

# 3. Slick Radius / Hydrodynamic Uncertainty Buffer (sigma_d in kilometers)
SLICK_RADIUS_KM: float = 2.5

# 4. Temporal Anchors (ISO 8601 UTC)
SPILL_TIME_T0_STR: str = "2026-09-22T02:00:00Z"
T_SAT_STR: str         = "2026-09-22T04:15:00Z"

# Pre-parsed for easy math
SPILL_TIME_T0: datetime = datetime.fromisoformat(SPILL_TIME_T0_STR.replace("Z", "+00:00"))
T_SAT: datetime         = datetime.fromisoformat(T_SAT_STR.replace("Z", "+00:00"))

# 5. MetOcean Environmental Forcing 
CURRENT_U_MS: float   = 0.25      # Ocean surface current Eastward velocity (m/s)
CURRENT_V_MS: float   = -0.15     # Ocean surface current Northward velocity (m/s)
WIND_SPEED_MS: float  = 6.5       # Wind speed at 10m height (m/s)
WIND_DIR_DEG: float   = 290.0     # Meteorological wind direction (degrees from North)
LEEWAY_FACTOR: float  = 0.02      # 2.0% aerodynamic leeway drift coefficient

# 6. Dark Vessel Parameters
DARK_CATCHMENT_RADIUS_KM: float = 20.0
DARK_WINDOW_BEFORE_MIN: float   = 45.0
DARK_WINDOW_AFTER_MIN: float    = 15.0

# 7. SAR Unresolved Radar Targets (at T_sat)
SAR_RADAR_TARGETS = [
    {"target_id": "RADAR_TGT_01", "lat": 19.1150, "lon": 72.9000},
]

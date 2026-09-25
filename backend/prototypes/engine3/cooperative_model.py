import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import minimize_scalar
import math
from typing import Dict, Any

from geo_utils import vincenty_distance_km
from config import SLICK_LOCATION_LAT, SLICK_LOCATION_LON, SPILL_TIME_T0, CURRENT_U_MS, CURRENT_V_MS

def process_cooperative_vessel(df_vessel: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes the Two-Stage CPA algorithm and STW back-calculation for a single 
    cooperative vessel using its AIS track.
    
    Expected columns: ['timestamp' (datetime), 'lat', 'lon']
    Returns a dictionary of kinematic attributes at exact CPA.
    """
    if len(df_vessel) < 2:
        raise ValueError("Requires at least 2 AIS pings to interpolate.")
        
    # Sort strictly by time to ensure monotonic increasing inputs for PCHIP
    df_vessel = df_vessel.sort_values('timestamp')
    
    # Convert timestamps to float seconds relative to T0
    # This centers the time domain around T0 = 0.0 for numeric stability
    t_sec = (df_vessel['timestamp'] - SPILL_TIME_T0).dt.total_seconds().values
    lats = df_vessel['lat'].values
    lons = df_vessel['lon'].values
    
    # 1. Fit PCHIP splines
    spline_lat = PchipInterpolator(t_sec, lats)
    spline_lon = PchipInterpolator(t_sec, lons)
    
    t_start, t_end = t_sec[0], t_sec[-1]
    
    # Helper to calculate distance to slick at time t
    def dist_to_slick(t: float) -> float:
        return vincenty_distance_km(spline_lat(t), spline_lon(t), 
                                    SLICK_LOCATION_LAT, SLICK_LOCATION_LON)
    
    # 2. Stage A: Coarse Grid Search (30-second steps)
    coarse_t = np.arange(t_start, t_end, 30.0)
    coarse_dists = [dist_to_slick(t) for t in coarse_t]
    
    min_idx = np.argmin(coarse_dists)
    t_coarse_min = coarse_t[min_idx]
    
    # Bracket for Stage B
    bracket_start = max(t_start, t_coarse_min - 30.0)
    bracket_end = min(t_end, t_coarse_min + 30.0)
    
    # 3. Stage B: Continuous Refinement (Brent's Method)
    res = minimize_scalar(dist_to_slick, bounds=(bracket_start, bracket_end), method='bounded')
    
    t_cpa_sec = res.x
    d_cpa_km = res.fun
    
    # 4. Extract position at CPA
    lat_cpa = float(spline_lat(t_cpa_sec))
    lon_cpa = float(spline_lon(t_cpa_sec))
    
    # 5. Differentiate PCHIP to get instantaneous SOG and COG
    # Derivative returns degrees per second
    dlat_dt = float(spline_lat(t_cpa_sec, nu=1))
    dlon_dt = float(spline_lon(t_cpa_sec, nu=1))
    
    # Convert to meters per second (V_N = North velocity, V_E = East velocity)
    V_N = dlat_dt * 111195.0
    V_E = dlon_dt * 111195.0 * math.cos(math.radians(lat_cpa))
    
    sog_ms = math.sqrt(V_N**2 + V_E**2)
    sog_kts = sog_ms / 0.514444
    
    cog_rad = math.atan2(V_E, V_N)
    cog_deg = (math.degrees(cog_rad) + 360) % 360
    
    # 6. Back-Calculate STW (MARPOL Evaluation)
    U_E = V_E - CURRENT_U_MS
    U_N = V_N - CURRENT_V_MS
    stw_ms = math.sqrt(U_E**2 + U_N**2)
    stw_kts = stw_ms / 0.514444
    
    # Re-construct actual timestamp
    timestamp_cpa = SPILL_TIME_T0 + pd.Timedelta(seconds=t_cpa_sec)
    
    return {
        'mmsi': df_vessel['mmsi'].iloc[0],
        't_cpa': timestamp_cpa,
        'd_cpa_km': d_cpa_km,
        'lat_cpa': lat_cpa,
        'lon_cpa': lon_cpa,
        'sog_kts': sog_kts,
        'cog_deg': cog_deg,
        'stw_kts': stw_kts
    }

if __name__ == "__main__":
    from scenario_generator import generate_fleet_telemetry
    
    df_fleet = generate_fleet_telemetry()
    
    # Test on V1 (MV ARABIAN DAWN) - Cooperative Prime Suspect
    df_v1 = df_fleet[df_fleet['mmsi'] == '538006890'].copy()
    
    result = process_cooperative_vessel(df_v1)
    
    print("Validation: Cooperative Vessel Reconstruction")
    print(f"MMSI: {result['mmsi']}")
    print(f"Time of CPA: {result['t_cpa']}")
    print(f"Distance at CPA: {result['d_cpa_km']:.3f} km")
    print(f"SOG at CPA: {result['sog_kts']:.2f} kts")
    print(f"COG at CPA: {result['cog_deg']:.2f} degrees")
    print(f"STW at CPA: {result['stw_kts']:.2f} kts")
    
    # Basic assertions against our theoretical synthetic fleet expectations
    assert result['d_cpa_km'] < 1.0, "V1 CPA should be less than 1.0 km"
    assert abs(result['cog_deg'] - 104.5) < 2.0, "V1 COG should be ~104.5 deg"
    
    # Ensure STW and SOG are distinct due to MetOcean subtraction
    assert abs(result['sog_kts'] - result['stw_kts']) > 0.1, "STW and SOG must differ due to current vector"
    
    print("Action 4: Cooperative Trajectory & CPA [PASSED]")

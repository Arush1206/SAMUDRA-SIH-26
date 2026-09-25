import pandas as pd
import numpy as np
import math
from typing import Dict, Any, List

from config import (
    SLICK_LOCATION_LAT, SLICK_LOCATION_LON, SLICK_ANGLE_DEG,
    SPILL_TIME_T0, T_SAT, SAR_RADAR_TARGETS,
    CURRENT_U_MS, CURRENT_V_MS, WIND_SPEED_MS, WIND_DIR_DEG, LEEWAY_FACTOR,
    DARK_CATCHMENT_RADIUS_KM, DARK_WINDOW_BEFORE_MIN, DARK_WINDOW_AFTER_MIN
)
from geo_utils import (
    vincenty_distance_km, latlon_to_xy_m, angular_difference_deg
)

def detect_dark_candidates(df_ais: pd.DataFrame) -> List[str]:
    """
    Identifies vessels whose AIS signal ceased within the dark catchment 
    window and spatial radius prior to the spill.
    Returns a list of candidate MMSIs.
    """
    t_start = SPILL_TIME_T0 - pd.Timedelta(minutes=DARK_WINDOW_BEFORE_MIN)
    t_end = SPILL_TIME_T0 - pd.Timedelta(minutes=DARK_WINDOW_AFTER_MIN)
    
    candidates = []
    
    for mmsi, group in df_ais.groupby('mmsi'):
        last_ping = group.sort_values('timestamp').iloc[-1]
        t_last = last_ping['timestamp']
        
        # Check temporal window (Signal lost around T - 30 min)
        if t_start <= t_last <= t_end:
            # Check spatial catchment
            dist = vincenty_distance_km(last_ping['lat'], last_ping['lon'], 
                                        SLICK_LOCATION_LAT, SLICK_LOCATION_LON)
            if dist <= DARK_CATCHMENT_RADIUS_KM:
                candidates.append(mmsi)
                
    return candidates

def _rk4_step(x_m: float, y_m: float, v_prop_x: float, v_prop_y: float, dt_sec: float) -> tuple[float, float]:
    """
    Performs a single 4th-Order Runge-Kutta integration step on the flat-earth Cartesian grid.
    Currently uses constant fields, but architecture supports time/space-varying NetCDF later.
    """
    # Wind vector (meteorological direction is where wind blows FROM)
    # Wind blowing FROM 290 deg means it blows TOWARD 110 deg
    wind_rad = math.radians(WIND_DIR_DEG)
    u_wind = -WIND_SPEED_MS * math.sin(wind_rad)
    v_wind = -WIND_SPEED_MS * math.cos(wind_rad)
    
    u_leeway = u_wind * LEEWAY_FACTOR
    v_leeway = v_wind * LEEWAY_FACTOR
    
    # Effective velocity field function
    def get_v_eff(pos_x, pos_y, t):
        eff_x = v_prop_x + CURRENT_U_MS + u_leeway
        eff_y = v_prop_y + CURRENT_V_MS + v_leeway
        return eff_x, eff_y
        
    t = 0.0 # Time independent for now
    
    k1_x, k1_y = get_v_eff(x_m, y_m, t)
    k2_x, k2_y = get_v_eff(x_m + 0.5 * dt_sec * k1_x, y_m + 0.5 * dt_sec * k1_y, t + 0.5 * dt_sec)
    k3_x, k3_y = get_v_eff(x_m + 0.5 * dt_sec * k2_x, y_m + 0.5 * dt_sec * k2_y, t + 0.5 * dt_sec)
    k4_x, k4_y = get_v_eff(x_m + dt_sec * k3_x, y_m + dt_sec * k3_y, t + dt_sec)
    
    new_x = x_m + (dt_sec / 6.0) * (k1_x + 2*k2_x + 2*k3_x + k4_x)
    new_y = y_m + (dt_sec / 6.0) * (k1_y + 2*k2_y + 2*k3_y + k4_y)
    
    return new_x, new_y

def simulate_dark_drift_rk4(df_vessel: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the full deterministic RK4 drift for a dark vessel from its last known ping
    to both the spill time (T0) and the satellite pass time (T_sat).
    """
    last_ping = df_vessel.sort_values('timestamp').iloc[-1]
    t_last = last_ping['timestamp']
    
    # Base reference for Cartesian projection (origin)
    ref_lat = last_ping['lat']
    ref_lon = last_ping['lon']
    
    x_m, y_m = 0.0, 0.0 # We start at the origin relative to ref_lat/ref_lon
    
    # Propulsion vectors from last SOG/COG (assume constant autopilot)
    sog_ms = last_ping['sog'] * 0.514444
    cog_rad = math.radians(last_ping['cog'])
    v_prop_x = sog_ms * math.sin(cog_rad)
    v_prop_y = sog_ms * math.cos(cog_rad)
    
    dt_sec = 60.0 # 1 minute steps
    
    # 1. Propagate to Spill Time (T0)
    seconds_to_t0 = (SPILL_TIME_T0 - t_last).total_seconds()
    steps_t0 = int(seconds_to_t0 // dt_sec)
    remainder_t0 = seconds_to_t0 % dt_sec
    
    for _ in range(steps_t0):
        x_m, y_m = _rk4_step(x_m, y_m, v_prop_x, v_prop_y, dt_sec)
    if remainder_t0 > 0:
        x_m, y_m = _rk4_step(x_m, y_m, v_prop_x, v_prop_y, remainder_t0)
        
    # Convert back to lat/lon for T0
    lat_t0 = ref_lat + (y_m / 111195.0)
    lon_t0 = ref_lon + (x_m / (111195.0 * math.cos(math.radians(ref_lat))))
    
    d_cpa = vincenty_distance_km(lat_t0, lon_t0, SLICK_LOCATION_LAT, SLICK_LOCATION_LON)
    
    # 2. Propagate to Satellite Time (T_sat)
    seconds_to_tsat = (T_SAT - SPILL_TIME_T0).total_seconds()
    steps_tsat = int(seconds_to_tsat // dt_sec)
    remainder_tsat = seconds_to_tsat % dt_sec
    
    for _ in range(steps_tsat):
        x_m, y_m = _rk4_step(x_m, y_m, v_prop_x, v_prop_y, dt_sec)
    if remainder_tsat > 0:
        x_m, y_m = _rk4_step(x_m, y_m, v_prop_x, v_prop_y, remainder_tsat)
        
    # Convert back to lat/lon for T_sat
    lat_tsat = ref_lat + (y_m / 111195.0)
    lon_tsat = ref_lon + (x_m / (111195.0 * math.cos(math.radians(ref_lat))))
    
    # 3. Radar Correlation at T_sat
    matched_radar_id = None
    min_radar_dist = float('inf')
    
    for radar in SAR_RADAR_TARGETS:
        dist = vincenty_distance_km(lat_tsat, lon_tsat, radar['lat'], radar['lon'])
        if dist < 2.0 and dist < min_radar_dist: # 2.0 km binary correlation threshold
            min_radar_dist = dist
            matched_radar_id = radar['target_id']
            
    return {
        'mmsi': last_ping['mmsi'],
        'shutoff_time': t_last,
        'd_cpa_km': d_cpa,
        'lat_t0': lat_t0,
        'lon_t0': lon_t0,
        'cog_deg': last_ping['cog'], # COG is preserved
        'sog_kts': last_ping['sog'], # SOG is preserved
        'radar_match': matched_radar_id,
        'radar_dist_km': min_radar_dist if matched_radar_id else None
    }


if __name__ == "__main__":
    from scenario_generator import generate_fleet_telemetry
    
    df_fleet = generate_fleet_telemetry()
    
    # Test Catchment Filter
    dark_suspects = detect_dark_candidates(df_fleet)
    print(f"Validation: Dark Candidates Detected: {dark_suspects}")
    assert '636092587' in dark_suspects, "V6 (Shadow Mariner) must be detected as dark!"
    assert '538009123' in dark_suspects, "V8 (Night Runner) must be detected as dark!"
    
    # Test V6 Drift Simulation (Prime Suspect)
    df_v6 = df_fleet[df_fleet['mmsi'] == '636092587'].copy()
    res_v6 = simulate_dark_drift_rk4(df_v6)
    
    print("\nValidation: V6 (SHADOW MARINER) RK4 Simulation")
    print(f"Simulated CPA to slick at T0: {res_v6['d_cpa_km']:.3f} km")
    print(f"Matched SAR Radar ID at T_sat: {res_v6['radar_match']}")
    
    assert res_v6['d_cpa_km'] < 2.5, "V6 should intersect the spill zone!"
    assert res_v6['radar_match'] == 'RADAR_TGT_01', "V6 should perfectly correlate with the radar target!"
    
    # Test V8 Drift Simulation (False Positive check)
    df_v8 = df_fleet[df_fleet['mmsi'] == '538009123'].copy()
    res_v8 = simulate_dark_drift_rk4(df_v8)
    
    print("\nValidation: V8 (NIGHT RUNNER) RK4 Simulation")
    print(f"Simulated CPA to slick at T0: {res_v8['d_cpa_km']:.3f} km")
    print(f"Matched SAR Radar ID at T_sat: {res_v8['radar_match']}")
    
    assert res_v8['d_cpa_km'] > 10.0, "V8 should be nowhere near the spill!"
    assert res_v8['radar_match'] is None, "V8 should NOT correlate with any radar target!"
    
    print("\nAction 5: Dark Vessel RK4 Simulation [PASSED]")

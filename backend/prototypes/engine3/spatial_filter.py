import h3
import pandas as pd
from typing import Set

# Uber H3 Resolution Level
# Resolution 8: Area ~0.73 km^2, Edge ~461m
H3_RESOLUTION = 8

def snap_to_h3(lat: float, lon: float, resolution: int = H3_RESOLUTION) -> str:
    """
    Snaps a geographic coordinate to its Uber H3 hexagonal cell index.
    Returns the hex string.
    """
    # h3.geo_to_h3 in older versions, but standard is latlng_to_cell in h3-py v3.7+
    # For h3 v3.7.x, the function is geo_to_h3
    try:
        return h3.geo_to_h3(lat, lon, resolution)
    except AttributeError:
        # Fallback for newer h3 versions (v4+)
        return h3.latlng_to_cell(lat, lon, resolution)

def get_attribution_disk(lat: float, lon: float, k: int = 3) -> Set[str]:
    """
    Generates a concentric hexagonal disk representing the forensic attribution catchment zone.
    k=3 yields 37 hexagons, covering approximately 2.5km radial distance.
    """
    center_hex = snap_to_h3(lat, lon)
    
    try:
        # h3 v3.7.x
        disk = h3.k_ring(center_hex, k)
    except AttributeError:
        # h3 v4+
        disk = h3.grid_disk(center_hex, k)
        
    return set(disk)

def get_radar_disk(lat: float, lon: float, k: int = 2) -> Set[str]:
    """
    Generates a concentric hexagonal disk for SAR radar target fusion.
    k=2 yields 19 hexagons, covering approximately 1.6 - 2.0km radial distance.
    """
    center_hex = snap_to_h3(lat, lon)
    
    try:
        disk = h3.k_ring(center_hex, k)
    except AttributeError:
        disk = h3.grid_disk(center_hex, k)
        
    return set(disk)

def filter_ais_by_h3_disk(df_ais: pd.DataFrame, h3_disk: Set[str]) -> pd.DataFrame:
    """
    O(1) Spatial Pre-Filter:
    Takes an AIS telemetry dataframe and drops all vessels that never intersect
    the provided H3 hexagonal disk.
    
    Expected DataFrame columns: ['mmsi', 'lat', 'lon']
    NOTE: Does NOT mutate the input DataFrame.
    """
    if df_ais.empty:
        return df_ais.copy()
        
    # Work on an internal copy to avoid mutating the caller's data
    df_work = df_ais.copy()
    
    # Map each AIS ping to its H3 cell
    df_work['h3_cell'] = df_work.apply(lambda row: snap_to_h3(row['lat'], row['lon']), axis=1)
        
    # Check which rows fall inside the disk (O(1) set lookup)
    df_work['in_disk'] = df_work['h3_cell'].isin(h3_disk)
    
    # Get MMSIs of vessels that have AT LEAST ONE ping inside the disk
    suspect_mmsis = df_work[df_work['in_disk']]['mmsi'].unique()
    
    # Return the full trajectory only for suspects, dropping temp columns
    df_candidates = df_work[df_work['mmsi'].isin(suspect_mmsis)].copy()
    df_candidates.drop(columns=['h3_cell', 'in_disk'], inplace=True, errors='ignore')
    
    return df_candidates


if __name__ == "__main__":
    # ─── VALIDATION TEST SCRIPT ───────────────────────────────────────────────
    # Scenario: Mumbai Offshore slick origin
    test_lat, test_lon = 19.11019, 72.88979
    
    radar_disk = get_radar_disk(test_lat, test_lon, k=2)
    attr_disk = get_attribution_disk(test_lat, test_lon, k=3)
    
    print("Validation: Uber H3 Spatial Pre-Filter")
    print(f"Radar Disk (k=2) Cell Count: {len(radar_disk)} (Expected: 19)")
    print(f"Attribution Disk (k=3) Cell Count: {len(attr_disk)} (Expected: 37)")
    
    assert len(radar_disk) == 19, "k=2 ring must produce exactly 19 hexagons!"
    assert len(attr_disk) == 37, "k=3 ring must produce exactly 37 hexagons!"
    
    # Mock AIS Data Test
    mock_data = {
        'mmsi': ['V1', 'V1', 'V2', 'V2'],
        'lat': [19.11020, 19.11030, 20.0, 20.1],  # V1 is inside, V2 is way off
        'lon': [72.88980, 72.88990, 73.0, 73.1]
    }
    df = pd.DataFrame(mock_data)
    
    filtered_df = filter_ais_by_h3_disk(df, attr_disk)
    remaining_mmsis = filtered_df['mmsi'].unique()
    
    print(f"Original vessels: {list(df['mmsi'].unique())}")
    print(f"Filtered vessels: {list(remaining_mmsis)}")
    
    assert 'V1' in remaining_mmsis, "Vessel 1 should have been kept!"
    assert 'V2' not in remaining_mmsis, "Vessel 2 should have been dropped!"
    
    print("Action 2: Uber H3 Spatial Pre-Filter [PASSED]")

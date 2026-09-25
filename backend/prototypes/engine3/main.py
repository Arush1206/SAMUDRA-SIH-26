import json
import math
import pandas as pd
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional

from config import SLICK_LOCATION_LAT, SLICK_LOCATION_LON
from scenario_generator import generate_fleet_telemetry
from spatial_filter import get_attribution_disk, filter_ais_by_h3_disk
from dark_vessel_model import detect_dark_candidates, simulate_dark_drift_rk4
from cooperative_model import process_cooperative_vessel
from ahp_scoring import score_vessel

# ─── PYDANTIC SCHEMAS (CONTRACT C) ────────────────────────────────────────────

class VesselScore(BaseModel):
    mmsi: str
    vessel_name: str
    vessel_type: str
    is_dark: bool
    d_cpa_km: float
    cog_deg: float
    sog_kts: float
    stw_kts: Optional[float] = None
    radar_match_id: Optional[str] = None
    composite_score: float
    probability_pct: Optional[float] = 0.0
    tier: str
    f_dist: float
    f_head: float
    f_anom: float
    f_type: float

class Engine3Response(BaseModel):
    scenario: str = "Mumbai Offshore Spill"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_vessels_processed: int = 0
    cooperative_count: int = 0
    dark_count: int = 0
    suspects: List[VesselScore] = []

# ─── MAIN ORCHESTRATOR ────────────────────────────────────────────────────────

def run_engine_3() -> str:
    """
    Executes the full Engine 3 pipeline and returns the JSON output path.
    All output is written to output_contract_c.json — no terminal output.
    """
    # 1. Load Data
    df_ais = generate_fleet_telemetry()
    
    results: List[VesselScore] = []
    
    # 2. Identify Dark Candidates
    dark_mmsis = detect_dark_candidates(df_ais)
    
    # 3. Process Cooperative Vessels (With H3 Spatial Pre-Filter)
    df_coop = df_ais[~df_ais['mmsi'].isin(dark_mmsis)]
    
    attr_disk = get_attribution_disk(SLICK_LOCATION_LAT, SLICK_LOCATION_LON, k=3)
    df_coop_filtered = filter_ais_by_h3_disk(df_coop, attr_disk)
    
    valid_coop_mmsis = df_coop_filtered['mmsi'].unique()
    
    for mmsi in valid_coop_mmsis:
        df_v = df_coop_filtered[df_coop_filtered['mmsi'] == mmsi]
        v_info = df_v.iloc[0]
        
        kinematics = process_cooperative_vessel(df_v)
        scores = score_vessel(
            vessel_type=v_info['type'],
            d_cpa_km=kinematics['d_cpa_km'],
            cog_deg=kinematics['cog_deg'],
            is_dark=False,
            stw_kts=kinematics['stw_kts']
        )
        
        results.append(VesselScore(
            mmsi=mmsi,
            vessel_name=v_info['vessel_name'],
            vessel_type=v_info['type'],
            is_dark=False,
            d_cpa_km=kinematics['d_cpa_km'],
            cog_deg=kinematics['cog_deg'],
            sog_kts=kinematics['sog_kts'],
            stw_kts=kinematics['stw_kts'],
            composite_score=scores['score'],
            tier=scores['tier'],
            f_dist=scores['f_dist'],
            f_head=scores['f_head'],
            f_anom=scores['f_anom'],
            f_type=scores['f_type']
        ))

    # 4. Process Dark Vessels (RK4 Physics Drift)
    for mmsi in dark_mmsis:
        df_v = df_ais[df_ais['mmsi'] == mmsi]
        v_info = df_v.iloc[0]
        
        kinematics = simulate_dark_drift_rk4(df_v)
        scores = score_vessel(
            vessel_type=v_info['type'],
            d_cpa_km=kinematics['d_cpa_km'],
            cog_deg=kinematics['cog_deg'],
            is_dark=True
        )
        
        results.append(VesselScore(
            mmsi=mmsi,
            vessel_name=v_info['vessel_name'],
            vessel_type=v_info['type'],
            is_dark=True,
            d_cpa_km=kinematics['d_cpa_km'],
            cog_deg=kinematics['cog_deg'],
            sog_kts=kinematics['sog_kts'],
            radar_match_id=kinematics['radar_match'],
            composite_score=scores['score'],
            tier=scores['tier'],
            f_dist=scores['f_dist'],
            f_head=scores['f_head'],
            f_anom=scores['f_anom'],
            f_type=scores['f_type']
        ))

    # 5. Sort Leaderboard
    results.sort(key=lambda x: x.composite_score, reverse=True)
    
    # 6. Softmax Normalization
    if results:
        temperature = 10.0
        max_score = results[0].composite_score
        exps = [math.exp((r.composite_score - max_score) / temperature) for r in results]
        sum_exps = sum(exps)
        for i, r in enumerate(results):
            r.probability_pct = round((exps[i] / sum_exps) * 100.0, 2)
            
    # 7. Assemble & Export JSON (Contract C)
    coop_count = sum(1 for r in results if not r.is_dark)
    dark_count = sum(1 for r in results if r.is_dark)
    
    export_payload = Engine3Response(
        total_vessels_processed=len(results),
        cooperative_count=coop_count,
        dark_count=dark_count,
        suspects=results
    )
    
    output_path = "output_contract_c.json"
    with open(output_path, "w") as f:
        f.write(export_payload.model_dump_json(indent=2))
        
    return output_path

if __name__ == "__main__":
    path = run_engine_3()
    print(path)

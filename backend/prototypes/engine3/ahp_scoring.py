import math
from typing import Dict, Any, Optional

from config import SLICK_ANGLE_DEG, SLICK_RADIUS_KM
from geo_utils import angular_difference_deg

# AHP Saaty Weights
W_DIST = 0.56
W_HEAD = 0.23
W_ANOM = 0.13
W_TYPE = 0.08

# F_type Risk Priors
VESSEL_RISK_PRIORS = {
    'Tanker': 1.00,
    'Bulk': 0.75,
    'Container': 0.75,
    'Cargo': 0.50,
    'Tug': 0.10,
    'Fishing': 0.10
}

def calculate_f_dist(d_cpa_km: float) -> float:
    """
    Computes proximity score using a Gaussian decay based on hydrodynamic 
    uncertainty (sigma_d = SLICK_RADIUS_KM).
    F_dist = exp(-0.5 * (d_CPA / sigma_d)^2)
    """
    return math.exp(-0.5 * (d_cpa_km / SLICK_RADIUS_KM)**2)

def calculate_f_heading(cog_deg: float) -> float:
    """
    Computes wake alignment score. Assumes bidirectional wake symmetry.
    F_heading = |cos(COG - SLICK_ANGLE)|
    """
    # Alternatively, using the angular difference function:
    diff_deg = angular_difference_deg(cog_deg, SLICK_ANGLE_DEG, symmetric=True)
    return abs(math.cos(math.radians(diff_deg)))

def calculate_f_anomaly(is_dark: bool, stw_kts: Optional[float] = None) -> float:
    """
    Computes statutory anomaly score.
    - Dark vessels automatically get 1.0 (AIS Shutoff violation).
    - Cooperative vessels are evaluated against MARPOL Annex I discharge 
      envelope [6.0, 14.0] kts using Speed Through Water (STW).
    """
    if is_dark:
        return 1.00
        
    if stw_kts is None:
        return 0.00
        
    if 6.0 <= stw_kts <= 14.0:
        return 1.00
        
    # Gaussian decay outside the boundary
    if stw_kts < 6.0:
        dist = 6.0 - stw_kts
    else:
        dist = stw_kts - 14.0
        
    return math.exp(-0.1 * (dist**2))

def score_vessel(vessel_type: str, d_cpa_km: float, cog_deg: float, is_dark: bool, stw_kts: Optional[float] = None) -> Dict[str, Any]:
    """
    Applies the AHP composite weighting matrix to the component metrics to 
    generate the final suspect tier.
    """
    f_dist = calculate_f_dist(d_cpa_km)
    f_head = calculate_f_heading(cog_deg)
    f_anom = calculate_f_anomaly(is_dark, stw_kts)
    f_type = VESSEL_RISK_PRIORS.get(vessel_type, 0.10)
    
    composite_score = 100.0 * (
        W_DIST * f_dist +
        W_HEAD * f_head +
        W_ANOM * f_anom +
        W_TYPE * f_type
    )
    
    tier = 'LOW'
    if composite_score >= 80.0:
        tier = 'HIGH'
    elif composite_score >= 50.0:
        tier = 'MEDIUM'
        
    return {
        'f_dist': f_dist,
        'f_head': f_head,
        'f_anom': f_anom,
        'f_type': f_type,
        'score': composite_score,
        'tier': tier
    }


if __name__ == "__main__":
    # ─── VALIDATION TEST SCRIPT ───────────────────────────────────────────────
    
    # 1. Test Prime Cooperative Suspect (V1)
    # Target: High F_dist (d_cpa < 1km), High F_head (aligned to 104.5), High F_anom (STW ~9.8kts)
    v1_score = score_vessel(
        vessel_type='Tanker',
        d_cpa_km=0.80,
        cog_deg=104.5,
        is_dark=False,
        stw_kts=9.8
    )
    
    print("Validation: V1 (Prime Cooperative Suspect)")
    print(f"Score: {v1_score['score']:.1f} | Tier: {v1_score['tier']}")
    assert v1_score['tier'] == 'HIGH', "V1 must be in HIGH tier!"
    
    # 2. Test Prime Dark Suspect (V6)
    # Target: High F_dist (d_cpa ~1.2km), High F_head (318 deg vs 104.5 is ~33 deg diff -> cos(33) = 0.83), F_anom = 1.0 (Dark)
    v6_score = score_vessel(
        vessel_type='Tanker',
        d_cpa_km=1.20,
        cog_deg=318.0,
        is_dark=True
    )
    
    print("\nValidation: V6 (Prime Dark Suspect)")
    print(f"Score: {v6_score['score']:.1f} | Tier: {v6_score['tier']}")
    assert v6_score['tier'] == 'HIGH', "V6 must be in HIGH tier!"
    
    # 3. Test Innocent Transit (V2)
    # Target: Low F_dist (d_cpa > 6km), F_anom penalty (STW > 21kts)
    v2_score = score_vessel(
        vessel_type='Container',
        d_cpa_km=6.55,
        cog_deg=45.0,
        is_dark=False,
        stw_kts=21.1
    )
    
    print("\nValidation: V2 (Innocent Transit)")
    print(f"Score: {v2_score['score']:.1f} | Tier: {v2_score['tier']}")
    assert v2_score['tier'] == 'LOW', "V2 must be in LOW tier!"
    
    print("\nAction 6: AHP Multi-Factor Scoring [PASSED]")

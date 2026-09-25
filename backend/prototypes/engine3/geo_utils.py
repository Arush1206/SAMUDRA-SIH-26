import math
from typing import Tuple

# WGS-84 Reference Ellipsoid Constants
WGS84_A = 6378137.0           # semi-major axis in meters
WGS84_B = 6356752.314245      # semi-minor axis in meters
WGS84_F = 1 / 298.257223563   # flattening

# Spherical Earth Radius for Haversine
EARTH_RADIUS_KM = 6371.0


def _vincenty_inverse(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float, float]:
    """
    Solves the inverse geodesic problem using Vincenty's formulae on WGS-84.
    Returns (distance_in_meters, initial_bearing_deg, final_bearing_deg).
    If points are nearly identical, returns (0.0, 0.0, 0.0).
    """
    # Convert degrees to radians
    phi1, L1 = math.radians(lat1), math.radians(lon1)
    phi2, L2 = math.radians(lat2), math.radians(lon2)
    
    L = L2 - L1
    
    # Reduced latitudes
    U1 = math.atan((1 - WGS84_F) * math.tan(phi1))
    U2 = math.atan((1 - WGS84_F) * math.tan(phi2))
    
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)
    
    lambda_val = L
    lambda_prime = 0.0
    iterations = 0
    max_iterations = 200
    converged = False
    
    sin_lambda = 0.0
    cos_lambda = 0.0
    sin_sigma = 0.0
    cos_sigma = 0.0
    sigma = 0.0
    sin_alpha = 0.0
    cos_sq_alpha = 0.0
    cos2_sigma_m = 0.0
    
    while abs(lambda_val - lambda_prime) > 1e-12 and iterations < max_iterations:
        lambda_prime = lambda_val
        sin_lambda, cos_lambda = math.sin(lambda_val), math.cos(lambda_val)
        
        sin_sigma = math.sqrt((cosU2 * sin_lambda)**2 + 
                              (cosU1 * sinU2 - sinU1 * cosU2 * cos_lambda)**2)
        
        if sin_sigma == 0:
            # Co-incident points
            return 0.0, 0.0, 0.0
            
        cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cos_lambda
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cosU1 * cosU2 * sin_lambda / sin_sigma
        cos_sq_alpha = 1 - sin_alpha**2
        
        if cos_sq_alpha == 0:
            cos2_sigma_m = 0.0  # Equatorial line
        else:
            cos2_sigma_m = cos_sigma - 2 * sinU1 * sinU2 / cos_sq_alpha
            
        C = WGS84_F / 16 * cos_sq_alpha * (4 + WGS84_F * (4 - 3 * cos_sq_alpha))
        lambda_val = L + (1 - C) * WGS84_F * sin_alpha * \
            (sigma + C * sin_sigma * (cos2_sigma_m + C * cos_sigma * (-1 + 2 * cos2_sigma_m**2)))
        
        iterations += 1
        
    if iterations == max_iterations:
        raise ValueError("Vincenty formula failed to converge")
        
    u_sq = cos_sq_alpha * (WGS84_A**2 - WGS84_B**2) / (WGS84_B**2)
    A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sigma = B * sin_sigma * (cos2_sigma_m + B / 4 * (cos_sigma * (-1 + 2 * cos2_sigma_m**2) - 
                  B / 6 * cos2_sigma_m * (-3 + 4 * sin_sigma**2) * (-3 + 4 * cos2_sigma_m**2)))
                  
    distance_m = WGS84_B * A * (sigma - delta_sigma)
    
    initial_bearing = math.atan2(cosU2 * sin_lambda, 
                                 cosU1 * sinU2 - sinU1 * cosU2 * cos_lambda)
    final_bearing = math.atan2(cosU1 * sin_lambda, 
                               -sinU1 * cosU2 + cosU1 * sinU2 * cos_lambda)
                               
    initial_bearing = (math.degrees(initial_bearing) + 360) % 360
    final_bearing = (math.degrees(final_bearing) + 360) % 360
    
    return distance_m, initial_bearing, final_bearing


def vincenty_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns the forensic-grade geodesic distance between two points in kilometers on the WGS-84 ellipsoid."""
    dist_m, _, _ = _vincenty_inverse(lat1, lon1, lat2, lon2)
    return dist_m / 1000.0


def vincenty_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns the forward azimuth (initial bearing) in degrees from point 1 to point 2."""
    _, bearing, _ = _vincenty_inverse(lat1, lon1, lat2, lon2)
    return bearing


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns the spherical distance between two points in kilometers.
    Used exclusively as a fast pre-filter for H3 disk tagging.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def latlon_to_xy_m(lat: float, lon: float, ref_lat: float, ref_lon: float) -> Tuple[float, float]:
    """
    Projects geographic coordinates to an equirectangular flat-earth Cartesian grid in meters.
    Useful for local spatial search (KD-Tree) and local vector kinematics (RK4).
    """
    # 1 degree of latitude is roughly 111,195 meters
    lat_rad = math.radians(ref_lat)
    x_m = (lon - ref_lon) * 111195.0 * math.cos(lat_rad)
    y_m = (lat - ref_lat) * 111195.0
    return x_m, y_m


def angular_difference_deg(angle1: float, angle2: float, symmetric: bool = True) -> float:
    """
    Computes the minimum absolute angular difference between two degrees.
    If symmetric=True (e.g., wake alignments), difference wraps at 180 as well as 360.
    """
    diff = abs((angle1 - angle2) % 360)
    diff = diff if diff <= 180 else 360 - diff
    if symmetric:
        diff = diff if diff <= 90 else 180 - diff
    return diff


if __name__ == "__main__":
    # ─── VALIDATION TEST SCRIPT ───────────────────────────────────────────────
    # Benchmark: Mumbai to Tokyo approx distance
    pt1 = (19.0760, 72.8777)
    pt2 = (35.6895, 139.6917)
    
    v_dist = vincenty_distance_km(*pt1, *pt2)
    h_dist = haversine_km(*pt1, *pt2)
    error_pct = abs(v_dist - h_dist) / v_dist * 100
    
    print(f"Validation: WGS-84 Vincenty vs Spherical Haversine")
    print(f"Vincenty Distance: {v_dist:.3f} km")
    print(f"Haversine Distance: {h_dist:.3f} km")
    print(f"Deviation Error: {error_pct:.3f}% (Expected: ~0.3 - 0.5%)")
    
    assert 0.2 < error_pct < 0.6, "Haversine deviation outside expected spherical error bounds!"
    
    # Validation: Symmetric angle (e.g. slick axis at 10 degrees, vessel heading at 190 degrees = 0 difference)
    assert angular_difference_deg(10, 190, symmetric=True) == 0.0
    assert angular_difference_deg(350, 10, symmetric=False) == 20.0
    
    print("Action 1: Geodesic Math Core [PASSED]")

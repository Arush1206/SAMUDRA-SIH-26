import pandas as pd
from datetime import datetime

def generate_fleet_telemetry() -> pd.DataFrame:
    """
    Generates a Pandas DataFrame containing the synthetic 8-vessel fleet telemetry
    for the Mumbai Offshore 2026-09-22 scenario.
    """
    raw_data = [
        # V1: MV ARABIAN DAWN (Cooperative, Prime Suspect)
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.2002, 'lon': 72.5461, 'sog': 10.3, 'cog': 104.2},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.1789, 'lon': 72.6332, 'sog': 10.1, 'cog': 104.7},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.1576, 'lon': 72.7206, 'sog': 10.2, 'cog': 104.5},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.1363, 'lon': 72.8078, 'sog': 10.4, 'cog': 104.3},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.1150, 'lon': 72.8950, 'sog': 10.2, 'cog': 104.5},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.0937, 'lon': 72.9822, 'sog': 10.1, 'cog': 104.6},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 19.0724, 'lon': 73.0694, 'sog': 10.3, 'cog': 104.4},
        {'mmsi': '538006890', 'vessel_name': 'MV ARABIAN DAWN', 'type': 'Tanker', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 19.0369, 'lon': 73.2001, 'sog': 10.2, 'cog': 104.5},

        # V2: MV PACIFIC MERCHANT (Cooperative, Innocent)
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 18.9628, 'lon': 72.8278, 'sog': 21.6, 'cog': 44.8},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 18.9886, 'lon': 72.8534, 'sog': 21.4, 'cog': 45.2},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.0139, 'lon': 72.8789, 'sog': 21.5, 'cog': 45.0},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.0393, 'lon': 72.9045, 'sog': 21.3, 'cog': 44.9},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.0650, 'lon': 72.9300, 'sog': 21.5, 'cog': 45.0},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.0904, 'lon': 72.9556, 'sog': 21.6, 'cog': 45.1},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 19.1157, 'lon': 72.9811, 'sog': 21.4, 'cog': 45.0},
        {'mmsi': '477998100', 'vessel_name': 'MV PACIFIC MERCHANT', 'type': 'Container', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 19.1792, 'lon': 73.0450, 'sog': 21.5, 'cog': 45.0},

        # V3: MV KRISHNA SAGAR (Cooperative, Medium)
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.2244, 'lon': 72.4915, 'sog': 11.9, 'cog': 117.8},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.1996, 'lon': 72.5858, 'sog': 11.7, 'cog': 118.2},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.1747, 'lon': 72.6802, 'sog': 11.8, 'cog': 118.0},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.1499, 'lon': 72.7752, 'sog': 11.6, 'cog': 118.3},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.1250, 'lon': 72.8700, 'sog': 11.8, 'cog': 118.0},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.1002, 'lon': 72.9643, 'sog': 11.9, 'cog': 117.9},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 19.0753, 'lon': 73.0587, 'sog': 11.7, 'cog': 118.1},
        {'mmsi': '419001234', 'vessel_name': 'MV KRISHNA SAGAR', 'type': 'Bulk', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 19.0319, 'lon': 73.2003, 'sog': 11.8, 'cog': 118.0},

        # V4: MV COASTAL PRIDE (Cooperative, Low)
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.3554, 'lon': 72.8738, 'sog': 8.6, 'cog': 184.8},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.2862, 'lon': 72.8706, 'sog': 8.4, 'cog': 185.3},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.2170, 'lon': 72.8672, 'sog': 8.5, 'cog': 185.0},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.1475, 'lon': 72.8637, 'sog': 8.3, 'cog': 185.2},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.0780, 'lon': 72.8600, 'sog': 8.5, 'cog': 185.0},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.0088, 'lon': 72.8563, 'sog': 8.6, 'cog': 184.9},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 18.9396, 'lon': 72.8531, 'sog': 8.4, 'cog': 185.1},
        {'mmsi': '419007654', 'vessel_name': 'MV COASTAL PRIDE', 'type': 'Cargo', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 18.8357, 'lon': 72.8472, 'sog': 8.5, 'cog': 185.0},

        # V5: FV SEA HARVEST (Cooperative, Outlier)
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.0533, 'lon': 72.9098, 'sog': 1.8, 'cog': 338.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.0694, 'lon': 72.9035, 'sog': 2.3, 'cog': 342.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.0857, 'lon': 72.8968, 'sog': 0.8, 'cog': 15.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.0990, 'lon': 72.8928, 'sog': 2.4, 'cog': 335.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.1180, 'lon': 72.8850, 'sog': 2.1, 'cog': 340.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.1304, 'lon': 72.8792, 'sog': 1.9, 'cog': 343.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 19.1396, 'lon': 72.8760, 'sog': 2.2, 'cog': 338.0},
        {'mmsi': '419002345', 'vessel_name': 'FV SEA HARVEST', 'type': 'Fishing', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 19.1607, 'lon': 72.8668, 'sog': 2.0, 'cog': 341.0},

        # V6: MV SHADOW MARINER (Dark Vessel, Prime Suspect) - Terminates at 01:30
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 18.8720, 'lon': 73.1500, 'sog': 13.4, 'cog': 318.5},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:15:00Z', 'lat': 18.8958, 'lon': 73.1290, 'sog': 13.6, 'cog': 317.8},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 18.9195, 'lon': 73.1078, 'sog': 13.5, 'cog': 318.2},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:45:00Z', 'lat': 18.9433, 'lon': 73.0866, 'sog': 13.3, 'cog': 318.6},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 18.9670, 'lon': 73.0655, 'sog': 13.5, 'cog': 318.0},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:15:00Z', 'lat': 18.9908, 'lon': 73.0443, 'sog': 13.6, 'cog': 317.9},
        {'mmsi': '636092587', 'vessel_name': 'MV SHADOW MARINER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.0145, 'lon': 73.0231, 'sog': 13.5, 'cog': 318.0},

        # V7: TUG MUMBAI GUARDIAN (Cooperative, Outlier)
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.2133, 'lon': 72.5738, 'sog': 7.6, 'cog': 105.8},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.1975, 'lon': 72.6396, 'sog': 7.4, 'cog': 106.3},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.1816, 'lon': 72.7054, 'sog': 7.5, 'cog': 106.0},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T01:30:00Z', 'lat': 19.1658, 'lon': 72.7702, 'sog': 7.3, 'cog': 106.2},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T02:00:00Z', 'lat': 19.1500, 'lon': 72.8350, 'sog': 7.5, 'cog': 106.0},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T02:30:00Z', 'lat': 19.1342, 'lon': 72.9008, 'sog': 7.6, 'cog': 105.9},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T03:00:00Z', 'lat': 19.1183, 'lon': 72.9666, 'sog': 7.4, 'cog': 106.1},
        {'mmsi': '419009876', 'vessel_name': 'TUG MUMBAI GUARDIAN', 'type': 'Tug', 'timestamp': '2026-09-22T04:15:00Z', 'lat': 19.0935, 'lon': 73.0653, 'sog': 7.5, 'cog': 106.0},
        
        # V8: MV NIGHT RUNNER (Dark Vessel, Cleared) - Terminates at 01:32
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:00:00Z', 'lat': 19.3212, 'lon': 72.9390, 'sog': 12.1, 'cog': 209.7},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:15:00Z', 'lat': 19.2977, 'lon': 72.9265, 'sog': 11.9, 'cog': 210.3},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:30:00Z', 'lat': 19.2741, 'lon': 72.9142, 'sog': 12.0, 'cog': 210.0},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T00:45:00Z', 'lat': 19.2505, 'lon': 72.9017, 'sog': 12.2, 'cog': 209.8},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:00:00Z', 'lat': 19.2268, 'lon': 72.8893, 'sog': 12.0, 'cog': 210.1},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:15:00Z', 'lat': 19.2033, 'lon': 72.8770, 'sog': 11.8, 'cog': 210.2},
        {'mmsi': '538009123', 'vessel_name': 'MV NIGHT RUNNER', 'type': 'Tanker', 'timestamp': '2026-09-22T01:32:00Z', 'lat': 19.1600, 'lon': 72.8200, 'sog': 12.0, 'cog': 210.0},
    ]
    
    df = pd.DataFrame(raw_data)
    
    # Convert string timestamps to actual datetime objects in UTC
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df

if __name__ == "__main__":
    df_fleet = generate_fleet_telemetry()
    
    print(f"Validation: Synthetic Scenario Generator")
    print(f"Total Rows: {len(df_fleet)}")
    print(f"Total Unique Vessels: {df_fleet['mmsi'].nunique()} (Expected: 8)")
    print(f"Columns: {list(df_fleet.columns)}")
    
    assert df_fleet['mmsi'].nunique() == 8, "Expected exactly 8 vessels in the fleet"
    
    # Verify dark vessel cutoff
    v6 = df_fleet[df_fleet['mmsi'] == '636092587']
    v6_max_time = v6['timestamp'].max()
    assert v6_max_time == pd.Timestamp('2026-09-22T01:30:00Z'), "V6 must terminate at exactly 01:30Z"
    
    print("Action 3: Scenario Generator [PASSED]")

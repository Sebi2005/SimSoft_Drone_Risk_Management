import math
from airspace_manager import AirspaceManager

airspace = AirspaceManager()


def get_heading(history):
    if len(history) < 2: return 0
    p1, p2 = history[-2], history[-1]
    lat1, lon1 = math.radians(p1['lat']), math.radians(p1['lng'])
    lat2, lon2 = math.radians(p2['lat']), math.radians(p2['lng'])
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def get_proximity_trend(history, current_alt):
    if current_alt <= 0:
        return "🛑 STATIONARY"

    if len(history) < 10:  # Need enough data points for a stable trend
        return "STABLE"

    # Compare current distance vs distance 10 points ago
    current_pos = history[-1]
    past_pos = history[-10]

    current_dist = airspace.get_distance_to_closest_zone_3d(current_pos['lat'], current_pos['lng'], current_alt)[0]
    past_dist = airspace.get_distance_to_closest_zone_3d(past_pos['lat'], past_pos['lng'], current_alt)[0]

    diff = current_dist - past_dist

    if diff < -5: return "🔻 CLOSING"  # Distance is decreasing
    if diff > 5:  return "🔹 RECEDING"  # Distance is increasing
    return "↔️ HOVERING"


def assess_risk(drone):
    pos = drone.get('droneData', {}).get('location', {})
    lat, lng = pos.get('lat'), pos.get('lng')
    alt = drone.get('droneData', {}).get('altitudes', {}).get('agl', 0) or 0

    dist_to_zone, zone_name = airspace.get_distance_to_closest_zone_3d(lat, lng, alt)

    if dist_to_zone == 0:
        status, reason = "🔴 CRITICAL", f"BREACH: {zone_name}"
    elif dist_to_zone < 500:
        status, reason = "🟡 WARNING", f"Near {zone_name}"
    elif alt > 60:
        status, reason = "🟡 WARNING", "Altitude Violation"
    else:
        status, reason = "🟢 CLEAR", "Normal Ops"

    history = drone.get('history', [])
    trend = get_proximity_trend(history, alt)
    heading = get_heading(history)

    return status, dist_to_zone, trend, heading, alt, reason, zone_name
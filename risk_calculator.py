import math
from ai_predictor import AIDronePredictor
from airspace_manager import AirspaceManager  # Assuming this is your class name
from training_utils import get_heading

# Initialize AI and Airspace once
drone_ai = AIDronePredictor('drone_model.h5')
airspace = AirspaceManager()


def assess_risk(d, history):
    """
    Returns: status, dist, trend, hdg, alt, reason, zone, speed, ai_path
    """
    # 1. Basic Data Extraction
    drone_data = d.get('droneData', {})
    loc = drone_data.get('location', {})
    lat = loc.get('lat', 0)
    lng = loc.get('lng', 0)
    alt = drone_data.get('altitudes', {}).get('agl', 0)
    speed = drone_data.get('groundSpeed', 0)
    v_speed = drone_data.get('verticalSpeed', 0)
    hdg = get_heading(history)

    # 2. Current Status Check
    dist, zone_name = airspace.get_distance_to_closest_zone_3d(lat, lng, alt)

    status = "🟢 SAFE"
    reason = "Normal flight"
    ai_path = None

    if dist == 0:
        status = "🔴 CRITICAL BREACH"
        reason = f"Inside {zone_name}"

    # 3. AI Predictive Analysis (The "Sleek" Move)
    elif len(history) >= 10:
        ai_path = drone_ai.predict_path(history)
        if ai_path is not None:
            for i, point in enumerate(ai_path):
                f_lat, f_lng, f_alt = point
                f_dist, f_zone = airspace.get_distance_to_closest_zone_3d(f_lat, f_lng, f_alt)

                if f_dist < 50:
                    status = "🟣 PREDICTIVE"
                    seconds = i + 1
                    reason = f"Collision with {f_zone} in ~{seconds}s"
                    break

    # 4. Proximity Warning Fallback
    if status == "🟢 SAFE" and dist < 300:
        status = "🟡 WARNING"
        reason = f"Close to {zone_name}"

    # Return 9-tuple for radar.py
    return status, dist, "STABLE", hdg, alt, reason, zone_name, speed, ai_path
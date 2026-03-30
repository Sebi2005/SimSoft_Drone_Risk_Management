import requests
import time
import os
import csv
import math
from risk_calculator import assess_risk
from config import (
    SENSOR_URL,
    TOKEN_IANNIS,
    DRONE_BODY_RADIUS_M,
    ARROW_TIP_M,
    ARROW_WIDTH_M,
    ARROW_BACK_M
)
from utils import get_status_color

# Persistence for state tracking
if 'active_missions' not in globals():
    active_missions = {}
if 'drone_alert_states' not in globals():
    drone_alert_states = {}
# --- 🧠 AI PERSISTENCE ADDED ---
if 'drone_history_buffer' not in globals():
    drone_history_buffer = {}

import random


def generate_synthetic_data():
    """Generates 10 artificial drones around Cluj-Napoca for UI testing."""
    synthetic_drones = []
    # Center of Cluj
    base_lat, base_lng = 46.77, 23.60

    for i in range(3):
        sn = f"TEST-DRONE-{i:03d}"
        # Spread them out
        lat = base_lat + random.uniform(-0.03, 0.03)
        lng = base_lng + random.uniform(-0.03, 0.03)

        # Give some drones high speed to trigger the AI
        speed = random.choice([5, 12, 25, 40])
        heading = random.uniform(0, 360)

        synthetic_drones.append({
            "serial": sn,
            "droneId": f"ALPHA-{i}",
            "pilotId": f"PILOT-{random.randint(100, 999)}",
            "droneData": {
                "location": {"lat": lat, "lng": lng},
                "altitudes": {"agl": random.randint(40, 200)},
                "groundSpeed": speed,
                "verticalSpeed": random.choice([-2, 0, 5]),
                "heading": heading
            }
        })
    return synthetic_drones


def log_incident(drone_id, status, dist, trend, reason):
    global drone_alert_states
    if drone_alert_states.get(drone_id) == status:
        return
    drone_alert_states[drone_id] = status
    file_path = 'drone_incidents.csv'
    try:
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            if not file_exists:
                writer.writerow(['Date', 'Timestamp', 'Drone ID', 'Status', 'Distance', 'Trend', 'Reason'])
            writer.writerow(
                [time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), drone_id, status, dist, trend, reason])
    except Exception as e:
        print(f"Log Error: {e}")


def status_priority(status):
    """
    Assigns a numerical rank to statuses for sorting and UI prominence.
    Higher number = Higher urgency.
    """
    s = str(status).upper()

    # 1. Active Emergency (Red)
    if "CRITICAL" in s or "BREACH" in s:
        return 4

    # 2. AI Intercept (Purple) - High Stakes Proactive Alert
    if "PREDICTIVE" in s:
        return 3

    # 3. Proximity Caution (Yellow)
    if "WARNING" in s:
        return 2

    # 4. Routine Operations (Green)
    return 1


def build_heading_arrow_polygon(lat, lng, heading_deg, tip_m=180, width_m=120, back_m=40):
    """
    Builds a small triangular arrow polygon connected to the drone point.
    """
    if lat is None or lng is None:
        return []

    try:
        heading = float(heading_deg or 0)
    except Exception:
        heading = 0.0

    def project(lat0, lng0, bearing_deg, dist_m):
        rad = math.radians(bearing_deg)
        dlat = (dist_m * math.cos(rad)) / 111320.0
        dlng = (dist_m * math.sin(rad)) / (111320.0 * math.cos(math.radians(lat0)))
        return [lng0 + dlng, lat0 + dlat]

    tip = project(lat, lng, heading, tip_m)
    left_base = project(lat, lng, heading + 140, width_m)
    right_base = project(lat, lng, heading - 140, width_m)
    tail = project(lat, lng, heading + 180, back_m)

    return [tip, left_base, tail, right_base]


def process_drones_for_ui():
    global drone_history_buffer
    headers = {"Authorization": f"Bearer {TOKEN_IANNIS}"}
    try:
        resp = requests.get(f"{SENSOR_URL}/api/fused-data/map/50000/0", headers=headers, timeout=5)
        raw_data = resp.json()
        if not raw_data or not isinstance(raw_data, list):
            raw_data = generate_synthetic_data()
    except Exception:
        raw_data = generate_synthetic_data()

    unique_drones = {}
    if not isinstance(raw_data, list):
        return []

    for d in raw_data:
        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn:
            continue

        drone_id = d.get('droneId') or sn

        # --- 🧠 UPDATE AI HISTORY BUFFER ---
        if sn not in drone_history_buffer:
            drone_history_buffer[sn] = []

        curr_lat = d.get('droneData', {}).get('location', {}).get('lat')
        curr_lng = d.get('droneData', {}).get('location', {}).get('lng')

        drone_history_buffer[sn].append({
            'lat': curr_lat,
            'lng': curr_lng,
            'droneData': d.get('droneData', {})
        })

        if len(drone_history_buffer[sn]) > 10:
            drone_history_buffer[sn].pop(0)

        # --- 🛡️ RUN ENHANCED RISK ASSESSMENT ---
        # Passing history to get the 9-tuple return including ai_path
        status, dist, trend, hdg, alt, reason, zone, speed, ai_path = assess_risk(d, drone_history_buffer[sn])

        log_incident(drone_id, status, dist, trend, reason)

        # Heading arrow uses the heading calculated by the AI/History
        heading_arrow = build_heading_arrow_polygon(
            curr_lat,
            curr_lng,
            hdg,
            tip_m=ARROW_TIP_M,
            width_m=ARROW_WIDTH_M,
            back_m=ARROW_BACK_M
        )

        pilot_lat = d.get('pilotData', {}).get('location', {}).get('lat')
        pilot_lng = d.get('pilotData', {}).get('location', {}).get('lng')

        ai_path_for_map = []

        # Calculate Future Lat/Lng from AI if available, else fallback
        if ai_path is not None:
            ai_path_clean = ai_path.tolist() if hasattr(ai_path, 'tolist') else ai_path
            f_lat, f_lng = ai_path_clean[-1][0], ai_path_clean[-1][1]
            ai_path_for_map = [[p[1], p[0], p[2]] for p in ai_path_clean]
        else:
            # Simple projection fallback for new drones
            rad_hdg = math.radians(hdg or 0)
            f_lat = curr_lat + (speed * 20 * math.cos(rad_hdg)) / 111320.0
            f_lng = curr_lng + (speed * 20 * math.sin(rad_hdg)) / (111320.0 * math.cos(math.radians(curr_lat)))

        history_list = [[p['lng'], p['lat'], p.get('droneData', {}).get('altitudes', {}).get('agl', 0)]
                        for p in drone_history_buffer[sn]]

        unique_drones[sn] = {
            "Drone ID": drone_id,
            "Pilot ID": d.get('pilotId') or d.get('pilotData', {}).get('id', 'Unknown'),
            "Status": status,
            "Distance (m)": int(dist),
            "Trend": trend,
            "Heading (°)": int(hdg) if hdg is not None else 0,
            "Altitude AGL": alt,
            "Latitude": curr_lat,
            "Longitude": curr_lng,
            "Future_Lat": f_lat,
            "Future_Lng": f_lng,
            "Pilot_Lat": pilot_lat,
            "Pilot_Lng": pilot_lng,
            "heading_arrow": heading_arrow,
            "Speed": speed,
            "Reasons": reason,
            "Zone": zone,
            "Label": f"{drone_id} ({alt}m)",
            "color": get_status_color(status),
            "elevation": alt,
            "raw": d,
            "ai_path": ai_path_for_map,
            "history_path": history_list,
            "pilot_link": [[pilot_lng, pilot_lat], [curr_lng, curr_lat]] if pilot_lat else []
        }

    # Sort by priority before returning to UI
    final_list = list(unique_drones.values())
    final_list.sort(key=lambda x: status_priority(x['Status']), reverse=True)
    return final_list


def reset_radar_state():
    global active_missions, drone_alert_states, drone_history_buffer
    active_missions.clear()
    drone_alert_states.clear()
    drone_history_buffer.clear()
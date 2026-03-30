import math
import numpy as np

def get_heading(history):
    """Calculates bearing between the last two points in history."""
    if len(history) < 2: return 0
    p1, p2 = history[-2], history[-1]
    lat1, lon1 = math.radians(p1['lat']), math.radians(p1['lng'])
    lat2, lon2 = math.radians(p2['lat']), math.radians(p2['lng'])

    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def normalize_sequence(history):
    if len(history) < 10: return None

    raw = []
    for i in range(len(history) - 10, len(history)):
        curr = history[i]
        prev = history[i - 1] if i > 0 else curr

        heading = get_heading([prev, curr])
        d_data = curr.get('droneData', {})

        raw.append([
            curr['lat'],
            curr['lng'],
            d_data.get('altitudes', {}).get('agl', 0),
            heading,
            d_data.get('groundSpeed', 0),
            d_data.get('verticalSpeed', 0)
        ])

    coords = np.array(raw)
    origin = coords[-1, :3].copy()

    coords[:, :3] -= origin
    coords[:, 0] *= 111139
    coords[:, 1] *= 77000

    coords[:, 3] /= 360.0
    coords[:, 4] /= 30.0
    coords[:, 5] /= 10.0

    return coords, origin
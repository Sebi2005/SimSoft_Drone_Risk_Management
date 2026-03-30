import numpy as np


def normalize_sequence(history):
    """
    Converts a list of history points into a 6-feature normalized
    numpy array for the AI model.
    """
    if len(history) < 10: return None, None

    # 1. Establish the 3D origin for denormalization later
    last_point = history[-1]
    last_alt = last_point.get('droneData', {}).get('altitudes', {}).get('agl', 0)
    origin = np.array([last_point['lat'], last_point['lng'], last_alt])

    # 2. Build the 6-column feature set
    seq = []
    for p in history[-10:]:
        d_data = p.get('droneData', {})

        # Feature 1 & 2: Relative Lat/Lng
        lat_rel = p['lat'] - origin[0]
        lng_rel = p['lng'] - origin[1]

        # Feature 3: Altitude
        alt = d_data.get('altitudes', {}).get('agl', 0)

        # Feature 4: Ground Speed
        gs = d_data.get('groundSpeed', 0)

        # Feature 5: Vertical Speed
        vs = d_data.get('verticalSpeed', 0)

        # Feature 6: Heading (check root or nested)
        hdg = p.get('heading') if p.get('heading') is not None else d_data.get('heading', 0)

        seq.append([lat_rel, lng_rel, alt, gs, vs, hdg])

    relative_coords = np.array(seq, dtype=np.float32)

    # 3. Scaling (Matches your training logic)
    relative_coords[:, 0] *= 111139  # Lat to Meters
    relative_coords[:, 1] *= 77000  # Lng to Meters

    return relative_coords, origin
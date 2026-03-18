import json
import math
import pandas as pd
from shapely.geometry import shape, Point
from utils import parse_altitude


class AirspaceManager:
    def __init__(self, file_path='zone_restriction_uav.json'):
        self.file_path = file_path
        self.raw_geojson = None  # Store the raw data for the UI
        self.restricted_features = []
        self.load_zones()

    def load_zones(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.raw_geojson = json.load(f)

            # Pre-process features into Shapely objects for fast 3D distance math
            self.restricted_features = self.raw_geojson.get("features", [])
            print(f"✅ Airspace Manager: Loaded {len(self.restricted_features)} zones.")
        except Exception as e:
            print(f"❌ Airspace Load Error: {e}")
            self.raw_geojson = {"type": "FeatureCollection", "features": []}

    def get_distance_to_closest_zone_3d(self, lat, lng, alt_m):
        """Standard 3D distance logic using pre-loaded features."""
        drone_point = Point(lng, lat)
        min_dist_3d = float('inf')
        closest_zone_name = "None"

        for feature in self.restricted_features:
            poly = shape(feature["geometry"])
            props = feature.get("properties", {})
            z_min = parse_altitude(props.get("lower_lim", "GND"))
            z_max = parse_altitude(props.get("upper_lim", "120M"))

            h_dist = 0 if poly.contains(drone_point) else drone_point.distance(poly) * 111139
            v_dist = max(0, z_min - alt_m, alt_m - z_max)
            d_3d = math.sqrt(h_dist ** 2 + v_dist ** 2)

            if d_3d < min_dist_3d:
                min_dist_3d = d_3d
                closest_zone_name = props.get("zone_id", "Unknown")
                if min_dist_3d == 0: break
        return int(min_dist_3d), closest_zone_name


# --- UI HELPER (Sits outside the class) ---
def build_zone_df(airspace_manager):
    """
    Takes the AirspaceManager instance and extracts
    the DataFrame for Pydeck.
    """
    zones = []
    features = airspace_manager.raw_geojson.get("features", [])

    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        if geom.get("type") != "Polygon": continue

        lower_m = parse_altitude(props.get("lower_lim", "GND"))
        upper_m = parse_altitude(props.get("upper_lim", "120M"))

        zones.append({
            "polygon": geom.get("coordinates", [])[0],
            "zone_id": props.get("zone_id", "Unknown"),
            "min_alt": f"{lower_m:.1f}m",
            "max_alt": f"{upper_m:.1f}m",
            "elevation": upper_m,
            "status": props.get("status", "")
        })
    return pd.DataFrame(zones)
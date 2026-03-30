import numpy as np
import os


def generate_flight_path(points=20, maneuver_type="straight"):
    path = np.zeros((points, 6))

    current_lat, current_lng = 46.77, 23.60
    current_alt = np.random.uniform(20, 100)
    heading = np.random.uniform(0, 360)
    g_speed = np.random.uniform(5, 15)
    v_speed = np.random.uniform(-0.2, 0.2)

    path[0] = [current_lat, current_lng, current_alt, heading, g_speed, v_speed]

    for i in range(1, points):
        if maneuver_type == "curve":
            heading = (heading + np.random.uniform(1, 3)) % 360
        elif maneuver_type == "zigzag" and i % 5 == 0:
            heading = (heading + np.random.choice([45, -45, 90, -90])) % 360
        else:
            heading += np.random.normal(0, 0.5)

        rad = np.radians(heading)
        current_lat += (g_speed * np.cos(rad)) / 111139
        current_lng += (g_speed * np.sin(rad)) / 77000
        current_alt += v_speed

        g_speed = max(2, g_speed + np.random.normal(0, 0.1))
        v_speed += np.random.normal(0, 0.05)

        path[i] = [current_lat, current_lng, current_alt, heading % 360, g_speed, v_speed]

    return path


def create_dataset(samples=10000):
    X, Y = [], []
    types = ["straight"] * 70 + ["curve"] * 20 + ["zigzag"] * 10

    print(f"🛰️ Generating {samples} 6-feature flight paths...")
    for _ in range(samples):
        m_type = np.random.choice(types)
        full_path = generate_flight_path(points=20, maneuver_type=m_type)

        origin = full_path[9, :3].copy()

        norm_path = full_path.copy()
        norm_path[:, :3] -= origin

        norm_path[:, 0] *= 111139
        norm_path[:, 1] *= 77000

        norm_path[:, 3] /= 360.0
        norm_path[:, 4] /= 30.0
        norm_path[:, 5] /= 10.0

        X.append(norm_path[:10])
        Y.append(norm_path[10:, :3])

    return np.array(X), np.array(Y)


if __name__ == "__main__":
    X_train, Y_train = create_dataset(10000)
    np.save('X_train.npy', X_train)
    np.save('Y_train.npy', Y_train)
    print("✅ 6-Feature Training data saved.")
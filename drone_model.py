from tensorflow.keras import layers, models


def build_drone_predictor():
    model = models.Sequential([
        layers.Input(shape=(10, 6)),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32, return_sequences=True),
        layers.TimeDistributed(layers.Dense(3)),
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


if __name__ == "__main__":
    model = build_drone_predictor()
    model.summary()
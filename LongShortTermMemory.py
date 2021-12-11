import csv

import keras_tuner as kt
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras.layers import Dense, LSTM
from keras.models import Sequential
from sklearn.metrics import max_error, mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


def scale_and_split_dataset(input_csv, scaler, is_test=False):
    features = ['energy_price_ahead_' + str(n) for n in range(50, -1, -1)]
    class_labels = ['energy_price_forward_' + str(n) for n in range(1, 13)]

    df = pd.read_csv(input_csv)
    if is_test:
        df = df.sample(frac=0.30)

    x = df[features]
    y = df[class_labels]

    scaled_x = scaler.fit_transform(x)
    scaled_y = scaler.fit_transform(y)

    # shuffle and split into train (60%), test (20%), validation (20%)
    x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, shuffle=True, random_state=42,
                                                        test_size=0.2)
    x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, shuffle=True, random_state=42,
                                                      test_size=0.25)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
    x_val = np.reshape(x_val, (x_val.shape[0], x_val.shape[1], 1))

    y_train = np.reshape(y_train, (y_train.shape[0], y_train.shape[1], 1))
    y_val = np.reshape(y_val, (y_val.shape[0], y_val.shape[1], 1))

    return x_train, x_test, y_train, y_test, x_val, y_val


def build_model(x_train, y_train):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(y_train.shape[1]))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x_train, y_train, epochs=10, batch_size=1, verbose=2)
    return model


def LongShortTermMemory(input_csv, output_csv, is_test=False):
    scaler = MinMaxScaler(feature_range=(0, 1))

    x_train, x_test, y_train, y_test, x_val, y_val = scale_and_split_dataset(input_csv, scaler, is_test)

    model = build_model(x_train, y_train)

    # Hyperparameters tuning
    tuner = kt.RandomSearch(model, objective='val_loss', max_trials=20)
    tuner.search(x_train, y_train, epochs=5, validation_data=(x_val, y_val))
    best_model = tuner.get_best_models()[0]

    print(best_model)

    preds = model.predict(x_test)
    preds = scaler.transform(preds)
    y_test = scaler.transform(y_test)
    preds /= 100
    y_test /= 100

    with open(output_csv, "w") as file_obj:
        csv.writer(file_obj).writerow([
            "predictions01",
            "predictions02",
            "predictions03",
            "predictions04",
            "predictions05",
            "predictions06",
            "predictions07",
            "predictions08",
            "predictions09",
            "predictions10",
            "predictions11",
            "predictions12",
            "reals01",
            "reals02",
            "reals03",
            "reals04",
            "reals05",
            "reals06",
            "reals07",
            "reals08",
            "reals09",
            "reals10",
            "reals11",
            "reals12"
        ])
        for index in range(preds.shape[0]):
            row = np.concatenate([preds[index, :], y_test[index, :]])
            row = map(str, row)
            csv.writer(file_obj).writerow(row)

    # root means square error values
    rms = np.sqrt(np.mean(np.power((y_test - preds), 2)))
    print("Root means quared error: ", rms)

    # plotting the training data and new Predictions
    plt.plot(y_test[:, 0])
    plt.plot(preds[:, 0])
    blue_patch = mpatches.Patch(color='#5497c5', label='y_test')
    orange_patch = mpatches.Patch(color='#ff902e', label='preds')
    plt.legend(handles=[blue_patch, orange_patch])
    plt.show()

    loss = model.evaluate(x_test, y_test, verbose=0)
    print("Loss:", loss)
    print("Max error:", max_error(y_test.reshape(-1, 1), preds.reshape(-1, 1)))
    print("Mean Absolute error:", mean_absolute_error(y_test.reshape(-1, 1), preds.reshape(-1, 1)))
    print("Mean Squared error:", mean_squared_error(y_test.reshape(-1, 1), preds.reshape(-1, 1)))

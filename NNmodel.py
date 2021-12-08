import csv

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


def NN_model(input_csv, output_csv, is_test=False):
    features = ['energy_price_ahead_' + str(n) for n in range(50, -1, -1)]
    class_labels = ['energy_price_forward_' + str(n) for n in range(1, 13)]

    df = pd.read_csv(input_csv)
    if is_test:
        df = df.sample(frac=0.30)

    x = df[features]
    y = df[class_labels]

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_x = scaler.fit_transform(x)
    scaled_y = scaler.fit_transform(y)

    # shuffle and split
    x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, shuffle=True, random_state=42,
                                                        train_size=0.7)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
    y_train = np.reshape(y_train, (y_train.shape[0], y_train.shape[1], 1))

    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(y_train.shape[1]))
    model.compile(optimizer='adam', loss='mean_squared_error')  # rmsprop
    model.fit(x_train, y_train, epochs=10, batch_size=1, verbose=2)

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


if __name__ == '__main__':
    energy_price_file = "./datas/energy.60.csv"
    profiles_file = "profiles.csv"
    new_profiles_file = "new_profiles.csv"
    folder = "./datas/muratori_5"
    prices_and_consumptions_file = "./datas/prices_and_consumptions.csv"
    NN_datas_file = "./datas/NN_datas.csv"
    NN_result_file = './datas/NN_results.csv'
    NN_model(NN_datas_file, NN_result_file, True)

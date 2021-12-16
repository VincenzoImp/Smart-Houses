import csv

import keras_tuner as kt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras.layers import Dense, LSTM, Flatten
from keras.models import Sequential
from sklearn.metrics import max_error, mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.metrics import RootMeanSquaredError
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.layers import Dropout


def hypermodel_builder(hp):
    model = Sequential()
    model.add(LSTM(units=hp.Int('units', min_value=32, max_value=512, step=32),
                   return_sequences=True,
                   input_shape=(51, 1)))

    model.add(Dropout(hp.Float('Dropout_rate', min_value=0, max_value=0.5, step=0.1)))

    for i in range(hp.Int('n_layers', 1, 4)):
        model.add(LSTM(units=hp.Int('units', min_value=32, max_value=512, step=32), return_sequences=True))

    model.add(Dropout(hp.Float('Dropout_rate', min_value=0, max_value=0.5, step=0.1)))

    model.add(Flatten())

    model.add(Dense(12, activation=hp.Choice('dense_activation', values=['relu', 'sigmoid'], default='relu')))

    # Tune the learning rate for the optimizer
    model.compile(optimizer=Adam(lr=hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])), loss=['mean_squared_error'],
                  metrics=[RootMeanSquaredError()])
    return model


def evaluate(model, preds, x_test, y_test):
    loss = model.evaluate(x_test[:, 1:].astype('float64'), y_test, verbose=0)
    param_max_error = max_error(y_test.reshape(-1, 1), preds.reshape(-1, 1))
    param_mean_absolute_error = mean_absolute_error(y_test.reshape(-1, 1), preds.reshape(-1, 1))
    param_mean_squared_error = mean_squared_error(y_test.reshape(-1, 1), preds.reshape(-1, 1))

    return loss, param_max_error, param_mean_absolute_error, param_mean_squared_error


def plot(preds, y_test, output):
    fig, ax = plt.subplots()
    ax.plot(y_test[0::2, 0], preds[0::2, 0], 'r.', alpha=0.5, label="hour + 1")
    ax.plot(y_test[0::2, 5], preds[0::2, 5], 'b.', alpha=0.5, label="hour + 6")
    ax.plot(y_test[0::2, 11], preds[0::2, 11], 'g.', alpha=0.5, label="hour + 12")
    ax.plot(np.linspace(y_test.min(), y_test.max()), np.linspace(y_test.min(), y_test.max()),
            linestyle="dashed")
    ax.set_ylabel("predicted")
    ax.set_xlabel("real")
    ax.legend()
    fig.savefig(output, dpi=1200)
    fig.clf()


def LongShortTermMemory(input_csv, output_baseline_csv, output_hypermodel_csv, is_test=False):
    scaler = MinMaxScaler(feature_range=(0, 1))

    features = ['energy_price_ahead_' + str(n) for n in range(50, -1, -1)]
    class_labels = ['energy_price_forward_' + str(n) for n in range(1, 13)]

    df = pd.read_csv(input_csv)
    if is_test:
        df = df.sample(frac=0.30)

    x = df[features]
    y = df[class_labels]

    scaled_x = (pd.DataFrame(df['timestamp']).join(pd.DataFrame(scaler.fit_transform(x)))).to_numpy()
    scaled_y = scaler.fit_transform(y)

    x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, shuffle=True, random_state=42,
                                                        test_size=0.2)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    y_train = np.reshape(y_train, (y_train.shape[0], y_train.shape[1], 1))

    # baseline model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(51, 1)))
    model.add(Dropout(0.5))
    model.add(LSTM(units=50))
    model.add(Dropout(0.5))
    model.add(Dense(12))
    model.compile(optimizer='adam', loss=['mean_squared_error'])

    model.fit(x_train[:, 1:].astype('float64'), y_train, epochs=10, batch_size=32, verbose=2)

    preds = model.predict(x_test[:, 1:].astype('float64'))

    # undo scaling to save them
    preds_normal = scaler.inverse_transform(preds)
    y_test_normal = scaler.inverse_transform(y_test)

    with open(output_baseline_csv, "w") as file_obj:
        csv.writer(file_obj).writerow([
            "timestamp",
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
        for index in range(preds_normal.shape[0]):
            row = np.concatenate([x_test[index, 0], preds_normal[index, :], y_test_normal[index, :]])
            row = map(str, row)
            csv.writer(file_obj).writerow(row)
    # root means square error values
    rms = np.sqrt(np.mean(np.power((y_test - preds), 2)))
    print("Root means squared error: ", rms)

    # plotting the training data and new Predictions
    plot(preds, y_test, "datas/plot/baseline_model.svg")

    base_loss, base_max_error, base_mean_absolute_error, base_mean_squared_error = evaluate(model, preds, x_test,
                                                                                            y_test)

    # Instantiate the tuner
    tuner = kt.Hyperband(hypermodel_builder,  # the hypermodel
                         kt.Objective("root_mean_squared_error", direction="min"),  # objective to optimize
                         max_epochs=10,
                         factor=3,
                         directory='output',  # directory to save logs
                         project_name='LSTM Regressor Trials')

    tuner.search_space_summary()

    callback = EarlyStopping(monitor='loss', patience=3)

    # Perform hypertuning
    tuner.search(x_train[:, 1:].astype('float64'), y_train, validation_split=0.2, callbacks=[callback])
    best_hyperparameters = tuner.get_best_hyperparameters(1)[0]

    print(best_hyperparameters)

    model = tuner.get_best_models(num_models=1)[0]

    print(model.summary())

    model.fit(x_train[:, 1:].astype('float64'), y_train, epochs=10,
              validation_data=(x_test[:, 1:].astype('float64'), y_test))

    preds = model.predict(x_test[:, 1:].astype('float64'))

    preds_normal = scaler.inverse_transform(preds)
    y_test_normal = scaler.inverse_transform(y_test)

    with open(output_hypermodel_csv, "w") as file_obj:
        csv.writer(file_obj).writerow([
            "timestamp",
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
        for index in range(preds_normal.shape[0]):
            row = np.concatenate([x_test[index, 0], preds_normal[index, :], y_test_normal[index, :]])
            row = map(str, row)
            csv.writer(file_obj).writerow(row)
    # root means square error values
    rms = np.sqrt(np.mean(np.power((y_test - preds), 2)))
    print("Root means squared error: ", rms)

    # plotting the training data and new Predictions
    plot(preds, y_test, "datas/plot/hyper_model.svg")

    hyper_loss, hyper_max_error, hyper_mean_absolute_error, hyper_mean_squared_error = evaluate(model, preds, x_test,
                                                                                                y_test)

    print("EVALUATION")
    print("Base model loss:", base_loss)
    print("Hypermodel loss:", hyper_loss)
    print("Base model max error:", base_max_error)
    print("Hypermodel max error:", hyper_max_error)
    print("Base model MAE:", base_mean_absolute_error)
    print("Hyper model MAE:", hyper_mean_absolute_error)
    print("Base model MSE:", base_mean_squared_error)
    print("Hyper model MSE:", hyper_mean_squared_error)

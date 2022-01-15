import csv

import keras_tuner as kt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras.layers import Dense, LSTM, Flatten
from keras.models import Sequential
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.metrics import RootMeanSquaredError
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.layers import Dropout


def hypermodel_builder(hp):
    model = Sequential()
    model.add(LSTM(units=hp.Int('units_first_layer', min_value=32, max_value=512, step=32),
                   return_sequences=True,
                   input_shape=(50, 1)))

    model.add(Dropout(hp.Float('Dropout_rate_first_layer', min_value=0.1, max_value=0.5, step=0.1)))

    for i in range(hp.Int('n_additional_layers', 1, 4)):
        model.add(LSTM(units=hp.Int('units_add_layer', min_value=32, max_value=512, step=32), return_sequences=True))
        for j in range(hp.Int('n_additional_dropout_layers', 0, 1)):
            model.add(Dropout(hp.Float('Dropout_rate_add_layer', min_value=0.1, max_value=0.5, step=0.1)))

    model.add(Flatten())

    model.add(Dense(12, activation=hp.Choice('dense_activation', values=['relu', 'sigmoid'], default='relu')))

    # Tune the learning rate for the optimizer
    model.compile(optimizer=Adam(lr=hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])), loss=['mean_squared_error'],
                  metrics=['mse', 'mae', 'mape', RootMeanSquaredError()])
    return model


def plot_predictions(preds, y_test, output):
    fig, ax = plt.subplots()
    ax.plot(y_test[0::2, 0], preds[0::2, 0], 'r.', alpha=0.5, label="hour + 1")
    ax.plot(y_test[0::2, 5], preds[0::2, 5], 'b.', alpha=0.5, label="hour + 6")
    ax.plot(y_test[0::2, 11], preds[0::2, 11], 'g.', alpha=0.5, label="hour + 12")
    ax.plot(np.linspace(y_test.min(), y_test.max()), np.linspace(y_test.min(), y_test.max()),
            linestyle="dashed")
    ax.set_ylabel("predicted")
    ax.set_xlabel("real")
    ax.legend()
    fig.savefig("datas/plot/" + output, dpi=1200)
    fig.clf()


def plot_loss(history, plot_name):
    fig, axs = plt.subplots(2, 2, figsize=(12, 12))

    x = range(1, len(history.history['loss']) + 1)

    axs[0, 0].plot(x, history.history['loss'], label='loss')
    axs[0, 0].plot(x, history.history['val_loss'], label='val_loss')
    axs[0, 0].set_title('Loss')

    axs[0, 1].plot(x, history.history['mse'], label="mse")
    axs[0, 1].plot(x, history.history['val_mse'], label="val_mse")
    axs[0, 1].set_title('Mean Squared Error')

    axs[1, 0].plot(x, history.history['mae'], label="mae")
    axs[1, 0].plot(x, history.history['val_mae'], label="val_mae")
    axs[1, 0].set_title('Mean Absolute Error')

    axs[1, 1].plot(x, history.history['mape'], label="mape")
    axs[1, 1].plot(x, history.history['val_mape'], label='val_mape')
    axs[1, 1].set_title('Mean Absolute Percentage Error')

    for ax in axs.flat:
        ax.set(xlabel='Epochs', ylabel='Loss')
        ax.grid(which='both')
        ax.legend(loc='upper right')

    # # Hide x labels and tick labels for top plots and y ticks for right plots.
    # for ax in axs.flat:
    #     ax.label_outer()

    fig.savefig("datas/plot/" + plot_name, dpi=1200)
    fig.clf()


def run_hypermodel(output_hypermodel_csv, scaler, x_test, x_train, y_test, y_train):
    # Instantiate the tuner
    tuner = kt.Hyperband(hypermodel_builder,  # the hypermodel
                         kt.Objective("root_mean_squared_error", direction="min"),  # objective to optimize
                         max_epochs=30,
                         factor=3,
                         directory='output',  # directory to save logs
                         project_name='LSTM 3.0')

    # tuner.search_space_summary()

    # Callback to stop the training when validation loss increases
    callback = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    # Perform hypertuning
    tuner.search(x_train[:, 1:].astype('float64'), y_train, validation_split=0.2, callbacks=[callback])

    print("Best Hyperparameters:")
    best_hyperparameters = tuner.get_best_hyperparameters(1)[0]
    for key in best_hyperparameters.values.keys():
        print(key, ":", best_hyperparameters.values[key])

    print("Best model:")
    model = tuner.get_best_models(num_models=1)[0]
    print(model.summary())

    hyper_history = model.fit(x_train[:, 1:].astype('float64'), y_train,
                              epochs=best_hyperparameters.values["tuner/epochs"],
                              batch_size=64, validation_split=0.2)

    plot_loss(hyper_history, "hypermodel_loss.svg")

    # unscale predictions to save them for reinforcement
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

    # root means square error
    rms = np.sqrt(mean_squared_error(y_test, preds))
    print("Root means squared error: ", rms)

    # plotting the training data and new Predictions
    plot_predictions(preds, y_test, "hyper_model.svg")

    return rms, preds


def run_base_model(output_baseline_csv, scaler, x_test, x_train, y_test, y_train):
    # baseline model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(50, 1)))
    model.add(Dropout(0.5))
    model.add(LSTM(units=50))
    model.add(Dropout(0.5))
    model.add(Dense(12))
    model.compile(optimizer='adam', loss="mse", metrics=['mse', 'mae', 'mape'])

    # callback stops the traning when the val_loss is increasing
    callback = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    # fit the model with a validation dataset
    base_history = model.fit(x_train[:, 1:].astype('float64'), y_train, epochs=30, batch_size=64, verbose=2,
                             validation_split=0.2, callbacks=[callback])

    # save the plot of the loss during epochs
    plot_loss(base_history, "baseline_loss.svg")

    # predict
    preds = model.predict(x_test[:, 1:].astype('float64'))

    # undo scaling to save results for the reinforcement learning
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

    # root means square error
    rms = np.sqrt(mean_squared_error(y_test, preds))
    print("Root means squared error Base Model: ", rms)

    # plotting the training data and new Predictions
    plot_predictions(preds, y_test, "baseline_model.svg")

    return rms, preds


def LongShortTermMemory(input_csv, output_baseline_csv, output_hypermodel_csv, is_test=False):
    # prepare dataset
    features = ['energy_price_ahead_' + str(n) for n in range(50, 0, -1)]
    class_labels = ['energy_price_forward_' + str(n) for n in range(1, 13)]

    df = pd.read_csv(input_csv)
    if is_test:
        df = df.sample(frac=0.30)

    x = df[features]
    y = df[class_labels]

    # scaling
    scaler = MinMaxScaler(feature_range=(0, 1))

    scaled_x = (pd.DataFrame(df['timestamp']).join(pd.DataFrame(scaler.fit_transform(x)))).to_numpy()
    scaled_y = scaler.fit_transform(y)

    # splitting into train and test without shuffling
    x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, shuffle=False, test_size=0.3)

    # reshape to train the models
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    y_train = np.reshape(y_train, (y_train.shape[0], y_train.shape[1], 1))

    # run the first simple model
    rms_base, pred_base = run_base_model(output_baseline_csv, scaler, x_test, x_train, y_test,
                                         y_train)

    rms_hyper, pred_hyper = run_hypermodel(output_hypermodel_csv, scaler, x_test, x_train, y_test,
                                           y_train)

    print("EVALUATION")
    eval = pd.DataFrame([["Base model", rms_base,
                          mean_squared_error(y_test, pred_base),
                          mean_absolute_error(y_test, pred_base),
                          mean_absolute_percentage_error(y_test, pred_base)],
                         ["Hypertuned model", rms_hyper,
                          mean_squared_error(y_test, pred_hyper),
                          mean_absolute_error(y_test, pred_hyper),
                          mean_absolute_percentage_error(y_test, pred_hyper)]],
                        columns=['MODEL TYPE', 'RMS', 'MSE', 'MAE', 'MAPE'])
    print(eval)

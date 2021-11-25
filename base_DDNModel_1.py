import tensorflow as tf
from tensorflow import keras
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.model_selection import train_test_split


def neural_network(csv):
    feature_names = ['day_of_the_week', 'hour_of_the_day', 'is_holiday', 'electricity_demand_hour1',
                     'electricity_demand_h2', 'electricity_demand_h3', 'electricity_demand_h24',
                     'electricity_demand_h25', 'electricity_demand_h26', 'hour_ahead_price_h1', 'hour_ahead_price_h2',
                     'hour_ahead_price_h3', 'hour_ahead_price_h24', 'hour_ahead_price_h25', 'hour_ahead_price_h26',
                     'hour_ahead_price_h48', 'hour_ahead_price_h49', 'hour_ahead_price_h50']
    class_labels = ['foward_price_h1', 'foward_price_h2', 'foward_price_h3', 'foward_price_h4', 'foward_price_h5',
                    'foward_price_h6', 'foward_price_h7', 'foward_price_h8', 'foward_price_h9', 'foward_price_h10',
                    'foward_price_h11', 'foward_price_h12']

    df = pd.read_csv(csv)
    # mix data in order to avoid training the NN on a precise period
    df_shuffled = df.sample(frac=1).reset_index(drop=True)

    x = df_shuffled[feature_names]
    y = df_shuffled[class_labels]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3)

    # --------- 1°
    tf.keras.backend.clear_session()
    tf.random.set_seed(60)

    # building the model
    model = keras.Sequential([
        keras.layers.Dense(18, input_dim=x_train.shape[1], activation='relu'),  # input layer (1)
        keras.layers.Dense(40, activation='relu'),  # hidden layer (2)
        keras.layers.Dense(20, activation='relu'),  # hidden layer (2)
        keras.layers.Dense(10, activation='relu'),  # hidden layer (2)
        keras.layers.Dense(1)  # output layer (3)
    ])

    optimizer = keras.optimizers.Adam()

    model.compile(optimizer=optimizer,
                  loss='mean_absolute_error')

    history = model.fit(x_train, y_train,
                        epochs=200, batch_size=1024,
                        validation_data=(x_test, y_test),
                        verbose=1)

    # plot result
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

    predictions = model.predict(x_test)
    print(predictions)


if __name__ == '__main__':
    nn_datas = './datas/NN_datas_with_labels.csv'
    neural_network(nn_datas)

from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv


def NN_model(input_csv, output_csv):

    feature_names = ['day_of_the_week', 'hour_of_the_day', 'is_holiday', 'electricity_demand_hour1',
                        'electricity_demand_h2', 'electricity_demand_h3', 'electricity_demand_h24',
                        'electricity_demand_h25', 'electricity_demand_h26', 'hour_ahead_price_h1', 'hour_ahead_price_h2',
                        'hour_ahead_price_h3', 'hour_ahead_price_h24', 'hour_ahead_price_h25', 'hour_ahead_price_h26',
                        'hour_ahead_price_h48', 'hour_ahead_price_h49', 'hour_ahead_price_h50']
    class_labels = ['foward_price_h1', 'foward_price_h2', 'foward_price_h3', 'foward_price_h4', 'foward_price_h5',
                        'foward_price_h6', 'foward_price_h7', 'foward_price_h8', 'foward_price_h9', 'foward_price_h10',
                        'foward_price_h11', 'foward_price_h12']

    df = pd.read_csv(input_csv)

    x = df[feature_names]
    y = df[class_labels]

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_x = scaler.fit_transform(x)
    scaled_y = scaler.fit_transform(y)

    rows_df = df.shape[0]
    len_train = int(rows_df*0.7)

    x_train = scaled_x[:len_train, :]
    x_test = scaled_x[len_train:, :]
    y_train = scaled_y[:len_train, :]
    y_test = scaled_y[len_train:, :]

    x_train = np.reshape(x_train, (x_train.shape[0],x_train.shape[1],1))
    x_test = np.reshape(x_test, (x_test.shape[0],x_test.shape[1],1))
    y_train = np.reshape(y_train, (y_train.shape[0],y_train.shape[1],1))

    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1],1)))
    model.add(LSTM(units=50))
    model.add(Dense(y_train.shape[1]))
    model.compile(loss='mean_squared_error', optimizer='adam')
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
            row = np.concatenate([preds[index, :],y_test[index, :]])
            row = map(str, row)
            csv.writer(file_obj).writerow(row)

    #root means square error values
    rms=np.sqrt(np.mean(np.power((y_test-preds),2)))
    print(rms)

    #plotting the training data and new Predictions
    plt.plot(y_test[:,0])
    plt.plot(preds[:,0])
    blue_patch = mpatches.Patch(color='#5497c5', label='y_test')
    orange_patch = mpatches.Patch(color='#ff902e', label='preds')
    plt.legend(handles=[blue_patch,orange_patch])                                     
    plt.show()

    return

if __name__ == '__main__':    
    input_csv = './datas/NN_datas_with_labels.csv'
    output_csv = './datas/NN_results.csv'
    NN_model(input_csv, output_csv)

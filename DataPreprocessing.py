import csv
import os
from itertools import islice

import pandas as pd
from sklearn.impute import KNNImputer


def k_nearest_neighborhood(data):
    # compute k-nearest neighbour
    df = pd.read_csv(data)
    imputer = KNNImputer(n_neighbors=2, weights='uniform')
    transformed_data = pd.DataFrame(imputer.fit_transform(df[['energy_market_price']]),
                                    columns=['energy_market_price'])
    new_dataset = df[['starting']].join(transformed_data)
    new_dataset.to_csv(data, index=False)


def format_correctly(energy_file):
    transformed = []
    with open(energy_file, "r") as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            if index == 0:
                continue
            transformed.append([row[0], format(float(row[1]), '.5f')])

    with open(energy_file, "w") as file:
        writer = csv.writer(file)
        writer.writerow(['starting', 'energy_market_price'])
        writer.writerows(transformed)


def get_future_price(energy_DF, current_day, current_hour):
    try:
        row = current_day * 24 + current_hour
        future_price = energy_DF.at[row, "energy_market_price"]
    except KeyError:
        return None
    return future_price


def get_timestamp(energy_DF, current_day, current_hour):
    try:
        row = current_day * 24 + current_hour
        timestamp = energy_DF.at[row, "starting"]
    except KeyError:
        return None
    return timestamp


def for_each_home(current_folder, energy_price_file, old_profiles_name, new_profiles_name):
    for element in os.listdir(current_folder):
        if os.path.isdir(os.path.join(current_folder, element)):
            for_each_home(os.path.join(current_folder, element),
                          energy_price_file, old_profiles_name, new_profiles_name)
        elif os.path.isfile(os.path.join(current_folder, element)) and element == old_profiles_name:
            read_old_build_new(energy_price_file, os.path.join(
                current_folder, element), os.path.join(current_folder, new_profiles_name))
            update_new(os.path.join(current_folder, new_profiles_name))
    return


def read_old_build_new(energy_price_file, old_profiles_file, new_profiles_file):
    print(old_profiles_file)
    energy_DF = pd.read_csv(energy_price_file)
    profile_DF = pd.read_csv(old_profiles_file)
    with open(new_profiles_file, "w") as file_object:
        csv.writer(file_object).writerow([
            "timestamp",
            "energy_market_price",
            "consumption_kwh",
            "PV_kwh",
            "PEV_input_state_of_charge",
            "PEV_hours_of_charge"
        ])
        current_day = 0
        current_hour = 0
        row = 0
        last_input_state_of_charge = -1
        while True:
            timestamp = get_timestamp(energy_DF, current_day, current_hour)
            future_price = get_future_price(
                energy_DF, current_day, current_hour)
            if timestamp == None or future_price == None:
                break
            consumption_kwh = 0.0
            PV_kwh = 0.0
            state = 0
            pre_busy_count = 0
            post_busy_count = 0
            input_state_of_charge = -1
            for i in range(row, row + 12):
                try:
                    tmp = profile_DF.at[i, "phev_initial_state_of_charge_kwh"]
                except KeyError:
                    break
                consumption_kwh += profile_DF.at[i, "consumption_nopev_kw"]
                PV_kwh += profile_DF.at[i, "production_kw"]
                if state == 0:
                    if tmp == -1:
                        pre_busy_count += 1
                    else:
                        input_state_of_charge = tmp
                        state = 1
                elif state == 1:
                    if tmp == -1:
                        post_busy_count += 1
                        state = 2
                elif state == 2:
                    if tmp == -1:
                        post_busy_count += 1
            if pre_busy_count == 0:
                if last_input_state_of_charge != -1:
                    input_state_of_charge = -2
            try:
                last_input_state_of_charge = profile_DF.at[row +
                                                           11, "phev_initial_state_of_charge_kwh"]
            except KeyError:
                break
            row += 12
            csv.writer(file_object).writerow([
                timestamp,
                future_price,
                consumption_kwh,
                PV_kwh,
                input_state_of_charge
            ])
            current_hour += 1
            if current_hour == 24:
                current_day += 1
                current_hour = 0
    return


def update_new(new_profiles_file):
    newprofile_DF = pd.read_csv(new_profiles_file)
    with open(new_profiles_file, "w") as file_object:
        csv.writer(file_object).writerow([
            "timestamp",
            "energy_market_price",
            "consumption_kwh",
            "PV_kwh",
            "PEV_input_state_of_charge",
            "PEV_hours_of_charge"
        ])
        for i, row in newprofile_DF.iterrows():
            timestamp = row["timestamp"]
            energy_market_price = row["energy_market_price"]
            consumption_kwh = row["consumption_kwh"]
            PV_kwh = row["PV_kwh"]
            PEV_input_state_of_charge = row["PEV_input_state_of_charge"]
            PEV_hours_of_charge = 0
            if newprofile_DF.at[i, "PEV_input_state_of_charge"] != -1:
                j = i + 1
                while newprofile_DF.at[j, "PEV_input_state_of_charge"] == -2:
                    j += 1
                PEV_hours_of_charge = j - i
            csv.writer(file_object).writerow([
                timestamp,
                energy_market_price,
                consumption_kwh,
                PV_kwh,
                PEV_input_state_of_charge,
                PEV_hours_of_charge])
    return


def get_prices_and_consumptions(folder, energy_price_file, new_file, new_profiles_name):
    with open(energy_price_file) as energy_price_file_obj:
        reader = csv.reader(
            islice(energy_price_file_obj, 1, None), delimiter=",")
        list_energy_consumption = [0 for _ in reader]
        list_energy_consumption = fill_list_energy_consumption(
            folder, new_profiles_name, list_energy_consumption)
    with open(energy_price_file) as energy_price_file_obj, open(new_file, "w") as new_file_obj:
        reader = csv.reader(
            islice(energy_price_file_obj, 1, None), delimiter=",")
        writer = csv.writer(new_file_obj)
        headers = ['timestamp', 'energy_market_price', 'consumption_kwh']
        writer.writerow(headers)
        for index, row in enumerate(reader):
            timestamp = row[0]
            energy_price = row[1]
            new_row = [timestamp, energy_price, list_energy_consumption[index]]
            writer.writerow(new_row)
    return


def fill_list_energy_consumption(current_folder, new_profiles_name, list_energy_consumption):
    for element in os.listdir(current_folder):
        if os.path.isdir(os.path.join(current_folder, element)):
            list_energy_consumption = fill_list_energy_consumption(os.path.join(current_folder, element),
                                                                   new_profiles_name, list_energy_consumption)
        elif os.path.isfile(os.path.join(current_folder, element)) and element == new_profiles_name:
            with open(os.path.join(current_folder, element)) as new_profiles_file_obj:
                reader = csv.reader(
                    islice(new_profiles_file_obj, 1, None), delimiter=",")
                for index, row in enumerate(reader):
                    list_energy_consumption[index] += float(row[2])
    return list_energy_consumption


def read_csv(old_file_name, new_file_name):
    consumption_kwh = []
    energy_market_price = []

    with open(old_file_name) as file_profiles, open(new_file_name, "w") as new_file_properties:
        # exclude headers
        reader = csv.reader(islice(file_profiles, 1, None), delimiter=",")

        # Prepare new file
        writer = csv.writer(new_file_properties)
        headers = ['electricity_demand_hour1', 'electricity_demand_h2', 'electricity_demand_h3',
                   'electricity_demand_h24', 'electricity_demand_h25', 'electricity_demand_h26', 'hour_ahead_price_h1',
                   'hour_ahead_price_h2', 'hour_ahead_price_h3', 'hour_ahead_price_h24', 'hour_ahead_price_h25',
                   'hour_ahead_price_h26', 'hour_ahead_price_h48', 'hour_ahead_price_h49', 'hour_ahead_price_h50']
        writer.writerow(headers)

        for index, row in enumerate(reader):
            # Save first 50 rows
            energy_market_price.append(row[1])
            consumption_kwh.append(row[2])

            new_row = []
            if index >= 50:
                # Get Day of the week, hour of the week, holiday
                # date_time_obj = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')

                # new_row.append(date_time_obj.weekday() + 1)
                # new_row.append(date_time_obj.hour + 1)

                # if date_time_obj in holidays.NLD():
                #    new_row.append(1)  # True
                # else:
                #    new_row.append(0)  # False

                # Electricity Demand
                new_row.append(consumption_kwh[index - 1])  # h -1
                new_row.append(consumption_kwh[index - 2])  # h -2
                new_row.append(consumption_kwh[index - 3])  # h - 3
                new_row.append(consumption_kwh[index - 24])  # h - 24
                new_row.append(consumption_kwh[index - 25])  # h - 25
                new_row.append(consumption_kwh[index - 26])  # h - 26

                # Hour ahead price of hour
                new_row.append(energy_market_price[index - 1])  # h - 1
                new_row.append(energy_market_price[index - 2])  # h - 2
                new_row.append(energy_market_price[index - 3])  # h - 3
                new_row.append(energy_market_price[index - 24])  # h - 24
                new_row.append(energy_market_price[index - 25])  # h - 25
                new_row.append(energy_market_price[index - 26])  # h - 26
                new_row.append(energy_market_price[index - 48])  # h - 48
                new_row.append(energy_market_price[index - 49])  # h - 49
                new_row.append(energy_market_price[index - 50])  # h - 50

                # Write to file
                # print(index)
                writer.writerow(new_row)


def add_class_labels(prices_and_consumptions_file, NN_datas_file, new_file):
    headers = ['electricity_demand_hour1', 'electricity_demand_h2', 'electricity_demand_h3', 'electricity_demand_h24',
               'electricity_demand_h25', 'electricity_demand_h26', 'hour_ahead_price_h1', 'hour_ahead_price_h2',
               'hour_ahead_price_h3', 'hour_ahead_price_h24', 'hour_ahead_price_h25', 'hour_ahead_price_h26',
               'hour_ahead_price_h48', 'hour_ahead_price_h49', 'hour_ahead_price_h50',
               'foward_price_h1', 'foward_price_h2', 'foward_price_h3', 'foward_price_h4', 'foward_price_h5',
               'foward_price_h6', 'foward_price_h7', 'foward_price_h8', 'foward_price_h9', 'foward_price_h10',
               'foward_price_h11', 'foward_price_h12']

    prices_and_consumptions = pd.read_csv(prices_and_consumptions_file)
    NN_datas_file = pd.read_csv(NN_datas_file)

    with open(new_file, "w") as NN_datas_file_with_labels:
        writer = csv.writer(NN_datas_file_with_labels)
        writer.writerow(headers)

        for index, row in enumerate(NN_datas_file.iterrows()):
            if index + 63 < len(prices_and_consumptions.index):
                new_row = [n for n in row[1]]
                new_row.append(prices_and_consumptions.iloc[index + 52]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 53]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 54]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 55]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 56]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 57]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 58]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 59]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 60]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 61]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 62]['energy_market_price'])
                new_row.append(prices_and_consumptions.iloc[index + 63]['energy_market_price'])
                writer.writerow(new_row)


def prepare_NN_data(energy, nn_datas):
    energy_market_price = []

    with open(energy, "r") as energy_60_file, open(nn_datas, "w") as nn_datas_file:
        reader = csv.reader(energy_60_file)
        writer = csv.writer(nn_datas_file)
        headers = []
        headers.extend(['energy_price_ahead_' + str(n) for n in range(50, -1, -1)])
        headers.extend(['energy_price_forward_' + str(n) for n in range(1, 13)])
        writer.writerow(headers)

        for index, row in islice(enumerate(reader), 1, None):
            if index == 0:
                continue
            energy_market_price.append(row[1])
            if index > 62:
                new_line = []
                new_line.extend(energy_market_price[index - 63: index])
                writer.writerow(new_line)

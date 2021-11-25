import csv
import os
from itertools import islice
import pandas as pd


def get_prices_and_consumptions(folder, energy_price_file, new_file, new_profiles_name):
    with open(energy_price_file) as energy_price_file_obj, open(new_file, "w") as new_file_obj:
        reader = csv.reader(islice(energy_price_file_obj, 1, None), delimiter=",")
        writer = csv.writer(new_file_obj)
        headers = ['timestamp', 'energy_market_price', 'consumption_kwh']
        writer.writerow(headers)
        for index, row in enumerate(reader):
            timestamp = row[0]
            energy_price = row[2]
            energy_consumption = get_total_energy_consumption(folder, new_profiles_name, index)
            new_row = [timestamp, energy_price, energy_consumption]
            writer.writerow(new_row)
    return


def get_total_energy_consumption(current_folder, new_profiles_name, index):
    energy_consumption = 0
    for element in os.listdir(current_folder):
        if os.path.isdir(os.path.join(current_folder, element)):
            energy_consumption += get_total_energy_consumption(os.path.join(current_folder, element), new_profiles_name,
                                                               index)
        elif os.path.isfile(os.path.join(current_folder, element)) and element == new_profiles_name:
            new_profile_DF = pd.read_csv(os.path.join(current_folder, element))
            energy_consumption += new_profile_DF.at[index, "consumption_kwh"]
    return energy_consumption


if __name__ == '__main__':
    folder = "./datas/muratori_5"
    energy_price_file = "./datas/energy.60.csv"
    new_file = "./datas/prices_and_consumptions.csv"
    new_profiles_name = "new_profiles.csv"
    get_prices_and_consumptions(folder, energy_price_file, new_file, new_profiles_name)

# unisce tutte le info utili e genera un newprofile che va rinomivato come profile e inserito nella directory home
# di seguito viene eseguito Q-learning passandogli come argomento la directory home
import pandas as pd
import sys
import os.path
import csv

current_day = 0
current_hour = 0


def get_future_price(energy_DF):
    try:
        row = current_day * 24 + current_hour
        future_price = energy_DF.at[row, "energy_market_price"]
    except KeyError:
        return None
    return future_price


def get_timestamp(energy_DF):
    try:
        row = current_day * 24 + current_hour
        timestamp = energy_DF.at[row, "starting"]
    except KeyError:
        return None
    return timestamp


def get_input(argv):
    try:
        path_energy = argv[1]
        path_dir_home = argv[2]
        if not os.path.isfile(path_energy) or not os.path.isdir(path_dir_home):
            print("error arguments: <path_energy> <path_dir_home>")
            return None
    except IndexError:
        print("missing arguments: <path_energy> <path_dir_home>")
        return None
    return (path_energy, path_dir_home)


def main1():
    global current_day
    global current_hour
    result = get_input(sys.argv)
    if result == None: return
    path_energy, path_dir_home = result
    energy_DF = pd.read_csv(path_energy)
    profile_DF = pd.read_csv(os.path.join(path_dir_home, "profiles.csv"))
    filename = os.path.join(path_dir_home, "newprofiles.csv")
    with open(filename, "w") as file_object:
        csv.writer(file_object).writerow(
            ["timestamp", "energy_market_price", "consumption_kwh", "PV_kwh", "PEV_input_state_of_charge",
             "PEV_hours_of_charge"])
    with open(filename, "a") as file_object:
        row = 0
        last_input_state_of_charge = -1
        check = False
        while True:
            timestamp = get_timestamp(energy_DF)
            future_price = get_future_price(energy_DF)
            if timestamp == None or future_price == None: break
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
                last_input_state_of_charge = profile_DF.at[row + 11, "phev_initial_state_of_charge_kwh"]
            except KeyError:
                break
            row += 12
            csv.writer(file_object).writerow([timestamp, future_price, consumption_kwh, PV_kwh, input_state_of_charge])
            current_hour += 1
            if current_hour == 24:
                current_day += 1
                current_hour = 0
    return


def main2():
    path_dir_home = get_input(sys.argv)[1]
    newprofile_DF = pd.read_csv(os.path.join(path_dir_home, "newprofiles.csv"))
    filename = os.path.join(path_dir_home, "newprofiles.csv")
    with open(filename, "w") as file_object:
        csv.writer(file_object).writerow(
            ["timestamp", "energy_market_price", "consumption_kwh", "PV_kwh", "PEV_input_state_of_charge",
             "PEV_hours_of_charge"])
    with open(filename, "a") as file_object:
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
            csv.writer(file_object).writerow(
                [timestamp, energy_market_price, consumption_kwh, PV_kwh, PEV_input_state_of_charge,
                 PEV_hours_of_charge])
    return


if __name__ == "__main__":
    main1()
    main2()

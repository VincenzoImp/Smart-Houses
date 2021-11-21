
import pandas as pd
import csv

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

def read_old_build_new(price_energy_file, old_profiles_file, new_profiles_file):
    energy_DF = pd.read_csv(price_energy_file)
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
            future_price = get_future_price(energy_DF, current_day, current_hour)
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

if __name__ == "__main__":
    price_energy_file = "./datas/energy.60.csv"
    old_profiles_file = "./datas/profiles.csv"
    new_profiles_file = "./datas/new_profiles.csv"
    read_old_build_new(price_energy_file, old_profiles_file, new_profiles_file)
    update_new(new_profiles_file)
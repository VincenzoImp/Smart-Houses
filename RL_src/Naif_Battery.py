from libraries import *

class Naif_Battery(object):

    def __init__(self, id, max_capacity, current_state_of_charge, deficit = 0, energy_demand = 0, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"): #Tini, Tw, Tend devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours
        self.id = id
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        self.deficit = deficit
        self.energy_demand = energy_demand
        self.column_info = column_info
        self.working_hours = working_hours
        self.hours_available = -1 #totale ore disponibili comprese tra tini/ora corrente e tend contenente tw e lunghe maggiore o uguale di tne
        self.filename = os.path.join(directory, str(self.id)+".csv")
        self.initialize_file()
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            new_state_of_charge = house_profile_DF.at[count_row, self.column_info[0]]
            hours_available = house_profile_DF.at[count_row, self.column_info[1]]
            if new_state_of_charge == -1:
                self.working_hours = "(-1)$"
            elif new_state_of_charge == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.hours_available = hours_available
                self.current_state_of_charge = new_state_of_charge
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0, -1])
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if re.match(self.working_hours, str(current_hour)):
            current_kwh = 0.0
            state_of_charge = min(self.max_capacity, self.current_state_of_charge + self.deficit)
            d = {(array_price[index], index) : 0.0 for index in range(self.hours_available)}
            for k in sorted(list(d.keys())):
                kwh = min(self.energy_demand, self.max_capacity-state_of_charge)
                d[k] = kwh
                state_of_charge += kwh
                if k[1] == 0:
                    current_kwh = kwh
            E = current_kwh
            U = (1-p)*array_price[0]*E
            self.current_state_of_charge += E
            self.hours_available -= 1
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


def insert_Naif_Battery(device_list, path_dir_home):
    battery_DF = pd.read_csv(os.path.join(path_dir_home, "Naifpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        energy_demand = float(row["charge_speed_kw"])
        deficit = float(row["deficit"])
        max_capacity = float(row["battery_capacity_kwh"])
        new_battery = Naif_Battery("Naif_Battery."+str(row_index), max_capacity, 0, deficit, energy_demand, ("PEV_input_state_of_charge","PEV_hours_of_charge"))
        device_list.add(new_battery)
        row_index += 1
    return
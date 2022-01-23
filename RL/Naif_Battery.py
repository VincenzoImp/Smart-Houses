from Device import Device
from libraries import csv, pd, os, datetime

class Naif_Battery(Device):

    def __init__(self, simulation, id, max_capacity, current_state_of_charge, deficit=0, energy_demand=0, column_info=None, plots_directory="", is_active=False):  # Tini, Tw, Tend devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con is_active
        super().__init__(simulation, id, column_info, plots_directory, is_active)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        self.deficit = deficit
        self.energy_demand = energy_demand
        self.hours_available = -1  # totale ore disponibili comprese tra tini/ora corrente e tend contenente tw e lunghe maggiore o uguale di tne
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if self.is_active:
                csv.writer(file_object).writerow([self.simulation.timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self):
        if self.column_info != None:
            new_state_of_charge = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[0]]
            hours_available = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[1]]
            if new_state_of_charge == -1:
                self.is_active = False
            elif new_state_of_charge == -2:
                self.is_active = True
            else:
                self.is_active = True
                self.hours_available = hours_available
                self.current_state_of_charge = new_state_of_charge
        return

    def function(self, dict_results):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if self.is_active:
            current_kwh = 0.0
            state_of_charge = min(self.max_capacity, self.current_state_of_charge + self.deficit)
            d = {(self.simulation.array_price[index], index): 0.0 for index in range(min(self.hours_available, len(self.simulation.array_price)))}
            for k in sorted(list(d.keys())):
                kwh = min(self.energy_demand, self.max_capacity - state_of_charge)
                d[k] = kwh
                state_of_charge += kwh
                if k[1] == 0:
                    current_kwh = kwh
            E = current_kwh
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E
            self.current_state_of_charge += E
            self.hours_available -= 1
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        dict_results[self.id] = {'E':E, 'U':U, 'SOC':self.current_state_of_charge}
        return


def insert_Naif_Battery(simulation):
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "Naifpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        energy_demand = float(row["charge_speed_kw"])
        deficit = float(row["deficit"])
        max_capacity = float(row["battery_capacity_kwh"])
        new_battery = Naif_Battery(simulation, "Naif_Battery." + str(row_index), max_capacity, 0, deficit, energy_demand, ("PEV_input_state_of_charge", "PEV_hours_of_charge"))
        simulation.device_list.add(new_battery)
        row_index += 1
    return

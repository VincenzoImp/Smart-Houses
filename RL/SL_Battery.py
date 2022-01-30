from SL import Shiftable_load
from libraries import csv, pd, os


class SL_Battery(Shiftable_load):

    def __init__(self, simulation, id, k, T_ne, state_number, max_capacity, current_state_of_charge=0, T_ini=0,
                 T_end=23, energy_demand=0, column_info=None, plots_directory="", is_active=False):
        # T_ini, T_w, T_end devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours
        super().__init__(simulation, id, k, T_ne, state_number, T_ini, T_end, energy_demand, column_info,
                         plots_directory, is_active)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if self.is_active:
                csv.writer(file_object).writerow(
                    [self.simulation.timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self):
        # TO DO
        return

    def function(self, dict_results):
        # TO DO
        return

    def discretize_state_of_charge(self, state_of_charge):
        state = 0
        if self.state_number == 1: return state
        delta = self.max_capacity / (self.state_number - 1)
        if state_of_charge == self.max_capacity:
            state = self.state_number - 1
        else:
            for i in range(self.state_number - 1):
                if delta * i <= state_of_charge < delta * (i + 1):
                    state = i
                    break
        return state


def insert_SL_Battery(simulation):
    # TO DO
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "SLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        device_id = "SL_Battery." + str(row_index)
        k = float(row["k"])
        max_capacity = float(row["battery_capacity_kwh"])
        state_number = int(row["state_number"])
        energy_demand = float(row["charge_speed_kw"])
        new_battery = SL_Battery(simulation, device_id, k, 0, state_number, max_capacity, 0, 0, 0, energy_demand,
                                 ("PEV_input_state_of_charge", "PEV_hours_of_charge"))
        simulation.device_list.add(new_battery)
        row_index += 1
    return

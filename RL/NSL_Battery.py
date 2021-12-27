from NSL import Non_shiftable_load
from libraries import pd, csv, datetime, os


class NSL_Battery(Non_shiftable_load):

    def __init__(self, simulation, id, max_capacity, current_state_of_charge=0, energy_demand=0, column_info=None, is_active=False):
        super().__init__(simulation, id, energy_demand, column_info, is_active)
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
                csv.writer(file_object).writerow([self.simulation.timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self):
        if self.column_info != None:
            tmp = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info]
            if tmp == -1:
                self.is_active = False
                self.current_state_of_charge = -1
            elif tmp == -2:
                self.is_active = True
            else:
                self.is_active = True
                self.current_state_of_charge = tmp
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if self.is_active:
            E = min(self.energy_demand, self.max_capacity - self.current_state_of_charge)
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E
            self.current_state_of_charge += E
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        return E, U


def insert_NSL_Battery(simulation):
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "NSLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        max_capacity = float(row["battery_capacity_kwh"])
        energy_demand = float(row["charge_speed_kw"])
        new_NSL_Battery = NSL_Battery(simulation, "NSL_Battery." + str(row_index), max_capacity, 0, energy_demand, "PEV_input_state_of_charge")
        simulation.device_list.add(new_NSL_Battery)
        row_index += 1
    return

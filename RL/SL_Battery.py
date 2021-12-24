from SL import Shiftable_load
from libraries import csv, re, np, pd, os, datetime, math


class SL_Battery(Shiftable_load):

    def __init__(self, simulation, id, k, max_capacity, current_state_of_charge, Tne, state_number, energy_demand=0,
                 column_info=None, Tini=0, Tend=23,
                 working_hours="([0-9]|1[0-9]|2[0-3])$"):  # Tini, Tw, Tend devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours
        Shiftable_load.__init__(self, simulation, id, k, Tne, state_number, energy_demand, column_info, Tini, Tend,
                                working_hours)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(self.simulation.current_hour)):
                csv.writer(file_object).writerow(
                    [self.simulation.timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self):
        if self.column_info != None:
            new_state_of_charge = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[0]]
            hours_available = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[1]]
            # Tne deve essere minore o uguale a hours_of_work (si assume sempre che vengano sempre rispettati i vincoli del sistema)
            if new_state_of_charge == -1:
                self.working_hours = "(-1)$"
                self.hours_worked = -1
            elif new_state_of_charge == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.Tini = self.simulation.current_hour
                self.Tw = -1
                self.Tend = (self.simulation.current_hour + hours_available - 1) % 24
                self.hours_available = hours_available
                self.current_state_of_charge = new_state_of_charge
                self.Tne = min(self.hours_available,
                               math.ceil((self.max_capacity - self.current_state_of_charge) / self.energy_demand))
                self.hours_worked = -1
        return

    def get_state(self, state_of_charge):
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

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if re.match(self.working_hours,
                    str(self.simulation.current_hour)):  # caso in cui posso stare nelle righe diverse da -1
            if not self.simulation.home.one_memory:
                self.Q = np.zeros((24, self.state_number, 2), dtype=float)
            while i < self.simulation.home.loops:
                index = 0
                hour = self.simulation.current_hour
                state = self.get_state(self.current_state_of_charge)
                Tw = self.Tw
                hours_available = self.hours_available
                hours_worked = self.hours_worked
                state_of_charge = self.current_state_of_charge
                while hours_available > 0:
                    bin_action, new_Tw, new_hours_available, new_hours_worked = self.chose_action(hour, state, Tw,
                                                                                                  hours_available,
                                                                                                  hours_worked)
                    kwh = min(self.max_capacity - state_of_charge, bin_action * self.energy_demand)
                    new_state_of_charge = state_of_charge + kwh
                    reward = self.get_reward(index, new_Tw, kwh)
                    new_hour = (hour + 1) % 24
                    new_state = self.get_state(new_state_of_charge)
                    self.Q[hour][state][bin_action] = self.Q[hour][state][bin_action] + self.simulation.home.teta * (
                            reward + self.simulation.home.gamma * self.Q[new_hour][new_state][
                        self.chose_action(new_hour, new_state, new_Tw, new_hours_available, new_hours_worked, True)[
                            0]] - self.Q[hour][state][bin_action])
                    index += 1
                    hour = new_hour
                    state = new_state
                    Tw = new_Tw
                    hours_available = new_hours_available
                    hours_worked = new_hours_worked
                    state_of_charge = new_state_of_charge
                i += 1
            bin_action, self.Tw, self.hours_available, self.hours_worked = self.chose_action(
                self.simulation.current_hour,
                self.get_state(
                    self.current_state_of_charge),
                self.Tw,
                self.hours_available,
                self.hours_worked, True)
            E = min(self.max_capacity - self.current_state_of_charge, bin_action * self.energy_demand)
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E + self.simulation.home.p * (
                        self.k * (((self.Tw + 24) - self.Tini) % 24))
            self.current_state_of_charge += E
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        return E, U


def insert_SL_Battery(simulation):
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "SLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        k = float(row["k"])
        max_capacity = float(row["battery_capacity_kwh"])
        state_number = int(row["state_number"])
        energy_demand = float(row["charge_speed_kw"])
        new_battery = SL_Battery(simulation, "SL_Battery." + str(row_index), k, max_capacity, 0, 0, state_number,
                                 energy_demand,
                                 ("PEV_input_state_of_charge", "PEV_hours_of_charge"))
        simulation.device_list.add(new_battery)
        row_index += 1
    return

from CL import Controlable_load
from CL_Battery_GreedyQLearning import CL_Battery_GeedyQLearning
from libraries import csv, datetime, copy, plt, os, pd


class CL_Battery(Controlable_load):

    def __init__(self, simulation, id, beta, min_energy_demand, max_energy_demand, state_number, action_number,
                 max_capacity, current_state_of_charge=0, column_info=None, plots_directory="", is_active=False):
        super().__init__(simulation, id, beta, min_energy_demand, max_energy_demand, state_number, action_number,
                         column_info, plots_directory, is_active)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        self.LIMIT = 24
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
        if self.column_info != None:
            new_current_state_of_charge = self.simulation.house_profile_DF.at[
                self.simulation.count_row, self.column_info]
            if new_current_state_of_charge == -1:
                self.is_active = False
                self.current_state_of_charge = -1
            elif new_current_state_of_charge == -2:
                self.is_active = True
            else:
                self.is_active = True
                self.current_state_of_charge = new_current_state_of_charge
        return

    def function(self, dict_results):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if self.is_active:  # caso in cui posso stare nelle righe diverse da -1
            if self.plots_directory != "":
                q_list = []
            if self.current_state_of_charge + self.action_list[self.action_list.index(0) + 1] > self.max_capacity:
                action = self.action_list.index(0)
            else:

                CL_Battery_model = CL_Battery_GeedyQLearning(self)
                while (self.simulation.loops != None and i <= self.simulation.loops) or self.simulation == None:
                    if self.simulation.loops == None:
                        old_CL_Battery_model = copy(CL_Battery_model)
                    state_key = (1, self.discretize_state_of_charge(self.current_state_of_charge))
                    limit = min(self.LIMIT, len(self.simulation.array_price))
                    CL_Battery_model.learn(state_key, limit)

                    if self.plots_directory != "":
                        next_action_list = CL_Battery_model.extract_possible_actions(state_key,
                                                                                     self.current_state_of_charge)
                        action_key = CL_Battery_model.predict_next_action(state_key, next_action_list)
                        q_df = CL_Battery_model.get_q_df()
                        q_df = q_df[q_df.state_key == state_key]
                        q_list.append(q_df[q_df.action_key == action_key]["q_value"].values[0])
                    i += 1
                    if self.simulation == None and CL_Battery_model.convergence(old_CL_Battery_model):
                        break
                state_key = (1, self.discretize_state_of_charge(self.current_state_of_charge))
                next_action_list = CL_Battery_model.extract_possible_actions(state_key, self.current_state_of_charge)
                action = CL_Battery_model.predict_next_action(state_key, next_action_list)

            if self.plots_directory != "":
                x_list = list(range(len(q_list)))
                plt.plot(x_list, q_list)
                plt.suptitle(self.id + "." + self.simulation.timestamp.replace(":", "_"))
                plt.xlabel('epochs')
                plt.ylabel('q_value')
                plt.savefig(os.path.join(self.plots_directory,
                                         self.id + "." + self.simulation.timestamp.replace(":", "_") + ".png"))

            kwh = self.action_list[action]
            local_max_energy_demand = min(self.max_energy_demand, self.max_capacity - self.current_state_of_charge)
            if kwh == 0 and self.current_state_of_charge + self.action_list[
                action + 1] > self.max_capacity:  # niente index out of range per costruzione
                kwh = min(self.max_energy_demand,
                          self.max_capacity - self.current_state_of_charge)  # a causa di un'assenza di totale liberta' di range, quando la action genera E == 0 allora "rabbocco" E al current_max_energy_demand
            self.current_state_of_charge += kwh
            E = kwh
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E + self.simulation.home.p * (
                    self.beta * ((E - local_max_energy_demand) ** 2))
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        dict_results[self.id] = {'E': E, 'U': U, 'SOC': self.current_state_of_charge}
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

    def get_min_max_index_action(self, state_of_charge):
        min_action = -1
        max_action = -1
        check = False
        for i, action in enumerate(self.action_list):
            if not check and state_of_charge + action >= 0 and state_of_charge + action <= self.max_capacity:
                check = True
                min_action = i
                max_action = i
            if check and state_of_charge + action >= 0 and state_of_charge + action <= self.max_capacity:
                max_action = i
        return (min_action, max_action)


def insert_CL_Battery(simulation):
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "CLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        device_id = "CL_Battery." + str(row_index)
        plots_directory = ""
        if bool(row["plots"]):
            plots_directory = os.path.join(simulation.directory, device_id + "_plots")
            os.mkdir(plots_directory)
        max_energy_demand = float(row["charge_speed_kw"])
        min_energy_demand = 0  # -float(row["discharge_speed_kw"]) #attualmente l'algoritmo non e' pensato per device che producono energia (va rivista la formula delle reward, e forse anche la formula di U, ma penso sono la prima)
        action_number = int(row["action_number"])
        state_number = int(row["state_number"])
        beta = float(row["beta"])
        max_capacity = float(row["battery_capacity_kwh"])
        new_battery = CL_Battery(simulation, device_id, beta, min_energy_demand, max_energy_demand,
                                 state_number, action_number, max_capacity, 0, "PEV_input_state_of_charge",
                                 plots_directory)
        simulation.device_list.add(new_battery)
        row_index += 1
    return

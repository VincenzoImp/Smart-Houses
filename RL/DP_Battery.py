from CL_Battery import CL_Battery
from libraries import pd, os, datetime, copy


class DP_Battery(CL_Battery):
    class Info(object):

        def __init__(self, value=0.0, first_action=-1):
            self.setter(value, first_action)
            return

        def clone(self, info_obj):
            self.value = info_obj.value
            self.first_action = info_obj.first_action
            return

        def setter(self, value, first_action):
            self.value = value
            self.first_action = first_action
            return

    def __init__(self, simulation, id, beta, current_state_of_charge, max_capacity, min_energy_demand,
                 max_energy_demand, action_number, state_number, column_info=None, plots_directory="",
                 is_active=False):  # si assume che action_number >=2
        super().__init__(simulation, id, beta, min_energy_demand, max_energy_demand, state_number, action_number,
                         max_capacity, current_state_of_charge, column_info, plots_directory, is_active)
        self.hours_of_charge = 0
        return

    def update_data(self):
        if self.column_info != None:
            input_state_of_charge = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[0]]
            hours_of_charge = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info[1]]
            if input_state_of_charge == -1:
                self.is_active = False
                self.current_state_of_charge = -1
            elif input_state_of_charge == -2:
                self.is_active = True
                self.hours_of_charge -= 1
            else:
                self.is_active = True
                self.current_state_of_charge = input_state_of_charge
                self.hours_of_charge = hours_of_charge
        return

    def function(self, dict_results):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if self.is_active:

            len_x = self.discretize_state_of_charge(self.max_capacity - self.current_state_of_charge) + 1
            len_y = min(len(self.simulation.array_price), self.hours_of_charge) + 1
            action_zero = self.action_list.index(0.0)
            Q = []
            for hour in range(len_y):
                Q_row = []
                for state in range(len_x):
                    if state == 0 and hour > 0:
                        Q_row.append(self.Info(self.get_reward(0, 0, 0), [action_zero]))
                    else:
                        Q_row.append(self.Info())
                Q.append(Q_row)

            tmp_info = self.Info()
            for hour in range(1, len_y):

                for state in range(1, len_x):
                    state_of_charge = self.state_to_charge(state)
                    min_index, max_index = self.get_min_max_index_action(state_of_charge)
                    local_max_energy_demand = min(self.max_energy_demand, self.max_capacity - state_of_charge)
                    best_action = action_zero

                    for action in range(min_index, max_index + 1):
                        kwh = self.action_list[action]
                        if kwh == 0:
                            if state_of_charge + self.action_list[
                                action + 1] > self.max_capacity:  # niente index out of range per costruzione
                                kwh = local_max_energy_demand  # a causa di un'assenza di totale liberta' di range, quando la action genera kwh == 0 allora "rabbocco" kwh al current_max_energy_demand
                        tmp_info = copy.deepcopy(Q[hour - 1][self.discretize_state_of_charge(
                            self.max_capacity - self.current_state_of_charge - (state_of_charge + kwh))])
                        tmp_info.value += self.get_reward(hour - 1, kwh, local_max_energy_demand)

                        if tmp_info.value > Q[hour][state].value:
                            Q[hour][state].clone(tmp_info)
                            best_action = action

                    if Q[hour][state].first_action == -1:
                        Q[hour][state].first_action = [best_action]
                    else:
                        Q[hour][state].first_action.append(best_action)

            if len_x != 1:
                action = Q[len_y - 1][len_x - 1].first_action[0]
            else:
                action = action_zero
            E = self.action_list[action]
            local_max_energy_demand = min(self.max_energy_demand, self.max_capacity - self.current_state_of_charge)
            if E == 0:
                if self.current_state_of_charge + self.action_list[
                    action + 1] > self.max_capacity:  # niente index out of range per costruzione
                    E = local_max_energy_demand  # a causa di un'assenza di totale liberta' di range, quando la action genera kwh == 0 allora "rabbocco" kwh al current_max_energy_demand
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E + self.simulation.home.p * (
                    self.beta * ((E - local_max_energy_demand) ** 2))
            self.current_state_of_charge += E

        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        dict_results[self.id] = {'E': E, 'U': U, 'SOC': self.current_state_of_charge}
        return

    def state_to_charge(self, state):
        # l'output e' da leggere nel modo seguente: 
        # es (self.max_capacity / (self.state_number - 1)) = 0.5, state = 2
        # considero le casistiche dove 0.5 < charge <= 1.0
        return state * (self.max_capacity / (self.state_number - 1))

    def get_reward(self, index, kwh, max_energy_demand):
        value = (1 - self.simulation.home.p) * self.simulation.array_price[index] * kwh + self.simulation.home.p * (
                self.beta * ((kwh - max_energy_demand) ** 2))
        if value == 0:
            return 1
        return 1 / value


def insert_DP_Battery(simulation):
    battery_DF = pd.read_csv(os.path.join(simulation.home.path_dir_home, "DPpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        max_energy_demand = float(row["charge_speed_kw"])
        min_energy_demand = 0  # -float(row["discharge_speed_kw"]) #attualmente l'algoritmo non e' pensato per device che producono energia (va rivista la formula delle reward, e forse anche la formula di U, ma penso sono la prima)
        action_number = int(row["action_number"])
        state_number = int(row["state_number"])
        beta = float(row["beta"])
        max_capacity = float(row["battery_capacity_kwh"])
        new_battery = DP_Battery(simulation, "DP_Battery." + str(row_index), beta, 0, max_capacity, min_energy_demand,
                                 max_energy_demand, action_number, state_number,
                                 ("PEV_input_state_of_charge", "PEV_hours_of_charge"))
        simulation.device_list.add(new_battery)
        row_index += 1
    return

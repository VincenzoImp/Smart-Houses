from libraries import *

class DP_Battery(object):

    class Info(object):
        def __init__(self, value = 0.0, first_action = -1):
            self.value = value
            self.first_action = first_action
        def clone(self, info_obj):
            self.value = info_obj.value
            self.first_action = info_obj.first_action

    def __init__(self, id, beta, current_state_of_charge, max_capacity, min_energy_demand, max_energy_demand, action_number, state_number, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"): #si assume che action_number >=2
            self.id = id
            self.beta = beta
            self.current_state_of_charge = current_state_of_charge
            self.max_capacity = max_capacity
            self.min_energy_demand = min_energy_demand #si assuma sia diverso da max_energy_demand
            self.max_energy_demand = max_energy_demand #si assuma sia diverso da min_energy_demand
            self.action_number = action_number
            self.state_number = state_number
            self.column_info = column_info
            self.working_hours = working_hours
            self.action_list = self.initialize_action_list(action_number) #min e max energy demand ci sono sempre per costruzione
            self.filename = os.path.join(directory, str(self.id)+".csv")
            self.initialize_file()
            self.hours_of_charge = 0
            return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def initialize_action_list(self, action_number):
        delta_grid = (self.max_energy_demand-self.min_energy_demand)/(action_number-1)
        action_list = []
        for i in range(0,action_number-1):
            action_list.append(self.min_energy_demand+(delta_grid*i))
        action_list.append(self.max_energy_demand)
        return action_list

    def get_min_max_index_action(self, state_of_charge, max_capacity):
        min_action = -1
        max_action = -1
        check = False
        for i, action in enumerate(self.action_list):
            if not check and state_of_charge+action >= 0 and state_of_charge+action <= max_capacity:
                check = True
                min_action = i
                max_action = i
            if check and state_of_charge+action >= 0 and state_of_charge+action <= max_capacity:
                max_action = i
        return (min_action, max_action)

    def charge_to_state(self, state_of_charge):
        state = 0
        delta = self.max_capacity/(self.state_number-1)
        if state_of_charge != 0.0:
            for i in range(self.state_number-1):
                state = i
                if delta*i < state_of_charge <= delta*(i+1):
                    break
        return state

    def state_to_charge(self, state):
        return state*(self.max_capacity/(self.state_number-1))

    def get_reward(self, index, kwh, max_energy_demand):
        value = (1-p)*array_price[index]*kwh+p*(self.beta*((kwh-max_energy_demand)**2)) +0.00000001
        return 1/value

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            input_state_of_charge = house_profile_DF.at[count_row, self.column_info[0]]
            hours_of_charge = house_profile_DF.at[count_row, self.column_info[1]]
            if input_state_of_charge == -1:
                self.working_hours = "(-1)$"
                self.current_state_of_charge = -1
            elif input_state_of_charge == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.hours_of_charge -= 1
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.current_state_of_charge = input_state_of_charge
                self.hours_of_charge = hours_of_charge
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if re.match(self.working_hours, str(current_hour)):
            tmp_info = self.Info()
            action_zero = self.action_list.index(0.0)
            len_x = self.hours_of_charge+1
            len_y = self.charge_to_state(self.max_capacity-self.current_state_of_charge)+1
            Q = [[self.Info() for _ in range(len_x)] for _ in range(len_y)]
            
            for state in range(1, len_y):
                state_of_charge = self.current_state_of_charge
                local_max_capacity = self.current_state_of_charge+self.state_to_charge(state)

                for hour in range(1, len_x):
                    min_index, max_index = self.get_min_max_index_action(state_of_charge, local_max_capacity)
                    best_action = action_zero

                    for action in range(min_index, max_index+1):
                        kwh = self.action_list[action]
                        if kwh == 0:
                            if state_of_charge+self.action_list[action+1] > local_max_capacity: #niente index out of range per costruzione
                                kwh = min(self.max_energy_demand, local_max_capacity-state_of_charge) #a causa di un'assenza di totale liberta' di range, quando la action genera kwh == 0 allora "rabbocco" kwh al current_max_energy_demand
                        tmp_info.clone(Q[self.charge_to_state(self.max_capacity-(state_of_charge+kwh))][hour-1])
                        tmp_info.value += self.get_reward(hour-1, kwh, local_max_capacity-state_of_charge)
                        if tmp_info.first_action == -1:
                            tmp_info.first_action = action
                        if tmp_info.value > Q[state][hour].value:
                            Q[state][hour].clone(tmp_info)
                            best_action = action
                    state_of_charge += self.action_list[best_action]
            if len_y != 1:
                action = Q[len_y-1][len_x-1].first_action
            else:
                action = action_zero
            E = self.action_list[action]
            if E == 0:
                if self.current_state_of_charge+self.action_list[action+1] > self.max_capacity: #niente index out of range per costruzione
                    E = min(self.max_energy_demand, self.max_capacity-self.current_state_of_charge) #a causa di un'assenza di totale liberta' di range, quando la action genera kwh == 0 allora "rabbocco" kwh al current_max_energy_demand
            U = (1-p)*array_price[0]*E+p*(self.beta*((E-self.max_energy_demand)**2))
            self.current_state_of_charge += E
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U 


def insert_DP_Battery(device_list, path_dir_home):
    battery_DF = pd.read_csv(os.path.join(path_dir_home, "DPpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        max_energy_demand = float(row["charge_speed_kw"])
        min_energy_demand = 0 #-float(row["discharge_speed_kw"]) #attualmente l'algoritmo non e' pensato per device che producono energia (va rivista la formula delle reward, e forse anche la formula di U, ma penso sono la prima)
        action_number = int(row["action_number"])
        state_number = int(row["state_number"])
        beta = float(row["beta"])
        max_capacity = float(row["battery_capacity_kwh"])
        new_battery = DP_Battery("DP_Battery."+str(row_index), beta, 0, max_capacity, min_energy_demand, max_energy_demand, action_number, state_number, ("PEV_input_state_of_charge","PEV_hours_of_charge"))
        device_list.add(new_battery)
        row_index += 1
    return
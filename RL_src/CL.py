from libraries import *

class Controlable_load(object):

    def __init__(self, id, beta, min_energy_demand, max_energy_demand, state_number, action_number, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"): #si assume che action_number >=2
        self.id = id
        self.beta = beta
        self.min_energy_demand = min_energy_demand #si assuma sia diverso da max_energy_demand
        self.max_energy_demand = max_energy_demand #si assuma sia diverso da min_energy_demand
        self.state_number = state_number
        self.action_number = action_number
        self.column_info = column_info
        self.working_hours = working_hours
        self.action_list = self.initialize_action_list() #min e max energy demand ci sono sempre per costruzione
        self.Q = np.zeros((24, self.state_number, self.action_number), dtype=float)
        self.filename = os.path.join(directory, str(self.id)+".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

    def initialize_action_list(self):
        delta_grid = (self.max_energy_demand-self.min_energy_demand)/(self.action_number-1)
        action_list = []
        for i in range(self.action_number):
            action_list.append(self.min_energy_demand+(delta_grid*i))
        action_list.append(self.max_energy_demand)
        return action_list

    def chose_action(self, hour, state, randomless=False):
        if randomless or np.random.random() >= epsilon:
            action = np.random.choice(np.where(self.Q[hour][state] == max(self.Q[hour][state]))[0], 1)[0]
        else:
            action = np.random.choice(self.action_number, 1)[0]
        return action

    def get_reward(self, index, kwh):
        value = (1-p)*array_price[index]*kwh+p*(self.beta*((kwh-self.max_energy_demand)**2)) + 0.0000001
        return 1/value

    def get_state(self):
        return 0

    def next_state(self, state):
        return state

    def is_final_state(self, state):
        return False

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0])
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            tmp = house_profile_DF.at[count_row, self.column_info]
            if tmp == -1:
                self.working_hours = "(-1)$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if re.match(self.working_hours, str(current_hour)): #caso in cui posso stare nelle righe diverse da -1
            if not one_memory:
                self.Q = np.zeros((24, self.state_number, self.action_number), dtype=float)
            while i < loops:
                index = 0
                hour = current_hour
                state = self.get_state()
                while index < 24  and not self.is_final_state(state):
                    action = self.chose_action(hour)
                    reward = self.get_reward(index, self.action_list[action])
                    new_hour = (hour+1)%24
                    new_state = self.next_state(state)
                    self.Q[hour][state][action] = self.Q[hour][state][action]+teta*(reward+gamma*self.Q[new_hour][new_state][self.chose_action(new_hour, new_state, True)[0]]-self.Q[hour][state][action])
                    index += 1
                    hour = new_hour
                    state = new_state
                i += 1
            action = self.chose_action(current_hour, self.get_state(), True)
            E = self.action_list[action]
            U = (1-p)*array_price[0]*E+p*(self.beta*((E-self.max_energy_demand)**2))
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


class CL_Battery(Controlable_load):

    def __init__(self, id, beta, min_energy_demand, max_energy_demand, state_number, action_number, max_capacity, current_state_of_charge = 0, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"):
        Controlable_load.__init__(self, id, beta, min_energy_demand, max_energy_demand, state_number, action_number, column_info, working_hours)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def get_min_max_index_action(self, state_of_charge):
        min_action = -1 #forse meglio inizializzare a -1 perche' nel caso in cui non sia possibili effettuare nessuna azione e non vi sia l'azione che carica 0 kwh verrebbe effettuata l'azione all'indice 0 che e' un'azione invalida siccome siamo nel caso in cui nessuna azione e' possibile. con l'inizzializzazione a -1, nel caso descritto dovrebbe avvenite un errore
        max_action = self.action_number-1
        check = False
        for i, action in enumerate(self.action_list):
            if not check and state_of_charge+action >= 0 and state_of_charge+action <= self.max_capacity:
                check = True
                min_action = i
                max_action = i
            if check and state_of_charge+action >= 0 and state_of_charge+action <= self.max_capacity:
                max_action = i
        return (min_action, max_action)

    def get_state(self, state_of_charge):
        state = 0
        if self.state_number == 1: return state
        delta = self.max_capacity/(self.state_number-1)
        if state_of_charge == self.max_capacity:
            state = self.state_number-1
        else:
            for i in range(self.state_number-1):
                if delta*i <= state_of_charge < delta*(i+1):
                    state = i
                    break
        return state

    def get_reward(self, index, kwh, max_energy_demand):
        value = (1-p)*array_price[index]*kwh+p*(self.beta*((kwh-max_energy_demand)**2)) + 0.0000001
        return 1/value
        
    def chose_action(self, hour, state, state_of_charge, randomless=False):
        min_action, max_action = self.get_min_max_index_action(state_of_charge)
        if randomless or np.random.random() >= epsilon:
            action = min_action+np.random.choice(np.where(self.Q[hour][state][min_action:max_action+1] == max(self.Q[hour][state][min_action:max_action+1]))[0], 1)[0]
        else:
            action = min_action+np.random.choice(len(self.Q[hour][state][min_action:max_action+1]), 1)[0]
        return action

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            new_current_state_of_charge = house_profile_DF.at[count_row, self.column_info]
            if new_current_state_of_charge == -1:
                self.working_hours = "(-1)$"
                self.current_state_of_charge = -1
            elif new_current_state_of_charge == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.current_state_of_charge = new_current_state_of_charge
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        t = 1
        if re.match(self.working_hours, str(current_hour)):
            if not one_memory:
                self.Q = np.zeros((24, self.state_number, self.action_number), dtype=float)
            while i < loops:
                index = 0
                hour = current_hour
                state = self.get_state(self.current_state_of_charge)
                state_of_charge = self.current_state_of_charge
                while state_of_charge != self.max_capacity and index < 24:
                    action = self.chose_action(hour, state, state_of_charge)
                    kwh = self.action_list[action]
                    if kwh == 0:
                        if state_of_charge+self.action_list[action+1] > self.max_capacity: #niente index out of range per costruzione
                            kwh = min(self.max_energy_demand, self.max_capacity-state_of_charge) #a causa di un'assenza di totale liberta' di range, quando la action genera kwh == 0 allora "rabbocco" kwh al current_max_energy_demand
                    local_max_energy_demand = min(self.max_energy_demand, self.max_capacity-state_of_charge)
                    reward = self.get_reward(index, kwh, local_max_energy_demand)
                    new_state_of_charge = state_of_charge + kwh
                    new_hour = (hour+1)%24
                    new_state = self.get_state(new_state_of_charge)
                    self.Q[hour][state][action] = self.Q[hour][state][action]+teta*(reward+gamma*self.Q[new_hour][new_state][self.chose_action(new_hour, new_state, new_state_of_charge, True)]-self.Q[hour][state][action])
                    hour = new_hour
                    state = new_state
                    state_of_charge = new_state_of_charge
                    t += 1
                    index += 1
                i += 1
            action = self.chose_action(current_hour, self.get_state(self.current_state_of_charge), self.current_state_of_charge, True)
            E = self.action_list[action]
            if E == 0:
                if self.current_state_of_charge+self.action_list[action+1] > self.max_capacity: #niente index out of range per costruzione
                    E = min(self.max_energy_demand, self.max_capacity-self.current_state_of_charge) #a causa di un'assenza di totale liberta' di range, quando la action genera E == 0 allora "rabbocco" E al current_max_energy_demand
            local_max_energy_demand = min(self.max_energy_demand, self.max_capacity-self.current_state_of_charge)
            U = (1-p)*array_price[0]*E+p*(self.beta*((E-local_max_energy_demand)**2))
            self.current_state_of_charge += E
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


def insert_CL(home):

    return


def insert_CL_Battery(home):
    battery_DF = pd.read_csv(os.path.join(home.path_dir_home, "CLpev.csv"))
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
        new_battery = CL_Battery("CL_Battery."+str(row_index), beta, min_energy_demand, max_energy_demand, state_number, action_number, max_capacity, 0, "PEV_input_state_of_charge")
        home.device_list.add(new_battery)
        row_index += 1
    return
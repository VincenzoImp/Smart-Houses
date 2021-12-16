from libraries import csv, np, os, datetime, re


class Controlable_load(object):

    def __init__(self, simulation, id, beta, min_energy_demand, max_energy_demand, state_number, action_number, column_info=None,
                 working_hours="([0-9]|1[0-9]|2[0-3])$"):  # si assume che action_number >=2
        self.simulation = simulation
        self.id = id
        self.beta = beta
        self.min_energy_demand = min_energy_demand  # si assuma sia diverso da max_energy_demand
        self.max_energy_demand = max_energy_demand  # si assuma sia diverso da min_energy_demand
        self.state_number = state_number
        self.action_number = action_number
        self.column_info = column_info
        self.working_hours = working_hours
        self.action_list = self.initialize_action_list()  # min e max energy demand ci sono sempre per costruzione
        self.Q = np.zeros((24, self.state_number, self.action_number), dtype=float)
        self.filename = os.path.join(self.simulation.directory, str(self.id) + ".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

    def initialize_action_list(self):
        delta_grid = (self.max_energy_demand - self.min_energy_demand) / (self.action_number - 1)
        action_list = []
        for i in range(self.action_number):
            action_list.append(self.min_energy_demand + (delta_grid * i))
        action_list.append(self.max_energy_demand)
        return action_list

    def chose_action(self, hour, state, randomless=False):
        if randomless or np.random.random() >= self.simulation.home.epsilon:
            action = np.random.choice(np.where(self.Q[hour][state] == max(self.Q[hour][state]))[0], 1)[0]
        else:
            action = np.random.choice(self.action_number, 1)[0]
        return action

    def get_reward(self, index, kwh):
        value = (1 - self.simulation.home.p) * self.simulation.array_price[index] * kwh + self.simulation.home.p * (self.beta * ((kwh - self.max_energy_demand) ** 2)) + 0.0000001
        return 1 / value

    def get_state(self):
        return 0

    def next_state(self, state):
        return state

    def is_final_state(self, state):
        return False

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(self.simulation.current_hour)):
                csv.writer(file_object).writerow([self.simulation.timestamp, "on", E, U, time])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0])
        return

    def update_data(self):
        if self.column_info != None:
            tmp = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info]
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
        if re.match(self.working_hours, str(self.simulation.current_hour)):  # caso in cui posso stare nelle righe diverse da -1
            if not self.simulation.home.one_memory:
                self.Q = np.zeros((24, self.state_number, self.action_number), dtype=float)
            while i < self.simulation.home.loops:
                index = 0
                hour = self.simulation.current_hour
                state = self.get_state()
                while index < 24 and not self.is_final_state(state):
                    action = self.chose_action(hour)
                    reward = self.get_reward(index, self.action_list[action])
                    new_hour = (hour + 1) % 24
                    new_state = self.next_state(state)
                    self.Q[hour][state][action] = self.Q[hour][state][action] + self.simulation.home.teta * (
                            reward + self.simulation.home.gamma * self.Q[new_hour][new_state][
                        self.chose_action(new_hour, new_state, True)[0]] - self.Q[hour][state][action])
                    index += 1
                    hour = new_hour
                    state = new_state
                i += 1
            action = self.chose_action(self.simulation.current_hour, self.get_state(), True)
            E = self.action_list[action]
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E + self.simulation.home.p * (self.beta * ((E - self.max_energy_demand) ** 2))
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        return E, U


def insert_CL(simulation):
    return
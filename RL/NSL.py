from libraries import re, csv, os, datetime


class Non_shiftable_load(object):

    def __init__(self, simulation, id, energy_demand=0, column_info=None, working_hours="([0-9]|1[0-9]|2[0-3])$"):
        self.simulation = simulation
        self.id = id
        self.energy_demand = energy_demand
        self.column_info = column_info
        self.working_hours = working_hours
        self.filename = os.path.join(self.simulation.directory, str(self.id) + ".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

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
                self.energy_demand = 0
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.energy_demand = tmp
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if re.match(self.working_hours, str(self.simulation.current_hour)):
            E = self.energy_demand
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        return E, U


def insert_NSL(simulation):
    new_NSL = Non_shiftable_load(simulation, "NSL_house.0", 0, "consumption_kwh")
    simulation.device_list.add(new_NSL)
    return
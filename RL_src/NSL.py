from libraries import *

class Non_shiftable_load(object):

    def __init__(self, id, energy_demand = 0, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"):
        self.id = id
        self.energy_demand = energy_demand
        self.column_info = column_info
        self.working_hours = working_hours
        self.filename = os.path.join(directory, str(self.id)+".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

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
                self.energy_demand = 0
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.energy_demand = tmp
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if re.match(self.working_hours, str(current_hour)):
            E = self.energy_demand
            U = (1-p)*array_price[0]*E
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


class NSL_Battery(Non_shiftable_load):

    def __init__(self, id, max_capacity, current_state_of_charge = 0, energy_demand = 0, column_info = None, working_hours = "([0-9]|1[0-9]|2[0-3])$"):
        Non_shiftable_load.__init__(self, id, energy_demand, column_info, working_hours)
        self.max_capacity = max_capacity
        self.current_state_of_charge = current_state_of_charge
        return
    
    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time", "output_state_of_charge"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time, self.current_state_of_charge])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0, -1])
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            tmp = house_profile_DF.at[count_row, self.column_info]
            if tmp == -1:
                self.working_hours = "(-1)$"
                self.current_state_of_charge = -1
            elif tmp == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.current_state_of_charge = tmp
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if re.match(self.working_hours, str(current_hour)):
            E = min(self.energy_demand, self.max_capacity-self.current_state_of_charge)
            U = (1-p)*array_price[0]*E
            self.current_state_of_charge += E
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


def insert_NSL(device_list, path_dir_home):
    new_NSL = Non_shiftable_load("NSL_house.0", 0, "consumption_kwh")
    device_list.add(new_NSL)
    return


def insert_NSL_Battery(device_list, path_dir_home):
    battery_DF = pd.read_csv(os.path.join(path_dir_home, "NSLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        max_capacity = float(row["battery_capacity_kwh"])
        energy_demand = float(row["charge_speed_kw"])
        new_NSL_Battery = NSL_Battery("NSL_Battery."+str(row_index), max_capacity, 0, energy_demand, "PEV_input_state_of_charge")
        device_list.add(new_NSL_Battery)
        row_index += 1
    return
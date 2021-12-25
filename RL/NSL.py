from Device import Device
from libraries import datetime

class Non_shiftable_load(Device):

    def __init__(self, simulation, id, energy_demand=0, column_info=None, is_active=False):
        super().__init__(simulation, id, column_info, is_active)
        self.energy_demand = energy_demand
        return

    def update_data(self):
        if self.column_info != None:
            tmp = self.simulation.house_profile_DF.at[self.simulation.count_row, self.column_info]
            if tmp == -1:
                self.is_active = False
                self.energy_demand = 0
            else:
                self.is_active = True
                self.energy_demand = tmp
        return

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        if self.is_active:
            E = self.energy_demand
            U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        return E, U


def insert_NSL(simulation):
    new_NSL = Non_shiftable_load(simulation, "NSL_house.0", 0, "consumption_kwh")
    simulation.device_list.add(new_NSL)
    return
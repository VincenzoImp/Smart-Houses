from Device import Device


class Controlable_load(Device):

    def __init__(self, simulation, id, beta, min_energy_demand, max_energy_demand, state_number, action_number,
                 column_info=None, plots_directory="", is_active=False):  # si assume che action_number >=2
        super().__init__(simulation, id, column_info, plots_directory, is_active)
        self.beta = beta
        self.min_energy_demand = min_energy_demand  # si assuma sia diverso da max_energy_demand
        self.max_energy_demand = max_energy_demand  # si assuma sia diverso da min_energy_demand
        self.state_number = state_number
        self.action_number = action_number
        self.action_list = self.get_action_list()  # min e max energy demand ci sono sempre per costruzione
        return

    def update_data(self):
        # TO DO
        return

    def function(self, dict_results):
        # TO DO
        return

    def get_action_list(self):
        delta_grid = (self.max_energy_demand - self.min_energy_demand) / (self.action_number - 1)
        action_list = []
        for i in range(self.action_number):
            action_list.append(self.min_energy_demand + (delta_grid * i))
        action_list.append(self.max_energy_demand)
        return action_list


def insert_CL(simulation):
    # TO DO
    return

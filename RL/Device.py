from libraries import os, csv, ABCMeta, abstractmethod


class Device(metaclass=ABCMeta):

    def __init__(self, simulation, id, column_info=None, plots_directory="", is_active=False):
        self.simulation = simulation
        self.id = id
        self.column_info = column_info
        self.plots_directory = plots_directory
        self.is_active = is_active
        self.filename = os.path.join(self.simulation.directory, str(self.id) + ".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if self.is_active:
                csv.writer(file_object).writerow([self.simulation.timestamp, "on", E, U, time])
            else:
                csv.writer(file_object).writerow([self.simulation.timestamp, "off", 0, 0, 0])
        return

    @abstractmethod
    def update_data(self):
        raise NotImplementedError("This method must be implemented.")

    @abstractmethod
    def function(self, dict_results):
        raise NotImplementedError("This method must be implemented.")

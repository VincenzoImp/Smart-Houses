from Home import Home
from NSL_Battery import *
from Naif_Battery import *
from libraries import os, csv, datetime, pd, multiprocessing


class Simulation(object):

    def __init__(self, home: Home, path_results, loops):
        # simulation datas
        self.home = home
        self.path_results = path_results
        self.directory = ""
        self.device_list = set()
        self.count_row = 0
        self.array_price = []
        self.timestamp = ""
        self.loops = loops
        self.house_profile_DF = None
        self.energy_price_DF = None
        return

    def insert_devices(self):
        # insert_NSL(self)
        insert_NSL_Battery(self)
        # insert_CL(self)
        # insert_CL_Battery(self)
        # insert_DP_Battery(self)
        insert_Naif_Battery(self)
        return

    def run(self):
        self.directory = os.path.join(self.path_results,
                                      self.home.id + "_" + datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S"))
        os.mkdir(self.directory)
        self.insert_devices()
        self.house_profile_DF = pd.read_csv(os.path.join(self.home.path_dir_home, "new_profiles.csv"))
        self.energy_price_DF = pd.read_csv(self.home.path_energy_price)
        start_index = self.house_profile_DF.index[
            self.house_profile_DF["timestamp"] == self.energy_price_DF.iloc[0]["timestamp"]].tolist()[0]
        end_index = self.house_profile_DF.index[
            self.house_profile_DF["timestamp"] == self.energy_price_DF.iloc[-1]["timestamp"]].tolist()[0]
        self.house_profile_DF = self.house_profile_DF[start_index: end_index + 1]
        self.house_profile_DF.reset_index(drop=True, inplace=True)
        main_filename = os.path.join(self.directory, "main.csv")
        with open(main_filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "E", "U", "time"])
        while True:
            time = datetime.datetime.now()
            E = 0.0
            U = 0.0
            try:
                self.timestamp = self.house_profile_DF.at[self.count_row, "timestamp"]
                self.array_price = self.energy_price_DF.iloc[self.count_row, 1:13].to_list()
            except KeyError:
                break
            dict_results = multiprocessing.Manager().dict()
            thread_list = []
            for device in self.device_list:
                device.update_data()
                thread = multiprocessing.Process(target=device.function, args=(dict_results,))
                thread_list.append(thread)
                thread.start()
            for thread in thread_list:
                thread.join()
            for device in self.device_list:
                E += dict_results[device.id]['E']
                U += dict_results[device.id]['U']
                if 'SOC' in dict_results[device.id].keys():
                    device.current_state_of_charge = dict_results[device.id]['SOC']
            time = datetime.datetime.now() - time
            with open(main_filename, "a") as file_object:
                csv.writer(file_object).writerow([self.timestamp, E, U, time])
            self.count_row += 1
        info_filename = os.path.join(self.directory, "info.txt")
        with open(info_filename, "w") as file_object:
            file_object.write(
                "p: {} (p ∈ [0,1] é la prioritá di ottimizzare i disservizi. (1-p) é la prioritá di ottimizzare i consumi. Nell'articolo é [0.8, 0.5, 0.3])\n".format(
                    self.home.p))
            file_object.write(
                "teta: {} (θ ∈ [0,1] è un tasso di apprendimento che rappresenta in che misura il nuovo prevale sui vecchi valori Q. Nell'articolo é 0.1)\n".format(
                    self.home.teta))
            file_object.write(
                "gamma: {} (γ ∈ [0,1] è un fattore di attualizzazione che indica l'importanza relativa dei premi futuri rispetto a quelli attuali. Nell'articolo é 0.95)\n".format(
                    self.home.gamma))
            file_object.write(
                "epsilon: {} (epsilon é la probabilitá di scegliere un azione random. (1-epsilon) é la probabilitá di scegliere l'azione migliore)\n".format(
                    self.home.epsilon))
            file_object.write("loops: {}\n".format(self.loops))
        return

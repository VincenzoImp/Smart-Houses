from NSL import *
from NSL_Battery import *
from CL import *
from CL_Battery import *
from DP_Battery import *
from Naif_Battery import *
from Home import Home
from Evaluation import *
from libraries import os, csv, datetime, pd, multiprocessing

class Simulation(object):

    def __init__(self, home: Home, path_results, loops):
        #simulation datas
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
        #insert_NSL(self)
        insert_NSL_Battery(self)
        #insert_CL(self)
        insert_CL_Battery(self)
        #insert_DP_Battery(self)
        insert_Naif_Battery(self)
        return

    def setup(self):
        self.house_profile_DF = pd.read_csv(os.path.join(self.home.path_dir_home, "new_profiles.csv"))
        self.energy_price_DF = pd.read_csv(self.home.path_energy_price)
        start_index = self.house_profile_DF.index[self.house_profile_DF["timestamp"] == self.energy_price_DF.iloc[0]["timestamp"]].tolist()[0]
        end_index = self.house_profile_DF.index[self.house_profile_DF["timestamp"] == self.energy_price_DF.iloc[-1]["timestamp"]].tolist()[0]
        self.house_profile_DF = self.house_profile_DF[start_index : end_index+1]
        self.house_profile_DF.reset_index(drop=True, inplace=True)
        return

    def simulate(self):
        self.directory = os.path.join(self.path_results, self.home.id + "_" + datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S"))
        os.mkdir(self.directory)
        self.insert_devices()
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
        info_filename = os.path.join(self.directory, "info.csv")
        with open(info_filename, "w") as file_object:
            csv.writer(file_object).writerow(["p", "theta", "gamma", "epsilon", "loops"])
            csv.writer(file_object).writerow([self.home.p, self.home.teta, self.home.gamma, self.home.epsilon, self.loops])
        return

    def evaluate(self):
        evaluation_obj = Evaluation(self)
        evaluation_obj.run()
        return

    def run(self):
        self.setup()
        self.simulate()
        self.evaluate()
        return

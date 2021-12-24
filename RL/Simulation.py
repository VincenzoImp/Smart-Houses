from CL import *
from CL_Battery import *
from DP_Battery import *
from Home import Home
from NSL import *
from NSL_Battery import *
from Naif_Battery import *
from SL import *
from SL_Battery import *
from libraries import threading, os, csv, datetime, pd


class Simulation(object):

    def __init__(self, home: Home, loops, one_memory, current_day=0, current_hour=0):
        # simulation datas
        self.home = home
        self.directory = ""
        self.device_list = set()
        self.current_day = current_day
        self.current_hour = current_hour
        self.count_row = current_day * 24 + current_hour
        self.array_price = []
        self.timestamp = ""
        self.loops = loops
        self.one_memory = one_memory
        self.house_profile_DF = None
        self.energy_price_DF = None
        return

    def insert_devices(self):
        insert_NSL(self)
        insert_NSL_Battery(self)
        insert_SL(self)
        insert_SL_Battery(self)
        insert_CL(self)
        insert_CL_Battery(self)
        insert_DP_Battery(self)
        insert_Naif_Battery(self)
        return

    def run(self):
        self.directory = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        os.mkdir(self.directory)
        self.insert_devices()
        self.house_profile_DF = pd.read_csv(os.path.join(self.home.path_dir_home, "new_profiles.csv"))
        self.energy_price_DF = pd.read_csv(self.home.path_energy_price)
        main_filename = os.path.join(self.directory, "main.csv")
        with open(main_filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "E", "U", "time"])
        while True:
            time = datetime.datetime.now()
            E = 0.0
            U = 0.0
            try:
                self.timestamp = self.house_profile_DF.at[self.count_row, "timestamp"]
                self.array_price = [1 for _ in range(12)]  # self.energy_price_DF.at[self.count_row, :]
            except:
                break
            thread_list = []
            for device in self.device_list:
                device.update_data()
                thread = Device_thread(device)
                thread_list.append(thread)
                thread.start()
            for thread in thread_list:
                e, u = thread.join()
                E += e
                U += u
            time = datetime.datetime.now() - time
            with open(main_filename, "a") as file_object:
                csv.writer(file_object).writerow([self.timestamp, E, U, time])
            self.current_hour += 1
            if self.current_hour == 24:
                self.current_day += 1
                self.current_hour = 0
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
            file_object.write("one_memory: {}\n".format(self.home.one_memory))
            file_object.write("loops: {}\n".format(self.home.loops))
        return


class Device_thread(threading.Thread):

    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
        self.E = None
        self.U = None
        return

    def run(self):
        E, U = self.device.function()
        self.E = E
        self.U = U
        return

    def join(self):
        threading.Thread.join(self)
        return self.E, self.U

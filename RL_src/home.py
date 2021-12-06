from CL import *
from DP_Battery import *
from NSL import *
from Naif_Battery import *
from SL import *


class Home(object):
    def __init__(self, path_dir_home, p=0.8, teta=0.1, gamma=0.95, epsilon=0.2, loops=1000, one_memory=False):
        self.p = p  # (1-p) é la prioritá di ottimizzare i consumi, e p é la prioritá di ottimizzare i disservizi #[0.3, 0.5, 0.8]
        self.teta = teta  # θ ∈ [0,1] è un tasso di apprendimento che rappresenta in che misura il nuovo prevale sui vecchi valori Q
        self.gamma = gamma  # γ ∈ [0,1] è un fattore di attualizzazione che indica l'importanza relativa dei premi futuri rispetto a quelli attuali
        self.epsilon = epsilon  # epsilon é la probabilitá di scegliere un azione random. (1-epsilon) é la probabilitá di scegliere l'azione migliore
        self.directory = os.path.join(path_dir_home, datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S"))
        self.timestamp = ""
        self.current_day = 0
        self.current_hour = 0
        self.count_row = 0
        self.array_price = [0.0 for _ in range(24)]
        self.loops = loops
        self.one_memory = one_memory
        self.path_dir_home = path_dir_home
        self.device_list = set()
        return

    def insert_devices(self):
        insert_NSL(self)
        insert_NSL_Battery(self)
        insert_SL_Battery(self)
        insert_Naif_Battery(self)
        insert_CL_Battery(self)
        insert_DP_Battery(self)
        return

    def run(self):
        os.mkdir(self.directory)
        self.insert_devices()
        house_profile_DF = pd.read_csv(os.path.join(self.path_dir_home, "newprofiles.csv"))
        filename_main = os.path.join(self.directory, "main.csv")
        with open(filename_main, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "E", "U", "time"])
        while True:
            time = datetime.datetime.now()
            E = 0.0
            U = 0.0
            try:
                timestamp = house_profile_DF.at[self.count_row, "timestamp"]
                for i in range(24):
                    self.array_price[i] = house_profile_DF.at[self.count_row + i, "energy_market_price"]
            except:
                break
            thread_list = []
            for device in self.device_list:
                device.update_data(house_profile_DF)
                thread = Device_thread(device)
                thread_list.append(thread)
                thread.start()
            for thread in thread_list:
                e, u = thread.join()
                E += e
                U += u
            time = datetime.datetime.now() - time
            with open(filename_main, "a") as file_object:
                csv.writer(file_object).writerow([timestamp, E, U, time])
            current_hour += 1
            if current_hour == 24:
                self.current_day += 1
                current_hour = 0
            self.count_row += 1
        file_name = os.path.join(self.directory, "info.txt")
        with open(file_name, "w") as file_object:
            file_object.write(
                "p: {} (p ∈ [0,1] é la prioritá di ottimizzare i disservizi. (1-p) é la prioritá di ottimizzare i consumi. Nell'articolo é [0.8, 0.5, 0.3])\n".format(
                    self.p))
            file_object.write(
                "teta: {} (θ ∈ [0,1] è un tasso di apprendimento che rappresenta in che misura il nuovo prevale sui vecchi valori Q. Nell'articolo é 0.1)\n".format(
                    self.teta))
            file_object.write(
                "gamma: {} (γ ∈ [0,1] è un fattore di attualizzazione che indica l'importanza relativa dei premi futuri rispetto a quelli attuali. Nell'articolo é 0.95)\n".format(
                    self.gamma))
            file_object.write(
                "epsilon: {} (epsilon é la probabilitá di scegliere un azione random. (1-epsilon) é la probabilitá di scegliere l'azione migliore)\n".format(
                    self.epsilon))
            file_object.write("one_memory: {}\n".format(self.one_memory))
            file_object.write("loops: {}\n".format(self.loops))
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

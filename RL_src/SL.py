from libraries import *

class Shiftable_load(object):

    def __init__(self, id, k, Tne, state_number, energy_demand = 0, column_info = None, Tini = 0, Tend = 23, working_hours = "([0-9]|1[0-9]|2[0-3])$"):
        #Tne deve essere maggiore di zero e minore di 24 altrimenti sarebbe stato modellato come NSL
        #Tini, Tw, Tend devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours (e anche tutte le ore tra Tini e Tend devono matchare con working_hours)
        #l'attuale implementazione prevede una distanza tra Tini e Tend inferiore o uguale alle 24 ore (ad esempio Tini=0, Tend=23, Tne=24, e' un obj che deve assolutamente lavorare tutto il giorno)
        self.id = id
        self.k = k
        self.state_number = state_number
        self.Tne = Tne #numero di ore che l'oggetto deve restare in esecuzione per poter terminare
        self.Tini = Tini #prima ora del range disponibile
        self.Tw = -1 #utile nella funzione self.function
        self.Tend = Tend #ultima ora del range disponibile
        self.energy_demand = energy_demand
        self.column_info = column_info #colonne utili per fare l'update dei dati qualora l'implementazione lo preveda
        self.working_hours = working_hours
        self.hours_available = -1 #totale ore disponibili comprese tra tini/ora corrente e tend contenente tw e lunghe maggiore o uguale di tne
        self.hours_worked = -1
        #hours_worked e' il contatore delle ore che il device ha svolto (obiettivo: raggiungere le Tne ore di lavoro) 
        #se hours_worked == -1 non e' ancora stato definito
        #se hours_worked == 0 il device non e' ancora in funzione
        #se 0 < hours_worked < Tne il device e' in funzione
        #se hours_worked == Tne il device ha finito il suo lavoro e non e' piu' in funzione
        #hours_worked e' un dato che va letto al termine dell'ora corrente
        self.Q = np.zeros((24, self.state_number, 2), dtype=float)
        self.filename = os.path.join(directory, str(self.id)+".csv")
        self.initialize_file()
        return

    def initialize_file(self):
        with open(self.filename, "w") as file_object:
            csv.writer(file_object).writerow(["timestamp", "on/off", "E", "U", "time"])
        return

    def get_reward(self, index, Tw, kwh):
        value = (1-p)*array_price[index]*kwh + p*(self.k*(((Tw+24)-self.Tini)%24)) + 0.0000001
        return 1/value

    def get_state(self):
        return 0
    
    def next_state(self, state):
        return state

    def update_history(self, E, U, time):
        with open(self.filename, "a") as file_object:
            if re.match(self.working_hours, str(current_hour)):
                csv.writer(file_object).writerow([timestamp, "on", E, U, time])
            else:
                csv.writer(file_object).writerow([timestamp, "off", 0, 0, 0])
        return

    def update_data(self, house_profile_DF):
        if self.column_info != None:
            Tne = house_profile_DF.at[count_row, self.column_info[0]]
            hours_available = house_profile_DF.at[count_row, self.column_info[1]]
            #Tne deve essere minore o uguale a hours_of_work (si assume sempre che vengano sempre rispettati i vincoli del sistema)
            if Tne == -1:
                self.working_hours = "(-1)$"
                self.hours_worked = -1
            elif Tne == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.Tini = current_hour
                self.Tw = -1
                self.Tend = (current_hour+hours_available-1)%24
                self.hours_available = hours_available
                self.Tne = Tne
                self.hours_worked = -1
        return

    def chose_action(self, hour, state, Tw, hours_available, hours_worked, randomless=False):
        if hours_worked <= 0:                                       #se non e' attivo
            if hours_available == self.Tne:
                return 1, hour, hours_available-1, 1
            else:
                if randomless or np.random.random() >= epsilon:
                    bin_action = np.random.choice(np.where(self.Q[hour][state] == max(self.Q[hour][state]))[0], 1)[0]
                else:
                    bin_action = np.random.choice(2, 1)[0]
                if bin_action == 1:
                    return 1, hour, hours_available-1, 1
                else: #bin_action == 0
                    return 0, (hour+1)%24, hours_available-1, 0
        if hours_worked > 0 and hours_worked < self.Tne:            #se e' attivo
            return (1, Tw, hours_available-1, hours_worked+1)
        if hours_worked >= self.Tne:                                #se ha terminato
            return (0, self.Tini, hours_available-1, hours_worked)
        
    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if re.match(self.working_hours, str(current_hour)): #caso in cui posso stare nelle righe diverse da -1
            if not one_memory:
                self.Q = np.zeros((24, self.state_number, 2), dtype=float)
            while i < loops:
                index = 0
                hour = current_hour
                state = self.get_state()
                Tw = self.Tw
                hours_available = self.hours_available
                hours_worked = self.hours_worked
                while hours_available > 0:
                    bin_action, new_Tw, new_hours_available, new_hours_worked = self.chose_action(hour, state, Tw, hours_available, hours_worked)
                    reward = self.get_reward(index, new_Tw, bin_action*self.energy_demand)
                    new_hour = (hour+1)%24
                    new_state = self.next_state(state)
                    self.Q[hour][state][bin_action] = self.Q[hour][state][bin_action]+teta*(reward+gamma*self.Q[new_hour][new_state][self.chose_action(new_hour, new_state, new_Tw, new_hours_available, new_hours_worked, True)[0]]-self.Q[hour][state][bin_action])
                    index += 1
                    hour = new_hour
                    state = new_state
                    Tw = new_Tw
                    hours_available = new_hours_available
                    hours_worked = new_hours_worked
                i += 1
            bin_action, self.Tw, self.hours_available, self.hours_worked = self.chose_action(current_hour, self.get_state(), self.Tw, self.hours_available, self.hours_worked, True)
            E = bin_action*self.energy_demand
            U = (1-p)*array_price[0]*E + p*(self.k*(((self.Tw+24)-self.Tini)%24))
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


class SL_Battery(Shiftable_load):

    def __init__(self, id, k, max_capacity, current_state_of_charge, Tne, state_number, energy_demand = 0, column_info = None, Tini = 0, Tend = 23, working_hours = "([0-9]|1[0-9]|2[0-3])$"): #Tini, Tw, Tend devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours
        Shiftable_load.__init__(self, id, k, Tne, state_number, energy_demand, column_info, Tini, Tend, working_hours)
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
            new_state_of_charge = house_profile_DF.at[count_row, self.column_info[0]]
            hours_available = house_profile_DF.at[count_row, self.column_info[1]]
            #Tne deve essere minore o uguale a hours_of_work (si assume sempre che vengano sempre rispettati i vincoli del sistema)
            if new_state_of_charge == -1:
                self.working_hours = "(-1)$"
                self.hours_worked = -1
            elif new_state_of_charge == -2:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
            else:
                self.working_hours = "([0-9]|1[0-9]|2[0-3])$"
                self.Tini = current_hour
                self.Tw = -1
                self.Tend = (current_hour+hours_available-1)%24
                self.hours_available = hours_available
                self.current_state_of_charge = new_state_of_charge
                self.Tne = min(self.hours_available, math.ceil((self.max_capacity-self.current_state_of_charge)/self.energy_demand))
                self.hours_worked = -1
        return

    def get_state(self, state_of_charge):
        state = 0
        if self.state_number == 1: return state
        delta = self.max_capacity/(self.state_number-1)
        if state_of_charge == self.max_capacity:
            state = self.state_number-1
        else:
            for i in range(self.state_number-1):
                if delta*i <= state_of_charge < delta*(i+1):
                    state = i
                    break
        return state

    def function(self):
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if re.match(self.working_hours, str(current_hour)): #caso in cui posso stare nelle righe diverse da -1
            if not one_memory:
                self.Q = np.zeros((24, self.state_number, 2), dtype=float)
            while i < loops:
                index = 0
                hour = current_hour
                state = self.get_state(self.current_state_of_charge)
                Tw = self.Tw
                hours_available = self.hours_available
                hours_worked = self.hours_worked
                state_of_charge = self.current_state_of_charge
                while hours_available > 0:
                    bin_action, new_Tw, new_hours_available, new_hours_worked = self.chose_action(hour, state, Tw, hours_available, hours_worked)
                    kwh = min(self.max_capacity-state_of_charge, bin_action*self.energy_demand)
                    new_state_of_charge = state_of_charge + kwh
                    reward = self.get_reward(index, new_Tw, kwh)
                    new_hour = (hour+1)%24
                    new_state = self.get_state(new_state_of_charge)
                    self.Q[hour][state][bin_action] = self.Q[hour][state][bin_action]+teta*(reward+gamma*self.Q[new_hour][new_state][self.chose_action(new_hour, new_state, new_Tw, new_hours_available, new_hours_worked, True)[0]]-self.Q[hour][state][bin_action])
                    index += 1
                    hour = new_hour
                    state = new_state
                    Tw = new_Tw
                    hours_available = new_hours_available
                    hours_worked = new_hours_worked
                    state_of_charge = new_state_of_charge
                i += 1
            bin_action, self.Tw, self.hours_available, self.hours_worked = self.chose_action(current_hour, self.get_state(self.current_state_of_charge), self.Tw, self.hours_available, self.hours_worked, True)
            E = min(self.max_capacity-self.current_state_of_charge, bin_action*self.energy_demand)
            U = (1-p)*array_price[0]*E + p*(self.k*(((self.Tw+24)-self.Tini)%24))
            self.current_state_of_charge += E
        time = datetime.datetime.now()-time
        self.update_history(E, U, time)
        return E, U


def insert_SL(device_list, path_dir_home):
    return


def insert_SL_Battery(device_list, path_dir_home):
    battery_DF = pd.read_csv(os.path.join(path_dir_home, "SLpev.csv"))
    row_index = 0
    while True:
        try:
            row = battery_DF.iloc[row_index]
        except IndexError:
            break
        k = float(row["k"])
        max_capacity = float(row["battery_capacity_kwh"])
        state_number = int(row["state_number"])
        energy_demand = float(row["charge_speed_kw"])
        new_battery = SL_Battery("SL_Battery."+str(row_index), k, max_capacity, 0, 0, state_number, energy_demand, ("PEV_input_state_of_charge", "PEV_hours_of_charge"))
        device_list.add(new_battery)
        row_index += 1
    return
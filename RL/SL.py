from SL_GreedyQLearning import SL_GreedyQLearning
from Device import Device
from libraries import datetime, copy, plt, os

class Shiftable_load(Device):

    def __init__(self, simulation, id, k, T_ne, state_number, T_ini = 0, T_end = 23, energy_demand=0, column_info=None, plots_directory="", is_active=False):
        super().__init__(simulation, id, column_info, plots_directory, is_active)
        #T_ne deve essere maggiore di zero e minore di 24 altrimenti sarebbe stato modellato come NSL
        #T_ini, T_w, T_end devono rispettare i vincoli descritti nell'articolo e dovrebbero matchare con working_hours (e anche tutte le ore tra T_ini e T_end devono matchare con working_hours)
        #l'attuale implementazione prevede una distanza tra T_ini e T_end inferiore o uguale alle 24 ore (ad esempio T_ini=0, T_end=23, T_ne=24, e' un obj che deve assolutamente lavorare tutto il giorno)
        self.k = k
        self.T_ne = T_ne #numero di ore che l'oggetto deve restare in esecuzione per poter terminare
        self.state_number = state_number
        self.T_ini = T_ini #prima ora del range disponibile
        self.T_end = T_end #ultima ora del range disponibile
        self.T_w = -1 #utile nella funzione self.function
        self.energy_demand = energy_demand
        self.hours_available = -1 #totale ore disponibili comprese tra T_ini/ora corrente e T_end contenente T_w e lunghe maggiore o uguale di T_ne
        self.hours_worked = -1
        #hours_worked e' il contatore delle ore che il device ha svolto (obiettivo: raggiungere le T_ne ore di lavoro) 
        #se hours_worked == -1 non e' ancora stato definito
        #se hours_worked == 0 il device non e' ancora in funzione
        #se 0 < hours_worked < T_ne il device e' in funzione
        #se hours_worked == T_ne il device ha finito il suo lavoro e non e' piu' in funzione
        #hours_worked e' un dato che va letto al termine dell'ora corrente
        self.LIMIT = 7
        return
        
    def update_data(self):
        #TO DO
        return

    def function(self, dict_results):
        #TO DO
        time = datetime.datetime.now()
        E = 0.0
        U = 0.0
        i = 1
        if self.is_active:  # caso in cui posso stare nelle righe diverse da -1
            if self.plots_directory != "":
                q_list = []
            SL_model = SL_GreedyQLearning(self)
            while (self.simulation.loops != None and i <= self.simulation.loops) or self.simulation == None:
                if self.simulation.loops == None:
                    old_SL_model = copy(SL_model)
                state_key = 1
                limit = min(self.LIMIT, len(self.simulation.array_price))
                SL_model.learn(state_key, limit)

                if self.plots_directory != "":
                    next_action_list = SL_model.extract_possible_actions(state_key)
                    action_key = SL_model.predict_next_action(state_key, next_action_list)
                    q_df = SL_model.get_q_df()
                    q_df = q_df[q_df.state_key == state_key]
                    q_list.append(q_df[q_df.action_key == action_key]["q_value"].values[0])   
                i += 1
                if self.simulation == None and SL_model.convergence(old_SL_model):
                    break
            state_key = 1
            next_action_list = SL_model.extract_possible_actions(state_key)
            action = SL_model.predict_next_action(state_key, next_action_list)

        if self.plots_directory != "":
            x_list = list(range(len(q_list)))
            plt.plot(x_list, q_list)
            plt.suptitle(self.id + "." + self.simulation.timestamp.replace(":", "_"))
            plt.xlabel('epochs')
            plt.ylabel('q_value')
            plt.savefig(os.path.join(self.plots_directory, self.id + "." + self.simulation.timestamp.replace(":", "_") +".png"))

        E = action*self.energy_demand
        U = (1 - self.simulation.home.p) * self.simulation.array_price[0] * E + self.simulation.home.p*(self.k*(((self.T_w+24)-self.T_ini)%24))
        time = datetime.datetime.now() - time
        self.update_history(E, U, time)
        dict_results[self.id] = {'E':E, 'U':U}
        return


def insert_SL(simulation):
    #TO DO
    return
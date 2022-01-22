from CL_GreedyQLearning import CL_GeedyQLearning
from libraries import random

class CL_Battery_GeedyQLearning(CL_GeedyQLearning):

    def __init__(self, device):
        super().__init__(device)
        self.tmp_state_of_charge = None
        return

    def extract_possible_actions(self, state_key, state_of_charge):
        min_action, max_action = self.device.get_min_max_index_action(state_of_charge)
        return [action_key for action_key in range(min_action, max_action+1)]

    def observe_reward_value(self, state_key, action_key):
        kwh = self.device.action_list[action_key]
        if kwh == 0 and self.tmp_state_of_charge + self.device.action_list[action_key + 1] > self.device.max_capacity:  # niente index out of range per costruzione
            kwh = min(self.device.max_energy_demand, self.device.max_capacity - self.tmp_state_of_charge)  # a causa di un'assenza di totale liberta' di range, quando la action genera E == 0 allora "rabbocco" E al current_max_energy_demand
        local_max_energy_demand = min(self.device.max_energy_demand, self.device.max_capacity - self.tmp_state_of_charge)
        value = (1 - self.device.simulation.home.p) * self.device.simulation.array_price[state_key[0]-1] * kwh + self.device.simulation.home.p * (self.device.beta * ((kwh - local_max_energy_demand) ** 2))
        if value == 0:
            return 1
        return 1 / value
    
    def update_state(self, state_key, action_key):
        kwh = self.device.action_list[action_key]
        if kwh == 0 and self.tmp_state_of_charge + self.device.action_list[action_key + 1] > self.device.max_capacity:  # niente index out of range per costruzione
            kwh = min(self.device.max_energy_demand, self.device.max_capacity - self.tmp_state_of_charge)  # a causa di un'assenza di totale liberta' di range, quando la action genera E == 0 allora "rabbocco" E al current_max_energy_demand
        return (state_key[0]+1, self.device.discretize_state_of_charge(self.tmp_state_of_charge + kwh)), self.tmp_state_of_charge + kwh

    def check_the_end_flag(self, state_key):
        return self.tmp_state_of_charge == self.device.max_capacity

    def visualize_learning_result(self, state_key):
        next_action_list = self.extract_possible_actions((1, self.device.discretize_state_of_charge(self.device.current_state_of_charge)), self.device.current_state_of_charge)
        if self.q_df is not None:
            next_action_q_df = self.q_df[self.q_df.state_key == state_key]
            next_action_q_df = next_action_q_df[next_action_q_df.action_key.isin(next_action_list)]
            if next_action_q_df.shape[0] == 0:
                return random.choice(next_action_list)
            else:
                if next_action_q_df.shape[0] == 1:
                    max_q_action = next_action_q_df["action_key"].values[0]
                else:
                    next_action_q_df = next_action_q_df.sort_values(by=["q_value"], ascending=False)
                    max_q_action = next_action_q_df.iloc[0, :]["action_key"]
                return max_q_action
        else:
            return random.choice(next_action_list)

    def convergence(self, old_model):
        #TO DO
        return

    def learn(self, state_key, limit):
        '''
        Learning and searching the optimal solution.
        
        Args:
            state_key:      Initial state.
            limit:          The maximum number of iterative updates based on value iteration algorithms.
        '''
        self.tmp_state_of_charge = self.device.current_state_of_charge
        
        self.t = 1
        while self.t <= limit:
            next_action_list = self.extract_possible_actions(state_key, self.tmp_state_of_charge)
            if len(next_action_list):
                action_key = self.select_action(
                    state_key=state_key,
                    next_action_list=next_action_list
                )
                reward_value = self.observe_reward_value(state_key, action_key)

            if len(next_action_list):
                # Max-Q-Value in next action time.
                next_state_key, next_tmp_state_of_charge = self.update_state(
                    state_key=state_key,
                    action_key=action_key
                )
                next_next_action_list = self.extract_possible_actions(next_state_key, next_tmp_state_of_charge)
                next_action_key = self.predict_next_action(next_state_key, next_next_action_list)
                next_max_q = self.extract_q_df(next_state_key, next_action_key)

                # Update Q-Value.
                self.update_q(
                    state_key=state_key,
                    action_key=action_key,
                    reward_value=reward_value,
                    next_max_q=next_max_q
                )
                # Update State.
                state_key = next_state_key
                self.tmp_state_of_charge = next_tmp_state_of_charge

            # Normalize.
            #self.normalize_q_value()
            #self.normalize_r_value()

            # Vis.
            self.visualize_learning_result(state_key)
            # Check.
            if self.check_the_end_flag(state_key) is True:
                break

            # Epsode.
            self.t += 1
        return

from libraries import GreedyQLearning, abstractmethod

class Device_GreedyQLearning(GreedyQLearning):
    
    def __init__(self, device):
        super().__init__()
        self.device = device
        self.set_alpha_value(self.device.simulation.home.teta)
        self.set_gamma_value(self.device.simulation.home.gamma)
        self.set_epsilon_greedy_rate(self.device.simulation.home.epsilon)
        return

    @abstractmethod
    def extract_possible_actions(self, state_key):
        raise NotImplementedError("This method must be implemented.")

    @abstractmethod
    def observe_reward_value(self, state_key, action_key):
        raise NotImplementedError("This method must be implemented.")
    
    @abstractmethod
    def update_state(self, state_key, action_key):
        raise NotImplementedError("This method must be implemented.")

    @abstractmethod
    def check_the_end_flag(self, state_key):
        raise NotImplementedError("This method must be implemented.")

    @abstractmethod
    def visualize_learning_result(self, state_key):
        raise NotImplementedError("This method must be implemented.")

    @abstractmethod
    def convergence(self, old_model):
        raise NotImplementedError("This method must be implemented.")

    def normalize_q_value(self):
        '''
        Normalize q-value.
        
        Override.
        
        This method is called in each learning steps.
        
        For example:
            self.q_df.q_value = self.q_df.q_value / self.q_df.q_value.sum()
        '''
        if self.q_df is not None and self.q_df.shape[0]:
            # min-max normalization
            self.q_df.q_value = (self.q_df.q_value - self.q_df.q_value.min()) / (self.q_df.q_value.max() - self.q_df.q_value.min())
        return

    def normalize_r_value(self):
        '''
        Normalize r-value.
        Override.
        This method is called in each learning steps.
        For example:
            self.r_df = self.r_df.r_value / self.r_df.r_value.sum()
        '''
        if self.r_df is not None and self.r_df.shape[0]:
            # z-score normalization.
            self.r_df.r_value = (self.r_df.r_value - self.r_df.r_value.mean()) / self.r_df.r_value.std()
        return
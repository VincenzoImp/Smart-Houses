
class Home(object):

    def __init__(self, id, path_dir_home, path_energy_price, p=0.5, teta=0.1, gamma=0.95, epsilon=0.2):
        #home datas
        self.id = id
        self.path_dir_home = path_dir_home
        self.path_energy_price = path_energy_price
        self.p = p  # (1-p) é la prioritá di ottimizzare i consumi, e p é la prioritá di ottimizzare i disservizi #[0.3, 0.5, 0.8]
        self.teta = teta  # θ ∈ [0,1] è un tasso di apprendimento che rappresenta in che misura il nuovo prevale sui vecchi valori Q
        self.gamma = gamma  # γ ∈ [0,1] è un fattore di attualizzazione che indica l'importanza relativa dei premi futuri rispetto a quelli attuali
        self.epsilon = epsilon  # epsilon é la probabilitá di scegliere un azione random. (1-epsilon) é la probabilitá di scegliere l'azione migliore
        return
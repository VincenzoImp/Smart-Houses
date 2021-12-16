from Home import Home
from Simulation import Simulation


def main(path_dir_home, path_energy_price):
    home = Home(path_dir_home, path_energy_price)
    simulation = Simulation(home, loops=None, one_memory=False)
    simulation.run()
    return


if __name__ == "__main__":
    path_dir_home = './../datas/muratori_5/home_1/'
    path_energy_price = './../datas/energy.60.csv'
    main(path_dir_home, path_energy_price)
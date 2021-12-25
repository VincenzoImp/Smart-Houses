from Home import Home
from Simulation import Simulation


def main(path_dir_home, path_energy_price, path_results):
    home = Home(path_dir_home, path_energy_price)
    simulation = Simulation(home, path_results, loops=1000)
    simulation.run()
    return


if __name__ == "__main__":
    path_dir_home = './../datas/muratori_5/home_1/'
    path_energy_price = './../datas/energy.60.csv'
    path_results = './../datas/simulations'
    main(path_dir_home, path_energy_price, path_results)
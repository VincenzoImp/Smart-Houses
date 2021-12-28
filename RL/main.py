from Home import Home
from Simulation import Simulation
from libraries import os


def main(houses_to_simulate, houses_folder, path_energy_price, path_results):
    for id in houses_to_simulate:
        id = "home_{}".format(id)
        path_dir_home = os.path.join(houses_folder, id)
        home = Home(id, path_dir_home, path_energy_price)
        simulation = Simulation(home, path_results, loops=1000)
        simulation.run()
    return


if __name__ == "__main__":
    houses_to_simulate = {1}
    houses_folder = './../datas/muratori_5'
    path_energy_price = './../datas/NN_hypermodel_results.csv'
    path_results = './../datas/simulations'
    main(houses_to_simulate, houses_folder, path_energy_price, path_results)
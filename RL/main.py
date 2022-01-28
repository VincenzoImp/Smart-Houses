from Home import Home
from Simulation import Simulation
from libraries import os, multiprocessing


def main(houses_to_simulate, houses_folder, path_energy_price, path_results):
    process_list = []
    for id in houses_to_simulate:
        id = "home_{}".format(id)
        path_dir_home = os.path.join(houses_folder, id)
        home = Home(id, path_dir_home, path_energy_price, p=0.2)
        simulation = Simulation(home, path_results, loops=1000)
        process = multiprocessing.Process(target=simulation.run)
        process_list.append(process)
    for process in process_list:
        process.start()
    for process in process_list:
        process.join()
    return


if __name__ == "__main__":

    houses_to_simulate = {69}
    houses_folder = './../datas/muratori_5'
    path_energy_price = './../datas/NN_hypermodel_results.csv'
    path_results = './../datas/simulations'
    main(houses_to_simulate, houses_folder, path_energy_price, path_results)

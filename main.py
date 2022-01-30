import sys

from DataPreprocessing import k_nearest_neighborhood, format_correctly, for_each_home, plot_prices_and_consumptions, \
    create_dataset
from LongShortTermMemory import LongShortTermMemory

if __name__ == '__main__':
    energy_price_file = "./datas/energy.60.csv"
    profiles_file = "profiles.csv"
    new_profiles_file = "new_profiles.csv"
    folder = "./datas/muratori_5"
    prices_and_consumptions_file = "./datas/prices_and_consumptions.csv"
    NN_datas_file = "./datas/NN_datas.csv"
    NN_baseline_result_file = './datas/NN_baseline_results.csv'
    NN_hypermodel_result_file = './datas/NN_hypermodel_results.csv'

    print('Process Energy 60')
    k_nearest_neighborhood(energy_price_file)
    format_correctly(energy_price_file)

    print('get_new_profiles')
    for_each_home(folder, energy_price_file, profiles_file, new_profiles_file)

    plot_prices_and_consumptions(prices_and_consumptions_file)

    print('get_NN_datas')
    create_dataset(energy_price_file, NN_datas_file)

    print('NNmodel')
    # from command line, choose to select test mode (=True) or not - Test mode is faster because takes only 30% of the dataset
    if len(sys.argv) < 2:
        LongShortTermMemory(NN_datas_file, NN_baseline_result_file, NN_hypermodel_result_file)
    else:
        LongShortTermMemory(NN_datas_file, NN_baseline_result_file, NN_hypermodel_result_file, sys.argv[1])

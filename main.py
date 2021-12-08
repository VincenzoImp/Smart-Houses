from DataPreprocessing import k_nearest_neighborhood, for_each_home, format_correctly, \
    prepare_NN_data
from NNmodel import NN_model

if __name__ == '__main__':
    energy_price_file = "./datas/energy.60.csv"
    profiles_file = "profiles.csv"
    new_profiles_file = "new_profiles.csv"
    folder = "./datas/muratori_5"
    prices_and_consumptions_file = "./datas/prices_and_consumptions.csv"
    NN_datas_file = "./datas/NN_datas.csv"
    NN_result_file = './datas/NN_results.csv'

    print('Process Energy 60')
    k_nearest_neighborhood(energy_price_file)
    format_correctly(energy_price_file)

    print('get_new_profiles')
    for_each_home(folder, energy_price_file, profiles_file, new_profiles_file)

    """print('get_prices_and_consumptions')
    get_prices_and_consumptions(
        folder, energy_price_file, prices_and_consumptions_file, new_profiles_file)"""

    print('get_NN_datas')
    """read_csv(prices_and_consumptions_file, NN_datas_file)
    add_class_labels(prices_and_consumptions_file, NN_datas_file, NN_datas_with_labels_file)"""
    prepare_NN_data(energy_price_file, NN_datas_file)

    print('NNmodel')
    NN_model(NN_datas_file, NN_result_file, True)

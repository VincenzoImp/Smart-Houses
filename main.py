from get_new_profiles import *
from get_prices_and_consumption import *
from get_NN_datas import *
from NNmodel import *

print('get_new_profiles')
energy_price_file = "./datas/energy.60.csv"
old_profiles_name = "profiles.csv"
new_profiles_name = "new_profiles.csv"
folder = "./datas/muratori_5"
for_each_home(folder, energy_price_file, old_profiles_name, new_profiles_name)

print('get_prices_and_consumptions')
folder = "./datas/muratori_5"
energy_price_file = "./datas/energy.60.csv"
new_file = "./datas/prices_and_consumptions.csv"
new_profiles_name = "new_profiles.csv"
get_prices_and_consumptions(
    folder, energy_price_file, new_file, new_profiles_name)

print('get_NN_datas')
old_file = "./datas/prices_and_consumptions.csv"
new_file = "./datas/NN_datas.csv"
read_csv(old_file, new_file)
new_file_with_labels = "./datas/NN_datas_with_labels.csv"
add_class_labels(old_file, new_file, new_file_with_labels)

print('NNmodel')
input_csv = './datas/NN_datas_with_labels.csv'
output_csv = './datas/NN_results.csv'
NN_model(input_csv, output_csv)

from numpy import sort
from CL_Battery import CL_Battery
from NSL_Battery import NSL_Battery
from Naif_Battery import Naif_Battery
from libraries import os, csv, pd


class Evaluation(object):

    def __init__(self, simulation):
        self.simulation = simulation
        return

    def compute(self, file_csv):
        costo_energia, prezzo_medio_carico, kw_caricati, SOC_medio_output = 0, 0, 0, 0
        df_device = pd.read_csv(file_csv)
        index = 0
        tot_plugin = 0
        tot_output_SOC = 0
        while True:
            try:
                PEV_hours_of_charge = self.simulation.house_profile_DF.at[index, "PEV_hours_of_charge"]
                real_price = self.simulation.energy_price_DF.at[index, "reals01"]
                on_off = df_device.at[index, "on/off"]
                E = df_device.at[index, "E"]
                output_SOC = df_device.at[index, "output_state_of_charge"]
            except KeyError:
                break
            if on_off =='on':
                costo_energia += real_price*E
                kw_caricati += E
                if PEV_hours_of_charge == 1:
                    tot_plugin += 1
                    tot_output_SOC += output_SOC
            index += 1
        prezzo_medio_carico = costo_energia/kw_caricati
        SOC_medio_output = tot_output_SOC/tot_plugin
        return costo_energia, prezzo_medio_carico, kw_caricati, SOC_medio_output

    def run(self):
        evaluation_filename = os.path.join(self.simulation.directory, "evaluation.csv")
        with open(evaluation_filename, "w") as file_object:
            csv.writer(file_object).writerow(["Device", "Diff_costo_energia", "Diff_prezzo_medio_carico", "Diff_kw_caricati", "Diff_SOC_medio_output"])
            NSL_Battery_csv = os.path.join(self.simulation.directory, "NSL_Battery.0.csv")
            NSL_costo_energia, NSL_prezzo_medio_carico, NSL_kw_caricati, NSL_SOC_medio_output = self.compute(NSL_Battery_csv)
            print_list = []
            for device in self.simulation.device_list:
                if type(device) in [Naif_Battery, CL_Battery, NSL_Battery]:
                    Device = device.id
                    Device_Battery_csv = device.filename
                    Device_costo_energia, Device_prezzo_medio_carico, Device_kw_caricati, Device_SOC_medio_output = self.compute(Device_Battery_csv)
                    
                    Diff_costo_energia = (NSL_costo_energia - Device_costo_energia)/max(NSL_costo_energia, Device_costo_energia) 
                    Diff_prezzo_medio_carico = (NSL_prezzo_medio_carico - Device_prezzo_medio_carico)/max(NSL_prezzo_medio_carico, Device_prezzo_medio_carico)
                    Diff_kw_caricati = (Device_kw_caricati - NSL_kw_caricati)/max(NSL_kw_caricati, Device_kw_caricati)
                    Diff_SOC_medio_output = (Device_SOC_medio_output - NSL_SOC_medio_output)/max(NSL_SOC_medio_output, Device_SOC_medio_output)
                    
                    print_list.append([Device, Diff_costo_energia, Diff_prezzo_medio_carico, Diff_kw_caricati, Diff_SOC_medio_output])
            print_list = sorted(print_list, key=lambda x: x[0])
            for to_print in print_list:
                csv.writer(file_object).writerow(to_print)
        return
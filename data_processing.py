import csv
from datetime import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar
from itertools import islice
import holidays


def read_csv(old_file_name, new_file_name):
    consumption_kwh = []
    energy_market_price = []

    with open(old_file_name) as file_profiles, open(new_file_name, "w") as new_file_properties:
        # exclude headers
        reader = csv.reader(islice(file_profiles, 1, None), delimiter=",")

        # Prepare new file
        writer = csv.writer(new_file_properties)
        headers = ['day_of_the_week', 'hour_of_the_day', 'is_holiday', 'electricity_demand_hour1',
                   'electricity_demand_h2', 'electricity_demand_h3', 'electricity_demand_h24',
                   'electricity_demand_h25', 'electricity_demand_h26', 'hour_ahead_price_h1', 'hour_ahead_price_h2',
                   'hour_ahead_price_h3', 'hour_ahead_price_h24', 'hour_ahead_price_h25', 'hour_ahead_price_h26',
                   'hour_ahead_price_h48', 'hour_ahead_price_h49', 'hour_ahead_price_h50']
        writer.writerow(headers)

        for index, row in enumerate(reader):
            # Save first 50 rows
            energy_market_price.append(row[1])
            consumption_kwh.append(row[2])

            new_row = []
            if index >= 50:
                # Get Day of the week, hour of the week, holiday
                date_time_obj = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')

                new_row.append(date_time_obj.weekday() + 1)
                new_row.append(date_time_obj.hour + 1)

                if date_time_obj in holidays.NLD():
                    new_row.append(1)  # True
                else:
                    new_row.append(0)  # False

                # Electricity Demand
                new_row.append(consumption_kwh[index - 1])  # h -1
                new_row.append(consumption_kwh[index - 2])  # h -2
                new_row.append(consumption_kwh[index - 3])  # h - 3
                new_row.append(consumption_kwh[index - 24])  # h - 24
                new_row.append(consumption_kwh[index - 25])  # h - 25
                new_row.append(consumption_kwh[index - 26])  # h - 26

                # Hour ahead price of hour
                new_row.append(energy_market_price[index - 1])  # h - 1
                new_row.append(energy_market_price[index - 2])  # h - 2
                new_row.append(energy_market_price[index - 3])  # h - 3
                new_row.append(energy_market_price[index - 24])  # h - 24
                new_row.append(energy_market_price[index - 25])  # h - 25
                new_row.append(energy_market_price[index - 26])  # h - 26
                new_row.append(energy_market_price[index - 48])  # h - 48
                new_row.append(energy_market_price[index - 49])  # h - 49
                new_row.append(energy_market_price[index - 50])  # h - 50

                # Write to file
                # print(index)
                writer.writerow(new_row)


if __name__ == '__main__':
    old_file = "./datas/newprofiles.csv"
    new_file = "./datas/newprofilesprocessed.csv"
    read_csv(old_file, new_file)

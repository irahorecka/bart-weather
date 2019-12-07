"""
File to gather live BART data aquisition
as it is leaving a station. Save file to 
csv but look into using postgresql for data
storage.
"""

import os
import pandas as pd
from pybart.api import BART

class DataFile:
    def __init__(self, csv_name):
        self.csv_name = csv_name        

    def read_csv(self):
        self.working_csv = pd.read_csv(self.csv_name, sep=',')

    def append_csv(self, row_dat):
        self.working_csv = self.working_csv.append(row_dat)

    def write_csv(self):
        self.working_csv.to_csv(self.csv_name, sep=',', index=False)


class BartAPI:
    def __init__(self):
        self.BART = BART(json_format=True)

    def fetch_live_delays(self, station_json, index):
        return station_json[index][0]

    def fetch_live_departure(self, station):
        try:
            return self.BART.etd.etd(station)['station'][0]['etd']
        except KeyError:
            return None

    def fetch_leaving_train(self, first_departure_dict):
        if not isinstance(first_departure_dict, dict):
            raise TypeError('Please input datatype as dictionary.')
        for station, minute_departure in first_departure_dict.items():
            if minute_departure == 'Leaving':
                print(station, 'is leaving!')

    def fetch_first_departures(self):
        stn_abbr_dict = {}
        for station in self.bart_stations(): 
            departure = self.fetch_live_departure(station['abbr'])
            if not departure:
                continue
            first_departure = self.sort_station_departures(departure)
            stn_abbr_dict[station['abbr']] = first_departure
        return stn_abbr_dict

    def sort_station_departures(self, stn_departures):
        times_departure = []
        for index,destination in enumerate(stn_departures):
            minute_departure = destination['estimate'][0]['minutes']
            minute_departure = 0 if minute_departure == 'Leaving' else minute_departure
            times_departure.append((index, int(minute_departure)))
        sorted_times_departure = sorted(times_departure, key = lambda x: x[1])
        first_departure = sorted_times_departure[0][1]
        first_departure = 'Leaving' if first_departure == 0 else first_departure
        return first_departure

    def bart_stations(self):
        return self.BART.stn.stns()['stations']['station']


class WeatherAPI:
    def __init__(self):
        self.api_key = ''


def main():
    bart = BartAPI()
    while True:
        current_departures = bart.fetch_first_departures()
        bart.fetch_leaving_train(current_departures)


if __name__ == '__main__':
    main()
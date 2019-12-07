"""
File to gather live BART data aquisition
as it is leaving a station. Save file to 
csv but look into using postgresql for data
storage.
"""

import os
import pandas as pd
import pyowm
from pybart.api import BART
from StationKey import all_stations

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
            detail = minute_departure['detail']
            if minute_departure['time'][0] == 'Leaving':
                if station == 'SFIA':
                    weather = WeatherAPI("Millbrae, California")    
                else:
                    weather = WeatherAPI(f"{detail['city']}, California")
                print(station, 'is leaving with', minute_departure['time'][1], 'second(s) delay.')
                print('Weather :', weather.atmosphere_weather())

    def fetch_first_departures(self):
        stn_abbr_dict = {}
        for station in self.bart_stations(): 
            departure = self.fetch_live_departure(station['abbr'])
            if not departure:
                continue
            first_departure = self.sort_station_departures(departure)
            stn_abbr_dict[station['abbr']] = {'time': first_departure,
                                              'detail': all_stations[station['abbr']]}
        return stn_abbr_dict

    def sort_station_departures(self, stn_departures):
        times_departure = []
        for index, destination in enumerate(stn_departures):
            minute_departure = destination['estimate'][0]['minutes']
            seconds_delay = destination['estimate'][0]['delay']
            minute_departure = 0 if minute_departure == 'Leaving' else minute_departure
            times_departure.append([int(minute_departure), int(seconds_delay)])
        sorted_times_departure = sorted(times_departure, key = lambda x: x[0])
        first_departure = sorted_times_departure[0]  # does not capture multiple 0min departures if present
        first_departure[0] = 'Leaving' if first_departure[0] == 0 else first_departure[0]
        return first_departure

    def bart_stations(self):
        return self.BART.stn.stns()['stations']['station']


class WeatherAPI:
    def __init__(self, city_state_location):
        self.owm = pyowm.OWM('984bf5177e2f7b06b6b4fd0a909e8206')
        self.owm.get_API_key()
        self.obs = self.owm.weather_at_place(city_state_location)  

    def atmosphere_weather(self):
        atmos = self.obs.get_weather().get_detailed_status()
        return atmos


def main():
    bart = BartAPI()
    while True:
        current_departures = bart.fetch_first_departures()
        bart.fetch_leaving_train(current_departures)


if __name__ == '__main__':
    main()
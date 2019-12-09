"""
File to gather live BART data
as train leaves a station. Save file to
csv but look into using postgresql for data
storage.
"""

import datetime
import json
import os
import time
import pandas as pd
import pyowm
from pybart.api import BART
import TimeOut as timeout
from StationKey import all_stations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DataFile:
    def __init__(self, json_obj):
        self.json_obj = json_obj
        self.header = [i for i in json_obj[0]]
        self.csv_name = 'BART_weather.csv'

    def read_csv(self):
        self.working_csv = pd.read_csv(self.csv_name, sep=',')

    def write_csv(self):
        self.working_csv.to_csv(self.csv_name, sep=',', index=False)

    def append_csv(self):
        append_list = self.extend_header()
        for item in append_list:
            self.working_csv.loc[len(self.working_csv)] = item

    def extend_header(self):
        masterlist = []
        for i in range(len(self.json_obj)):
            slavelist = []
            for head in self.header:
                slavelist.append(self.json_obj[i][head])
            masterlist.append(slavelist)
        return masterlist


class BartAPI:
    def __init__(self):
        self.BART = BART(json_format=True)
        self.suspended_trains = {}

    def fetch_live_delays(self, station_json, index):
        return station_json[index][0]

    @timeout.timeout(5)  # timeout connection after 5 seconds of inactivity
    def fetch_live_departure(self, station):
        try:
            return self.BART.etd.etd(station)['station'][0]['etd']
        except KeyError:
            return None

    def fetch_leaving_train(self, first_departure_dict):
        if not isinstance(first_departure_dict, dict):
            raise TypeError('Please input datatype as dictionary.')
        wthr_stn_list = []
        for station, minute_departure in first_departure_dict.items():
            detail = minute_departure['detail']
            station_train_key = "{}_{}".format(detail['abbr'], minute_departure['time'][2])
            self.rem_overly_suspended_trains()  # remove suspended train if passed time limit
            if minute_departure['time'][0] == 'Leaving':
                if station_train_key in self.suspended_trains:
                    continue
                # introduce 240 sec latency prior to station_train_key removal
                self.suspended_trains[station_train_key] = datetime.datetime.now() + datetime.timedelta(0, 240)
                wthr = self.fetch_weather(detail)
                stn = self.station_json_to_dict(detail)
                stn['delay'] = minute_departure['time'][1]
                station_dict = {'station_key': station_train_key}
                wthr_stn = {**stn, **wthr, **station_dict}
                wthr_stn_list.append(wthr_stn)
        return wthr_stn_list

    def fetch_first_departures(self):
        stn_abbr_dict = {}
        for stn_abbr, value in all_stations.items():
            departure = self.fetch_live_departure(stn_abbr)
            if not departure:
                continue
            first_departure = self.sort_station_departure_time(departure)
            stn_abbr_dict[stn_abbr] = {'time': first_departure,
                                       'detail': all_stations[stn_abbr]}
        return stn_abbr_dict

    def fetch_weather(self, stn_detail):
        weather = WeatherAPI(float(stn_detail['gtfs_latitude']),
                             float(stn_detail['gtfs_longitude']))
        weather_dict = self.weather_json_to_dict(weather.json_weather())
        return weather_dict

    def sort_station_departure_time(self, stn_departures):
        times_departure = []
        for index, destination in enumerate(stn_departures):
            first_estimate = destination['estimate'][0]
            minute_departure = first_estimate['minutes']
            minute_departure = 0 if minute_departure == 'Leaving' else minute_departure
            seconds_delay = first_estimate['delay']
            train_key = "{}_{}".format(first_estimate['color'], first_estimate['length'])
            times_departure.append([int(minute_departure), int(seconds_delay), train_key])
        sorted_times_departure = sorted(times_departure, key=lambda x: x[0])
        # does not capture multiple 0min departures if present
        first_departure = sorted_times_departure[0]
        first_departure[0] = 'Leaving' if first_departure[0] == 0 else first_departure[0]
        return first_departure

    def rem_overly_suspended_trains(self):
        remove_key_list = []
        for station_train, time_val in self.suspended_trains.items():
            if datetime.datetime.now() > time_val:
                remove_key_list.append(station_train)
        for rem_station_train in remove_key_list:
            del self.suspended_trains[rem_station_train]

    def weather_json_to_dict(self, json_weather):
        jw = json_weather
        parse_jw = {
            'reference_time': jw['reference_time'],
            'sunset_time': jw['sunset_time'],
            'sunrise_time': jw['sunrise_time'],
            'clouds': jw['clouds'],
            'rain': jw['rain'],
            'snow': jw['snow'],
            'wind': jw['wind'],
            'humidity': jw['humidity'],
            'pressure': jw['pressure'],
            'temperature': jw['temperature'],
            'status': jw['status'],
            'detailed_status': jw['detailed_status'],
            'weather_code': jw['weather_code'],
            'weather_icon_name': jw['weather_icon_name'],
            'visibility_distance': jw['visibility_distance'],
            'time': datetime.datetime.now(),
            'dewpoint': jw['dewpoint'],
            'humidex': jw['humidex'],
            'heat_index': jw['heat_index']
        }
        return parse_jw

    def station_json_to_dict(self, json_station):
        js = json_station
        parse_js = {
            'abbr': js['abbr'],
            'address': js['address'],
            'city': js['city'],
            'county': js['county'],
            'gtfs_latitude': js['gtfs_latitude'],
            'gtfs_longitude': js['gtfs_longitude'],
            'name': js['name'],
            'state': js['state'],
            'zipcode': js['zipcode']
        }
        return parse_js


class WeatherAPI:
    owm = pyowm.OWM('984bf5177e2f7b06b6b4fd0a909e8206')
    owm.get_API_key()

    def __init__(self, lat, lon):
        self.obs = self.owm.weather_at_coords(lat, lon)

    def json_weather(self):
        get_json = json.loads(self.obs.get_weather().to_JSON())
        return get_json


def handle_exceptions():
    time.sleep(1)


def main():
    os.chdir(BASE_DIR)
    bart = BartAPI()
    while True:
        try:
            current_departures = bart.fetch_first_departures()
        except (KeyError, timeout.TimeoutError):
            handle_exceptions()
            continue
        z = bart.fetch_leaving_train(current_departures)
        try:
            test = DataFile(z)
        except IndexError:
            handle_exceptions()
            continue
        test.read_csv()
        test.append_csv()
        test.write_csv()


if __name__ == '__main__':
    main()

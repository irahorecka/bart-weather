import datetime
from pybart.api import BART
from StationKey import all_stations
import TimeOut as timeout
from WeatherAPI import Weather


class Bart:
    def __init__(self):
        self.BART = BART(json_format=True)
        self.suspended_trains = {}

    def fetch_leaving_train(self, first_departure_dict):
        wthr_stn_list = []
        for station, minute_departure in first_departure_dict.items():
            stn_detail = minute_departure['detail']
            time_detail = minute_departure['time']
            station_train_key = "{}_{}".format(stn_detail['abbr'], time_detail[2])
            if time_detail[0] == 'Leaving':
                if not self.handle_suspended_trains(station_train_key):
                    continue
                json_package = JSONify(time_detail, stn_detail, station_train_key)
                json_dict = json_package.package_jsons_to_dict()
                wthr_stn_list.append(json_dict)
        return wthr_stn_list

    def fetch_multi_first_departures(self):
        stn_abbr_dict = {}
        for stn_abbr, value in all_stations.items():
            departure = self.fetch_single_live_departure(stn_abbr)
            if not departure:
                continue
            first_departure = return_first_sorted_departure(departure)
            stn_abbr_dict[stn_abbr] = {'time': first_departure,
                                       'detail': all_stations[stn_abbr]}
        return stn_abbr_dict

    @timeout.timeout(5)  # timeout connection after 5 seconds of inactivity
    def fetch_single_live_departure(self, station):
        try:
            return self.BART.etd.etd(station)['station'][0]['etd']
        except KeyError:
            return 0

    def handle_suspended_trains(self, station_key):
        self.rem_overly_suspended_trains()  # remove suspended train if passed time limit
        if station_key in self.suspended_trains:
            return 0
        # introduce 240 sec latency prior to station_train_key removal
        self.suspended_trains[station_key] = datetime.datetime.now() + datetime.timedelta(0, 240)
        return 1

    def rem_overly_suspended_trains(self):
        remove_key_list = []
        for station_train, time_val in self.suspended_trains.items():
            if datetime.datetime.now() > time_val:
                remove_key_list.append(station_train)
        for rem_station_train in remove_key_list:
            del self.suspended_trains[rem_station_train]


def return_first_sorted_departure(stn_departures):
    sorted_stn_time_departures = sort_departure_time(stn_departures)
    first_departure = sorted_stn_time_departures[0]
    if first_departure[0] == 0:
        first_departure[0] = 'Leaving'
    # does not capture multiple 0min departures if present
    return first_departure


def sort_departure_time(stn_departures):
    times_departure = []
    for index, destination in enumerate(stn_departures):
        first_estimate = destination['estimate'][0]
        minute_departure = first_estimate['minutes']
        if minute_departure == 'Leaving':
            minute_departure = 0
        seconds_delay = first_estimate['delay']
        train_key = "{}_{}".format(first_estimate['color'], first_estimate['length'])
        times_departure.append([int(minute_departure), int(seconds_delay), train_key])
    sorted_times_departure = sorted(times_departure, key=lambda x: x[0])
    return sorted_times_departure


class JSONify:
    def __init__(self, time_json, station_json, station_key):
        self.time_json = time_json
        self.stn_json = station_json
        self.stn_key = station_key

    def package_jsons_to_dict(self):
        wthr = self.fetch_weather()
        stn = self.station_json_to_dict()
        stn['delay'] = self.time_json[1]
        station_dict = self.station_key_to_dict()
        wthr_stn = {**stn, **wthr, **station_dict}
        return wthr_stn

    def fetch_weather(self):
        weather = Weather(float(self.stn_json['gtfs_latitude']),
                          float(self.stn_json['gtfs_longitude']))
        weather_dict = self.weather_json_to_dict(weather.json_weather())
        return weather_dict

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

    def station_json_to_dict(self):
        js = self.stn_json
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

    def station_key_to_dict(self):
        stn_key_dict = {'station_key': self.stn_key}
        return stn_key_dict

"""
File to gather live BART data
as train leaves a station. Save file to
csv but look into using postgresql for data
storage.
"""

import os
import time
import pandas as pd
import BartAPI
import TimeOut as timeout
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DataFile:
    def __init__(self, json_obj):
        self.json_obj = json_obj
        self.csv_name = 'BART_weather.csv'

    def read_csv(self):
        self.working_csv = pd.read_csv(self.csv_name, sep=',')
        self.header = list(self.working_csv)

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


def handle_exceptions():
    time.sleep(1)


def main():
    os.chdir(BASE_DIR)
    bart = BartAPI.Bart()
    while True:
        try:
            current_departures = bart.fetch_multi_first_departures()
        except (ConnectionError, KeyError, timeout.TimeoutError):
            handle_exceptions()
            continue
        leaving_trains = bart.fetch_leaving_train(current_departures)
        try:
            bart_csv = DataFile(leaving_trains)
        except IndexError:
            handle_exceptions()
            continue
        bart_csv.read_csv()
        bart_csv.append_csv()
        bart_csv.write_csv()


if __name__ == '__main__':
    main()

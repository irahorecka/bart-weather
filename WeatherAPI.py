import json
import pyowm


class Weather:
    owm = pyowm.OWM('984bf5177e2f7b06b6b4fd0a909e8206')
    owm.get_API_key()

    def __init__(self, lat, lon):
        self.obs = self.owm.weather_at_coords(lat, lon)

    def json_weather(self):
        get_json = json.loads(self.obs.get_weather().to_JSON())
        return get_json
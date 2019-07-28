import requests
import json
from definitions import CONFIG_PATH

with open(CONFIG_PATH) as json_file:
    config_json = json.load(json_file)

OWM_API_KEY = config_json['owm_token']


class VAWeather:
    def get_weather(self):
        geo_info = requests.get("https://ipapi.co/json/").json()
        url = "http://api.openweathermap.org/data/2.5/weather" + "?zip=" + geo_info['postal'] + "," + \
              geo_info['country'] + "&units=metric&lang=ru&APPID=" + OWM_API_KEY

        weather_info = requests.get(url).json()
        return f'Сейчас на улице {weather_info["main"]["temp"]}°, {weather_info["weather"][0]["description"]}'

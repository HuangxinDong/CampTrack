import requests
from datetime import datetime
import logging

class WeatherService:
    BASE_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    BASE_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    @staticmethod
    def get_coordinates(location_query):

        try:
            params = {"name": location_query, "count": 1, "language": "en", "format": "json"}

            response = requests.get(WeatherService.BASE_GEO_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "results" in data and data["results"]:
                return data["results"][0]["latitude"], data["results"][0]["longitude"]
            return None, None
        


        except Exception as e:
            logging.error(f"Geocoding error for {location_query}: {e}")
            raise e
        
    

    @staticmethod
    def get_forecast(lat, lon):
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode",
                "timezone": "auto"
            }

            response = requests.get(WeatherService.BASE_WEATHER_URL, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        

        except Exception as e:
            logging.error(f"Forecast error: {e}")
            raise e
        
    @staticmethod
    def interpret_weather_code(code):

        if code in [0, 1, 2, 3, 45, 48]:
            return "Good"
        elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            return "Rainy"
        elif code >= 71:
            return "Stormy"

        return "Unknown"
    
    def get_weekly_forecast(self, location_query):
        try:
            lat, lon = self.get_coordinates(location_query)
        except requests.exceptions.ConnectionError:
            return None, "Connection Error: Please check your internet connection to view weather data."
        except Exception as e:
            return None, f"Geocoding Service Unavailable: {e}"
        

        if not lat:
            return None, f"Could not find coordinates for '{location_query}'. Please Try using the nearest town, detailed national park name, or a major landmark."
        

        try:
            data = self.get_forecast(lat, lon)
        except requests.exceptions.ConnectionError:
            return None, "Connection Error: Please check your internet connection to view weather data."
        except Exception as e:
            return None, f"Forecast Service Unavailable: {e}. Inconvenience is regretted"
        
        if not data or 'daily' not in data:
            return None, "No daily weather data is available right now. Inconvenience is regretted"
        

        try:
            import pandas as pd
        except ImportError:
            logging.error("Pandas not found")
            return None, "Pandas Library is not installed. Please install Pandas."
        
        codes = data['daily']['weathercode']
        dates = data['daily']['time']

        df = pd.DataFrame({
            'date': dates,
            'code': codes
        })

        df['status'] = df['code'].apply(self.interpret_weather_code)

        return df[['date', 'status', 'code']], None
        

        
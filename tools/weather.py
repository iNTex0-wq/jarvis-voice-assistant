"""Weather tool — Open-Meteo, free, no API key."""
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy with frost",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "light rain showers", 81: "rain showers", 82: "heavy rain showers",
    95: "thunderstorms", 96: "thunderstorms with hail", 99: "severe thunderstorms",
}


def get_weather(location: str) -> dict:
    geo_resp = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10)
    geo_resp.raise_for_status()
    results = geo_resp.json().get("results")
    if not results:
        return {"error": f"Couldn't find a location matching '{location}'"}

    place = results[0]
    lat, lon = place["latitude"], place["longitude"]
    resolved_name = f"{place['name']}, {place.get('country', '')}".strip(", ")

    weather_resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
        },
        timeout=10,
    )
    weather_resp.raise_for_status()
    current = weather_resp.json().get("current", {})
    code = current.get("weather_code")

    return {
        "location": resolved_name,
        "temperature_f": current.get("temperature_2m"),
        "feels_like_f": current.get("apparent_temperature"),
        "conditions": WEATHER_CODES.get(code, "unknown"),
        "wind_mph": current.get("wind_speed_10m"),
    }

import requests
from datetime import datetime, timedelta

def get_last_24h_earthquakes():

    url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

    response = requests.get(url)

    if response.status_code != 200:
        return []

    data = response.json()

    earthquakes = []

    for eq in data["result"]:
        # API yeni format: date_time, koordinatlar geojson.coordinates içinde [lon, lat]
        time_str = eq.get("date_time") or eq.get("date")
        if not time_str:
            continue

        try:
            eq_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        if eq_time > datetime.now() - timedelta(hours=24):
            coords = eq.get("geojson", {}).get("coordinates", [])
            if len(coords) >= 2:
                earthquakes.append({
                    "lon": float(coords[0]),
                    "lat": float(coords[1]),
                })

    return earthquakes

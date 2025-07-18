import requests
import pandas as pd
import time
from datetime import datetime
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
stations = [
    "467490","C0F0A0", "C0F0B0", "C0F0C0", "C0F0D0", "C0F0E0",
    "C0F850", "C0F970", "C0F9I0", "C0F9K0", "C0F9L0",
    "C0F9M0", "C0F9N0", "C0F9O0", "C0F9P0", "C0F9Q0",
    "C0F9R0", "C0F9S0", "C0F9T0", "C0F9U0", "C0F9V0",
    "C0F9X0", "C0F9Y0", "C0F9Z0", "C0FA10", "C0FA20",
    "C0FA30", "C0FA40", "C0FA50", "C0FA60", "C0FA70",
    "C0FA80", "C0FA90", "C0FB00", "C0FB10", "C0FB20",
    "C0FB30", "C0FB40"
]

API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001"
API_KEY = "CWA-30D7BCC9-9115-4267-8501-F74F507E2C28"

def get_station_data(station_id):
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
        "StationId": station_id,
        "RainfallElement": ""
    }
    try:
        response = requests.get(API_URL, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("records", {}).get("Station", [])
    except Exception as e:
        print(f"Error fetching station {station_id}: {e}")
        return []

def fetch_all_stations():
    result = []
    for station in stations:
        stations_data = get_station_data(station)
        for s in stations_data:
            try:
                name = s["StationName"]
                sid = s["StationId"]
                county = s["GeoInfo"]["CountyName"]
                town = s["GeoInfo"]["TownName"]
                wgs84 = next(c for c in s["GeoInfo"]["Coordinates"] if c["CoordinateName"] == "WGS84")
                lat = float(wgs84["StationLatitude"])
                lon = float(wgs84["StationLongitude"])
                rain_data = s["RainfallElement"]

                result.append({
                    "StationId": sid,
                    "StationName": name,
                    "County": county,
                    "Town": town,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Now": float(rain_data["Now"]["Precipitation"]),
                    "Past10Min": float(rain_data["Past10Min"]["Precipitation"]),
                    "Past1hr": float(rain_data["Past1hr"]["Precipitation"]),
                    "Past3hr": float(rain_data["Past3hr"]["Precipitation"]),
                    "Past6Hr": float(rain_data["Past6Hr"]["Precipitation"]),
                    "Past12hr": float(rain_data["Past12hr"]["Precipitation"]),
                    "Past24hr": float(rain_data["Past24hr"]["Precipitation"]),
                    "Past2days": float(rain_data["Past2days"]["Precipitation"]),
                    "Past3days": float(rain_data["Past3days"]["Precipitation"]),
                })
            except Exception as e:
                print(f"Error parsing station {s.get('StationId')}: {e}")
    return result

if __name__ == "__main__":
    while True:
        print("Fetching data...")
        data = fetch_all_stations()
        df = pd.DataFrame(data)
        df.to_csv("rainfall_detailed.csv", index=False, encoding='utf-8-sig')
        print(df)
        print(datetime.now())
        print("Waiting 10 minutes for next update...")
        time.sleep(600)  # 10分鐘

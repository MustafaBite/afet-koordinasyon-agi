import requests

url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

response = requests.get(url)

if response.status_code == 200:

    data = response.json()

    print("\nLast 10 Earthquakes\n")

    for earthquake in data["result"][:10]:

        print("----- Earthquake Info -----")

        for key, value in earthquake.items():
            print(f"{key}: {value}")

        print("---------------------------\n")

else:
    print("API connection failed")
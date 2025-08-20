import pandas as pd
import requests
import time

# First, I load the original station dataset, which includes latitude and longitude for each U-Bahn station
df = pd.read_csv("03-stations.csv")

# Then I clean the column names to ensure they are all lowercase and free of trailing spaces
df.columns = df.columns.str.strip().str.lower()

# Now I define a helper function to get the postcode for each station by sending its coordinates to the Nominatim API
def get_postcode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "simoun-asmar-postcode-script"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("address", {}).get("postcode", None)
    except Exception as e:
        print(f"Error at {lat}, {lon}: {e}")
    return None

# Now I loop through each row in the dataset and use the function to get the postcode for each station
postal_codes = []
for _, row in df.iterrows():
    lat, lon = row["latitude"], row["longitude"]
    print(f"Getting postcode for {row['name']} ...")
    postal_codes.append(get_postcode(lat, lon))
    time.sleep(1)  # To respect Nominatim's rate limit of 1 request per second

# Once I collect all postcodes, I add them as a new column in the existing DataFrame
df["postcode"] = postal_codes

# Finally, I export the cleaned and enriched station data (with lat/lon and postcode) to a new CSV file
df[[ "name", "longitude", "latitude", "postcode"]].to_csv("simoun-asmar-stations-with-postcode.csv", index=False)
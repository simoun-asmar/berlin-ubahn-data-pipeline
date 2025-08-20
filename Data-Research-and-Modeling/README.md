# 📚 Data Research & Modeling — Berlin U-Bahn

In this part of the project, my goal was to collect the basic data for Berlin’s U-Bahn network and prepare it for later transformation. I started with open data, cleaned it up, and then enriched it by adding postal codes.

---

## 🔎 Data Research (source)

The first step was to find a reliable source for Berlin U-Bahn stations and connections.  
I used the data from Clifford Anderson’s Gist:  
👉 https://gist.github.com/CliffordAnderson/7fb7473af31f9343f8a55518545480a0  

From there I worked with two CSV files:  

- `03-stations.csv` → a list of stations with latitude/longitude  
- `08-connections-no-dupes.csv` → station-to-station connections (already de-duplicated)

At this point, the data gave me the backbone of the U-Bahn system: **stations + how they connect**.

---

## 🧩 Enrichment — Add Postcodes from OpenStreetMap

I wanted to enrich the station data so that each station could be mapped not only by coordinates but also by its postal code.  
To do this, I wrote a small Python script that uses **reverse geocoding** (Nominatim / OpenStreetMap).

Here’s the script I used:

```python
import pandas as pd
import requests
import time

# Load stations data
df = pd.read_csv("03-stations.csv")

# Function to fetch postcode from coordinates
def get_postcode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        data = response.json()
        return data.get("address", {}).get("postcode", None)
    return None

# Add postcode column
postcodes = []
for _, row in df.iterrows():
    lat, lon = row["latitude"], row["longitude"]
    postcode = get_postcode(lat, lon)
    postcodes.append(postcode)
    time.sleep(1)  # respect Nominatim rate limits

df["postcode"] = postcodes

# Save new dataset
df.to_csv("simoun-asmar-berlin-stations-with-postcode.csv", index=False)
```

## 📂 Result

After running the script, I got a new enriched dataset:

`simoun-asmar-berlin-stations-with-postcode.csv`

**This file now contains:**
- **name** → station name  
- **line** → U-Bahn line  
- **latitude / longitude** → coordinates  
- **postcode** → added from OpenStreetMap

---

## 🗂️ Data Modeling

After collecting and enriching the datasets, I defined a simple schema for how the data fits together:

- **Stations table** → station metadata (name, line, coordinates, postcode)  
- **Connections table** → describes how stations are linked together

This basic model makes it easier to join, transform, and later visualize the U-Bahn network.

---

## ✅ Step 1 Summary

- Collected stations and connections datasets  
- Enriched station data with postal codes via API  
- Defined a two-table schema (stations + connections)
➡️ Next Step: [Data Transformation & Enrichment](../Data-Transformation-and-Enrichment)

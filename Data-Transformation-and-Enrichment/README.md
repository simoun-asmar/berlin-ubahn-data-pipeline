# 🔧 Step 2: Data Transformation & Enrichment

In this stage I turned the researched datasets into analysis-ready tables. I:
- joined station metadata with line connections,
- patched a few missing coordinates,
- reverse-geocoded **Stadtteil** and **Bezirk** (district),
- cleaned duplicates / invalid lines,
- produced a single tidy U-Bahn table for the next step.

---

## 📦 Inputs
- `03-stations.csv` (after Step 1 → enriched as `simoun-asmar-berlin-stations-with-postcode.csv`)
- `08-connections-no-dupes.csv`

## 📤 Main Outputs (from this step)
- `merged_ubahn_line.csv` – stations joined to lines (+ lat/lon, postcode)
- `ubahn_with_stadtteil.csv` – + `stadtteil` (sub-neighborhood)
- `ubahn_with_neighborhoods.csv` – + `neighborhood` (Berlin **Bezirk**)
- `ubahn.csv` – final, cleaned table for publishing

---

## 2.1  Join stations to lines (and patch a few coordinates)

**Notebook:** `joining_station_with_line_sql.ipynb`  
**Output:** `merged_ubahn_line.csv`

What I did:

1. **Normalize names** on both sides so they join reliably:
   - remove common prefixes: `U-Bahnhof`, `S-Bahnhof`, `Bahnhof`, `Bahnhöfe Berlin`, `Berlin-`
   - trim whitespace, drop placeholder rows that start with `Q*`
   - ensure `postcode` is treated as **string** (to preserve leading zeros / avoid `.0`)

2. **Join logic:** match `connections.point1_clean` ↔ `stations.station_clean`
   - attach `latitude`, `longitude`, and `postcode` for each connected station

3. **Manual coordinate patches (post-merge):** a small list of key hubs had no coordinates after the join, so I added them explicitly to avoid nulls later. Patched stations include (12 total):  
   `Beusselstraße`, `Charlottenburg`, `Fehrbelliner Platz (U3)`, `Fehrbelliner Platz (U7)`,  
   `Friedrichstraße`, `Hackescher Markt`, `Hermannstraße`, `Hohenzollerndamm`,  
   `Köllnische Heide`, `Ostkreuz`, `Südkreuz`, `Zoologischer Garten`.

Result: a joined table with **station · line · lat · lon · postcode**.

### 🔎 Code used (join + patches)
```python
import pandas as pd

# --- Load inputs ---
connections_df = pd.read_csv("08-connections-no-dupes.csv")
stations_df    = pd.read_csv("simoun-asmar-berlin-stations-with-postcode.csv")

# --- Cleaners ---
def clean_name(s: str) -> str:
    if pd.isna(s): 
        return s
    return (s.replace("U-Bahnhof ", "")
             .replace("S-Bahnhof ", "")
             .replace("Bahnhöfe Berlin ", "")
             .replace("Bahnhof Berlin ", "")
             .replace("Bahnhof ", "")
             .replace("Berlin-", "")
             .strip())

connections_df["point1_clean"] = connections_df["point1"].apply(clean_name)
stations_df["station_clean"]   = stations_df["name"].apply(clean_name)

# Drop placeholder rows like Q3831986
connections_df = connections_df[~connections_df["point1_clean"].str.startswith("Q", na=False)]
stations_df    = stations_df[~stations_df["station_clean"].str.startswith("Q", na=False)]

# Ensure postcode stays textual (preserve leading zeros / avoid .0)
stations_df["postcode"] = pd.to_numeric(stations_df["postcode"], errors="coerce").astype("Int64").astype(str).str.replace(r"\.0$", "", regex=True)

# de-dup stations on cleaned name
stations_df = stations_df.drop_duplicates(subset="station_clean")

# --- Join: point1 -> station metadata (lat/lon/postcode) ---
merged = connections_df.merge(
    stations_df[["station_clean", "latitude", "longitude", "postcode"]],
    how="left",
    left_on="point1_clean",
    right_on="station_clean"
).rename(columns={
    "latitude":  "latitude",
    "longitude": "longitude"
})

# --- Manual coordinate patches (post-merge) ---
patches = {
    "Beusselstraße": (52.534444, 13.329444),
    "Charlottenburg": (52.50505, 13.30452),
    "Fehrbelliner Platz (U3)": (52.4897, 13.3153),
    "Fehrbelliner Platz (U7)": (52.4897, 13.3153),
    "Friedrichstraße": (52.52000, 13.38700),
    "Hackescher Markt": (52.52333, 13.40278),
    "Hermannstraße": (52.46722, 13.43194),
    "Hohenzollerndamm": (52.48722, 13.31250),
    "Köllnische Heide": (52.46583, 13.46056),
    "Ostkreuz": (52.50278, 13.46917),
    "Südkreuz": (52.47500, 13.36500),
    "Zoologischer Garten": (52.50750, 13.33417),
}
for st, (lat, lon) in patches.items():
    mask = merged["point1_clean"].eq(st)
    merged.loc[mask, ["latitude", "longitude"]] = (lat, lon)

merged.to_csv("merged_ubahn_line.csv", index=False)
```
---

## 2.2  Reverse-geocode **Stadtteil** 

**Notebook:** `reverse_geo_coding_stadtteil.ipynb`  
**Input:** `merged_ubahn_line.csv`  
**Output:** `ubahn_with_stadtteil.csv`

What I did:

- Used **geopy + Nominatim** (OpenStreetMap) with `language='de'`.
- For each (lat, lon):
  - try `address['suburb']`, else fall back to `address['city_district']`.
- Wrote the result to a new column: **`stadtteil`**.
- Respected the API rate limit (**1 request / second**).

### 🔎 Code used (Stadtteil)

```python
import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

df = pd.read_csv("merged_ubahn_line.csv")

geolocator = Nominatim(user_agent="berlin_ubahn_stadtteil")

def get_stadtteil(lat, lon):
    try:
        loc = geolocator.reverse((lat, lon), exactly_one=True, language="de")
        sleep(1)  # Nominatim rate limit
        if not loc or "address" not in loc.raw:
            return None
        addr = loc.raw["address"]
        return addr.get("suburb") or addr.get("city_district")
    except:
        return None

df["stadtteil"] = df.apply(
    lambda r: get_stadtteil(r["latitude"], r["longitude"]) if pd.notnull(r["latitude"]) else None,
    axis=1
)

df.to_csv("ubahn_with_stadtteil.csv", index=False)
```
---

## 2.3  Reverse-geocode **Bezirk** (district / neighborhood)

**Notebook:** `reverse_geo_coding_neighborhood.ipynb`  
**Input:** `ubahn_with_stadtteil.csv`  
**Output:** `ubahn_with_neighborhoods.csv`

What I did:

- Again used **geopy + Nominatim**.
- Extracted the official district from one of:
  - `address['city_district']` → preferred,
  - or `address['borough']`,
  - or `address['county']`.
- Saved to a new column: **`neighborhood`** (Berlin **Bezirk**).

### 🔎 Code used (Neighborhood)
```python
import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

df = pd.read_csv("ubahn_with_stadtteil.csv")
geolocator = Nominatim(user_agent="berlin_ubahn_bezirk")

def get_bezirk(lat, lon):
    try:
        loc = geolocator.reverse((lat, lon), exactly_one=True, language="de")
        sleep(1)  # Nominatim rate limit
        if not loc or "address" not in loc.raw:
            return None
        addr = loc.raw["address"]
        return addr.get("city_district") or addr.get("borough") or addr.get("county")
    except:
        return None

df["neighborhood"] = df.apply(
    lambda r: get_bezirk(r["latitude"], r["longitude"]) if pd.notnull(r["latitude"]) else None,
    axis=1
)

df.to_csv("ubahn_with_neighborhoods.csv", index=False)
```
---

## 2.4  Final clean-up & validation

**Notebook:** `cleaned_ubah.ipynb`  
**Output:** `ubahn.csv`

What I cleaned:

1. **Drop only the unhelpful null-line duplicates**  
   - For stations that appear **multiple times**, remove the rows where `line` is **null**.  
   - If a station appears **once** and `line` is null, **keep it** (it can still be useful).

2. **Keep only valid U-Bahn line formats**  
   - Retained rows where `line` matches `^U\d+$` (e.g., `U2`, `U8`).  
   - Removed non-line strings like *“Berliner Stadtbahn”*, *“Preußische Ostbahn”*, *“Wriezener Bahn”*.

3. **Small manual fixes for missing lines**  
   - `Elsterwerdaer Platz` → `U5`  
   - `Grenzallee` → `U7`  
   - `Weinmeisterstraße` → `U8`

4. **Postcode formatting**  
   - Stored `postcode` as **string** and stripped any trailing `.0` so values like `10117` remain intact.

5. **Column types (end of step)**  
   - `station`, `line`, `postcode`, `stadtteil`, `neighborhood` → **string**  
   - `latitude`, `longitude` → **float**

> ℹ️ Note: The **district_id** (01–12) mapping is applied in Step 3 when loading to the target database/warehouse.

### 🔎 Code used (clean & finalize)
```python
import pandas as pd

df = pd.read_csv("ubahn_with_neighborhoods.csv")

# 1) Keep postcode as text and strip trailing ".0" if present
df["postcode"] = df["postcode"].astype(str).str.replace(r"\.0$", "", regex=True)

# 2) Drop only the unhelpful null-line duplicates
counts = df["station"].value_counts()
dupes  = counts[counts > 1].index
df = df[~((df["station"].isin(dupes)) & (df["line"].isna()))]

# 3) Keep only valid U-Bahn line pattern (U followed by digits) OR null (singletons kept earlier)
df = df[(df["line"].isna()) | (df["line"].str.match(r"^U\d+$"))]

# 4) Manual fixes for a few stations
df.loc[df["station"].eq("Elsterwerdaer Platz"), "line"] = "U5"
df.loc[df["station"].eq("Grenzallee"),           "line"] = "U7"
df.loc[df["station"].eq("Weinmeisterstraße"),    "line"] = "U8"

# 5) Save the final table
df.to_csv("ubahn.csv", index=False)
```
---

## 🔎 Files produced in this step

- `merged_ubahn_line.csv` – joined station/line + coords + postcode  
- `ubahn_with_stadtteil.csv` – + `stadtteil`  
- `ubahn_with_neighborhoods.csv` – + `neighborhood` (Bezirk)  
- `ubahn.csv` – final, cleaned U-Bahn table (ready to publish)

---

## ▶️ Reproduce (quick guide)

1) Run **`joining_station_with_line_sql.ipynb`** → creates `merged_ubahn_line.csv`  
2) Run **`reverse_geo_coding_stadtteil.ipynb`** → creates `ubahn_with_stadtteil.csv`  
3) Run **`reverse_geo_coding_neighborhood.ipynb`** → creates `ubahn_with_neighborhoods.csv`  
4) Run **`cleaned_ubah.ipynb`** → creates `ubahn.csv`

> If you re-run geocoding, keep the **1 req/sec** limit; consider caching to speed it up.

---

## ✅ Step 2 Summary
- Joined stations to lines with cleaned keys and patched a few coordinates.  
- Reverse-geocoded **Stadtteil** and **Bezirk** for every station.  
- Removed only unhelpful null-line duplicates, enforced `U#` line format, and fixed three missing lines.  
- Produced a single tidy table: **`ubahn.csv`** — ready for loading.

---

➡️ **Next: [Step 3 · Data Loading & Publishing](../Data-Loading-and-Publishing/README.md)**

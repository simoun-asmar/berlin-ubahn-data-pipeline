# 🚇 Berlin U-Bahn Data Pipeline — Overview

End-to-end pipeline that takes open U-Bahn data from raw CSVs → enriches it with **postcodes**, **Stadtteil** (sub-neighborhood), and **Bezirk** (district) → publishes a clean, query-ready table to **BigQuery**. The repo mirrors a real data lifecycle: **Research & Modeling → Transformation & Enrichment → Loading & Publishing**.

---

## 📦 Repository structure

- **/Data-Research-and-Modeling/**  
  Raw sources (stations + connections), data notes, and postcode enrichment (reverse geocoding).
- **/Data-Transformation-and-Enrichment/**  
  Clean joins, reverse geocoding for *Stadtteil* and *Bezirk*, deduping, line fixes, final tidy CSV.
- **/Data-Loading-and-Publishing/**  
  BigQuery schema, safe credential setup, and load notebook.

---

## 🔁 End-to-end flow

1) **Research & Modeling**  
   - Start from public U-Bahn datasets (stations + connections).  
   - Add **postcodes** via reverse geocoding (rate-limited).  
   - Define a simple model: `stations` and `connections`.

2) **Transformation & Enrichment**  
   - Join connections ↔ station metadata (lat/lon/postcode).  
   - Reverse-geocode **Stadtteil** and **Bezirk**, normalize names, dedupe, patch a few missing lines.  
   - Produce the final CSV: `ubahn.csv` with  
     `station, line, latitude, longitude, postcode, neighborhood, district, district_id`.

3) **Loading & Publishing**  
   - Map 12 Berlin Bezirke to a two-digit **district_id** (`"01"`–`"12"`).  
   - Define the explicit BigQuery schema and load the table.

---

## 🧰 Tech stack

**Python** (`pandas`, `requests`, `geopy`) • **SQLite** (intermediate joins) • **Google BigQuery** (`google-cloud-bigquery`, `pandas-gbq`) • **Git/GitHub** with `.gitignore` for secrets

---

## ▶️ Start here

[▶️ **Go to Step 1: Data Research & Modeling**](./Data-Research-and-Modeling/README.md)

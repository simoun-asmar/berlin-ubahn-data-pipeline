# 🚀 Step 3: Data Loading & Publishing (BigQuery)

In the final stage I took the enriched U-Bahn dataset and **published it to Google BigQuery** so it can be queried, joined with other sources, and used by BI tools.

---

## 📦 Inputs & Output

**Inputs**
- `ubahn.csv` – final cleaned table from Step 2 (`station, line, latitude, longitude, postcode, neighborhood, district, district_id`)
- `connecting_populating_to_gcp.ipynb` – notebook that connects to BigQuery and loads the data

**Output**
- BigQuery table: **`cohesive-idiom-441010-a8.berlin_data.ubahn`**
  - (Format: `<PROJECT_ID>.<DATASET>.<TABLE>`)

---

## 🔐 Secret handling (important)

I **do not commit real credentials**.

- The repo contains a `.gitignore` that ignores service-account keys, e.g.:
  - `bq_connector_key.json`, `*credentials*.json`, `*.key.json`, etc.
- A **sample** file `bq_connector_key_sample.json` shows the expected JSON shape with placeholders.
- Locally I point to the real key via env var:

```bash
# macOS/Linux
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/bq_connector_key.json"
```

### 🧰 What the notebook does
	1.	Loads ubahn.csv and fixes dtypes (keeps postcode as string to preserve leading zeros).
	2.	Renames columns for clarity (stadtteil → neighborhood, neighborhood → district).
	3.	Adds district_id by mapping Berlin’s 12 Bezirke to "01"–"12".
	4.	Defines an explicit BigQuery schema (types + nullability).
	5.	Loads the DataFrame → BigQuery using the official google-cloud-bigquery client.

 ###🧱 Table schema (BigQuery)

 ## 🧱 Table schema (BigQuery)

| Column        | Type    | Mode     | Notes                                       |
|---------------|---------|----------|---------------------------------------------|
| **station**   | STRING  | REQUIRED | Station name                                |
| **line**      | STRING  | REQUIRED | U–Bahn line (e.g., U2)                      |
| **latitude**  | FLOAT64 | REQUIRED | Decimal degrees                             |
| **longitude** | FLOAT64 | REQUIRED | Decimal degrees                             |
| **postcode**  | STRING  | NULLABLE | Kept as text to preserve leading zeros      |
| **neighborhood** | STRING | NULLABLE | (former `stadtteil`)                        |
| **district**  | STRING  | REQUIRED | Berlin Bezirk name                          |
| **district_id** | STRING | REQUIRED | Two-digit code `"01"–"12"`                  |

> BigQuery is a columnar analytics warehouse; I keep relationships in the model/queries rather than enforcing FKs.

### 🔑 Add `district_id` (join key) before loading to BigQuery

Before publishing, I create a **stable, normalized join key** called `district_id` so this U-Bahn table can be reliably joined to other warehouse tables (e.g., demographics per Bezirk). Using a short **two-character STRING** (`"01"`–`"12"`) avoids spelling/umlaut issues and keeps leading zeros.

**Rationale**
- **Consistent joins:** avoids free-text mismatches on `district` names.
- **Stable key:** independent of localization/accents.
- **Warehouse-friendly:** short STRING, easy to index and reference.

**Conventions**
- Type: **STRING** (not INT) → preserves leading zeros (`"01"`…`"12"`).
- Values map 1:1 to Berlin Bezirke.

**Implementation (right before the BigQuery load):**
### ▶️ Code
```bash
# BigQuery tooling for local notebooks / scripts
# (Install once in your environment

pip install --upgrade google-cloud-bigquery  # Official Python client for BigQuery (create tables, load/query data)
pip install --upgrade pandas-gbq             # Pandas connector: pd.read_gbq() / DataFrame.to_gbq()
pip install --upgrade db-dtypes              # BigQuery-compatible pandas dtypes (e.g., NUMERIC/GEOGRAPHY) for clean schemas
```
```python
from google.cloud import bigquery
import pandas as pd

# 1) Load final CSV and keep postcode as string (no lost leading zeros)
df = pd.read_csv("ubahn.csv", dtype={"postcode": "string"})

# 2) Rename for consistency
df.rename(columns={"stadtteil": "neighborhood", "neighborhood": "district"}, inplace=True)

# 3) Map district -> district_id
district_id_map = {
    "Mitte": "01",
    "Friedrichshain-Kreuzberg": "02",
    "Pankow": "03",
    "Charlottenburg-Wilmersdorf": "04",
    "Spandau": "05",
    "Steglitz-Zehlendorf": "06",
    "Tempelhof-Schöneberg": "07",
    "Neukölln": "08",
    "Treptow-Köpenick": "09",
    "Marzahn-Hellersdorf": "10",
    "Lichtenberg": "11",
    "Reinickendorf": "12",
}
df["district_id"] = df["district"].map(district_id_map)

# 4) BigQuery client (uses GOOGLE_APPLICATION_CREDENTIALS)
client = bigquery.Client()

# 5) Schema
schema = [
    bigquery.SchemaField("station", "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("line", "STRING",     mode="REQUIRED"),
    bigquery.SchemaField("latitude", "FLOAT64",mode="REQUIRED"),
    bigquery.SchemaField("longitude","FLOAT64",mode="REQUIRED"),
    bigquery.SchemaField("postcode","STRING",  mode="NULLABLE"),
    bigquery.SchemaField("neighborhood","STRING",mode="NULLABLE"),
    bigquery.SchemaField("district","STRING",  mode="REQUIRED"),
    bigquery.SchemaField("district_id","STRING",mode="REQUIRED"),
]

# 6) Destination table
table_id = "cohesive-idiom-441010-a8.berlin_data.ubahn"  # <project>.<dataset>.<table>

# 7) Load DataFrame → BigQuery (replace table each run)
job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()


```

## Step 3 Summary

- **Prepared the final DataFrame:** kept `postcode` as **STRING** (preserve leading zeros), renamed `stadtteil → neighborhood` and `neighborhood → district`, and added a two-digit **district_id**.
- **Kept credentials safe:** real JSON keys are **ignored** via `.gitignore`; a redacted **`bq_connector_key.sample.json`** shows the expected format.
- **Loaded to BigQuery:** wrote the table **`cohesive-idiom-441010-a8.berlin_data.ubahn`** with an explicit schema (STRING for text, FLOAT64 for latitude/longitude; `postcode`/`neighborhood` nullable).
- **Quick check:** previewed rows and verified non-null `district_id` and sensible counts.

---

## 🎉 Project complete

- **Step 1 — Research & Modeling:** gathered stations & connections, added postcodes, defined a simple model.  
- **Step 2 — Transformation & Enrichment:** joined sources, fixed edge cases, reverse-geocoded **neighborhood** and **district**, cleaned results.  
- **Step 3 — Publishing:** secured credentials and published the final **U-Bahn** table to **BigQuery**.

Thanks for reading!

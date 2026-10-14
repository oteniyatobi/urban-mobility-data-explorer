# Urban Mobility Data Explorer -- Technical Report

**Date:** October 14, 2026  
**Repository:** [github.com/oteniyatobi/urban-mobility-data-explorer](https://github.com/oteniyatobi/urban-mobility-data-explorer)

A fullstack web application for exploring and analyzing NYC yellow taxi trip data from January 2019. Built with Flask, MySQL, and vanilla HTML/CSS/JS.

---

## 1. Problem Framing and Dataset Analysis

### 1.1 Dataset Description

The project uses the NYC Taxi and Limousine Commission (TLC) Yellow Taxi Trip Records for January 2019, one of the largest publicly available urban mobility datasets in the world. The TLC publishes these records monthly as part of its regulatory mandate over for-hire vehicles in New York City, making them a widely used benchmark in data science, urban planning, and transportation research.

The raw dataset contains **7,667,792 trip records** across **18 columns**. Each row represents a single taxi trip and captures the following information:

- **Temporal data:** `tpep_pickup_datetime` and `tpep_dropoff_datetime`, recorded to the second, marking when the taximeter was engaged and disengaged.
- **Spatial data:** `PULocationID` and `DOLocationID`, integer codes referencing one of 265 TLC-defined taxi zones across the five boroughs of New York City. These replace raw GPS coordinates, which the TLC stopped publishing in 2016 for rider privacy.
- **Passenger and distance:** `passenger_count` (self-reported by the driver) and `trip_distance` (measured by the taximeter in miles).
- **Fare breakdown:** `fare_amount` (metered fare), `extra` (rush hour and overnight surcharges), `mta_tax` (flat $0.50 MTA surcharge), `tip_amount` (credit card tips only; cash tips are not recorded), `tolls_amount`, `improvement_surcharge` (flat $0.30), `congestion_surcharge` (introduced in 2019 for trips below 96th Street in Manhattan), and `total_amount` (sum of all charges).
- **Categorical fields:** `VendorID` (1 = Creative Mobile Technologies, 2 = VeriFone Inc.), `RatecodeID` (1 = Standard rate, 2 = JFK, 3 = Newark, 4 = Nassau/Westchester, 5 = Negotiated fare, 6 = Group ride), `store_and_fwd_flag` (Y/N, whether the trip record was held in vehicle memory before sending), and `payment_type` (1 = Credit card, 2 = Cash, 3 = No charge, 4 = Dispute, 5 = Unknown, 6 = Voided trip).

Two supplementary datasets support the main trip data:

1. **Taxi Zone Lookup CSV** (`taxi+_zone_lookup.csv`): Maps each of the 265 `LocationID` values to a human-readable `Borough` (Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR) and `Zone` name (e.g., "Upper East Side North," "JFK Airport"). This lookup is essential because the trip data contains only integer location codes with no geographic context.

2. **Taxi Zone Shapefile** (converted to GeoJSON via `scripts/convert_geojson.py`): A polygon boundary file defining the spatial extent of each taxi zone. The original shapefile used the NAD83 / New York Long Island (EPSG:2263) coordinate reference system, which is a projected system in feet suitable for local New York mapping. We reprojected this to WGS84 (EPSG:4326), the standard latitude/longitude coordinate system used by web mapping libraries, to ensure compatibility with any future map visualisation work. The conversion script uses GeoPandas and PyOGRIO for the reprojection.

### 1.2 Data Quality Problems Found

The cleaning pipeline (`scripts/clean_data.py`) applied ten distinct validation rules to every row. Each rule tests a specific data quality condition, and any row that fails at least one rule is removed from the dataset. Critically, every rejection is logged to `data/audit/cleaning_log.csv` with the row's trip data and the rule that triggered the rejection, creating a full audit trail that allows the cleaning decisions to be reviewed, challenged, or adjusted without rerunning the pipeline.

The cleaning script processes the data in the following order: null removal first (so subsequent rules operate on complete rows), then temporal validation, then distance and fare outlier detection, and finally speed-based filtering. This ordering matters because later rules depend on earlier ones — for example, the speed calculation (`trip_distance / trip_duration`) requires both a valid positive distance (checked by R2.d) and a valid positive duration (checked by R2.b and R2.c).

| Rule | Condition | Rows Removed | Explanation |
|------|-----------|--------------|-------------|
| R2.g | `passenger_count` is NULL | 28,672 | Missing passenger count makes the row incomplete for analysis. These likely result from driver hardware that did not prompt for entry. |
| R2.a | Pickup datetime outside January 2019 | 537 | Timestamps from December 2018 or February 2019 that leaked into the January file, likely from meter clock drift or delayed uploads. |
| R2.b | Dropoff datetime <= pickup datetime | 6,291 | Trips where the dropoff happened at or before pickup, indicating a reversed timestamp or a trip that was started and immediately cancelled without the meter advancing. |
| R2.c | Trip duration exceeds 24 hours | 5 | A taxi ride lasting more than a full day is not a real journey. These are meters left running after the passenger exited, or system glitches where the dropoff event was never properly registered. |
| R2.d | Distance <= 0 or > 100 miles | 48,803 | Zero-distance trips (meter engaged but no movement) and impossibly long trips (over 100 miles within NYC). The 100-mile cap reflects the furthest realistic yellow cab ride — Manhattan to the farthest point in the Rockaways is roughly 30 miles; even a JFK-to-Newark trip via Manhattan is under 50 miles. |
| R2.e | Negative fare amount | 5,694 | Fares below zero, representing refunds, adjustments, or data corruption. A legitimate trip cannot produce a negative metered fare. |
| R2.r | Fare exceeds $500 | 6 | Extreme fare outliers. The standard NYC taxi meter rate is $2.50 initial charge plus $0.50 per 1/5 mile. Even a 100-mile trip at metered rates would only reach approximately $252. Fares above $500 indicate negotiated rates logged incorrectly, test transactions, or data corruption. |
| R2.n | Tip amount exceeds total amount | 1 | A logical impossibility under normal circumstances — the tip is a component of the total, so it cannot exceed it. This single row is a clear data entry error. |
| R2.s | Tip amount exceeds fare amount | 4,963 | The standard TLC credit card interface presents tip options as percentages of the fare (typically 20%, 25%, 30%). A tip exceeding 100% of the fare falls outside this interface, suggesting manual override errors or data corruption. |
| R2.t | Computed speed exceeds 80 mph | 5,894 | Speed is derived as `trip_distance / (trip_duration_in_hours)`. NYC's highest speed limit is 50 mph (on certain expressways), and actual travel speeds including traffic rarely exceed 60 mph even on the FDR Drive or BQE. An 80 mph threshold gives generous headroom while catching rows where either distance or duration is grossly misrecorded. |

**Summary:** After cleaning, approximately **100,866 rows** (roughly **1.3%** of the dataset) were removed, leaving around **7.57 million** usable records. The pipeline also checks for exact duplicate rows, though none were found in the raw data — the TLC's ingestion system apparently deduplicates before publishing.

### 1.3 Derived Features

After cleaning, the pipeline adds six computed columns to enrich the analysis:

| Feature | Formula | Purpose |
|---------|---------|---------|
| `trip_duration_min` | `(dropoff - pickup).total_seconds() / 60` | Enables duration-based filtering and average speed calculation |
| `avg_speed_mph` | `trip_distance / (trip_duration_min / 60)` | Identifies traffic patterns and validates distance/time consistency |
| `tip_pct` | `tip_amount / fare_amount * 100` | Normalises tipping behaviour across different fare levels |
| `pickup_hour` | `pickup_datetime.hour` (0-23) | Powers the "Trips by hour" chart for temporal pattern analysis |
| `pickup_dow` | `pickup_datetime.dayofweek` (0=Mon, 6=Sun) | Enables weekday vs. weekend comparisons |
| `is_weekend` | `1 if pickup_dow >= 5 else 0` | Binary flag for quick weekend filtering |

### 1.4 Cleaning Assumptions

Every cleaning decision involves a judgement call about where to draw the line between "noisy but real" and "clearly wrong." The following assumptions guided our decisions:

**Temporal boundary assumption:** Trips whose pickup timestamp fell outside January 2019 were treated as recording errors rather than legitimate late entries from adjacent months. The TLC partitions its data by month of pickup, so a December 31st pickup appearing in the January file is a misassignment. We could have kept these and re-dated them, but with only 537 such rows (0.007% of the data), the impact of exclusion is negligible and avoids introducing uncertainty about whether the timestamps are correct at all.

**Duration ceiling assumption:** A 24-hour ceiling on trip duration assumed that any ride longer than a full day is a meter left running or a logging fault, not a real journey. New York City yellow cabs are metered vehicles designed for point-to-point trips within the five boroughs; they are not hired for multi-day journeys. The longest plausible trip — a slow ride from the northern Bronx to the southern tip of Staten Island in heavy traffic — would take roughly 3-4 hours at most.

**Speed cap assumption:** The 80 mph speed cap reflects the practical maximum speed achievable on NYC roads, including highways. The FDR Drive and the BQE have posted speed limits of 30-40 mph, and even the Cross Bronx Expressway, one of the fastest roads in the city, is posted at 50 mph. We used 80 mph rather than the posted 50 mph limit to account for brief periods of higher speed and measurement granularity (a trip measured over a very short duration can produce artificially high instantaneous speeds). Any computed speed above 80 mph almost certainly indicates a GPS glitch, a misrecorded distance, or a misrecorded duration.

**Fare ceiling assumption:** Fares above $500 were treated as anomalies. The standard metered fare structure ($2.50 base + $0.50 per 1/5 mile + time charges + surcharges) makes it extremely difficult to reach $500 on a legitimate trip. Even a 100-mile ride at metered rates with maximum surcharges would fall well below this threshold. The six trips exceeding $500 are likely negotiated flat-rate fares entered into the wrong field, test transactions, or corrupt records.

**Tip ceiling assumption:** Tips exceeding the fare amount itself were flagged as errors. The TLC-mandated credit card payment screen presents three tip options (typically 20%, 25%, and 30% of the fare), with a "custom" option. While passengers can enter any custom tip, a tip exceeding 100% of the fare is rare enough in practice to be more likely a decimal point error (e.g., $15.00 entered as $150.00) than a genuinely generous tip.

### 1.5 Unexpected Finding

The single largest category of rejected data was **Rule R2.d: 48,803 trips with zero or impossibly long distances** (over 100 miles). This was nearly half of all removed rows and represented roughly 0.6% of the entire dataset.

The overwhelming majority of these were **zero-distance trips** — records where the taximeter was engaged and then disengaged at the same location, recording a distance of 0.00 miles. These could represent several real-world scenarios: a passenger hails a cab, gets in, and immediately changes their mind; a driver starts the meter accidentally and resets it; or a driver starts the meter to claim a no-show after waiting at a pickup location. Whatever the cause, the meter system still records these as completed trips with a fare (usually just the $2.50 base charge plus surcharges), and they flow into the TLC dataset as if they were real rides.

The sheer volume — nearly 49,000 zero-distance records in a single month — suggests this is a **systemic issue in the TLC's metering infrastructure**, not isolated incidents. The meter system does not appear to have a minimum-distance threshold that would prevent a zero-distance trip from being recorded and uploaded. For the TLC, this is a data quality blind spot: these records inflate trip counts, deflect average distances downward, and produce undefined or infinite speed values that can corrupt downstream calculations if not caught.

For our analysis, removing these records was necessary to avoid distorting the distance distribution and speed calculations. However, it is worth noting that these zero-distance trips represent real economic activity — a driver who starts a meter and has the passenger cancel has still spent time and fuel — even if they do not represent actual transportation.

---

## 2. System Architecture and Design Decisions

### 2.1 Architecture Overview

The system follows a **three-tier architecture**: a browser-based frontend, a Python Flask backend, and a MySQL relational database, with an offline data pipeline that processes raw data and feeds cleaned records into the database.

```
+----------------------------------------------+    +----------------------------------------------+
|              FRONTEND                        |    |         DATA PIPELINE (offline)               |
|                                              |    |                                              |
|  +----------------+  +----------------+      |    |  +----------------------------------------+  |
|  |    Browser     |  |   Chart.js     |      |    |  |       Raw CSV (7.67M rows)             |  |
|  |  HTML/CSS/JS   |  | Bar,pie,donut  |      |    |  +----------------------------------------+  |
|  +-------+--------+  +--------+-------+      |    |                    |                         |
+----------|-----------------|------------------+    |                    v                         |
           |  fetch /api/*   |  ORM queries          |  +----------------------------------------+  |
           v                 v                       |  |       Convert to Parquet               |  |
+----------------------------------------------+    |  |    (csv_to_parquet.py)                  |  |
|              BACKEND                         |    |  +----------------------------------------+  |
|                                              |    |                    |                         |
|  +----------------+  +----------------+      |    |                    v                         |
|  |   Flask API    |  |  SQLAlchemy    |      |    |  +----------------------------------------+  |
|  | 6 REST endpts  |  |  ORM models   |      |    |  |  Clean and validate (10 rules)         |  |
|  +-------+--------+  +--------+-------+      |    |  |    (clean_data.py)                     |  |
+----------|-----------------|------------------+    |  +----------------------------------------+  |
           |       SQL       |                       |                    |                         |
           v                 v                       |                    v                         |
+----------------------------------------------+    |  +----------------------------------------+  |
|              DATABASE                        |    |  |    Derive features and load            |  |
|                                              |    |  |    (database.py)                       |  |
|  +----------------------------------------+  |    |  +----------------------------------------+  |
|  |     MySQL: 6 normalized tables         |  |<---|                    |                         |
|  |  vendors, fare_rates, payment_types,   |  |    |                    v                         |
|  |  zones, trips, trip_fares              |  |    |  +----------------------------------------+  |
|  +----------------------------------------+  |    |  |   Audit log (cleaning_log.csv)         |  |
+----------------------------------------------+    |  +----------------------------------------+  |
                                                    +----------------------------------------------+
```

**Data flow in detail:**

1. **Raw CSV ingestion:** The pipeline begins with the raw TLC CSV file (approximately 1.6 GB uncompressed for January 2019). This file is first converted to Apache Parquet format using `scripts/csv_to_parquet.py`, which uses PyArrow's columnar storage engine. The Parquet conversion reduces file size by 3-5x through dictionary encoding and run-length encoding of repetitive values (particularly the integer-coded categorical columns), and enables faster column-level reads for the cleaning script.

2. **Cleaning and validation:** The `scripts/clean_data.py` script reads the Parquet file into a pandas DataFrame and applies the ten validation rules described in Section 1. Each rule appends rejected rows to the audit log with the rule code that triggered the rejection. The script outputs a cleaned Parquet file with the six derived features added.

3. **Database loading:** The `database/database.py` script reads the cleaned Parquet file, creates the MySQL schema via SQLAlchemy ORM model definitions, and batch-inserts records in chunks of 5,000. The chunk size was chosen to balance between INSERT statement overhead (too small = too many round trips to MySQL) and memory usage (too large = pandas has to hold too many rows in a single INSERT buffer).

4. **API serving:** The Flask backend connects to MySQL and serves six REST endpoints that the frontend consumes via `fetch()` calls. Each endpoint returns JSON.

5. **Frontend rendering:** The browser receives JSON from the API, renders it into interactive charts using Chart.js, and displays tabular data with client-side pagination and filtering controls.

### 2.2 Frontend Architecture

The frontend is a **single HTML page** (`backend/templates/index.html`) served by Flask's Jinja2 template engine. It uses:

- **Vanilla JavaScript** for DOM manipulation, API calls via the Fetch API, and event handling. No framework (React, Vue, Angular) is used — the DOM is manipulated directly through `document.getElementById()`, `innerHTML`, and event listeners. This eliminates build tooling, bundling, and framework overhead for a dashboard that renders a fixed set of components.

- **Chart.js** (loaded from CDN) for rendering four visualisations:
  - A **bar chart** showing trips by hour of day (0-23), powered by the `pickup_hour` derived field
  - A **bar chart** showing trip distance groups (0-2mi, 2-5mi, 5-10mi, 10-20mi, 20+mi)
  - A **doughnut chart** showing payment type distribution (Credit card, Cash, No charge, Dispute, Unknown, Voided)
  - A **dynamic HTML list** of the top 5 busiest pickup zones by trip count

- **CSS** for responsive layout, styled filter controls (range sliders for distance and fare, dropdowns for payment type and zone), and a data table with alternating row colours.

**Filtering strategy:** The frontend implements a split filtering approach:

- **Server-side filters** (date range, payment type): These filters are passed as query parameters to the `/api/trip` endpoint, which builds a dynamic SQL `WHERE` clause. Server-side filtering is used for the most selective filters — a date range can reduce 7.57 million rows to a few hundred thousand, and filtering by payment type halves the dataset. Sending all rows to the browser and filtering there would be wasteful.

- **Client-side filters** (distance range, fare range, zone): After the server returns the filtered result set, JavaScript applies additional filters locally using array `.filter()` methods. These work on the already-reduced dataset and provide instant response without a network round trip. The trade-off is that the client must hold the full server-filtered result set in memory, which for broad date ranges could be tens of thousands of rows.

- **Pagination:** The API supports `LIMIT` and `OFFSET` parameters, defaulting to 100 rows per page. Page navigation buttons in the frontend increment/decrement the offset and re-fetch. Changing a server-side filter resets pagination to page 1; changing a client-side filter does not trigger a new API call.

### 2.3 Backend Architecture

Flask serves **six RESTful endpoints**, each constructing raw SQL queries via SQLAlchemy's `text()` function with parameterised bindings to prevent SQL injection:

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/` | GET | Serves the main HTML page via Jinja2 template rendering | None |
| `/api/trip` | GET | Returns trip records with optional filtering and pagination | `trip_id`, `payment_type`, `date_from`, `date_to`, `limit` (default 100), `offset` (default 0) |
| `/api/trip_fares` | GET | Returns fare breakdown data with pagination | `limit` (default 100), `offset` (default 0) |
| `/api/vendor` | GET | Returns vendor lookup table (ID to name mapping) | None |
| `/api/payment_types` | GET | Returns payment type lookup table | None |
| `/api/zone` | GET | Returns taxi zone lookup table (ID to borough + zone name) | None |
| `/api/fare_rates` | GET | Returns fare rate lookup table | None |

**Dynamic query construction:** The `/api/trip` endpoint builds its SQL `WHERE` clause at runtime based on which query parameters are present. If `date_from` is provided, it appends `AND pickup_datetime >= :date_from`; if `payment_type` is provided, it appends `AND payment_type_id = :payment_type`; and so on. The parameters are passed as bound variables (`:date_from`, `:payment_type`) rather than string-interpolated into the query, which prevents SQL injection attacks. The endpoint constructs the filter string as a Python string, then wraps the full query in `sqlalchemy.text()` for execution.

**Error handling:** All endpoints use a `try/except` block that catches any exception during query execution or JSON serialisation and returns a `500 Internal Server Error` with the exception message in the response body. While exposing raw exception messages is not recommended for production (it can leak database schema details), it is appropriate for a development/academic project where debugging is more important than security hardening.

**JSON response format:** Each endpoint returns a JSON array of objects, where each object represents one row. Keys match the column names from the SQL query. The response does not include metadata (total row count, pagination links, etc.), which means the frontend cannot display "Page X of Y" without a separate count query.

### 2.4 Database Schema

The MySQL database uses a **normalised schema** with six tables linked by foreign keys. Normalisation reduces data redundancy by storing each entity (vendor, payment type, rate code, zone) once and referencing it by ID:

```
vendors (2 rows)                   fare_rates (6 rows)
+----+-------+                     +----+-------------+
| id | name  |                     | id | description |
+----+-------+                     +----+-------------+

payment_types (6 rows)             zones (265 rows)
+----+-------------+               +----+---------+----------+
| id | description |               | id | borough | zone     |
+----+-------------+               +----+---------+----------+

trips (~7.57M rows)
+----------+-----------+----------+------------+-----------+-----------------+-----------+
| trip_id  | vendor_id | rate_id  | payment_id | pickup_dt | pickup_loc_id   | dropoff.. |
+----------+-----------+----------+------------+-----------+-----------------+-----------+
  FK → vendors    FK → fare_rates   FK → payment_types    FK → zones (x2)

trip_fares (~7.57M rows)
+----------+------+-------+-----+-------+-------+-------+---------------+
| trip_id  | fare | extra | mta | tip   | tolls | impr  | congestion    |
+----------+------+-------+-----+-------+-------+-------+---------------+
  FK → trips
```

**Design rationale for splitting trips and trip_fares:** The `trips` table contains temporal, spatial, and categorical data (when, where, how many passengers, which vendor). The `trip_fares` table contains the full financial breakdown (fare, extras, tax, tip, tolls, surcharges). Separating these into two tables joined on `trip_id` provides two benefits:

1. **Query efficiency:** Dashboard queries that only need spatial or temporal data (e.g., "count of trips by hour" or "busiest pickup zones") do not need to load the seven financial columns, reducing I/O.
2. **Logical separation:** Financial data has different access patterns and sensitivity characteristics than trip logistics. In a production system, this separation would make it easier to apply different access controls or audit requirements to fare data.

**The `nan_none()` helper:** The `database.py` loader includes a critical utility function that iterates through each row dictionary before insertion and converts any `NaN` value (pandas' representation of missing data) to Python `None` (which SQLAlchemy maps to SQL `NULL`). Without this conversion, MySQL rejects the `INSERT` because `NaN` is a floating-point concept with no SQL equivalent — MySQL interprets it as an invalid numeric literal rather than a null marker. This was one of the most difficult bugs to diagnose (see Section 5.1) because the error messages pointed to type mismatches rather than the actual cause.

**Batch insertion:** Records are inserted in chunks of 5,000 using SQLAlchemy's `session.execute(insert_stmt, rows)` bulk API. After each chunk, the session is committed to release the transaction lock. Loading 7.57 million rows at this batch size requires approximately 1,514 individual INSERT operations. A larger batch size (e.g., 50,000) would reduce round trips but increase memory pressure; 5,000 was chosen as a pragmatic middle ground that keeps memory usage modest while completing the load in a reasonable time.

### 2.5 Technology Choice Rationale

| Choice | Why | Trade-off |
|--------|-----|-----------|
| **Flask over Django** | Lightweight micro-framework with no built-in ORM, admin panel, or form handling overhead. Since we use raw SQL via `text()` rather than Django's ORM, Flask's minimalism avoids pulling in unused abstractions. Flask also has a shorter learning curve for a project of this scope. | No built-in admin panel for inspecting database contents. No built-in form validation, CSRF protection, or user authentication — all of which would matter in a production deployment but are unnecessary for this analytical dashboard. |
| **MySQL over SQLite** | MySQL runs as a separate server process, supporting concurrent reads from multiple API requests without file-level locking. It enforces foreign key constraints by default (SQLite requires `PRAGMA foreign_keys = ON`), making schema integrity violations fail loudly. MySQL also supports `EXPLAIN` for query plan analysis and has mature indexing for large tables. | Requires installing and running a MySQL server, managing credentials, and configuring connection strings. SQLite would have been simpler to set up (single file, no server) but struggles with concurrent writes and has limited support for `ALTER TABLE` operations. |
| **Parquet for intermediate storage** | Apache Parquet's columnar storage format compresses the dataset 3-5x compared to CSV, reducing disk I/O during the cleaning pipeline. Columnar reads allow the cleaning script to load only the columns it needs for each validation rule, rather than reading entire rows. Parquet also preserves data types (timestamps, integers, floats), eliminating the CSV parsing step where pandas has to infer types on every load. | Adds an extra conversion step (`csv_to_parquet.py`) to the pipeline. Parquet files are not human-readable (cannot be opened in a text editor for quick inspection), which makes ad-hoc debugging harder. The `scripts/inspect_data.py` utility partially mitigates this by printing summary statistics from the Parquet file. |
| **Chart.js over D3.js** | Chart.js provides a declarative, configuration-driven API for standard chart types (bar, line, doughnut, pie). A chart can be created with a single JavaScript object specifying labels, data arrays, and options. D3.js offers far more control over custom visualisations but requires imperative code to binddata to SVG elements, handle transitions, and manage scales — significantly more code for the same standard charts. | Less control over non-standard interactivity (custom tooltips, animated transitions, linked brushing between charts). Chart.js also imposes its own styling decisions, making it harder to match a specific design system. For our standard dashboard charts, these limitations are acceptable. |
| **Raw SQL via `text()` over ORM queries** | Full control over `JOIN`, `WHERE`, `GROUP BY`, and subquery logic. The dynamic `WHERE` clause construction in `/api/trip` would be awkward to express through SQLAlchemy's ORM query builder, which generates SQL behind an abstraction layer. Raw SQL is also easier to debug — the query string can be copied directly into a MySQL client for testing. | No compile-time type safety. Parameter binding must be done manually (though `text()` with `:param` syntax handles this safely). No automatic relationship loading — joins must be written explicitly. |
| **Client-side filtering for distance/fare/zone** | Instant response when the user adjusts a range slider. No network round trip means the UI feels responsive even on slow connections. Since these filters operate on an already-reduced dataset (server-side date and payment filters have already been applied), the in-memory filtering is fast. | The browser must hold the full server-filtered result set in memory. For broad date ranges with no payment type filter, this could be hundreds of thousands of rows, potentially causing performance issues on low-memory devices. Moving these filters server-side (see Section 5.2) would eliminate this concern. |

---

## 3. Algorithmic Logic and Data Structures

### 3.1 Problem Statement

Given approximately 7.57 million trip records, each containing a `pickup_location_id` field that references one of 265 TLC-defined taxi zones, determine the **top K busiest pickup locations** by frequency count. The constraint is that this must be implemented **without relying on built-in sorting or counting libraries** — no `collections.Counter`, no `pandas.value_counts()`, no SQL `GROUP BY ... ORDER BY`, no `sorted()` with a key function. The goal is to demonstrate understanding of the underlying data structures and algorithmic principles that these library functions abstract away.

The algorithm is described in `dsa/algo.py` and is intended to be integrated as a dedicated API endpoint in future work (see Section 5.2).

### 3.2 Algorithm: Hash Map Frequency Counter with Linear Scan

The algorithm solves the problem in two distinct phases:

**Phase 1 — Frequency Counting:** A single linear pass through all trip records builds a hash map (Python dictionary) where each key is a `pickup_location_id` and each value is the count of trips originating from that zone. For each record, the algorithm checks whether the location ID already exists in the map. If it does, the count is incremented by one. If it does not, a new entry is created with a count of one. This phase touches each record exactly once.

**Phase 2 — Top-K Extraction:** After the frequency map is built, the algorithm performs K repeated linear scans over the map entries to extract the K most frequent locations. Each scan finds the entry with the highest count that has not already been selected (tracked via a "seen" set). The winner of each scan is appended to the result list and added to the seen set. After K scans, the result list contains the K busiest zones in descending order of trip count.

### 3.3 Pseudocode

```
FUNCTION find_busiest_zones(pickup_locations, k):
    // Phase 1: Build frequency map
    // One pass through all n records, O(1) per record
    freq_map = empty hash map
    FOR EACH location_id IN pickup_locations:
        IF location_id IN freq_map:
            freq_map[location_id] = freq_map[location_id] + 1
        ELSE:
            freq_map[location_id] = 1
    
    // Phase 2: Find top K by repeated linear scan
    // K passes through m unique entries
    top_k = empty list
    seen = empty set
    REPEAT k TIMES:
        max_count = 0
        max_id = null
        FOR EACH (id, count) IN freq_map:
            IF count > max_count AND id NOT IN seen:
                max_count = count
                max_id = id
        APPEND (max_id, max_count) TO top_k
        ADD max_id TO seen
    
    RETURN top_k
```

### 3.4 Big O Analysis

| Operation | Time Complexity | Space Complexity | Explanation |
|-----------|----------------|-----------------|-------------|
| Build frequency map (Phase 1) | O(n) | O(m) | One pass through all n records. Each dictionary lookup and insertion is O(1) amortised. The map grows to at most m entries, one per unique location. |
| Find top K (Phase 2) | O(k * m) | O(k) | K linear scans, each iterating over m dictionary entries. The "seen" set lookup is O(1) per check. The result list holds K entries. |
| **Total** | **O(n + k * m)** | **O(m + k)** | The two phases are sequential, so their complexities add. |

Where:
- **n** = number of trip records ≈ 7,570,000
- **m** = number of unique taxi zones = 265
- **k** = number of top results desired = 5 (in our frontend)

**Practical simplification:** Since m is a small constant (265 zones, fixed by the TLC's zone system), the k * m term in Phase 2 becomes 5 * 265 = 1,325 operations — trivial compared to the 7.57 million operations in Phase 1. This means the overall runtime is **effectively O(n)**, dominated entirely by the single pass through all trip records in Phase 1. The algorithm's performance scales linearly with the size of the dataset and is independent of the number of zones (as long as zones remain a small, bounded set).

**Space usage** is O(m) = O(265), which requires approximately 265 dictionary entries regardless of whether the dataset contains 7 million or 70 million records. Each entry stores an integer key (4 bytes) and an integer count (8 bytes), so the total memory footprint of the frequency map is roughly 3 KB — negligible on any modern system.

### 3.5 Why This Approach Over Alternatives

**Alternative 1: Sort-and-count (O(n log n) time).** A naive approach would sort all 7.57 million records by `pickup_location_id` using a comparison sort (e.g., mergesort), then walk through the sorted array counting consecutive runs of the same ID. The sorting step alone costs O(n log n) ≈ 7,570,000 * 23 ≈ 174 million operations, compared to our approach's 7.57 million. Additionally, sorting requires either O(n) extra space (mergesort) or sacrifices stability (quicksort in-place), while our hash map uses only O(m) = O(265) space.

**Alternative 2: Min-heap of size K (O(m log k) extraction).** After building the same O(n) frequency map, a min-heap of size K could be used instead of the linear scan. Each of the m entries would be pushed onto the heap; if the heap exceeds size K, the smallest entry is popped. This produces O(m log k) extraction time instead of our O(k * m). With m = 265 and k = 5, this is O(265 * log 5) ≈ O(265 * 2.3) ≈ 610 operations, compared to our O(5 * 265) = 1,325 operations. The heap approach is asymptotically better for the extraction phase, but the constant-factor difference (610 vs. 1,325) is negligible — both complete in microseconds. The linear scan approach was chosen for its simplicity: it uses no additional data structures beyond a list and a set, and its correctness is immediately apparent from the pseudocode.

**Alternative 3: Array indexed by location ID.** Since location IDs range from 1 to 265, an array of size 266 (index 0 unused) could replace the hash map, with each index storing the count for that location ID. Array access is O(1) with no hash collision overhead. This approach would work and would be marginally faster due to better cache locality. However, the hash map was chosen because it handles sparse or non-contiguous IDs gracefully — if the TLC changed its zone numbering to include gaps or non-integer codes, the hash map would still work without modification. The code also reads more clearly when the key is the location ID itself (`freq_map[236]`) rather than an array index that happens to correspond to a location ID.

### 3.6 Data Structure Choice: Hash Map (Dictionary)

The Python dictionary was chosen as the primary data structure for frequency counting because of its combination of performance characteristics and code clarity:

- **O(1) amortised insertion and lookup:** Each `location_id in freq_map` check and each `freq_map[location_id] += 1` increment runs in constant amortised time, thanks to Python's open-addressing hash table implementation. This makes the counting phase a clean single-pass linear scan.

- **Dynamic sizing:** The dictionary grows automatically as new keys are added. With only 265 possible keys, the table never needs to resize more than a handful of times (Python dictionaries resize at 2/3 load factor, starting at size 8).

- **Key-value semantics:** Using the location ID as the key and the count as the value makes the code self-documenting: `freq_map[location_id]` clearly means "the count for this location." An equivalent array implementation would use `counts[location_id]`, which is slightly less readable and requires understanding that the array index corresponds to a zone ID.

- **Sparse-friendly:** The hash map allocates space only for keys that actually appear in the data. If certain zones have zero pickups (e.g., some Staten Island zones), they simply do not appear in the map, consuming no memory. An array would allocate space for all 265 slots regardless.

---

## 4. Insights and Interpretation

### Finding 1: Rush Hour Dominance — The Evening Peak Dwarfs the Morning

**Method:** The frontend's "Trips by hour of day" bar chart aggregates all cleaned trips by the derived `pickup_hour` field (integers 0 through 23), counting the number of pickups that fall within each one-hour window across the entire month of January 2019. This produces 24 bars, one for each hour of the day, showing the hourly distribution of taxi demand.

**Result:** Trip volume follows a clear **bimodal pattern** across the day, but the two peaks are markedly unequal. Starting from a daily minimum between 3 AM and 5 AM (when fewer than 100,000 trips occur across the month), volume rises steadily through the morning. A morning plateau forms between 8 AM and 10 AM, corresponding to the traditional morning commute window. After a slight midday dip, volume climbs again through the afternoon, building to a sharp **evening peak between 6 PM and 7 PM** that consistently records **30-40% more trips** than the morning plateau. After 8 PM, volume drops steadily back toward the overnight minimum.

**Interpretation:** The asymmetry between morning and evening peaks reveals a fundamental difference in how New Yorkers use taxis at each end of the workday.

In the morning, commuters have predictable schedules and multiple transit options competing for their patronage. The subway system runs at full frequency during the AM rush, and many workers have regular routines (same departure time, same route) that favour fixed-route transit over on-demand taxis. Morning taxi use tends to be concentrated among passengers for whom speed or convenience justifies the premium: people running late, travellers with luggage heading to airports, or those whose origin-destination pairs are poorly served by subway lines.

The evening, by contrast, bundles multiple demand drivers into the same 4 PM to 8 PM window. Work commuters leaving the office overlap with dinner-goers heading to restaurants, theatre patrons going to Broadway shows, social outings in the Lower East Side and Williamsburg, and airport-bound passengers catching evening flights. Unlike the morning, where people leave home at a specific time to arrive at work on time, evening departure times are more varied and flexible, spreading demand across a wider window but peaking higher because all categories stack on top of each other.

**Practical implication:** Taxi companies and ride-hail platforms could optimise fleet allocation by deploying more vehicles starting at 4 PM rather than distributing evenly across both rush hours. The current even distribution likely leaves drivers idle during the less busy morning hours while creating artificial scarcity (and longer wait times) during the evening peak.

### Finding 2: Cash Is Disappearing from New York Taxis

**Method:** The "Payment Types" doughnut chart on the frontend breaks down all 7.57 million cleaned trips by `payment_type_id`, mapped to descriptive labels (Credit card, Cash, No charge, Dispute, Unknown, Voided trip) via the `payment_types` lookup table in the database. Each slice represents the proportion of trips paid by that method.

**Result:** **Credit card payments account for roughly two-thirds** (approximately 67%) **of all trips**, with **cash making up the remaining third** (approximately 32%). The other four categories — no charge, dispute, unknown, and voided trip — together amount to **less than 1%** of total trips, with disputes and voided trips each below 0.3%.

**Interpretation:** The dominance of credit card payments in January 2019 is the product of both regulatory mandate and societal shift. The TLC has required all yellow cabs to accept credit cards since 2007, and the in-car payment terminals (operated by VeriFone and Creative Mobile Technologies, the two vendors in our dataset) present card payment as the default option with prominent tip suggestion buttons. Over the decade since the mandate, passenger behaviour has shifted accordingly — many riders now default to card payment without considering cash.

This payment split has a **critical methodological implication** for the dataset itself. Credit card trips record tip amounts precisely because the transaction is electronic — the tip is itemised on the receipt and flows into the TLC's data system. Cash trips, however, record a **$0.00 tip** regardless of whether the passenger actually tipped in cash. This is not because cash passengers do not tip; it is because the TLC's data collection system has no mechanism to capture cash tips. Industry surveys consistently show that cash tippers and card tippers behave similarly, but the dataset makes cash riders appear as non-tippers.

This means that any analysis of tipping behaviour using this dataset is **systematically biased toward credit card tipping patterns**. The dataset undercounts total tip revenue by approximately one-third (the share of cash trips), and any model trained on this data to predict tip amounts would learn that a significant fraction of passengers tip $0.00 — a pattern that reflects the data collection method, not actual rider behaviour. Researchers using TLC data for tipping studies must either restrict their analysis to credit card trips only (reducing sample size by a third) or explicitly model the cash tip censoring as a missing data problem.

The near-absence of disputes (< 0.3%) and voided trips (< 0.1%) suggests that the TLC's electronic payment infrastructure is reliable. Disputes represent fares contested by the passenger after the trip, and their rarity indicates that fare calculation errors or billing problems are uncommon — a positive signal about the accuracy of the metered fare data in our dataset.

### Finding 3: Most Taxi Trips Are Short Hops, Not Cross-Borough Journeys

**Method:** The "Trip distance groups" bar chart bins all cleaned trips into five distance brackets — 0-2 miles, 2-5 miles, 5-10 miles, 10-20 miles, and 20+ miles — using the `trip_distance` field from the cleaned dataset. Each bar shows the count of trips falling within that distance range.

**Result:** The distribution is **heavily right-skewed**. Trips under 2 miles make up the single largest category, and the 0-5 mile range accounts for the clear majority of all trips. The 5-10 mile bracket captures a moderate share, while trips over 10 miles represent a small fraction of the total. Trips over 20 miles — which would include rides to JFK Airport from northern Manhattan, or cross-borough trips between distant neighbourhoods — are rare.

**Interpretation:** Yellow taxis in Manhattan function primarily as **short-distance, intra-neighbourhood transport** rather than long-haul carriers. This pattern is a direct consequence of Manhattan's physical geography and urban design. The Manhattan street grid is dense, with blocks approximately 250 feet (east-west) and 900 feet (north-south) apart. A typical taxi ride of 10-20 blocks, which covers most practical within-neighbourhood trips (home to office, restaurant to theatre, hotel to meeting), falls well within the 0-2 mile bracket.

The dominance of short trips also explains why the **average fare is relatively modest** despite New York's reputation for expensive taxis. The TLC's standard metered rate is $2.50 initial charge plus $0.50 for each 1/5 mile (or $2.50 per mile). A 1.5-mile trip, roughly the median distance, costs approximately $2.50 + (1.5 * $2.50) = $6.25, plus the $0.50 MTA tax and $0.30 improvement surcharge, for a total under $8 before tip. Most riders pay less than $15 for a complete trip.

**Urban planning implication:** The finding that the vast majority of taxi trips are under 2 miles supports investment in **alternatives like bike-share programmes (Citi Bike) and micro-transit** for very short urban trips. A 2-mile distance is a 7-10 minute bike ride, making these trips prime candidates for modal shift. If even 10-20% of sub-2-mile taxi trips shifted to bike-share, the reduction in vehicle-miles-travelled would meaningfully reduce traffic congestion in Midtown and Lower Manhattan, without significantly impacting taxi revenue from the longer, higher-fare trips (airport runs, cross-borough rides) that generate disproportionate driver income.

---

## 5. Reflection and Future Work

### 5.1 Technical Challenges

**Challenge 1: Database NaN Compatibility**

The most persistent and difficult-to-diagnose bug in the entire project was loading cleaned data from pandas into MySQL. Pandas uses the floating-point value `NaN` (Not a Number) as its universal sentinel for missing data — any column with at least one missing value is promoted to float dtype, and the gaps are filled with `NaN`. This works seamlessly within the pandas ecosystem because pandas functions are designed to handle `NaN` gracefully.

MySQL, however, has no concept of `NaN`. Its equivalent for missing data is `NULL`, a SQL primitive that behaves differently from `NaN` in critical ways. When SQLAlchemy attempted to insert a row containing a pandas `NaN` value into a MySQL column, the database rejected it — but the error message was misleading. Instead of saying "cannot insert NaN," MySQL reported a type mismatch error (something like "Incorrect DOUBLE value"), because it tried to parse `NaN` as a numeric literal and failed.

The diagnosis was made harder by the fact that only certain columns had missing values (`passenger_count` and `congestion_surcharge` were the primary culprits). Rows with complete data inserted fine; rows with `NaN` in any field silently failed during batch inserts, causing the total row count in the database to fall short of the cleaned dataset size. It took several rounds of debugging — adding row-level try/except blocks, printing failing rows, and comparing pandas dtypes against MySQL column types — before the root cause was identified.

The fix was the `nan_none()` helper function in `database.py`, which iterates through each row dictionary before insertion and converts any `NaN` value to Python `None`. SQLAlchemy correctly maps Python `None` to SQL `NULL`, resolving the incompatibility. This taught us a broader lesson: **data type assumptions that hold within one ecosystem (pandas, where NaN is a float and fills any gap) break at the boundary between systems** (Python-to-SQL, Python-to-JSON, Python-to-Excel). Any data pipeline that moves data across system boundaries must explicitly handle type conversion at each crossing point.

**Challenge 2: Data Cleaning Trade-offs**

Deciding what to remove versus what to keep required judgement that no single automated rule could capture. Every cleaning threshold is a compromise between removing noise and preserving legitimate edge cases.

The clearest example is **zero-distance trips**. A zero-distance trip could be a legitimate event (a passenger gets in, realises they are at the wrong address, and immediately exits) or a meter error (the driver engages the meter accidentally and resets it). We chose to remove all zero-distance trips because they distort average distance calculations, produce undefined speed values (division by zero in duration), and inflate trip counts without representing actual transportation. However, this decision removes some real behaviour from the dataset — cancelled rides are a genuine part of the taxi ecosystem, and studying their frequency and spatial distribution could yield insights into pickup-zone reliability.

Similarly, the **80 mph speed threshold** sits in a grey area. Highway speeds on the FDR Drive or Belt Parkway can legitimately reach 60-65 mph in light traffic, and measurement granularity introduces noise: a very short trip (0.5 miles in 30 seconds) computes to 60 mph even if the actual driving speed was 30 mph with measurement rounding. We set 80 mph as a generous threshold to avoid catching these edge cases, but this means some legitimately erroneous records with speeds between 65 and 80 mph remain in the dataset. A more sophisticated approach would use trip distance as a moderating factor — a computed speed of 75 mph on a 20-mile trip is more plausible than the same speed on a 0.3-mile trip — but this would have added complexity without substantially changing the aggregate analysis.

We documented every assumption in the cleaning pipeline code (as comments on each rule) and logged every single rejection to the audit CSV. This means the cleaning decisions are fully **reproducible and adjustable**: a researcher who disagrees with the 80 mph threshold can modify the constant and rerun the pipeline, and the audit log lets them examine exactly which rows were affected.

**Challenge 3: Frontend-to-Backend Integration**

Connecting the Flask API to the frontend required coordinating **two fundamentally different filtering strategies** that operate at different stages of the data pipeline.

Server-side filters (date range and payment type) are encoded as query parameters in the API URL, transmitted over the network, and applied as SQL `WHERE` clauses in the database. Client-side filters (distance range, fare range, zone) are JavaScript `Array.filter()` calls that operate on the JSON data already loaded into the browser's memory. Getting these to compose correctly required careful sequencing:

1. When the user changes a server-side filter (selects a new date range or payment type), the frontend must make a new `fetch()` call to the API, receive the filtered data, and then re-apply any active client-side filters before rendering charts and tables.

2. When the user changes a client-side filter (adjusts a distance slider), the frontend must re-filter the already-loaded data and re-render without making a new API call. This provides instant feedback.

3. Pagination introduced another layer: changing a server-side filter resets the page offset to 0 (since the result set has changed), but changing a client-side filter should not trigger a new API call or reset pagination — the filtered results are drawn from the already-fetched page.

The main bug we encountered was a race condition where a client-side filter change triggered a re-render before the previous server-side fetch had completed, causing the charts to display stale data momentarily. The fix was to disable the filter controls during API fetches and re-enable them after the response was received and rendered.

### 5.2 What We Would Improve

**Implement the busiest-zones algorithm in production code.** The `dsa/algo.py` file currently queries pickup location IDs from the database but does not run the full frequency-counting algorithm described in Section 3. The algorithm is documented and analysed in this report and is ready for implementation. Integrating it as a dedicated API endpoint (`/api/busiest_zones?k=10`) would replace the current frontend approach of fetching all trips and counting client-side, reducing network transfer from megabytes of trip JSON to a few hundred bytes of aggregated results, and eliminating the client-side memory burden of holding thousands of rows just to count frequencies.

**Move all filtering to the server side.** Currently, distance, fare, and zone filtering happen in JavaScript after the data is fetched. This means the API returns all trips matching the date and payment type filters, and the browser discards the ones outside the distance/fare/zone range. For broad queries (e.g., all of January 2019 with no payment type filter), this could mean transferring and parsing hundreds of thousands of rows that are immediately thrown away. Moving these filters into the SQL `WHERE` clause would reduce data transfer, lower browser memory usage, and make the application perform consistently regardless of the result set size.

**Introduce a caching layer.** Repeated queries for the same date range and filter combination currently hit the MySQL database every time. The aggregation endpoints (trips by hour, payment type distribution, distance group counts) are particularly wasteful because they re-aggregate across millions of rows for each request, even when the underlying data has not changed. Adding **Redis** or even a simple in-memory Python dictionary as a cache for frequently requested aggregations would reduce database load and improve response times. The cache key would be the combination of all filter parameters, and the cache would be invalidated if new data were loaded into the database.

**Expand to multiple months.** The current dataset covers only January 2019. Extending to a full year (or multiple years) would enable analysis of seasonal patterns (do taxis get busier in summer or winter?), holiday effects (Christmas, New Year's Eve, Thanksgiving), weather correlations (rainy days vs. clear days), and long-term trends in taxi ridership versus ride-hail competition (Uber and Lyft). The cleaning pipeline and database schema are already designed to handle additional months without structural changes — the `validate_trip_times` function would need its date range parameter adjusted for each month, and the loader would batch-insert additional Parquet files into the same tables. The frontend's date range filter would automatically accommodate the wider time span.

---

## References

1. NYC Taxi and Limousine Commission, "TLC Trip Record Data," https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
2. NYC Taxi and Limousine Commission, "Taxi Zone Shapefile," https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
3. Chart.js Documentation, https://www.chartjs.org/docs/latest/
4. Flask Documentation, https://flask.palletsprojects.com/
5. SQLAlchemy Documentation, https://docs.sqlalchemy.org/
6. Pandas Documentation, https://pandas.pydata.org/docs/
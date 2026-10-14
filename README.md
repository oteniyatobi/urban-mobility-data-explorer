# Urban Mobility Data Explorer

An interactive dashboard and REST API for exploring New York City Yellow Taxi trips from January 2019. The application is built with Flask, MySQL, SQLAlchemy, and vanilla JavaScript; it displays trip records and summary charts using the NYC Taxi and Limousine Commission (TLC) dataset.

- **Live site:** [taxi.thetobi.tech](https://taxi.thetobi.tech)
- **Video demo:** [Watch the demo](https://youtu.be/H2avaVy0rmI)

This project was developed as a group summative assignment for the Software Engineering program at the African Leadership University (ALU).

## Features

- Browse trips in a paginated table and open a trip's available fields in a details dialog.
- Filter trips on the server by pickup date, payment type, and pickup zone.
- Sort the displayed page by trip ID, pickup time, dropoff time, distance, or passenger count.
- View overall trip counts by pickup hour and weekday/weekend, payment-type counts, and busiest pickup zones.
- View trip-distance groups for the trips currently loaded in the table.
- Retrieve trip, fare, vendor, fare-rate, payment-type, zone, and summary data through JSON API endpoints.
- Clean the source data, derive trip features, and load the processed trips into MySQL.

### Current dashboard behavior

Date, payment-type, and pickup-zone filters are sent to the API. The distance controls are intended to filter the current page in the browser, but are only applied after clicking a sortable table heading. The minimum- and maximum-fare fields are present in the interface, but fare amounts are not included in the trip-list API response, so those controls do not currently filter trips. The hourly, payment, and top-zone summaries cover the database; the distance chart covers only the current page.

## Technology

- **Application:** Python, Flask, Flask-CORS, SQLAlchemy
- **Database:** MySQL, accessed with PyMySQL
- **Data processing:** pandas, PyArrow, GeoPandas and related geospatial packages
- **Frontend:** HTML, CSS, vanilla JavaScript, [Chart.js](https://www.chartjs.org/) (loaded from jsDelivr)
- **Algorithm exercise:** Python dictionary-based vendor frequency counter

`requirements.txt` currently lists data-processing and geospatial packages, but not the Flask/MySQL application dependencies. Install both sets as shown under [Installation](#installation).

## Project layout

```text
.
├── backend/
│   ├── backend.py                 # Flask routes and application entry point
│   ├── static/
│   │   ├── app.js                 # Dashboard behavior and charts
│   │   └── style.css              # Dashboard styles
│   └── templates/
│       └── index.html             # Dashboard page
├── database/
│   └── database.py                # MySQL schema creation and Parquet data loader
├── data/
│   ├── raw/                       # Downloaded TLC trip and zone source files
│   ├── processed/                 # Cleaned trip Parquet and zone GeoJSON
│   └── audit/                     # Cleaning-rule counts
├── docs/
│   ├── documentation_report.md    # Technical report
│   ├── report.txt                 # Schema/report material
│   └── time_complexity_screenshot.png
├── dsa/
│   ├── algo.py                    # Busiest-vendor algorithm
│   └── testing_algo.py            # Simple runtime scaling exercise
├── scripts/
│   ├── clean_data.py              # Clean trips and add derived fields
│   ├── convert_geojson.py         # Convert taxi-zone shapefile to GeoJSON
│   ├── csv_to_parquet.py          # Convert raw trip CSV to Parquet
│   ├── inspect_data.py            # Print dataset diagnostics
│   └── parquet_to_csv.py          # Convert processed Parquet to CSV
├── requirements.txt
└── README.md
```

The raw trip data and some source files are not included in the repository. Download the inputs as described below before running the cleaning and loading steps.

## Dataset and processing

The project uses the TLC Yellow Taxi Trip Records for January 2019 and the TLC taxi-zone lookup. The cleaning script reads `data/raw/yellow_tripdata_2019-01.parquet`, adds derived fields (`trip_duration_min`, `avg_speed_mph`, `tip_pct`, `pickup_hour`, `pickup_dow`, and `is_weekend`), applies its validation rules, and writes:

- `data/processed/cleaned_trips.parquet`
- `data/audit/cleaning_log.csv`, containing counts removed by cleaning rule

The database loader reads the cleaned Parquet file and `data/raw/taxi_zone_lookup.csv`. It inserts trip and fare records in batches of 5,000. Run it once against a newly created, empty project database; it creates tables but does not create the MySQL database itself or make repeated loads idempotent.

## Installation

### Prerequisites

- Python 3.11 or later
- MySQL 8, with a database server accessible from the application
- `pip`

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/oteniyatobi/urban-mobility-data-explorer.git
cd urban-mobility-data-explorer

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install Flask Flask-Cors SQLAlchemy PyMySQL python-dotenv
```

### 2. Download the data

From the repository root:

```bash
mkdir -p data/raw
wget -O data/raw/yellow_tripdata_2019-01.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet
wget -O data/raw/taxi_zone_lookup.csv \
  https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
```

If you have the trip dataset as CSV instead, put it at `data/raw/yellow_tripdata_2019-01.csv` and run `python scripts/csv_to_parquet.py` from the repository root to create the Parquet input expected by the cleaning script.

### 3. Configure and create the MySQL database

Create a database, for example:

```sql
CREATE DATABASE taxi_analytics;
```

Create a `.env` file in the repository root with credentials for that database:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=taxi_analytics
```

Do not commit `.env` or real credentials.

### 4. Clean and load the data

Run these commands from the repository root:

```bash
python scripts/clean_data.py
python database/database.py
```

The loader creates six tables (`trips`, `trip_fares`, `vendors`, `fare_rates`, `payment_types`, and `zones`) and loads lookup and trip data. Loading several million records can take time and requires sufficient disk space and MySQL capacity.

### 5. Start the application

From the repository root:

```bash
python backend/backend.py
```

Open [http://127.0.0.1:7000](http://127.0.0.1:7000). The development server runs with Flask debug mode enabled; use a production WSGI server and appropriate deployment configuration for production.

## API

All endpoints return JSON. The API is served by the Flask application on the same host and port as the dashboard.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/trip` | Paginated trip records, with optional filters |
| `GET` | `/api/trip_fares` | Paginated fare records |
| `GET` | `/api/vendor` | Vendor lookup; optionally filter by `vendor_id` |
| `GET` | `/api/fare_rates` | Fare-rate lookup |
| `GET` | `/api/payment_types` | Payment-type lookup |
| `GET` | `/api/zone` | Taxi-zone lookup; optionally filter by `location_id` |
| `GET` | `/api/stats/hourly` | Trip counts grouped by pickup hour and weekend flag |
| `GET` | `/api/stats/payments` | Trip counts grouped by payment-type description |
| `GET` | `/api/stats/top-zones` | Pickup counts for the busiest zones |
| `GET` | `/api/busiest-vendor` | Busiest vendor, trip count, counts by vendor, and elapsed algorithm time |

### `/api/trip` query parameters

| Parameter | Default | Description |
|---|---:|---|
| `page` | `1` | Page number (must be at least 1) |
| `limit` | `100` | Number of records per page (must be at least 1) |
| `trip_id` | — | Return a specific trip ID |
| `payment_type` | — | Filter by payment-type ID |
| `date_from` | — | Inclusive pickup datetime lower bound, formatted `YYYY-MM-DD` |
| `date_to` | — | Pickup datetime upper-bound value, formatted `YYYY-MM-DD` (MySQL interprets it as midnight at the start of that date) |
| `pickup_location_id` | — | Filter by pickup-zone ID |

For example:

```text
/api/trip?page=1&limit=100&payment_type=1&date_from=2019-01-01&date_to=2019-01-31&pickup_location_id=161
```

`/api/trip_fares` accepts `page` and `limit`. `/api/vendor` accepts `vendor_id`; `/api/zone` accepts `location_id`; and `/api/stats/top-zones` accepts `k` (1–100, default 10). The trip and fare endpoints return their respective table records; they do not combine trips with fare details.

## Database schema

The database contains six tables:

- **`trips`** — Trip timestamps, vendor/rate/payment IDs, pickup/dropoff zone IDs, passenger count, distance, and derived time/speed fields.
- **`trip_fares`** — Fare, taxes, tip, tolls, surcharges, total amount, and tip ratio, keyed by `trip_id`.
- **`vendors`** — Vendor IDs and names.
- **`fare_rates`** — TLC fare-rate IDs and descriptions.
- **`payment_types`** — Payment-type IDs and descriptions.
- **`zones`** — TLC location IDs, boroughs, zone names, and service zones.

Trip and fare details are stored separately and can be associated using `trip_id`.

## Other utilities

- `python scripts/inspect_data.py` prints diagnostics for the raw Parquet, zone lookup, and processed GeoJSON files.
- `python scripts/convert_geojson.py` converts `data/raw/taxi_zones/taxi_zones.shp` into `data/processed/taxi_zones.geojson`; the shapefile bundle is an additional input and is not needed to run the dashboard.
- `python scripts/parquet_to_csv.py` exports the cleaned Parquet dataset to CSV.
- `python -m dsa.testing_algo` runs the busiest-vendor algorithm's simple input-doubling timing exercise.

Run these commands from the repository root. The conversion and inspection scripts expect their documented input files to exist.

## Team

- **Oteniya Oluwatobi Jeremiah** — Backend API development and deployment
- **Benson Maina** — Frontend and database
- **Nziza Denilson** — Data cleaning and documentation

## License

This project was built for academic purposes as part of the ALU Software Engineering program.

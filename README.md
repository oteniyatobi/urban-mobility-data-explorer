# Urban Mobility Data Explorer

A fullstack web application for exploring and analyzing NYC yellow taxi trip data from January 2019. Built with Flask, MySQL, and vanilla HTML/CSS/JavaScript.

**Live Site:** [taxi.thetobi.tech](https://taxi.thetobi.tech)

## About

This application provides an interactive dashboard for browsing over 7 million taxi trip records collected by the NYC Taxi and Limousine Commission. Users can filter trips by date range, payment type, and pickup zone, view trip details, and paginate through results.

The project was built as a group summative assignment for the Software Engineering program at the African Leadership University (ALU).

## Team

- **Oteniya Oluwatobi Jeremiah** (Backend API development, deployment)
- **Ben** (Frontend, database)
- **Nziza Denilson** (Data cleaning, documentation)

## Tech Stack

- **Backend:** Python 3, Flask, SQLAlchemy
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Database:** MySQL 8
- **Data Format:** Apache Parquet (source), MySQL (serving)
- **Deployment:** Ubuntu 20.04, nginx reverse proxy, Let's Encrypt SSL
- **Version Control:** Git, GitHub

## Features

- Browse taxi trips with pagination (configurable page size)
- Filter by date range, payment type, and pickup zone
- View full trip details in a modal dialog
- Reset all filters with one click
- Responsive layout
- RESTful API with parameterized queries to prevent SQL injection

## Project Structure

```
urban-mobility-data-explorer/
├── backend/
│   ├── backend.py              # Flask application and API routes
│   ├── static/
│   │   ├── app.js              # Frontend JavaScript
│   │   └── style.css           # Stylesheet
│   └── templates/
│       └── index.html          # Main page template
├── database/
│   └── database.py             # Schema definitions and data loader
├── data/
│   ├── raw/                    # Source parquet and zone lookup CSV
│   ├── processed/              # Cleaned parquet output
│   └── audit/                  # Cleaning log
├── scripts/
│   ├── clean_data.py           # Data cleaning pipeline
│   ├── inspect_data.py         # Data inspection utilities
│   ├── csv_to_parquet.py       # Format conversion
│   ├── parquet_to_csv.py       # Format conversion
│   └── convert_geojson.py      # GeoJSON conversion for zones
├── dsa/
│   └── algo.py                 # Custom algorithm implementation
├── docs/
│   └── documentation_report.md # Technical report
└── requirements.txt
```

## API Endpoints

| Method | Endpoint             | Description                          |
|--------|----------------------|--------------------------------------|
| GET    | `/api/trip`          | List trips with filters and pagination |
| GET    | `/api/payment_types` | List all payment type descriptions   |
| GET    | `/api/zone`          | List all taxi zones                  |
| GET    | `/api/vendor`        | List taxi vendors                    |
| GET    | `/api/fare_rates`    | List fare rate descriptions          |
| GET    | `/api/trip_fares`    | List trip fare details               |

### Query Parameters for `/api/trip`

| Parameter           | Type    | Default | Description                        |
|---------------------|---------|---------|------------------------------------|
| `page`              | int     | 1       | Page number                        |
| `limit`             | int     | 100     | Results per page                   |
| `trip_id`           | int     | —       | Filter by specific trip            |
| `payment_type`      | string  | —       | Filter by payment type ID          |
| `date_from`         | string  | —       | Pickup date lower bound (YYYY-MM-DD) |
| `date_to`           | string  | —       | Pickup date upper bound (YYYY-MM-DD) |
| `pickup_location_id`| int     | —       | Filter by pickup zone              |

## Database Schema

The application uses five tables:

- **trips** — Core trip records (pickup/dropoff times, distance, passenger count, location IDs, computed fields like duration and speed)
- **trip_fares** — Fare breakdown per trip (fare amount, tax, tip, tolls, surcharges, total)
- **vendors** — Taxi vendor names (Creative Mobile Technologies, VeriFone Inc., etc.)
- **payment_types** — Payment method descriptions (Credit card, Cash, No charge, Dispute, etc.)
- **zones** — NYC taxi zone lookup (location ID, borough, zone name, service zone)

## Dataset

The source data is the NYC TLC Yellow Taxi Trip Records for January 2019, publicly available from the [NYC Taxi and Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). The raw dataset contains approximately 7.6 million trip records. The cleaning pipeline (`scripts/clean_data.py`) removes invalid records (negative distances, zero passengers, trips outside January 2019) and computes derived fields (trip duration, average speed, pickup hour, day of week, weekend flag).

## Setup

### Prerequisites

- Python 3.8 or higher
- MySQL 8
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/oteniyatobi/urban-mobility-data-explorer.git
   cd urban-mobility-data-explorer
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your MySQL credentials:
   ```
   DB_HOST=your_mysql_host
   DB_PORT=3306
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_NAME=taxi_analytics
   ```

4. Download the source data:
   ```bash
   mkdir -p data/raw
   wget -O data/raw/yellow_tripdata_2019-01.parquet https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet
   wget -O data/raw/taxi_zone_lookup.csv https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
   ```

5. Clean the data:
   ```bash
   python scripts/clean_data.py
   ```

6. Create the database and load the data:
   ```bash
   python database/database.py
   ```

7. Run the application:
   ```bash
   cd backend
   python backend.py
   ```

   The app starts on `http://127.0.0.1:7000`.

## License

This project was built for academic purposes as part of the ALU Software Engineering program.
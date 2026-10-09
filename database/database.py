import os
import pyarrow.parquet as pq
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Column, ForeignKey,insert
from sqlalchemy.orm import DeclarativeBase


load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
PARQUET_FILE = "data/processed/cleaned_trips.parquet"

class Base(DeclarativeBase):
    pass

#Vendors table
class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id = Column(Integer, primary_key=True)
    name = Column(String(250))

#Fare rates table
class FareRate(Base):
    __tablename__ = "fare_rates"
    rate_id = Column(Integer, primary_key=True)
    description = Column(String(250))

#Payment types table
class PaymentType(Base):
    __tablename__ = "payment_types"
    payment_type_id = Column(Integer, primary_key=True)
    description = Column(String(250))

#taxi zones table
class TaxiZone(Base):
    __tablename__ = "zones"
    location_id = Column(Integer, primary_key=True)
    zone_name = Column(String(250))

#trips table
class Trip(Base):
    __tablename__ = "trips"
    trip_id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"), index=True)
    rate_id = Column(Integer, ForeignKey("fare_rates.rate_id"))
    payment_type_id = Column(Integer, ForeignKey("payment_types.payment_type_id"), index=True)
    pickup_location_id = Column(Integer, ForeignKey("zones.location_id"), index=True)
    dropoff_location_id = Column(Integer, ForeignKey("zones.location_id"), index=True)
    pickup_datetime = Column(DateTime, index=True)
    dropoff_datetime = Column(DateTime, index=True)
    passenger_count = Column(Integer)
    trip_distance = Column(Float)
    store_and_fwd_flag = Column(String(1))
    trip_duration_min = Column(Float)
    avg_speed_mph = Column(Float)
    pickup_hour = Column(Integer, index=True)
    pickup_dow = Column(Integer, index=True)
    is_weekend = Column(Boolean, index=True)

#Trip fare table
class TripFare(Base):
    __tablename__ = "trip_fares"
    trip_id = Column(Integer, ForeignKey("trips.trip_id"), primary_key=True)
    fare_amount = Column(Float)
    extra = Column(Float)
    mta_tax = Column(Float)
    tip_amount = Column(Float)
    tolls_amount = Column(Float)
    improvement_surcharge = Column(Float)
    congestion_surcharge = Column(Float)
    total_amount = Column(Float)
    tip_pct = Column(Float)

#Create the database tables 
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print("Db tables created successfully")

parquet = pq.ParquetFile(PARQUET_FILE)

lookup_data = pq.read_table(
    PARQUET_FILE,
    columns=[
        "VendorID",
        "RatecodeID",
        "payment_type",
        "PULocationID",
        "DOLocationID"
    ]
)

#prepare the vendors
vendor_ids = lookup_data.column("VendorID").unique().to_pylist()
vendors = []
for vendor_id in vendor_ids:
    vendor = {
        "vendor_id": vendor_id,
        "name": "Vendor" + str(vendor_id)

    }
    vendors.append(vendor)

#prepare the fare rates
rate_ids = lookup_data.column("RatecodeID").unique().to_pylist()
fare_rates = []
rate_descriptions = {
    1: "Standard rate",
    2: "JFK airport rate",
    3: "Newark airport rate",
    4: "Nassau or Westchester rate",
    5: "Negotiated fare",
    6: "Group ride"
}
for rate_id in rate_ids:
    fare_rate = {
        "rate_id": rate_id,
        "description": rate_descriptions.get(rate_id, "Unknown Rate")
    }
    fare_rates.append(fare_rate)

#prepare payment types
payment_ids = lookup_data.column("payment_type").unique().to_pylist()
payment_types = []
for payment_id in payment_ids:
    payment_type = {
        "payment_type_id": payment_id,
        "description": "Payment Type" + str(payment_id)

    }
    payment_types.append(payment_type)
#prepare taxi zones
pickup_zone_ids = lookup_data.column("PULocationID").unique().to_pylist()
dropoff_zone_ids = lookup_data.column("DOLocationID").unique().to_pylist()
all_zone_ids = set()

for zone_id in pickup_zone_ids:
    all_zone_ids.add(zone_id)
for zone_id in dropoff_zone_ids:
    all_zone_ids.add(zone_id)

zones = []
for zone_id in all_zone_ids:
    zone = {
        "location_id": zone_id,
        "zone_name": "Zone" + str(zone_id)

    }
    zones.append(zone)

#insert the lookup data into the db
with engine.begin() as connection:
    if vendors:
        connection.execute(insert(Vendor), vendors)
    if fare_rates:
        connection.execute(insert(FareRate), fare_rates)
    if payment_types:
        connection.execute(insert(PaymentType), payment_types)
    if zones:
        connection.execute(insert(TaxiZone), zones)
print("lookup tables filled")

#load trips in batches
trip_id = 1
loaded_rows = 0
for batch in parquet.iter_batches(batch_size=50000):
    trips = []
    fares = []
    rows = batch.to_pylist()
    for row in rows:
        trip = {
            "trip_id": trip_id,
            "vendor_id": row["VendorID"],
            "rate_id": row["RatecodeID"],
            "payment_type_id": row["payment_type"],
            "pickup_location_id": row["PULocationID"],
            "dropoff_location_id": row["DOLocationID"],
            "pickup_datetime": row["tpep_pickup_datetime"],
            "dropoff_datetime": row["tpep_dropoff_datetime"],
            "passenger_count": row["passenger_count"],
            "trip_distance": row["trip_distance"],
            "store_and_fwd_flag": row["store_and_fwd_flag"],
            "trip_duration_min": row["trip_duration_min"],
            "avg_speed_mph": row["avg_speed_mph"],
            "pickup_hour": row["pickup_hour"],
            "pickup_dow": row["pickup_dow"],
            "is_weekend": row["is_weekend"]
        }
        trips.append(trip)
        fare = {
            "trip_id": trip_id,
            "fare_amount": row["fare_amount"],
            "extra": row["extra"],
            "mta_tax": row["mta_tax"],
            "tip_amount": row["tip_amount"],
            "tolls_amount": row["tolls_amount"],
            "improvement_surcharge": row["improvement_surcharge"],
            "congestion_surcharge": row["congestion_surcharge"],
            "total_amount": row["total_amount"],
            "tip_pct": row["tip_pct"]
        }
        fares.append(fare)
        trip_id += 1
    with engine.begin() as connection:
        if trips:
            connection.execute(insert(Trip), trips)
        if fares:
            connection.execute(insert(TripFare), fares)

    loaded_rows += len(rows)
    print(f"Loaded {loaded_rows:,} rows into trips and trip_fares tables")
print("All trips have been loaded")







    


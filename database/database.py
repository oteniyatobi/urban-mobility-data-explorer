import os
import pandas as pd
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
ZONE_LOOKUP = "data/raw/taxi_zone_lookup.csv"

#helper function to solve the problem of Mysql rejecting pandas NaN
def nan_none(value):
    return None if pd.isna(value) else value

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
    borough = Column(String(50), index=True)
    zone_name = Column(String(250))
    service_zone = Column(String(50))

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
Base.metadata.create_all(engine)
print("Db tables created successfully")

parquet = pq.ParquetFile(PARQUET_FILE)



#prepare the vendors

vendor_names = {
    1: "Creative Mobile Technologies",
    2: "VeriFone Inc.",
    4: "Unknown",
    6: "Myle Technologies",
}

vendors = [{"vendor_id": k, "name": v} for k, v in vendor_names.items()]

#prepare the fare rates

rate_descriptions = {
    1: "Standard rate",
    2: "JFK airport rate",
    3: "Newark airport rate",
    4: "Nassau or Westchester rate",
    5: "Negotiated fare",
    6: "Group ride",
    99: "Unknown rate"
}

fare_rates =  [{"rate_id": k, "description": v} for k, v in rate_descriptions.items()]

#prepare payment types

payment_descriptions = {
    1 : "Credit card",
    2 : "Cash",
    3 : "No charge",
    4 : "Dispute",
    5 : "Unknown",
    6: "Voided trip"

}
payment_types = [{"payment_type_id": k, "description": v} for k, v in payment_descriptions.items()]
#prepare taxi zones from the official lookup csv file

zones_df = pd.read_csv(ZONE_LOOKUP)

zones = []

zones = [
    {
        "location_id": int(r.LocationID),
        "borough": nan_none(r.Borough),
        "zone_name": nan_none(r.Zone),
        "service_zone": nan_none(r.service_zone),
        }
    for r in zones_df.itertuples(index=False)
]


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
for batch in parquet.iter_batches(batch_size=5000):
    trips = []
    fares = []
    rows = batch.to_pylist()
    for row in rows:
        trip = {
            "trip_id": trip_id,
            "vendor_id": nan_none(row["VendorID"]),
            "rate_id": nan_none(row["RatecodeID"]),
            "payment_type_id": nan_none(row["payment_type"]),
            "pickup_location_id": nan_none(row["PULocationID"]),
            "dropoff_location_id": nan_none(row["DOLocationID"]),
            "pickup_datetime": nan_none(row["tpep_pickup_datetime"]),
            "dropoff_datetime": nan_none(row["tpep_dropoff_datetime"]),
            "passenger_count": nan_none(row["passenger_count"]),
            "trip_distance": nan_none(row["trip_distance"]),
            "store_and_fwd_flag": nan_none(row["store_and_fwd_flag"]),
            "trip_duration_min": nan_none(row["trip_duration_min"]),
            "avg_speed_mph": nan_none(row["avg_speed_mph"]),
            "pickup_hour": nan_none(row["pickup_hour"]),
            "pickup_dow": nan_none(row["pickup_dow"]),
            "is_weekend": nan_none(row["is_weekend"])
        }
        trips.append(trip)
        fare = {
            "trip_id": trip_id,
            "fare_amount": nan_none(row["fare_amount"]),
            "extra": nan_none(row["extra"]),
            "mta_tax": nan_none(row["mta_tax"]),
            "tip_amount": nan_none(row["tip_amount"]),
            "tolls_amount": nan_none(row["tolls_amount"]),
            "improvement_surcharge": nan_none(row["improvement_surcharge"]),
            "congestion_surcharge": nan_none(row["congestion_surcharge"]),
            "total_amount": nan_none(row["total_amount"]),
            "tip_pct": nan_none(row["tip_pct"])
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







    


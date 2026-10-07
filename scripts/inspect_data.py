import pandas as pd
import geopandas as gpd

RAW_TRIPS = "data/raw/yellow_tripdata_2019-01.parquet" # converted the .csv to . parquet for easier processing.
RAW_ZONES = "data/raw/taxi_zone_lookup.csv"
RAW_GEO = "data/processed/taxi_zones.geojson"

trips = pd. read_parquet(RAW_TRIPS)
print("SHAPE:", trips.shape)
print("DTYPES:\n", trips.dtypes)
print("NULLS:\n", trips.isnull().sum())
print("DUPES:\n", trips.duplicated().sum())
print("TIME RANGE:", trips.tpep_pickup_datetime.min(), trips.tpep_pickup_datetime.max())
print("DISTANCE:", trips.trip_distance.describe())
print("FARE:", trips.fare_amount.describe())

zones = pd.read_csv(RAW_ZONES)
print("\nZONES SHAPE:", zones.shape)
print("ZONES NULLS:\n", zones.isnull().sum())

gdf = gpd.read_file(RAW_GEO)
print("\nGEO FEATURES:", len(gdf))
print("GEO CRS:", gdf.crs)
print("GEO COLUMNS:", gdf.columns.tolist())
print("LOCATIONID RANGE:", gdf["LocationID"].min(), gdf["LocationID"].max())
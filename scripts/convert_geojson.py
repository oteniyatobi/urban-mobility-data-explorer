# A one time conversion: TLC shapefile bundle to GeoJSON
#RUN ONLY ONCE!!!!!!!!
import geopandas as gpd

SRC = "data/raw/taxi_zones/taxi_zones.shp"
DEST = "data/processed/taxi_zones.geojson"

gdf = gpd.read_file(SRC).to_crs(4326)
gdf.to_file(DEST, driver="GeoJSON")

print(f"Wrote {len(gdf)} features - {DEST}")
print("Columns:", gdf.columns.tolist())
print("LocationID range:", gdf["LocationID"].min(), "-", gdf["LocationID"].max())

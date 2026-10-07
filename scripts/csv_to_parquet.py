"""
convert yellow_tripdata_2019-01.csv
to parquet for easier and faster processing
"""
import pandas as pd

df = pd.read_csv("data/raw/yellow_tripdata_2019-01.csv")
df.to_parquet("data/raw/yellow_tripdata_2019-01.parquet", engine="pyarrow", index=False)


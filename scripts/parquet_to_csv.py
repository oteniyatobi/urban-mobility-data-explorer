#convaerting the clean parquet file to csv
import pandas as pd
df = pd.read_parquet("data/processed/cleaned_trips.parquet")
df.to_csv("data/processed/cleaned_trips.csv", index=False)
print("Parquet converted to Csv successfully")

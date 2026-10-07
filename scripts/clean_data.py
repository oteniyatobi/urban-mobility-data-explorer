"""
Now onto cleaning the data from 
yellow_tripdata_2019-01.
log it into audited and processed.

"""

import csv
import os
import pandas as pd

RAW_TRIPS = "data/raw/yellow_tripdata_2019-01.parquet"
OUT_TRIPS = "data/processed/cleaned_trips.parquet"
AUDIT_CSV = "data/audit/cleaning_log.csv"

cleaning_log = []

def _reject(df, condition, rule, reason):
    rows_removed = int(condition.sum())
    if rows_removed:
        cleaning_log.append({"rule": rule, "reason": reason, "rows_removed": rows_removed})
        print(f"{rule:5} {rows_removed:>10,} rows ({reason})")
    return df[~condition].copy()


def remove_null_values(df):
    # remove rows with missing vaklues in critical columns
    df = _reject(df, df["passenger_count"].isnull(), "R2.g", "passenger_count NULL")
    df = _reject(df, df["RatecodeID"].isnull(), "R2.l", "RatecodeID NULL")
    df = _reject(df, df["payment_type"].isnull(), "R2.m", "payment_type NULL")

    return df


def remove_duplicates(df):
    # remove duplicated records/rows
    original_count = len(df)
    df = df.drop_duplicates().copy()
    rows_removed = original_count - len(df)
    if rows_removed > 0:
        cleaning_log.append({"rule": "DUP", "reason": "duplicate rows", "rows_removed": rows_removed})
        print(f"DUP {rows_removed:>10,} rows (duplicate)")

    return df


def validate_trip_times(df):
    # remove invalid dates and durations

    january_start = pd.Timestamp("2019-01-01")
    february_start = pd.Timestamp("2019-02-01")


    df = _reject(df, (df["tpep_pickup_datetime"] < january_start) | (df["tpep_pickup_datetime"] >= february_start), "R2.a", "pickup outside Jan 2019")
    df = _reject(df, df["tpep_dropoff_datetime"] <= df["tpep_pickup_datetime"], "R2.b", "dropoff <= pickup")

    #trips should be less than 24hrs
    duration_hours = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 3600
    df = _reject(df, duration_hours > 24, "R2.c", "duration > 24h")

    return df


def remove_outliers(df):
    #remove illogical values of fare, distance
    df = _reject(df, (df["trip_distance"] <= 0) | (df["trip_distance"] > 100), "R2.d", "distance <= 0 or > 100")
    df = _reject(df, df["fare_amount"] < 0, "R2.e", "negative fare")

    df = _reject(df, df["fare_amount"] > 500, "R2.r", "fare > $500")
    df = _reject(df, df["tip_amount"] > df["total_amount"], "R2.n", "tip > total")

    df = _reject(df, df["tip_pct"] > 1, "R2.s", "tip > fare")
    df = _reject(df, df["avg_speed_mph"] > 80, "R2.t", "speed > 80 mph")

    return df


def add_derived_features(df):
    # add useful features for trip analysis
    #minutes
    minutes_taken = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
    df["trip_duration_min"] = minutes_taken

    #avg speed
    df["avg_speed_mph"] = (df["trip_distance"] / (minutes_taken / 60)).replace([float("inf")], 0)

    #tip ratio
    df["tip_pct"] = (df["tip_amount"] / df["fare_amount"].replace(0, pd.NA)).fillna(0)

    #pickup hour
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
    #weekday
    df["pickup_dow"] = df["tpep_pickup_datetime"].dt.weekday
    #weekend
    df["is_weekend"] = df["pickup_dow"] >= 5

    return df


def main():
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/audit", exist_ok=True)

    print(f"Loading {RAW_TRIPS} ...")
    df = pd.read_parquet(RAW_TRIPS)
    raw_count = len(df)
    print(f" raw: {raw_count:,}")

    print("\nAdding derived features:")
    df = add_derived_features(df)
    print(" trip_duration_min, avg_speed_mph, tip_pct, pickup_hour, pickup_dow, is_weekend")


    print("\nCleaning:")
    df = remove_null_values(df)
    df = remove_duplicates(df)
    df = validate_trip_times(df)
    #df = add_derived_features(df)
    df = remove_outliers(df)

    

    final_count = len(df)
    removed = raw_count - final_count
    pct = removed / raw_count * 100

    print(f"\n final: {final_count:,} (removed {removed:,} = {pct:.2f}%)")
    df.to_parquet(OUT_TRIPS, index=False)
    print(f" saved - {OUT_TRIPS}")

    with open(AUDIT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rule", "reason", "rows_removed"])
        writer.writeheader()
        writer.writerows(cleaning_log)
    print(f" audit - {AUDIT_CSV}")


if __name__ == "__main__":
    main()


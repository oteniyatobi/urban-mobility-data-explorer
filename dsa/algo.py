#Algorithm for finding the busiest vendor
import time

def find_busiest_vendor(vendor_ids):
    start = time.time()
    counts = {}

    for vendor_id in vendor_ids:
        if vendor_id in counts:
            counts[vendor_id] = counts[vendor_id] + 1
        else:
            counts[vendor_id] = 1

    busiest_vendor = None
    most_trips = 0
    for vendor_id in counts:
        if counts[vendor_id] > most_trips:
            most_trips = counts[vendor_id]
            busiest_vendor = vendor_id
    seconds = time.perf_counter() - start

    return{
        "busiest_vendor": busiest_vendor,
        "trips": most_trips,
        "all_counts": counts,
        "time_seconds": seconds
    }

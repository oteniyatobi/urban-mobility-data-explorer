import random
import time
from dsa.algo import find_busiest_vendor

VENDORS = [1,2,4,6]

def create_fake_data(n):
    data = []
    for i in range (n):
        data.append(random.choice(VENDORS))
    return data
def time_algorithm(data):
    start = time.perf_counter()
    find_busiest_vendor(data)
    end = time.perf_counter()
    return end - start
def run_testing(doublings=6, base=10000, repeats=3):
    results = []
    previous_time = None
    n = base

    for step in range(doublings):
        data = create_fake_data(n)
        best_time = time_algorithm(data)
        for r in range(repeats - 1):
            t = time_algorithm(data)
            if t < best_time:
                best_time = t
        if previous_time is None:
            ratio = None
        else:
            ratio = best_time / previous_time
        results.append({
            "n": n,
            "time_seconds": best_time,
            "time_per_item_us": best_time / n * 1000000,
            "ratio": ratio
        })

        previous_time = best_time
        n = n * 2
    return results
if __name__ == '__main__':
    print("n, time_seconds, time_per_item_us, ratio")
    for row in run_testing(8):
        print(row["n"], row["time_seconds"], row["time_per_item_us"], row["ratio"])


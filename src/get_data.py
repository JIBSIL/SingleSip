import requests
import pandas as pd
import json
import requests
import iso8601
import os

def load_data(file):
    dict = json.load(open(file))
    print(f'{len(dict["stats"])} datapoints were returned')
    return dict["stats"]


def get_data(ticker, apikey):
    # make data folder
    if not os.path.exists("data"):
        os.makedirs("data")
    # test if data.json exists
    try:
        jsondata = load_data(f"data/{ticker}.json")
        return jsondata
    except:
        print(f"Data for {ticker} not found. Fetching from CoinAPI...")
        pass

    # datapoints from https://coinapi.io
    apiurl = f"https://rest.coinapi.io/v1/exchangerate/{ticker}/USD/history"

    req = requests.get(
        apiurl,
        params={"period_id": "4HRS", "limit": 100000},
        headers={"X-CoinAPI-Key": apikey},
    )

    json_rate_raw = req.json()
    # prune bad data
    json_rate = []
    for eachdata in json_rate_raw:
        if eachdata["rate_open"] != 0:
            json_rate.append(eachdata)
    oldest_data = json_rate[-1]
    print(
        f'Oldest data that we have on {ticker} is {oldest_data["time_period_start"]}. Price is {oldest_data["rate_close"]}. Newest data is {json_rate[0]["time_period_start"]}'
    )
    stats = []
    # i = 0
    for item in json_rate:
        # for some reason i have to modify time to make it pandas compatible
        time = f'{item["time_close"].split(".")[0]}Z'
        timestamp = int(iso8601.parse_date(time).timestamp() * 1000)
        individual = [timestamp, item["rate_close"]]
        stats.append(individual)

    stats.reverse()
    print(f"{len(stats)} datapoints were returned")

    print(f"Saving data/{ticker}.json")
    with open(f"data/{ticker}.json", "w") as file:
        json.dump({"stats": stats}, file)

    return stats

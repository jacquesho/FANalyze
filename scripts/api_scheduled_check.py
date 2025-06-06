import os
import sys
import json
import requests
import argparse
import pandas as pd
from datetime import datetime

SETLISTFM_API_KEY = os.getenv("uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT")
HEADERS = {"Accept": "application/json", "x-api-key": SETLISTFM_API_KEY}

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", required=True)
parser.add_argument("--start_date", required=True)
parser.add_argument("--end_date", required=True)
parser.add_argument("--show_prefix", default="Update_")
parser.add_argument("--setlist_prefix", default="Update_")
args = parser.parse_args()

start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

band_list = [
    {"artist_id": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab", "artist_name": "Metallica"}
]

all_shows = []

for band in band_list:
    artist_id = band["artist_id"]
    artist_name = band["artist_name"]
    print(
        f"🗖️ Fetching shows for {artist_name} ({artist_id}) between {start_date.date()} and {end_date.date()}"
    )

    page = 1
    while True:
        url = f"https://api.setlist.fm/rest/1.0/artist/{artist_id}/setlists?p={page}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(
                f"⚠️ Error fetching page {page} for {artist_name}: {response.status_code}"
            )
            break

        data = response.json()
        setlist_items = data.get("setlist", [])

        if not setlist_items:
            break

        for show in setlist_items:
            event_date = datetime.strptime(show["eventDate"], "%d-%m-%Y")
            if start_date <= event_date <= end_date:
                all_shows.append(show)

        if page >= int(data.get("@totalPages", 1)):
            break

        page += 1

if all_shows:
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    df = pd.json_normalize(all_shows)
    csv_path = os.path.join(outdir, f"{args.show_prefix}shows.csv")
    df.to_csv(csv_path, index=False)
    print(f"✅ Wrote CSV to: {csv_path}")

    json_path = os.path.join(outdir, f"{args.setlist_prefix}setlists.json")
    with open(json_path, "w") as f:
        json.dump(all_shows, f)
    print(f"✅ Wrote JSON to: {json_path}")
else:
    print("⚠️ No shows found in the given date range.")

import os
import requests
import time
import json
import argparse
from datetime import datetime

API_KEY = "uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT"
HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "User-Agen": "Fanalyze/1.0 (jacquesho@gmail.com)",
}

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", required=True)
args = parser.parse_args()

OUTDIR = args.outdir  # ✅ Use the value passed from the DAG


def fetch_artist(artist_id, artist_name):
    all_shows = []
    page = 1
    while True:
        url = f"https://api.setlist.fm/rest/1.0/artist/{artist_id}/setlists?p={page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(
                f"Error fetching page {page} for {artist_name}: {response.status_code}"
            )
            break

        data = response.json()
        setlists = data.get("setlist", [])
        if not setlists:
            break

        for s in setlists:
            try:
                event_date = datetime.strptime(s["eventDate"], "%d-%m-%Y")

                if event_date < START_DATE or event_date > END_DATE:
                    continue

                s["load_type"] = "historical"  # ✅ Add tagging here
                all_shows.append(s)

            except Exception as e:
                print(f"Skipping show: {e}")
                continue

        page += 1
        time.sleep(1.1)

    print(f"{artist_name}: {len(all_shows)} shows collected.")
    return all_shows


def main():
    band_list = [{"artist_id": "some-id", "artist_name": "Metallica"}]

    for band in band_list:
        result = fetch_artist(band["artist_id"], band["artist_name"])
        os.makedirs(OUTDIR, exist_ok=True)
        out_path = os.path.join(
            OUTDIR, f"{band['artist_name'].replace(' ', '_')}_setlists.json"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()

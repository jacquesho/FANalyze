import requests
import csv
import os
import time
import json
import random
from datetime import datetime

API_KEY = "uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT"
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

ARTISTS = {
    "Metallica": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
    #    "Bloodywood": "4e478f4f-a1e5-4ac9-84a3-f58f5c6454ab",
    #    "Arch Enemy": "e631bb92-3e2b-43e3-a2cb-b605e2fb53bd",
    #    "Linkin Park": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
    #    "Disturbed": "4bb4e4e4-5f66-4509-98af-62dbb90c45c5",
    #    "The Warning": "7f625f35-7e53-4f08-9201-16643979484b",
    #    "Halestorm": "eaed2193-e026-493b-ac57-113360407b06",
    #    "Nita Strauss": "e73db0bc-22eb-4589-9c6b-f35ad14f5647",
    #    "Mammoth WVH": "49a6efb9-9b52-44ce-8167-7cb1c21a8c45",
    #    "Iron Maiden": "ca891d65-d9b0-4258-89f7-e6ba29d83767",
}

CUTOFF_DATE = datetime.now().replace(year=datetime.now().year - 3)
OUTPUT_JSON = "all_band_setlists.json"

# Start clean
if os.path.exists(OUTPUT_JSON):
    os.remove(OUTPUT_JSON)

all_setlists = []


def determine_ticket_tier(country, venue_name):
    country = country.lower()
    venue = venue_name.lower()

    if any(
        x in country
        for x in [
            "united states",
            "germany",
            "france",
            "japan",
            "australia",
            "canada",
            "uk",
        ]
    ):
        return "Tier 1"
    elif any(
        x in country
        for x in ["brazil", "mexico", "argentina", "czech", "poland", "romania"]
    ):
        return "Tier 2"
    else:
        return "Tier 3"


def simulate_ticket_price(tier):
    if tier == "Tier 1":
        return round(random.uniform(90, 150), 2)
    elif tier == "Tier 2":
        return round(random.uniform(60, 100), 2)
    else:
        return round(random.uniform(30, 70), 2)


def fetch_shows_and_setlists(artist_name, mbid):
    print(f"\n🎸 Fetching up to 25 shows for {artist_name}...")
    shows = []
    page = 1
    rows = []

    while len(shows) < 25:
        url = f"https://api.setlist.fm/rest/1.0/artist/{mbid}/setlists?p={page}"
        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            print(f"❌ Error fetching page {page} for {artist_name}: {res.status_code}")
            break

        data = res.json()
        if not data.get("setlist"):
            break

        for s in data["setlist"]:
            try:
                event_date_str = s["eventDate"]
                event_date = datetime.strptime(event_date_str, "%d-%m-%Y")
                if event_date < CUTOFF_DATE:
                    continue

                iso_date = event_date.strftime("%Y-%m-%d")

                venue = s["venue"]["name"]
                city = s["venue"]["city"]["name"]
                country = s["venue"]["city"]["country"]["name"]
                tour = s.get("tour", {}).get("name", "No Tour Info")
                setlist_id = s["id"]

                tier = determine_ticket_tier(country, venue)
                price = simulate_ticket_price(tier)

                rows.append(
                    [
                        mbid,
                        artist_name,
                        iso_date,
                        setlist_id,
                        venue,
                        city,
                        country,
                        tour,
                        tier,
                        price,
                    ]
                )

                # Fetch full setlist JSON
                json_url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
                json_res = requests.get(json_url, headers=HEADERS)
                if json_res.status_code == 200:
                    setlist_json = json_res.json()
                    setlist_json["band"] = artist_name
                    all_setlists.append(setlist_json)
                else:
                    print(
                        f"  ⚠️ Could not fetch full setlist for {setlist_id} ({json_res.status_code})"
                    )

                if len(shows) >= 25:
                    break
                shows.append(setlist_id)
            except Exception as e:
                print(f"  ⚠️ Skipping show due to error: {e}")

        page += 1
        time.sleep(1.2)

    filename = f"show_{artist_name.lower().replace(' ', '_')}_data.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "artist_id",
                "artist_name",
                "date",
                "setlist_id",
                "venue",
                "city",
                "country",
                "tour_name",
                "ticket_tier",
                "simulated_price_usd",
            ]
        )
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} rows to {filename}")


# Run fetch loop
for band, mbid in ARTISTS.items():
    fetch_shows_and_setlists(band, mbid)
    time.sleep(1.5)

# Save merged setlist JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
    json.dump(all_setlists, jf, ensure_ascii=False, indent=2)

print(f"\n✅ Combined setlist JSON saved at: {os.path.abspath(OUTPUT_JSON)}")

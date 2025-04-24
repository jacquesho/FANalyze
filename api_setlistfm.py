import requests
import csv
import os
import time
import json
import random
from datetime import datetime

API_KEY = "uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT"
HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json"
}

ARTISTS = {
    "Metallica": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
    "Bloodywood": "4e478f4f-a1e5-4ac9-84a3-f58f5c6454ab",
    "Arch Enemy": "e631bb92-3e2b-43e3-a2cb-b605e2fb53bd",
    "Linkin Park": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
    "Disturbed": "4bb4e4e4-5f66-4509-98af-62dbb90c45c5",
    "The Warning": "7f625f35-7e53-4f08-9201-16643979484b",
    "Halestorm": "eaed2193-e026-493b-ac57-113360407b06",
    "Nita Strauss": "e73db0bc-22eb-4589-9c6b-f35ad14f5647",
    "Mammoth WVH": "49a6efb9-9b52-44ce-8167-7cb1c21a8c45",
    "Iron Maiden": "ca891d65-d9b0-4258-89f7-e6ba29d83767"
}

CUTOFF_DATE = datetime.now().replace(year=datetime.now().year - 3)
OUTPUT_CSV = "all_band_tour_data.csv"
OUTPUT_JSON = "all_band_setlists.json"

# Start clean
if os.path.exists(OUTPUT_CSV):
    os.remove(OUTPUT_CSV)
if os.path.exists(OUTPUT_JSON):
    os.remove(OUTPUT_JSON)

all_setlists = []
csv_rows = []

def determine_ticket_tier(country, venue_name):
    country = country.lower()
    venue = venue_name.lower()

    if any(x in country for x in ['united states', 'germany', 'france', 'japan', 'australia', 'canada', 'uk']):
        return 'Tier 1'
    elif any(x in country for x in ['brazil', 'mexico', 'argentina', 'czech', 'poland', 'romania']):
        return 'Tier 2'
    else:
        return 'Tier 3'

def simulate_ticket_price(tier):
    if tier == 'Tier 1':
        return round(random.uniform(90, 150), 2)
    elif tier == 'Tier 2':
        return round(random.uniform(60, 100), 2)
    else:
        return round(random.uniform(30, 70), 2)

def fetch_shows_and_setlists(artist_name, mbid):
    print(f"\n🎸 Fetching up to 25 shows for {artist_name}...")
    shows = []
    page = 1

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

                venue = s["venue"]["name"]
                city = s["venue"]["city"]["name"]
                country = s["venue"]["city"]["country"]["name"]
                tour = s.get("tour", {}).get("name", "No Tour Info")
                setlist_id = s["id"]

                tier = determine_ticket_tier(country, venue)
                price = simulate_ticket_price(tier)

                csv_rows.append([
                    artist_name, event_date_str, venue, city, country,
                    tour, setlist_id, tier, price
                ])

                # Fetch full setlist JSON
                json_url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
                json_res = requests.get(json_url, headers=HEADERS)
                if json_res.status_code == 200:
                    setlist_json = json_res.json()
                    setlist_json['band'] = artist_name  # attach band name
                    all_setlists.append(setlist_json)
                else:
                    print(f"  ⚠️ Could not fetch full setlist for {setlist_id} ({json_res.status_code})")

                if len(shows) >= 25:
                    break
                shows.append(setlist_id)
            except Exception as e:
                print(f"  ⚠️ Skipping show due to error: {e}")

        page += 1
        time.sleep(1.2)

# Header once at the start
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Band", "Event Date", "Venue", "City", "Country",
        "Tour Name", "Setlist ID", "Ticket Tier", "Simulated Price (USD)"
    ])

# Loop through all bands
for band, mbid in ARTISTS.items():
    fetch_shows_and_setlists(band, mbid)
    time.sleep(1.5)

# Write all rows to CSV
with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

# Save merged setlist JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
    json.dump(all_setlists, jf, ensure_ascii=False, indent=2)

print(f"\n✅ Combined show CSV saved at: {os.path.abspath(OUTPUT_CSV)}")
print(f"✅ Combined setlist JSON saved at: {os.path.abspath(OUTPUT_JSON)}")

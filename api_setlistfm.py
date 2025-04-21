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
    "Disturbed": "4bb4e4e4-5f66-4509-98af-62dbb90c45c5"
}

CUTOFF_DATE = datetime.now().replace(year=datetime.now().year - 3)
SETLIST_DIR = "setlists_json"
os.makedirs(SETLIST_DIR, exist_ok=True)

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

def fetch_shows_and_save_json(artist_name, mbid):
    print(f"\n📡 Fetching up to 25 shows for {artist_name}...")
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

                shows.append([
                    event_date_str, venue, city, country, tour, setlist_id, tier, price
                ])

                # Save setlist JSON
                json_url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
                json_res = requests.get(json_url, headers=HEADERS)
                if json_res.status_code == 200:
                    filepath = os.path.join(SETLIST_DIR, f"{artist_name.lower().replace(' ', '_')}_{setlist_id}.json")
                    with open(filepath, "w", encoding="utf-8") as jf:
                        json.dump(json_res.json(), jf, ensure_ascii=False, indent=2)
                else:
                    print(f"  ⚠️ Failed setlist for {setlist_id} ({json_res.status_code})")

                if len(shows) >= 25:
                    break

            except Exception as e:
                print(f"  ⚠️ Skipping show due to error: {e}")

        page += 1
        time.sleep(1.2)

    if shows:
        shows.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y"), reverse=True)

        filename = f"{artist_name.lower().replace(' ', '_')}_tour_data.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Event Date", "Venue", "City", "Country", "Tour Name",
                "Setlist ID", "Ticket Tier", "Simulated Price (USD)"
            ])
            writer.writerows(shows)

        print(f"✅ Saved {len(shows)} shows to {filename}")
        print(f"📁 Path: {os.path.abspath(filename)}")
    else:
        print(f"⚠️ No recent shows found for {artist_name}")

# Run it!
for artist, mbid in ARTISTS.items():
    fetch_shows_and_save_json(artist, mbid)
    time.sleep(1.5)

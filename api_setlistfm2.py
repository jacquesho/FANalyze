import csv
import time
import requests
from datetime import datetime

# --- Embedded config ---
HEADERS = {
    "x-api-key": "uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT",
    "Accept": "application/json",
}
CUTOFF_DATE = datetime(2022, 1, 1)


# --- Inlined utility functions ---
def determine_ticket_tier(country, venue):
    if "stadium" in venue.lower() or country.lower() in ["us", "uk", "germany"]:
        return "premium"
    elif "arena" in venue.lower():
        return "mid"
    else:
        return "budget"


def simulate_ticket_price(tier):
    return {"premium": 125, "mid": 85, "budget": 45}.get(tier, 50)


def fetch_artist_shows(artist_name, mbid):
    print(f"\n🎸 Fetching 25 recent shows for {artist_name}...")
    collected = []
    page = 1

    while len(collected) < 25:
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

                iso_date = event_date.strftime("%Y-%m-%d")  # Cleaned date ✅

                venue = s["venue"]["name"]
                city = s["venue"]["city"]["name"]
                country = s["venue"]["city"]["country"]["name"]
                tour = s.get("tour", {}).get("name", "No Tour Info")
                setlist_id = s["id"]
                tier = determine_ticket_tier(country, venue)
                price = simulate_ticket_price(tier)

                collected.append(
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

                if len(collected) >= 25:
                    break
            except Exception as e:
                print(f"⚠️ Error processing event: {e}")
                continue

        page += 1
        time.sleep(1.2)

    if collected:
        filename = f"data_{artist_name.lower().replace(' ', '_')}_shows.csv"
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
            writer.writerows(collected)
        print(f"✅ Saved {len(collected)} shows to {filename}")
    else:
        print(f"⚠️ No recent shows found for {artist_name}")

if __name__ == "__main__":
    # Example call — update these with real artist/MBID combos
    fetch_artist_shows("Metallica", "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab")

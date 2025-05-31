import requests
import csv
import os
import time
import json
import random
import argparse
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", default=None, help="override output folder")
args = parser.parse_args()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DEFAULT_DIR = BASE_DIR / "models" / "01_staging" / "setlistfm_data"
STAGING_DIR = Path(args.outdir) if args.outdir else DEFAULT_DIR
STAGING_DIR.mkdir(parents=True, exist_ok=True)


# ── API config ─────────────────────────────────────────────────────────────────
API_KEY = "uIfQdN5pj3x-tVhY8I617-lLPz9XmX9pW3tT"
HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    # "Accept-Language": "vi",       # uncomment if you want VN localisation
}

# Artist Name : MusicBrainz ID
ARTISTS = {
    "Metallica": "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
    # "Guns N' Roses": "eeb1195b-f213-4ce1-b28c-8565211f8e43",
    # "Billie Eilish": "f4abc0b5-3f7a-4eff-8f78-ac078dbce533",
    # "Coldplay": "cc197bad-dc9c-440d-a5b5-d52ba2e14234",
    # "The Weeknd": "c8b03190-306c-4120-bb0b-6f2ebfc06ea9",
    #    "Nita Strauss": "e73db0bc-22eb-4589-9c6b-f35ad14f5647",
    #    "Steve Vai": '5e7ccd92-6277-451a-aab9-1efd587c50f3',
    #    "Bloodywood": "4e478f4f-a1e5-4ac9-84a3-f58f5c6454ab",
    #    "Arch Enemy": "e631bb92-3e2b-43e3-a2cb-b605e2fb53bd",
    #    "Linkin Park": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
    #    "Disturbed": "4bb4e4e4-5f66-4509-98af-62dbb90c45c5",
    #    "The Warning": "7f625f35-7e53-4f08-9201-16643979484b",
    #    "Halestorm": "eaed2193-e026-493b-ac57-113360407b06",
    #    "Mammoth WVH": "49a6efb9-9b52-44ce-8167-7cb1c21a8c45",
    #    "Iron Maiden": "ca891d65-d9b0-4258-89f7-e6ba29d83767",
}

CUTOFF_DATE = datetime.now().replace(year=datetime.now().year - 3)
OUTPUT_JSON = STAGING_DIR / "all_band_setlists.json"
all_setlists: list[dict] = []


# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_get(url: str, headers: dict, max_retries: int = 3, pause: float = 1.0):
    """GET with simple exponential back-off for 429/5xx."""
    for attempt in range(max_retries):
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code not in (429, 500, 502, 503, 504):
            return res
        sleep_for = pause * (2**attempt)
        print(f"  ↻  {res.status_code} – sleeping {sleep_for:.1f}s then retrying …")
        time.sleep(sleep_for)
    return res  # last response (may be error)


def determine_ticket_tier(country: str):
    t1 = {"united states", "germany", "france", "japan", "australia", "canada", "uk"}
    t2 = {"brazil", "mexico", "argentina", "czech", "poland", "romania"}
    country = country.lower()
    if country in t1:
        return "Tier 1"
    if country in t2:
        return "Tier 2"
    return "Tier 3"


def simulate_ticket_price(tier: str) -> float:
    bounds = {"Tier 1": (90, 150), "Tier 2": (60, 100), "Tier 3": (30, 70)}
    lo, hi = bounds[tier]
    return round(random.uniform(lo, hi), 2)


# ── Main fetch loop ────────────────────────────────────────────────────────────
def fetch_artist(artist: str, mbid: str):
    print(f"\n🎸  {artist}: pulling up to 25 recent shows")
    page, seen = 1, 0
    rows = []

    while seen < 25:
        url = f"https://api.setlist.fm/rest/1.0/artist/{mbid}/setlists?p={page}"
        res = safe_get(url, HEADERS)
        if res.status_code != 200:
            print(f"  ❌ page {page}: {res.status_code}")
            break

        data = res.json().get("setlist", [])
        if not data:
            break

        for s in data:
            event_date = datetime.strptime(s["eventDate"], "%d-%m-%Y")
            if event_date < CUTOFF_DATE:
                continue

            iso_date = event_date.strftime("%Y-%m-%d")
            venue = s["venue"]["name"]
            city = s["venue"]["city"]["name"]
            country = s["venue"]["city"]["country"]["name"]
            tour = s.get("tour", {}).get("name", "No Tour Info")
            setlist_id = s["id"]

            tier = determine_ticket_tier(country)
            price = simulate_ticket_price(tier)

            rows.append(
                [
                    mbid,
                    artist,
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

            # full setlist JSON (throttle each request)
            full_url = f"https://api.setlist.fm/rest/1.0/setlist/{setlist_id}"
            json_res = safe_get(full_url, HEADERS)
            if json_res.status_code == 200:
                data = json_res.json()
                data["band"] = artist
                all_setlists.append(data)
            time.sleep(0.5)  # per-request throttle

            seen += 1
            if seen >= 25:
                break
        page += 1
        time.sleep(1.0)  # page throttle

    # write CSV for this artist
    fname = STAGING_DIR / f"{artist.lower().replace(' ', '_')}_shows.csv"
    with fname.open("w", newline="", encoding="utf-8") as f:
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
    print(f"  ✅  Saved {len(rows)} rows → {fname.name}")


# ── Run ────────────────────────────────────────────────────────────────────────
for name, mbid in ARTISTS.items():
    fetch_artist(name, mbid)
    time.sleep(1.5)  # polite gap between artists

# Combined JSON
with OUTPUT_JSON.open("w", encoding="utf-8") as jf:
    json.dump(all_setlists, jf, ensure_ascii=False, indent=2)
print(f"\n✅  Combined setlists → {OUTPUT_JSON.relative_to(BASE_DIR)}")

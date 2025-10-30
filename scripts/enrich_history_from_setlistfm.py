#!/usr/bin/env python3
"""
Enrich Setlist.fm historical shows CSV with synthetic ticket metrics in-place.

Input:  data/raw/csv/shows_history.csv  (columns through COUNTRY_NAME from API)
Output: data/raw/csv/shows_history.csv  (same rows, extra ticket/derived columns)

Adds/derives per row (no new rows):
  - VENUE_TYPE, VENUE_CAPACITY, MARKET_SIZE, ARTIST_TIER
  - TICKETS_SOLD, SELLOUT_STATUS, ATTENDANCE_RATE
  - AVERAGE_TICKET_PRICE, TICKET_PRICE_RANGE, REVENUE
  - EVENT_DATE_STR, LAST_UPDATED, INGESTED_AT

Usage:
  uv run python scripts/enrich_history_from_setlistfm.py \
      --input data/raw/csv/shows_history.csv [--backup]
"""

import argparse
import os
import random
from datetime import datetime

import numpy as np
import pandas as pd


MAJOR_CITIES = {
    'new york', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia',
    'san antonio', 'san diego', 'dallas', 'san jose', 'austin', 'jacksonville',
    'columbus', 'charlotte', 'san francisco', 'indianapolis', 'seattle', 'denver',
    'washington', 'boston', 'nashville', 'detroit', 'portland', 'las vegas',
    'memphis', 'baltimore', 'milwaukee', 'kansas city', 'atlanta', 'miami',
}

ARTIST_TIER_MAP = {
    'Taylor Swift': 'A-list',
    'Beyoncé': 'A-list',
    'Metallica': 'A-list',
    'Ed Sheeran': 'A-list',
    'Bruno Mars': 'A-list',
    'Coldplay': 'A-list',
    'The Weeknd': 'A-list',
}

# Base price by (tier, venue type)
BASE_PRICE = {
    'A-list': {
        'Stadium': 200, 'Arena': 150, 'Theater': 120, 'Club': 100, 'Amphitheater': 140, 'Other': 110
    },
    'B-list': {
        'Stadium': 120, 'Arena': 90, 'Theater': 70, 'Club': 50, 'Amphitheater': 80, 'Other': 75
    }
}


def categorize_venue_type(venue_name: str) -> str:
    if pd.isna(venue_name) or venue_name == '':
        return 'Other'
    v = str(venue_name).lower()
    if any(k in v for k in ['stadium', 'field', 'dome', 'coliseum']):
        return 'Stadium'
    if any(k in v for k in ['arena', 'center', 'pavilion', 'auditorium']):
        return 'Arena'
    if any(k in v for k in ['theater', 'theatre', 'hall', 'opera']):
        return 'Theater'
    if any(k in v for k in ['club', 'bar', 'lounge', 'cafe']):
        return 'Club'
    if any(k in v for k in ['amphitheater', 'amphitheatre', 'outdoor']):
        return 'Amphitheater'
    return 'Other'


def estimate_capacity(venue_name: str, venue_type: str) -> int:
    if pd.isna(venue_name) or venue_name == '':
        return random.randint(1000, 5000)
    v = str(venue_name).lower()
    if venue_type == 'Stadium':
        if any(k in v for k in ['sofi', 'metlife', 'mercedes-benz', 'hard rock', 'bank of america', 'nissan']):
            return random.randint(60000, 90000)
        return random.randint(30000, 70000)
    if venue_type == 'Arena':
        if any(k in v for k in ['madison square', 'crypto.com', 'chase center', 'td garden', 'united center']):
            return random.randint(15000, 25000)
        return random.randint(8000, 20000)
    if venue_type == 'Theater':
        return random.randint(1000, 5000)
    if venue_type == 'Club':
        return random.randint(200, 1000)
    if venue_type == 'Amphitheater':
        return random.randint(5000, 20000)
    return random.randint(1000, 15000)


def market_size(city_name: str) -> str:
    if pd.isna(city_name) or city_name == '':
        return 'Large'
    return 'Major' if str(city_name).lower() in MAJOR_CITIES else 'Large'


def artist_tier(artist_name: str) -> str:
    return ARTIST_TIER_MAP.get(str(artist_name), 'B-list')


def price_for(tier: str, venue_type: str) -> int:
    base = BASE_PRICE.get(tier, BASE_PRICE['B-list']).get(venue_type, BASE_PRICE['B-list']['Other'])
    return int(base * random.uniform(0.9, 1.15))


def price_range(avg_price: int) -> str:
    lo = max(30, int(avg_price * 0.55))
    hi = int(avg_price * 2.0)
    return f"${lo}-${hi}"


def attendance_and_sold(capacity: int, tier: str) -> tuple[int, float, bool]:
    # Historical attendance skewed high for A-list
    if tier == 'A-list':
        rate = random.uniform(0.78, 0.98)
    else:
        rate = random.uniform(0.6, 0.9)
    sold = int(capacity * rate)
    sellout = sold >= capacity * 0.995
    return sold, rate * 100.0, sellout


def enrich_frame(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure expected base columns exist (tolerate varying case by adding normalized accessors)
    # Expected minimal: ARTIST_NAME, SHOW_DATE, VENUE_NAME, CITY_NAME, STATE_CODE, COUNTRY_NAME
    for col in ['ARTIST_NAME', 'SHOW_DATE', 'VENUE_NAME', 'CITY_NAME', 'STATE_CODE', 'COUNTRY_NAME']:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Derivations
    df['VENUE_TYPE'] = df['VENUE_NAME'].apply(categorize_venue_type)
    df['VENUE_CAPACITY'] = df.apply(lambda r: estimate_capacity(r['VENUE_NAME'], r['VENUE_TYPE']), axis=1)
    df['MARKET_SIZE'] = df['CITY_NAME'].apply(market_size)
    df['ARTIST_TIER'] = df['ARTIST_NAME'].apply(artist_tier)

    # Ticket metrics
    tickets_sold, attendance_rate, sellout = [], [], []
    avg_price_list, price_range_list, revenue_list = [], [], []

    for _, row in df.iterrows():
        cap = int(row['VENUE_CAPACITY']) if not pd.isna(row['VENUE_CAPACITY']) else 0
        tier = row['ARTIST_TIER']
        vtype = row['VENUE_TYPE']
        sold, rate_pct, sellout_flag = attendance_and_sold(cap, tier)
        avg_price = price_for(tier, vtype)
        tickets_sold.append(sold)
        attendance_rate.append(round(rate_pct, 1))
        sellout.append('TRUE' if sellout_flag else 'FALSE')
        avg_price_list.append(avg_price)
        price_range_list.append(price_range(avg_price))
        revenue_list.append(sold * avg_price)

    df['TICKETS_SOLD'] = tickets_sold
    df['SELLOUT_STATUS'] = sellout
    df['ATTENDANCE_RATE'] = attendance_rate
    df['AVERAGE_TICKET_PRICE'] = avg_price_list
    df['TICKET_PRICE_RANGE'] = price_range_list
    df['REVENUE'] = revenue_list

    # Dates/metadata
    # SHOW_DATE may be string like M/D/YYYY; preserve a string copy as EVENT_DATE_STR
    df['EVENT_DATE_STR'] = df['SHOW_DATE'].astype(str)
    now_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    df['LAST_UPDATED'] = now_iso
    df['INGESTED_AT'] = now_iso

    # Column ordering (best-effort to match shows_history.csv example)
    preferred = [
        'ARTIST_ID', 'ARTIST_NAME', 'SHOW_ID', 'SHOW_DATE', 'SOURCE',
        'VENUE_NAME', 'VENUE_ID', 'VENUE_TYPE', 'VENUE_CAPACITY',
        'CITY_NAME', 'STATE_CODE', 'COUNTRY_NAME', 'MARKET_SIZE', 'ARTIST_TIER',
        'TICKETS_SOLD', 'SELLOUT_STATUS', 'ATTENDANCE_RATE', 'AVERAGE_TICKET_PRICE',
        'TICKET_PRICE_RANGE', 'REVENUE', 'EVENT_DATE_STR', 'LAST_UPDATED', 'INGESTED_AT'
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    return df[cols]


def main():
    parser = argparse.ArgumentParser(description='Enrich historical shows CSV with synthetic ticket metrics (in-place).')
    parser.add_argument('--input', default='data/raw/csv/shows_history.csv', help='Path to shows_history.csv')
    parser.add_argument('--backup', action='store_true', help='Write a .bak copy before overwriting')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"CSV not found: {args.input}")

    df = pd.read_csv(args.input)

    if args.backup:
        backup_path = args.input + '.bak'
        df.to_csv(backup_path, index=False)

    enriched = enrich_frame(df)
    enriched.to_csv(args.input, index=False)
    print(f"✅ Enriched and overwrote: {args.input}  (rows={len(enriched)})")


if __name__ == '__main__':
    # Deterministic-ish randomness per run
    random.seed(42)
    np.random.seed(42)
    main()



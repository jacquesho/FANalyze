#!/usr/bin/env python3
"""
Update future concerts data by removing BLACKPINK and adding other artists
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducible results
np.random.seed(42)
random.seed(42)

# Artists to add (excluding BLACKPINK, keeping Metallica)
ARTISTS_TO_ADD = [
    "Beyoncé",
    "Bruno Mars",
    "Coldplay",
    "Ed Sheeran",
    "Taylor Swift",
    "The Weeknd",
]

# Venue data with realistic capacities and types
VENUES = [
    {
        "name": "Madison Square Garden",
        "city": "New York",
        "state": "NY",
        "capacity": 20789,
        "type": "Arena",
    },
    {
        "name": "Staples Center",
        "city": "Los Angeles",
        "state": "CA",
        "capacity": 19068,
        "type": "Arena",
    },
    {
        "name": "United Center",
        "city": "Chicago",
        "state": "IL",
        "capacity": 20917,
        "type": "Arena",
    },
    {
        "name": "TD Garden",
        "city": "Boston",
        "state": "MA",
        "capacity": 19156,
        "type": "Arena",
    },
    {
        "name": "Wells Fargo Center",
        "city": "Philadelphia",
        "state": "PA",
        "capacity": 20478,
        "type": "Arena",
    },
    {
        "name": "American Airlines Center",
        "city": "Dallas",
        "state": "TX",
        "capacity": 19200,
        "type": "Arena",
    },
    {
        "name": "Crypto.com Arena",
        "city": "Los Angeles",
        "state": "CA",
        "capacity": 19068,
        "type": "Arena",
    },
    {
        "name": "Barclays Center",
        "city": "Brooklyn",
        "state": "NY",
        "capacity": 17732,
        "type": "Arena",
    },
    {
        "name": "Capital One Arena",
        "city": "Washington",
        "state": "DC",
        "capacity": 20356,
        "type": "Arena",
    },
    {
        "name": "State Farm Arena",
        "city": "Atlanta",
        "state": "GA",
        "capacity": 18047,
        "type": "Arena",
    },
    {
        "name": "Fiserv Forum",
        "city": "Milwaukee",
        "state": "WI",
        "capacity": 17500,
        "type": "Arena",
    },
    {
        "name": "Target Center",
        "city": "Minneapolis",
        "state": "MN",
        "capacity": 19356,
        "type": "Arena",
    },
    {
        "name": "Ball Arena",
        "city": "Denver",
        "state": "CO",
        "capacity": 19520,
        "type": "Arena",
    },
    {
        "name": "Climate Pledge Arena",
        "city": "Seattle",
        "state": "WA",
        "capacity": 18000,
        "type": "Arena",
    },
    {
        "name": "Chase Center",
        "city": "San Francisco",
        "state": "CA",
        "capacity": 18064,
        "type": "Arena",
    },
    {
        "name": "Footprint Center",
        "city": "Phoenix",
        "state": "AZ",
        "capacity": 18055,
        "type": "Arena",
    },
    {
        "name": "Amway Center",
        "city": "Orlando",
        "state": "FL",
        "capacity": 18846,
        "type": "Arena",
    },
    {
        "name": "FTX Arena",
        "city": "Miami",
        "state": "FL",
        "capacity": 19600,
        "type": "Arena",
    },
    {
        "name": "Bridgestone Arena",
        "city": "Nashville",
        "state": "TN",
        "capacity": 19995,
        "type": "Arena",
    },
    {
        "name": "Smoothie King Center",
        "city": "New Orleans",
        "state": "LA",
        "capacity": 16867,
        "type": "Arena",
    },
]

# Artist pricing info
ARTIST_PRICING = {
    "Taylor Swift": {"base_price": 400, "price_range": "$200-$800"},
    "Beyoncé": {"base_price": 350, "price_range": "$150-$700"},
    "Metallica": {"base_price": 300, "price_range": "$100-$600"},
    "Ed Sheeran": {"base_price": 250, "price_range": "$80-$500"},
    "Bruno Mars": {"base_price": 280, "price_range": "$120-$550"},
    "Coldplay": {"base_price": 220, "price_range": "$80-$450"},
    "The Weeknd": {"base_price": 200, "price_range": "$60-$400"},
}


def generate_show_for_artist(artist, venue, show_date):
    """Generate a single show record for an artist"""

    # Calculate days until show
    days_until_show = (show_date - datetime.now()).days

    # Skip if show is in the past
    if days_until_show < 0:
        return None

    # Get pricing info
    pricing = ARTIST_PRICING.get(artist, {"base_price": 200, "price_range": "$50-$400"})

    # Simulate ticket sales based on artist popularity and time until show
    if artist in ["Taylor Swift", "Beyoncé"]:
        base_sales_rate = 0.85
    elif artist in ["Metallica", "Ed Sheeran", "Bruno Mars"]:
        base_sales_rate = 0.75
    else:
        base_sales_rate = 0.65

    # Adjust for time until show
    time_factor = max(0.1, 1.0 - (days_until_show / 365))
    random_factor = random.uniform(0.8, 1.2)
    sales_rate = min(0.95, base_sales_rate * time_factor * random_factor)

    tickets_sold = int(venue["capacity"] * sales_rate)
    revenue = tickets_sold * pricing["base_price"]

    # Generate IDs
    show_id = (
        f"future_{artist.lower().replace(' ', '_')}_{show_date.strftime('%Y%m%d')}"
    )
    venue_id = f"venue_{venue['name'].lower().replace(' ', '_').replace('.', '')}"

    # Determine market size
    market_size = "Major" if venue["capacity"] > 18000 else "Secondary"

    return {
        "artist_name": artist,
        "show_date": show_date.strftime("%Y-%m-%d"),
        "venue_name": venue["name"],
        "city_name": venue["city"],
        "state_code": venue["state"],
        "country_name": "United States",
        "VENUE_TYPE": venue["type"],
        "VENUE_CAPACITY": venue["capacity"],
        "ARTIST_TIER": "A-list",
        "MARKET_SIZE": market_size,
        "TICKETS_SOLD_SO_FAR": tickets_sold,
        "CURRENT_SALES_RATE": round(sales_rate * 100, 1),
        "DAYS_UNTIL_SHOW": days_until_show,
        "AVERAGE_TICKET_PRICE": pricing["base_price"],
        "TICKET_PRICE_RANGE": pricing["price_range"],
        "CURRENT_REVENUE": revenue,
        "source": "simulated",
        "show_id": show_id,
        "venue_id": venue_id,
        "collected_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }


def main():
    """Update future concerts data"""
    print("🎵 Updating future concerts data...")

    # Read existing data
    existing_file = "data/raw/csv/shows_future.csv"
    df_existing = pd.read_csv(existing_file)

    print(f"📊 Original data: {len(df_existing)} shows")
    print(
        f"🎤 Original artists: {', '.join(sorted(df_existing['artist_name'].unique()))}"
    )

    # Filter out BLACKPINK, keep Metallica
    df_filtered = df_existing[df_existing["artist_name"] != "BLACKPINK"].copy()
    print(f"📊 After removing BLACKPINK: {len(df_filtered)} shows")

    # Generate new shows for other artists
    new_shows = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 12, 31)

    for artist in ARTISTS_TO_ADD:
        # Generate 3-6 shows per artist
        num_shows = random.randint(3, 6)

        for i in range(num_shows):
            # Random date between start and end
            days_offset = random.randint(0, (end_date - start_date).days)
            show_date = start_date + timedelta(days=days_offset)

            # Random venue
            venue = random.choice(VENUES)

            # Generate show
            show = generate_show_for_artist(artist, venue, show_date)
            if show:
                new_shows.append(show)

    # Combine filtered existing data with new shows
    df_new = pd.DataFrame(new_shows)
    df_combined = pd.concat([df_filtered, df_new], ignore_index=True)

    # Sort by show date
    df_combined = df_combined.sort_values("show_date")

    # Save updated data
    output_file = "data/raw/csv/shows_future.csv"
    df_combined.to_csv(output_file, index=False)

    print(f"✅ Updated data: {len(df_combined)} shows")
    print(f"🎤 Artists: {', '.join(sorted(df_combined['artist_name'].unique()))}")
    print(
        f"📅 Date range: {df_combined['show_date'].min()} to {df_combined['show_date'].max()}"
    )
    print(f"🎫 Total tickets: {df_combined['TICKETS_SOLD_SO_FAR'].sum():,}")
    print(f"💰 Total revenue: ${df_combined['CURRENT_REVENUE'].sum():,.0f}")
    print(f"📁 Saved to: {output_file}")


if __name__ == "__main__":
    main()

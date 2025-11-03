#!/usr/bin/env python3
"""
Generate realistic future concert data for FANalyze v2.0
Creates simulated ticket sales data for upcoming shows through 2026
Note: This script does NOT use Faker or external sources. It uses
builtin Python randomness and curated in-file lists to synthesize shows.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid

# Set random seed for reproducible results
np.random.seed(42)
random.seed(42)

ARTISTS = [
    'Metallica',
    'Beyoncé', 
    'Bruno Mars',
    'Coldplay',
    'Ed Sheeran',
    'Taylor Swift',
    'The Weeknd'
]

# Venue data with realistic capacities and types
VENUES = [
    {'name': 'Madison Square Garden', 'city': 'New York', 'state': 'NY', 'capacity': 20789, 'type': 'Arena'},
    {'name': 'Staples Center', 'city': 'Los Angeles', 'state': 'CA', 'capacity': 19068, 'type': 'Arena'},
    {'name': 'United Center', 'city': 'Chicago', 'state': 'IL', 'capacity': 20917, 'type': 'Arena'},
    {'name': 'TD Garden', 'city': 'Boston', 'state': 'MA', 'capacity': 19156, 'type': 'Arena'},
    {'name': 'Wells Fargo Center', 'city': 'Philadelphia', 'state': 'PA', 'capacity': 20478, 'type': 'Arena'},
    {'name': 'American Airlines Center', 'city': 'Dallas', 'state': 'TX', 'capacity': 19200, 'type': 'Arena'},
    {'name': 'Crypto.com Arena', 'city': 'Los Angeles', 'state': 'CA', 'capacity': 19068, 'type': 'Arena'},
    {'name': 'Barclays Center', 'city': 'Brooklyn', 'state': 'NY', 'capacity': 17732, 'type': 'Arena'},
    {'name': 'Capital One Arena', 'city': 'Washington', 'state': 'DC', 'capacity': 20356, 'type': 'Arena'},
    {'name': 'State Farm Arena', 'city': 'Atlanta', 'state': 'GA', 'capacity': 18047, 'type': 'Arena'},
    {'name': 'Fiserv Forum', 'city': 'Milwaukee', 'state': 'WI', 'capacity': 17500, 'type': 'Arena'},
    {'name': 'Target Center', 'city': 'Minneapolis', 'state': 'MN', 'capacity': 19356, 'type': 'Arena'},
    {'name': 'Ball Arena', 'city': 'Denver', 'state': 'CO', 'capacity': 19520, 'type': 'Arena'},
    {'name': 'Climate Pledge Arena', 'city': 'Seattle', 'state': 'WA', 'capacity': 18000, 'type': 'Arena'},
    {'name': 'Chase Center', 'city': 'San Francisco', 'state': 'CA', 'capacity': 18064, 'type': 'Arena'},
    {'name': 'Footprint Center', 'city': 'Phoenix', 'state': 'AZ', 'capacity': 18055, 'type': 'Arena'},
    {'name': 'Amway Center', 'city': 'Orlando', 'state': 'FL', 'capacity': 18846, 'type': 'Arena'},
    {'name': 'FTX Arena', 'city': 'Miami', 'state': 'FL', 'capacity': 19600, 'type': 'Arena'},
    {'name': 'Bridgestone Arena', 'city': 'Nashville', 'state': 'TN', 'capacity': 19995, 'type': 'Arena'},
    {'name': 'Smoothie King Center', 'city': 'New Orleans', 'state': 'LA', 'capacity': 16867, 'type': 'Arena'}
]

# Artist tiers and pricing
ARTIST_TIERS = {
    'Taylor Swift': {'tier': 'A-list', 'base_price': 400, 'price_range': '$200-$800'},
    'Beyoncé': {'tier': 'A-list', 'base_price': 350, 'price_range': '$150-$700'},
    'Metallica': {'tier': 'A-list', 'base_price': 300, 'price_range': '$100-$600'},
    'Ed Sheeran': {'tier': 'A-list', 'base_price': 250, 'price_range': '$80-$500'},
    'Bruno Mars': {'tier': 'A-list', 'base_price': 280, 'price_range': '$120-$550'},
    'Coldplay': {'tier': 'A-list', 'base_price': 220, 'price_range': '$80-$450'},
    'The Weeknd': {'tier': 'A-list', 'base_price': 200, 'price_range': '$60-$400'}
}

# Number of shows to generate per artist (balanced)
NUM_SHOWS_PER_ARTIST = 10

def generate_show_dates(start_date, end_date, num_shows):
    """Generate num_shows future dates between start and end, roughly uniform.

    Ensures all returned dates are after "now" and before end_date, avoiding
    downstream skipping so each artist gets the same number of shows.
    """
    # Work with date objects for simplicity
    today = datetime.now().date()
    window_start = max(start_date.date(), today + timedelta(days=1))
    window_end = end_date.date()

    if window_start >= window_end:
        # Edge case: window exhausted; fall back to next num_shows days
        window_start = today + timedelta(days=1)
        window_end = window_start + timedelta(days=num_shows + 7)

    total_days = (window_end - window_start).days
    step = max(1, total_days // (num_shows + 1))

    dates: list[datetime] = []
    for i in range(1, num_shows + 1):
        base_day = window_start + timedelta(days=i * step)
        # Add small jitter (+/- up to 3 days) but keep in bounds
        jitter = random.randint(-3, 3)
        candidate = base_day + timedelta(days=jitter)
        candidate = min(max(candidate, window_start), window_end)
        # Convert to datetime at midnight
        dates.append(datetime.combine(candidate, datetime.min.time()))

    # Ensure uniqueness and sorted order
    dates = sorted(list(dict.fromkeys(dates)))
    # If de-dup reduced size, append incremental days to reach target
    while len(dates) < num_shows:
        extra_day = dates[-1].date() + timedelta(days=1)
        if extra_day > window_end:
            extra_day = window_end
        dates.append(datetime.combine(extra_day, datetime.min.time()))

    return dates[:num_shows]

def simulate_ticket_sales(artist, venue_capacity, days_until_show, base_price):
    """Simulate realistic ticket sales based on artist popularity and time until show"""
    
    # Base sales rate (percentage of capacity sold)
    if artist in ['Taylor Swift', 'Beyoncé']:
        base_rate = 0.85  # Very high demand
    elif artist in ['Metallica', 'Ed Sheeran', 'Bruno Mars']:
        base_rate = 0.75  # High demand
    else:
        base_rate = 0.65  # Good demand
    
    # Adjust for time until show (more sales as show gets closer)
    time_factor = max(0.1, 1.0 - (days_until_show / 365))  # More sales as show approaches
    
    # Add some randomness
    random_factor = random.uniform(0.8, 1.2)
    
    # Calculate final sales rate
    sales_rate = min(0.95, base_rate * time_factor * random_factor)
    
    # Calculate tickets sold
    tickets_sold = int(venue_capacity * sales_rate)
    
    # Calculate revenue
    revenue = tickets_sold * base_price
    
    return {
        'tickets_sold': tickets_sold,
        'sales_rate': round(sales_rate * 100, 1),
        'revenue': revenue,
        'is_sellout': tickets_sold >= venue_capacity * 0.95
    }

def generate_future_concerts():
    """Generate future concert data"""
    
    shows = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 12, 31)
    
    for artist in ARTISTS:
        # Generate a balanced number of shows per artist
        num_shows = NUM_SHOWS_PER_ARTIST
        show_dates = generate_show_dates(start_date, end_date, num_shows)
        
        for i, show_date in enumerate(show_dates):
            # Select random venue
            venue = random.choice(VENUES)
            
            # Calculate days until show (dates are already in the future)
            days_until_show = (show_date - datetime.now()).days
                
            # Get artist pricing info
            artist_info = ARTIST_TIERS[artist]
            
            # Simulate ticket sales
            sales_data = simulate_ticket_sales(
                artist, 
                venue['capacity'], 
                days_until_show, 
                artist_info['base_price']
            )
            
            # Generate show ID
            show_id = f"future_{artist.lower().replace(' ', '_')}_{show_date.strftime('%Y%m%d')}_{i+1}"
            venue_id = f"venue_{venue['name'].lower().replace(' ', '_').replace('.', '')}"
            
            # Determine market size
            market_size = 'Major' if venue['capacity'] > 18000 else 'Secondary'
            
            show = {
                'artist_name': artist,
                'show_date': show_date.strftime('%Y-%m-%d'),
                'venue_name': venue['name'],
                'city_name': venue['city'],
                'state_code': venue['state'],
                'country_name': 'United States',
                'source': 'simulated',
                'collected_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'show_date_parsed': show_date.strftime('%Y-%m-%d'),
                'show_id': show_id,
                'venue_id': venue_id,
                'TICKETS_SOLD_SO_FAR': sales_data['tickets_sold'],
                'CURRENT_SALES_RATE': sales_data['sales_rate'],
                'DAYS_UNTIL_SHOW': days_until_show,
                'AVERAGE_TICKET_PRICE': artist_info['base_price'],
                'TICKET_PRICE_RANGE': artist_info['price_range'],
                'CURRENT_REVENUE': sales_data['revenue'],
                'VENUE_TYPE': venue['type'],
                'VENUE_CAPACITY': venue['capacity'],
                'ARTIST_TIER': artist_info['tier'],
                'MARKET_SIZE': market_size
            }
            
            shows.append(show)
    
    return pd.DataFrame(shows)

def main():
    """Generate and save future concerts data"""
    print("🎵 Generating future concert data...")
    
    # Generate data
    df = generate_future_concerts()
    
    # Sort by show date
    print(f"Columns: {list(df.columns)}")
    df = df.sort_values('show_date')
    
    # Save to CSV
    output_file = 'data/raw/csv/shows_future.csv'
    df.to_csv(output_file, index=False)
    
    print(f"✅ Generated {len(df)} future concerts")
    print(f"📁 Saved to: {output_file}")
    print(f"🎤 Artists: {', '.join(sorted(df['artist_name'].unique()))}")
    print(f"📅 Date range: {df['show_date'].min()} to {df['show_date'].max()}")
    print(f"🎫 Total tickets: {df['TICKETS_SOLD_SO_FAR'].sum():,}")
    print(f"💰 Total revenue: ${df['CURRENT_REVENUE'].sum():,.0f}")

if __name__ == "__main__":
    main()

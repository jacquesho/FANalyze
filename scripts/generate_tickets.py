#!/usr/bin/env python3
"""
Generate synthetic ticket sales for future shows
Creates realistic ticket sales data based on show characteristics
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from api_config import get_snowflake_connection

# Set random seed for reproducible results
np.random.seed(42)
random.seed(42)

def get_future_shows():
    """Get future shows from Snowflake that need ticket sales data"""
    
    query = """
    SELECT 
        show_id,
        artist_name,
        venue_name,
        show_date,
        city_name,
        state_code,
        source,
        20000 as venue_capacity,
        200 as average_ticket_price,
        0 as tickets_sold,
        'A-list' as artist_tier
    FROM fan_staging.stg_shows_future 
    WHERE show_date > CURRENT_DATE()
    ORDER BY show_date
    """
    
    conn = get_snowflake_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Debug: print column names
    print(f"Columns returned: {list(df.columns)}")
    print(f"First row: {df.iloc[0].to_dict() if not df.empty else 'No data'}")
    
    return df

def calculate_sales_velocity(show_date, artist_tier, venue_capacity, days_until_show):
    """Calculate realistic sales velocity based on show characteristics"""
    
    # Base sales rate (percentage of capacity sold per day)
    base_rate = 0.02  # 2% per day
    
    # Artist tier multipliers
    tier_multipliers = {
        'A-list': 1.5,
        'B-list': 1.0,
        'C-list': 0.7
    }
    artist_multiplier = tier_multipliers.get(artist_tier, 1.0)
    
    # Venue size impact (larger venues sell slower)
    if venue_capacity > 50000:
        venue_multiplier = 0.6  # Stadium
    elif venue_capacity > 15000:
        venue_multiplier = 0.8  # Large arena
    else:
        venue_multiplier = 1.0  # Small venue
    
    # Time-based velocity (slower as show approaches, then rush)
    if days_until_show > 365:
        time_multiplier = 0.1  # Very slow for far future (1+ years)
    elif days_until_show > 180:
        time_multiplier = 0.3  # Slow for far future
    elif days_until_show > 90:
        time_multiplier = 0.6  # Slow
    elif days_until_show > 30:
        time_multiplier = 1.0  # Normal
    elif days_until_show > 7:
        time_multiplier = 1.5  # Accelerating
    else:
        time_multiplier = 2.0  # Last-minute rush
    
    # Weekend shows sell faster
    weekend_multiplier = 1.2 if show_date.weekday() >= 5 else 1.0
    
    # Calculate final sales rate
    sales_rate = base_rate * artist_multiplier * venue_multiplier * time_multiplier * weekend_multiplier
    
    return min(sales_rate, 0.15)  # Cap at 15% per day

def generate_ticket_sales(show_row):
    """Generate synthetic ticket sales for a single show"""
    
    show_date = pd.to_datetime(show_row['SHOW_DATE'])
    days_until_show = (show_date - datetime.now()).days
    
    print(f"  Show date: {show_date}, Days until show: {days_until_show}")
    
    # Skip if show is in the past
    if days_until_show < 0:
        print(f"  Skipping past show")
        return None
    
    # Set default values for missing columns
    venue_capacity = show_row.get('VENUE_CAPACITY', 20000)  # Default arena capacity
    current_tickets_sold = show_row.get('TICKETS_SOLD', 0) or 0
    average_ticket_price = show_row.get('AVERAGE_TICKET_PRICE', 200) or 200
    
    # Calculate how many days of sales to simulate
    days_to_simulate = min(days_until_show, 365)  # Max 1 year of sales history
    
    print(f"  Venue capacity: {venue_capacity}, Current tickets sold: {current_tickets_sold}")
    print(f"  Days to simulate: {days_to_simulate}")
    
    sales_data = []
    running_tickets_sold = current_tickets_sold
    
    for days_ago in range(1, days_to_simulate + 1):
        current_date = datetime.now() - timedelta(days=days_ago)
        
        # Debug: show what dates we're calculating
        if days_ago <= 5:  # Only show first 5 iterations to avoid spam
            print(f"    Days ago {days_ago}: {current_date} (now: {datetime.now()})")
        
        # Skip if this date is in the future (shouldn't happen for future shows)
        if current_date > datetime.now():
            if days_ago <= 5:
                print(f"    Skipping future date")
            continue
            
        # Calculate sales velocity for this day
        artist_tier = show_row.get('ARTIST_TIER', 'A-list')  # Default to A-list
        days_until_show_at_sale_time = days_until_show + days_ago
        sales_velocity = calculate_sales_velocity(
            show_date, 
            artist_tier, 
            venue_capacity, 
            days_until_show_at_sale_time
        )
        
        # Add some randomness
        daily_variance = random.uniform(0.5, 1.5)
        actual_velocity = sales_velocity * daily_variance
        
        # Calculate tickets sold on this day
        max_possible_sales = min(
            int(venue_capacity * actual_velocity),
            venue_capacity - running_tickets_sold
        )
        
        if max_possible_sales > 0:
            daily_tickets_sold = random.randint(0, max_possible_sales)
            running_tickets_sold += daily_tickets_sold
            
            if daily_tickets_sold > 0:
                sales_data.append({
                    'show_id': show_row['SHOW_ID'],
                    'sale_date': current_date.strftime('%Y-%m-%d'),
                    'tickets_sold': daily_tickets_sold,
                    'cumulative_tickets_sold': running_tickets_sold,
                    'revenue': daily_tickets_sold * average_ticket_price,
                    'cumulative_revenue': running_tickets_sold * average_ticket_price,
                    'sales_rate': round((running_tickets_sold / venue_capacity) * 100, 2),
                    'days_until_show': days_until_show_at_sale_time
                })
    
    print(f"  Generated {len(sales_data)} sales records")
    return sales_data

def generate_all_ticket_sales():
    """Generate synthetic ticket sales for all eligible future shows"""
    
    print("Fetching future shows from Snowflake...")
    future_shows = get_future_shows()
    
    if future_shows.empty:
        print("No future shows found that need ticket sales data")
        return
    
    print(f"Found {len(future_shows)} shows eligible for ticket sales")
    
    all_sales_data = []
    
    for idx, show_row in future_shows.iterrows():
        print(f"Processing {show_row['ARTIST_NAME']} at {show_row['VENUE_NAME']} on {show_row['SHOW_DATE']}")
        
        sales_data = generate_ticket_sales(show_row)
        if sales_data:
            all_sales_data.extend(sales_data)
    
    if not all_sales_data:
        print("No ticket sales data generated")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_sales_data)
    
    # Save to CSV
    output_file = 'data/raw/csv/synthetic_ticket_sales.csv'
    df.to_csv(output_file, index=False)
    
    print(f"Generated {len(df)} ticket sales records")
    print(f"Saved to: {output_file}")
    print(f"Date range: {df['sale_date'].min()} to {df['sale_date'].max()}")
    print(f"Total tickets: {df['tickets_sold'].sum():,}")
    print(f"Total revenue: ${df['revenue'].sum():,.0f}")
    
    return df

def main():
    """Main function to generate synthetic ticket sales"""
    print("Generating synthetic ticket sales for future shows...")
    
    try:
        df = generate_all_ticket_sales()
        if df is not None:
            print("Synthetic ticket sales generation complete!")
        else:
            print("No data generated")
    except Exception as e:
        print(f"Error generating ticket sales: {e}")
        raise

if __name__ == "__main__":
    main()

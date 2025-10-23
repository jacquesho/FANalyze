#!/usr/bin/env python3
"""
Generate realistic current ticket sales projections for future US concerts.
This script estimates where ticket sales would be today (this far in advance).
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurrentTicketSalesGenerator:
    """Generate realistic current ticket sales projections for future concerts"""
    
    def __init__(self):
        # Artist tier mapping
        self.artist_tiers = {
            'BLACKPINK': 'A-list',
            'Metallica': 'A-list',
            'Coldplay': 'B-list',
            'Taylor Swift': 'A-list',
            'Beyoncé': 'A-list',
            'Ed Sheeran': 'B-list',
            'The Weeknd': 'B-list',
            'Bruno Mars': 'B-list'
        }
        
        # Major US cities for market size
        self.major_cities = [
            'new york', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia',
            'san antonio', 'san diego', 'dallas', 'san jose', 'austin', 'jacksonville',
            'fort worth', 'columbus', 'charlotte', 'san francisco', 'indianapolis',
            'seattle', 'denver', 'washington', 'boston', 'el paso', 'nashville',
            'detroit', 'oklahoma city', 'portland', 'las vegas', 'memphis',
            'louisville', 'baltimore', 'milwaukee', 'albuquerque', 'tucson',
            'fresno', 'sacramento', 'mesa', 'kansas city', 'atlanta', 'long beach',
            'colorado springs', 'raleigh', 'miami', 'virginia beach', 'omaha',
            'oakland', 'minneapolis', 'tulsa', 'arlington', 'tampa'
        ]
    
    def categorize_venue_type(self, venue_name):
        """Categorize venue type based on venue name"""
        if pd.isna(venue_name) or venue_name == '':
            return 'Other'
        venue_lower = str(venue_name).lower()
        
        if any(word in venue_lower for word in ['stadium', 'field', 'dome', 'coliseum']):
            return 'Stadium'
        elif any(word in venue_lower for word in ['arena', 'center', 'pavilion', 'auditorium']):
            return 'Arena'
        elif any(word in venue_lower for word in ['theater', 'theatre', 'hall', 'opera']):
            return 'Theater'
        elif any(word in venue_lower for word in ['club', 'bar', 'lounge', 'cafe']):
            return 'Club'
        elif any(word in venue_lower for word in ['amphitheater', 'amphitheatre', 'outdoor']):
            return 'Amphitheater'
        else:
            return 'Other'
    
    def estimate_venue_capacity(self, venue_name, venue_type):
        """Estimate venue capacity based on venue name and type"""
        if pd.isna(venue_name) or venue_name == '':
            return random.randint(1000, 5000)
        
        venue_lower = str(venue_name).lower()
        
        # Stadium capacities
        if venue_type == 'Stadium':
            if any(word in venue_lower for word in ['sofi', 'metlife', 'mercedes-benz', 'hard rock', 'bank of america']):
                return random.randint(60000, 90000)
            else:
                return random.randint(30000, 70000)
        
        # Arena capacities
        elif venue_type == 'Arena':
            if any(word in venue_lower for word in ['madison square', 'crypto.com', 'chase center', 'chase center']):
                return random.randint(15000, 25000)
            else:
                return random.randint(8000, 20000)
        
        # Theater capacities
        elif venue_type == 'Theater':
            return random.randint(1000, 5000)
        
        # Club capacities
        elif venue_type == 'Club':
            return random.randint(200, 1000)
        
        # Amphitheater capacities
        elif venue_type == 'Amphitheater':
            return random.randint(5000, 20000)
        
        else:
            return random.randint(1000, 15000)
    
    def get_market_size(self, city_name):
        """Determine market size based on city name"""
        if pd.isna(city_name) or city_name == '':
            return 'Large'
        
        city_lower = str(city_name).lower()
        
        if any(city in city_lower for city in self.major_cities):
            return 'Major'
        else:
            return 'Large'  # Assume most concert cities are at least large markets
    
    def calculate_current_ticket_sales(self, artist_tier, venue_capacity, market_size, show_date):
        """Calculate realistic current ticket sales based on how far in advance the show is"""
        
        # Base sales rates by artist tier (percentage of capacity sold by now)
        base_sales_rates = {
            'A-list': 0.15,  # 15% of capacity sold by now
            'B-list': 0.08   # 8% of capacity sold by now
        }
        
        # Market size adjustments
        market_adjustments = {'Major': 1.2, 'Large': 1.0, 'Medium': 0.8}
        
        # Time-based sales factors
        show_date_parsed = pd.to_datetime(show_date)
        days_until_show = (show_date_parsed - datetime.now()).days
        
        # Sales velocity based on time until show
        if days_until_show > 365:  # More than 1 year out
            time_factor = 0.3  # Very slow initial sales
        elif days_until_show > 180:  # 6 months to 1 year
            time_factor = 0.6  # Moderate sales
        elif days_until_show > 90:   # 3-6 months
            time_factor = 0.8  # Good sales pace
        elif days_until_show > 30:   # 1-3 months
            time_factor = 1.0  # Strong sales
        else:  # Less than 1 month
            time_factor = 1.2  # Peak sales period
        
        base_rate = base_sales_rates[artist_tier]
        market_factor = market_adjustments[market_size]
        
        # Calculate current sales rate
        current_sales_rate = base_rate * market_factor * time_factor
        
        # Add some randomness (±20%)
        sales_variance = random.uniform(0.8, 1.2)
        current_sales_rate = max(0.05, min(0.4, current_sales_rate * sales_variance))  # Clamp between 5% and 40%
        
        tickets_sold_so_far = int(venue_capacity * current_sales_rate)
        
        return tickets_sold_so_far, current_sales_rate
    
    def calculate_ticket_pricing(self, artist_tier, venue_type, market_size, show_date):
        """Calculate realistic ticket pricing for future shows"""
        base_prices = {
            'A-list': {'Stadium': 200, 'Arena': 150, 'Theater': 120, 'Club': 100, 'Amphitheater': 140, 'Other': 130},
            'B-list': {'Stadium': 120, 'Arena': 90, 'Theater': 70, 'Club': 50, 'Amphitheater': 80, 'Other': 75}
        }
        
        # Market size multipliers
        market_multipliers = {'Major': 1.4, 'Large': 1.2, 'Medium': 1.0}
        
        # Future show premium (shows further out tend to be more expensive)
        show_date_parsed = pd.to_datetime(show_date)
        days_until_show = (show_date_parsed - datetime.now()).days
        
        if days_until_show > 180:  # More than 6 months out
            future_premium = 1.2
        elif days_until_show > 90:  # 3-6 months out
            future_premium = 1.1
        else:  # Less than 3 months
            future_premium = 1.0
        
        base_price = base_prices[artist_tier][venue_type]
        market_multiplier = market_multipliers[market_size]
        
        avg_price = base_price * market_multiplier * future_premium
        
        # Add some randomness (±25% for future shows)
        price_variance = random.uniform(0.75, 1.25)
        avg_price = int(avg_price * price_variance)
        
        # Calculate price range
        min_price = int(avg_price * 0.5)
        max_price = int(avg_price * 2.0)
        
        return avg_price, f"${min_price}-${max_price}"
    
    def generate_current_sales_data(self, concerts_df):
        """Generate current ticket sales data for future concerts"""
        logger.info("Generating current ticket sales projections for future concerts...")
        
        # Add venue categorization
        concerts_df['VENUE_TYPE'] = concerts_df['venue_name'].apply(self.categorize_venue_type)
        concerts_df['VENUE_CAPACITY'] = concerts_df.apply(
            lambda row: self.estimate_venue_capacity(row['venue_name'], row['VENUE_TYPE']), 
            axis=1
        )
        
        # Add artist tier
        concerts_df['ARTIST_TIER'] = concerts_df['artist_name'].map(self.artist_tiers).fillna('B-list')
        
        # Add market size
        concerts_df['MARKET_SIZE'] = concerts_df['city_name'].apply(self.get_market_size)
        
        # Generate current sales data for each concert
        sales_data = []
        
        for idx, row in concerts_df.iterrows():
            if idx % 10 == 0:
                logger.info(f"Processing concert {idx+1}/{len(concerts_df)}")
            
            # Calculate current ticket sales
            tickets_sold_so_far, current_sales_rate = self.calculate_current_ticket_sales(
                row['ARTIST_TIER'],
                row['VENUE_CAPACITY'],
                row['MARKET_SIZE'],
                row['show_date']
            )
            
            # Calculate pricing
            avg_price, price_range = self.calculate_ticket_pricing(
                row['ARTIST_TIER'],
                row['VENUE_TYPE'],
                row['MARKET_SIZE'],
                row['show_date']
            )
            
            # Calculate current revenue
            current_revenue = tickets_sold_so_far * avg_price
            
            sales_data.append({
                'TICKETS_SOLD_SO_FAR': tickets_sold_so_far,
                'CURRENT_SALES_RATE': round(current_sales_rate * 100, 1),
                'AVERAGE_TICKET_PRICE': avg_price,
                'TICKET_PRICE_RANGE': price_range,
                'CURRENT_REVENUE': current_revenue,
                'DAYS_UNTIL_SHOW': (pd.to_datetime(row['show_date']) - datetime.now()).days
            })
        
        # Add sales data to dataframe
        sales_df = pd.DataFrame(sales_data)
        enhanced_df = pd.concat([concerts_df, sales_df], axis=1)
        
        # Reorder columns
        column_order = [
            'artist_name', 'show_date', 'venue_name', 'city_name', 'state_code', 'country_name',
            'VENUE_TYPE', 'VENUE_CAPACITY', 'ARTIST_TIER', 'MARKET_SIZE',
            'TICKETS_SOLD_SO_FAR', 'CURRENT_SALES_RATE', 'DAYS_UNTIL_SHOW',
            'AVERAGE_TICKET_PRICE', 'TICKET_PRICE_RANGE', 'CURRENT_REVENUE',
            'source', 'show_id', 'venue_id', 'collected_at'
        ]
        
        enhanced_df = enhanced_df[column_order]
        
        return enhanced_df

def main():
    """Main function to generate current ticket sales data"""
    generator = CurrentTicketSalesGenerator()
    
    # Load US future concerts
    try:
        concerts_df = pd.read_csv('real_us_future_concerts_2025_2026.csv')
        logger.info(f"Loaded {len(concerts_df)} real US future concerts")
    except FileNotFoundError:
        logger.error("real_us_future_concerts_2025_2026.csv not found. Run real_us_future_concerts_2025_2026.py first.")
        return
    
    # Generate current sales data
    enhanced_df = generator.generate_current_sales_data(concerts_df)
    
    # Save enhanced data
    output_file = 'real_us_future_concerts_current_sales_2025_2026.csv'
    enhanced_df.to_csv(output_file, index=False)
    
    # Print summary
    print("\n=== REAL US FUTURE CONCERTS - CURRENT SALES PROJECTIONS ===")
    print(f"Total concerts: {len(enhanced_df)}")
    print(f"Total tickets sold so far: {enhanced_df['TICKETS_SOLD_SO_FAR'].sum():,}")
    print(f"Total current revenue: ${enhanced_df['CURRENT_REVENUE'].sum():,.2f}")
    print(f"Average ticket price: ${enhanced_df['AVERAGE_TICKET_PRICE'].mean():.2f}")
    print(f"Average current sales rate: {enhanced_df['CURRENT_SALES_RATE'].mean():.1f}%")
    print(f"Average days until show: {enhanced_df['DAYS_UNTIL_SHOW'].mean():.0f}")
    
    print("\n=== BY ARTIST TIER ===")
    tier_summary = enhanced_df.groupby('ARTIST_TIER').agg({
        'TICKETS_SOLD_SO_FAR': 'sum',
        'CURRENT_REVENUE': 'sum',
        'AVERAGE_TICKET_PRICE': 'mean',
        'CURRENT_SALES_RATE': 'mean',
        'DAYS_UNTIL_SHOW': 'mean'
    }).round(2)
    print(tier_summary)
    
    print("\n=== BY VENUE TYPE ===")
    venue_summary = enhanced_df.groupby('VENUE_TYPE').agg({
        'VENUE_CAPACITY': 'mean',
        'TICKETS_SOLD_SO_FAR': 'mean',
        'AVERAGE_TICKET_PRICE': 'mean',
        'CURRENT_SALES_RATE': 'mean'
    }).round(2)
    print(venue_summary)
    
    print("\n=== BY TIME UNTIL SHOW ===")
    time_summary = enhanced_df.groupby(pd.cut(enhanced_df['DAYS_UNTIL_SHOW'], bins=[0, 90, 180, 365, 1000], labels=['<3 months', '3-6 months', '6-12 months', '>1 year'])).agg({
        'TICKETS_SOLD_SO_FAR': 'mean',
        'CURRENT_SALES_RATE': 'mean',
        'AVERAGE_TICKET_PRICE': 'mean'
    }).round(2)
    print(time_summary)
    
    print(f"\nEnhanced data saved to: {output_file}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Real-time ticket sales stream generator
Simulates live ticket sales for future shows with realistic timing
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import time
import random
from datetime import datetime
from pathlib import Path
import argparse
import psycopg
from dotenv import load_dotenv

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from api_config import get_snowflake_connection

# Load environment variables
load_dotenv()

# Set random seed for reproducible results
np.random.seed(42)
random.seed(42)

class TicketSalesStreamer:
    def __init__(self, speed_multiplier=1.0, output_format='jsonl', save_to_postgres=True):
        """
        Initialize the ticket sales streamer
        
        Args:
            speed_multiplier: Speed up simulation (1.0 = real time, 10.0 = 10x faster)
            output_format: 'jsonl', 'kafka', or 'console'
            save_to_postgres: Whether to save events to PostgreSQL
        """
        self.speed_multiplier = speed_multiplier
        self.output_format = output_format
        self.save_to_postgres = save_to_postgres
        self.shows = self.get_future_shows()
        self.active_sales = {}  # Track ongoing sales for each show
        self.event_counter = 0  # Counter for unique event IDs
        
    def get_future_shows(self):
        """Get future shows from Snowflake with real ticket sales and venue capacity data"""
        
        query = """
        SELECT 
            fs.show_id,
            fs.artist_name,
            fs.venue_name,
            fs.show_date,
            fs.city_name,
            fs.state_code,
            fs.source,
            COALESCE(fact.venue_capacity, dv.venue_capacity, 20000) as venue_capacity,
            COALESCE(fact.average_ticket_price, dv.avg_ticket_price, 200) as average_ticket_price,
            COALESCE(fact.tickets_sold, 0) as tickets_sold,
            COALESCE(fact.sales_performance, 'Average Sales') as artist_tier
        FROM fan_staging.stg_shows_future fs
        LEFT JOIN fan_marts.fact_shows fact ON fs.show_id = fact.show_id
        LEFT JOIN fan_marts.dim_venues dv ON fs.venue_name = dv.venue_name
        WHERE fs.show_date > CURRENT_DATE()
        ORDER BY fs.show_date
        """
        
        conn = get_snowflake_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"Found {len(df)} shows for real-time sales simulation", file=sys.stderr)
        
        # Show summary of real data
        if not df.empty:
            total_capacity = df['VENUE_CAPACITY'].sum()
            total_sold = df['TICKETS_SOLD'].sum()
            avg_price = df['AVERAGE_TICKET_PRICE'].mean()
            print(f"📊 Real data summary:", file=sys.stderr)
            print(f"   Total venue capacity: {total_capacity:,}", file=sys.stderr)
            print(f"   Already sold: {total_sold:,} tickets", file=sys.stderr)
            print(f"   Average ticket price: ${avg_price:.2f}", file=sys.stderr)
            print(f"   Shows with existing sales: {(df['TICKETS_SOLD'] > 0).sum()}", file=sys.stderr)
        
        return df
    
    def get_postgres_connection(self):
        """Get PostgreSQL connection for data loading."""
        try:
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_PORT")
            dbname = os.getenv("POSTGRES_DB")
            user = os.getenv("POSTGRES_USER_INGEST")
            password = os.getenv("POSTGRES_PASSWORD_INGEST")

            missing = [name for name, val in [
                ("POSTGRES_HOST", host),
                ("POSTGRES_PORT", port),
                ("POSTGRES_DB", dbname),
                ("POSTGRES_USER_INGEST", user),
                ("POSTGRES_PASSWORD_INGEST", password),
            ] if not val]

            if missing:
                print(f"❌ Missing required environment variables: {', '.join(missing)}")
                return None

            conn = psycopg.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
            )
            return conn
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return None
    
    def save_event_to_postgres(self, sale_event):
        """Save a sale event to PostgreSQL staging table."""
        if not self.save_to_postgres:
            return True
            
        try:
            conn = self.get_postgres_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Increment event counter for unique ID
            self.event_counter += 1
            
            # Prepare data for insertion
            event_json = json.dumps(sale_event, separators=(",", ":"))
            file_name = f"stream_tickets_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            insert_sql = """
            INSERT INTO staging.test_ingest (id, data_content, file_name, loaded_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                data_content = EXCLUDED.data_content,
                file_name = EXCLUDED.file_name,
                loaded_at = NOW()
            """
            
            cursor.execute(insert_sql, (self.event_counter, event_json, file_name))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save event to PostgreSQL: {e}")
            return False
    
    def calculate_sales_velocity(self, show_date, artist_tier, venue_capacity, days_until_show):
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
    
    def generate_sale_event(self, show_row):
        """Generate a single ticket sale event for a show"""
        
        show_date = pd.to_datetime(show_row['SHOW_DATE'])
        days_until_show = (show_date - datetime.now()).days
        
        # Skip if show is in the past
        if days_until_show < 0:
            return None
        
        # Get or initialize sales tracking for this show
        show_id = show_row['SHOW_ID']
        if show_id not in self.active_sales:
            # Start with existing tickets sold from fact_shows
            initial_tickets_sold = show_row.get('TICKETS_SOLD', 0)
            self.active_sales[show_id] = {
                'tickets_sold': initial_tickets_sold,
                'last_sale_time': datetime.now(),
                'show_row': show_row
            }
        
        sales_tracker = self.active_sales[show_id]
        venue_capacity = show_row.get('VENUE_CAPACITY', 20000)
        average_ticket_price = show_row.get('AVERAGE_TICKET_PRICE', 200)
        artist_tier = show_row.get('ARTIST_TIER', 'A-list')
        
        # Check if venue is sold out
        if sales_tracker['tickets_sold'] >= venue_capacity:
            return None
        
        # Calculate sales velocity
        sales_velocity = self.calculate_sales_velocity(
            show_date, 
            artist_tier, 
            venue_capacity, 
            days_until_show
        )
        
        # Calculate time since last sale (in hours)
        hours_since_last_sale = (datetime.now() - sales_tracker['last_sale_time']).total_seconds() / 3600
        
        # Probability of a sale happening (based on velocity and time elapsed)
        sale_probability = min(sales_velocity * hours_since_last_sale * 24, 0.8)  # Cap at 80%
        
        if random.random() < sale_probability:
            # Generate sale
            tickets_in_sale = random.randint(1, min(8, venue_capacity - sales_tracker['tickets_sold']))
            revenue = tickets_in_sale * average_ticket_price
            
            # Update tracking
            sales_tracker['tickets_sold'] += tickets_in_sale
            sales_tracker['last_sale_time'] = datetime.now()
            
            # Create sale event
            sale_event = {
                'timestamp': datetime.now().isoformat(),
                'show_id': show_id,
                'artist_name': show_row['ARTIST_NAME'],
                'venue_name': show_row['VENUE_NAME'],
                'show_date': show_date.isoformat(),
                'city_name': show_row['CITY_NAME'],
                'state_code': show_row['STATE_CODE'],
                'tickets_sold': tickets_in_sale,
                'cumulative_tickets_sold': sales_tracker['tickets_sold'],
                'revenue': round(revenue, 2),
                'cumulative_revenue': round(sales_tracker['tickets_sold'] * average_ticket_price, 2),
                'venue_capacity': int(venue_capacity),
                'sales_rate': round((sales_tracker['tickets_sold'] / venue_capacity) * 100, 2),
                'days_until_show': days_until_show,
                'artist_tier': artist_tier,
                'average_ticket_price': round(average_ticket_price, 2),
                'tickets_remaining': int(venue_capacity - sales_tracker['tickets_sold'])
            }
            
            return sale_event
        
        return None
    
    def output_sale_event(self, sale_event):
        """Output a sale event in the specified format"""
        
        if self.output_format == 'jsonl':
            print(json.dumps(sale_event), flush=True)
        elif self.output_format == 'console':
            print(
                f"🎫 {sale_event['artist_name']} at {sale_event['venue_name']} - "
                f"{sale_event['tickets_sold']} tickets sold (${sale_event['revenue']:,.2f}) - "
                f"Total: {sale_event['cumulative_tickets_sold']}/{sale_event['venue_capacity']} "
                f"({sale_event['sales_rate']}%) - "
                f"Remaining: {sale_event['tickets_remaining']}",
                flush=True,
            )
        elif self.output_format == 'kafka':
            # TODO: Implement Kafka producer
            print(f"KAFKA: {json.dumps(sale_event)}")
    
    def run_stream(self, duration_minutes=None, max_events=None):
        """
        Run the real-time ticket sales stream
        
        Args:
            duration_minutes: How long to run (None = forever)
            max_events: Maximum number of events to generate (None = unlimited)
        """
        
        print(f"Starting real-time ticket sales stream...", file=sys.stderr)
        print(f"Speed multiplier: {self.speed_multiplier}x", file=sys.stderr)
        print(f"Output format: {self.output_format}", file=sys.stderr)
        print(f"Shows being tracked: {len(self.shows)}", file=sys.stderr)
        
        if duration_minutes:
            print(f"Duration: {duration_minutes} minutes", file=sys.stderr)
        if max_events:
            print(f"Max events: {max_events}", file=sys.stderr)
        
        print("=" * 50, file=sys.stderr)
        
        start_time = datetime.now()
        event_count = 0
        
        try:
            while True:
                # Check duration limit
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        break
                
                # Check event limit
                if max_events and event_count >= max_events:
                    break
                
                # Generate sales for each show
                for _, show_row in self.shows.iterrows():
                    sale_event = self.generate_sale_event(show_row)
                    if sale_event:
                        self.output_sale_event(sale_event)
                        event_count += 1
                        
                        # Check event limit after each sale
                        if max_events and event_count >= max_events:
                            break
                
                # Sleep between iterations (adjusted for speed multiplier)
                sleep_time = 1.0 / self.speed_multiplier  # 1 second real time
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nStream stopped by user", file=sys.stderr)
        
        print(f"\nStream completed. Generated {event_count} events in {duration_minutes or 'unlimited'} time.", file=sys.stderr)

def main():
    """Main function to run the ticket sales stream"""
    
    parser = argparse.ArgumentParser(description='Real-time ticket sales stream generator')
    parser.add_argument('--speed', type=float, default=1.0, 
                       help='Speed multiplier (1.0 = real time, 10.0 = 10x faster)')
    parser.add_argument('--format', choices=['jsonl', 'console', 'kafka'], default='console',
                       help='Output format')
    parser.add_argument('--duration', type=int, 
                       help='Duration in minutes (None = forever)')
    parser.add_argument('--max-events', type=int,
                       help='Maximum number of events to generate')
    
    args = parser.parse_args()
    
    # Create streamer
    streamer = TicketSalesStreamer(
        speed_multiplier=args.speed,
        output_format=args.format
    )
    
    # Run stream
    streamer.run_stream(
        duration_minutes=args.duration,
        max_events=args.max_events
    )

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Ticket Sales Producer
Business logic: generates ticket sales events and publishes to Kafka
Uses artist_name as message key for partitioning
"""

import sys
import time
import random
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from kafka import BaseProducer
from kafka.utils import serialize_json
from config.api_config import get_snowflake_connection

import logging

logger = logging.getLogger(__name__)


class TicketProducer(BaseProducer):
    """
    Producer for ticket sales events.
    Extends BaseProducer with business logic for generating and sending ticket sales.
    """
    
    def __init__(self, topic_name: str = "ticket_sales", **kwargs):
        """
        Initialize ticket producer.
        
        Args:
            topic_name: Kafka topic name for ticket sales
            **kwargs: Additional producer configuration
        """
        super().__init__(client_id="ticket-sales-producer", **kwargs)
        self.topic_name = topic_name
        self.shows_df = None
        self.active_sales = {}  # Track ongoing sales for each show
        
        # Create topic if it doesn't exist (3 partitions for artist distribution)
        self.create_topic_if_not_exists(topic_name, num_partitions=3, replication_factor=1)
    
    def get_artists_from_snowflake(self) -> List[str]:
        """
        Get list of active artists from Snowflake.
        
        Returns:
            List of artist names
        """
        try:
            query = """
            SELECT DISTINCT artist_name
            FROM fan_staging.stg_shows_future
            WHERE show_date > CURRENT_DATE()
            ORDER BY artist_name
            """
            
            conn = get_snowflake_connection()
            df = pd.read_sql(query, conn)
            conn.close()
            
            artists = df['ARTIST_NAME'].tolist() if not df.empty else []
            logger.info(f"Found {len(artists)} active artists: {', '.join(artists)}")
            return artists
            
        except Exception as e:
            logger.error(f"Failed to get artists from Snowflake: {e}")
            # Return sample artists as fallback
            return ['Metallica', 'Taylor Swift', 'Beyoncé', 'Ed Sheeran', 
                   'The Weeknd', 'Bruno Mars', 'Coldplay']
    
    def get_shows_for_artists(self, artists: List[str]) -> pd.DataFrame:
        """
        Get future shows for specified artists from Snowflake.
        
        Args:
            artists: List of artist names
            
        Returns:
            DataFrame with show data
        """
        try:
            # Build query with artist filter
            artists_str = "', '".join(artists)
            query = f"""
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
                COALESCE(fact.sales_performance, 'A-list') as artist_tier
            FROM fan_staging.stg_shows_future fs
            LEFT JOIN fan_marts.fact_shows fact ON fs.show_id = fact.show_id
            LEFT JOIN fan_marts.dim_venues dv ON fs.venue_name = dv.venue_name
            WHERE fs.show_date > CURRENT_DATE()
              AND fs.artist_name IN ('{artists_str}')
            ORDER BY fs.show_date
            LIMIT 100
            """
            
            conn = get_snowflake_connection()
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Loaded {len(df)} shows for {len(artists)} artists")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get shows from Snowflake: {e}")
            # Return sample data as fallback
            return pd.DataFrame([{
                'SHOW_ID': 'sample_001',
                'ARTIST_NAME': 'Sample Artist',
                'VENUE_NAME': 'Sample Venue',
                'SHOW_DATE': pd.Timestamp.now() + pd.Timedelta(days=30),
                'CITY_NAME': 'New York',
                'STATE_CODE': 'NY',
                'VENUE_CAPACITY': 20000,
                'AVERAGE_TICKET_PRICE': 150,
                'TICKETS_SOLD': 0,
                'ARTIST_TIER': 'A-list'
            }])
    
    def calculate_sales_velocity(
        self,
        show_date: pd.Timestamp,
        artist_tier: str,
        venue_capacity: int,
        days_until_show: int
    ) -> float:
        """
        Calculate realistic sales velocity based on show characteristics.
        
        Args:
            show_date: Date of the show
            artist_tier: Artist tier (A-list, B-list, etc.)
            venue_capacity: Venue capacity
            days_until_show: Days until show
            
        Returns:
            Sales velocity (percentage of capacity per day)
        """
        # Base sales rate
        base_rate = 0.02  # 2% per day
        
        # Artist tier multipliers
        tier_multipliers = {
            'A-list': 1.5,
            'B-list': 1.0,
            'C-list': 0.7
        }
        artist_multiplier = tier_multipliers.get(artist_tier, 1.0)
        
        # Venue size impact
        if venue_capacity > 50000:
            venue_multiplier = 0.6  # Stadium
        elif venue_capacity > 15000:
            venue_multiplier = 0.8  # Large arena
        else:
            venue_multiplier = 1.0  # Small venue
        
        # Time-based velocity
        if days_until_show > 365:
            time_multiplier = 0.1
        elif days_until_show > 180:
            time_multiplier = 0.3
        elif days_until_show > 90:
            time_multiplier = 0.6
        elif days_until_show > 30:
            time_multiplier = 1.0
        elif days_until_show > 7:
            time_multiplier = 1.5
        else:
            time_multiplier = 2.0  # Last-minute rush
        
        # Weekend multiplier
        weekend_multiplier = 1.2 if show_date.weekday() >= 5 else 1.0
        
        sales_rate = base_rate * artist_multiplier * venue_multiplier * time_multiplier * weekend_multiplier
        return min(sales_rate, 0.15)  # Cap at 15% per day
    
    def generate_sale_event(self, show_row: pd.Series) -> Dict[str, Any]:
        """
        Generate a single ticket sale event for a show.
        
        Args:
            show_row: Show data row
            
        Returns:
            Sale event dictionary or None if no sale should occur
        """
        show_date = pd.to_datetime(show_row['SHOW_DATE'])
        days_until_show = (show_date - datetime.now()).days
        
        # Skip if show is in the past
        if days_until_show < 0:
            return None
        
        # Get or initialize sales tracking for this show
        show_id = str(show_row['SHOW_ID'])
        artist_name = str(show_row['ARTIST_NAME'])
        
        if show_id not in self.active_sales:
            initial_tickets_sold = int(show_row.get('TICKETS_SOLD', 0))
            self.active_sales[show_id] = {
                'tickets_sold': initial_tickets_sold,
                'last_sale_time': datetime.now(),
                'show_row': show_row
            }
        
        sales_tracker = self.active_sales[show_id]
        venue_capacity = int(show_row.get('VENUE_CAPACITY', 20000))
        average_ticket_price = float(show_row.get('AVERAGE_TICKET_PRICE', 200))
        artist_tier = str(show_row.get('ARTIST_TIER', 'A-list'))
        
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
        
        # Probability of a sale happening
        sale_probability = min(sales_velocity * hours_since_last_sale * 24, 0.8)
        
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
                'artist_name': artist_name,
                'venue_name': str(show_row['VENUE_NAME']),
                'show_date': show_date.isoformat(),
                'city_name': str(show_row['CITY_NAME']),
                'state_code': str(show_row['STATE_CODE']),
                'tickets_sold': tickets_in_sale,
                'cumulative_tickets_sold': sales_tracker['tickets_sold'],
                'revenue': round(revenue, 2),
                'cumulative_revenue': round(sales_tracker['tickets_sold'] * average_ticket_price, 2),
                'venue_capacity': venue_capacity,
                'sales_rate': round((sales_tracker['tickets_sold'] / venue_capacity) * 100, 2),
                'days_until_show': days_until_show,
                'artist_tier': artist_tier,
                'average_ticket_price': round(average_ticket_price, 2),
                'tickets_remaining': venue_capacity - sales_tracker['tickets_sold']
            }
            
            return sale_event
        
        return None
    
    def run(self, interval_seconds: float = 10.0):
        """
        Run the producer, generating and sending ticket sales events.
        
        Args:
            interval_seconds: Time between iterations in seconds
        """
        # Get artists and shows
        artists = self.get_artists_from_snowflake()
        if not artists:
            logger.error("No artists found. Exiting.")
            return
        
        self.shows_df = self.get_shows_for_artists(artists)
        if self.shows_df.empty:
            logger.error("No shows found. Exiting.")
            return
        
        logger.info(f"Starting ticket sales producer for {len(artists)} artists")
        logger.info(f"Press Ctrl+C to stop")
        
        message_count = 0
        
        try:
            while True:
                # Generate sales for each show
                for _, show_row in self.shows_df.iterrows():
                    sale_event = self.generate_sale_event(show_row)
                    
                    if sale_event:
                        # Serialize to JSON bytes
                        value_bytes = serialize_json(sale_event)
                        
                        # Send to Kafka with artist_name as key (for partitioning)
                        artist_name = sale_event['artist_name']
                        self.send(
                            topic=self.topic_name,
                            key=artist_name,  # Key determines partition!
                            value=value_bytes
                        )
                        
                        message_count += 1
                        logger.info(
                            f"🎫 Produced message #{message_count}: "
                            f"{artist_name} at {sale_event['venue_name']} - "
                            f"{sale_event['tickets_sold']} tickets (${sale_event['revenue']:,.2f}) - "
                            f"Total: {sale_event['cumulative_tickets_sold']}/{sale_event['venue_capacity']} "
                            f"({sale_event['sales_rate']}%)"
                        )
                        
                        if message_count % 10 == 0:
                            logger.info(f"Total messages produced: {message_count}")
                
                # Sleep between iterations
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.close()
            logger.info(f"Producer shutdown complete. Total messages: {message_count}")


def main():
    """Main entry point"""
    producer = TicketProducer()
    producer.run(interval_seconds=10.0)


if __name__ == "__main__":
    main()


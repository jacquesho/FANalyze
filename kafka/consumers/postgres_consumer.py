#!/usr/bin/env python3
"""
PostgreSQL Consumer
Business logic: consumes ticket sales events from Kafka and inserts into PostgreSQL
"""

import sys
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from kafka import BaseConsumer
from kafka.utils import deserialize_json
import psycopg

import logging

logger = logging.getLogger(__name__)


class PostgresConsumer(BaseConsumer):
    """
    Consumer for ticket sales events that inserts into PostgreSQL.
    Extends BaseConsumer with business logic for processing and storing ticket sales.
    """
    
    def __init__(self, topic_name: str = "ticket_sales", **kwargs):
        """
        Initialize PostgreSQL consumer.
        
        Args:
            topic_name: Kafka topic name to consume from
            **kwargs: Additional consumer configuration
        """
        super().__init__(**kwargs)
        self.topic_name = topic_name
        self.postgres_dsn = self._get_postgres_dsn()
        
        # Create table if it doesn't exist
        self._create_ticket_sales_table()
    
    def _get_postgres_dsn(self) -> str:
        """Build PostgreSQL connection string from environment variables"""
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "postgres")
        
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        logger.info(f"PostgreSQL connection configured for {host}:{port}")
        return dsn
    
    def _create_ticket_sales_table(self) -> bool:
        """Create the ticket_sales table if it doesn't exist"""
        try:
            with (
                psycopg.connect(self.postgres_dsn, autocommit=True) as conn,
                conn.cursor() as cur,
            ):
                # Create staging schema if it doesn't exist
                cur.execute("CREATE SCHEMA IF NOT EXISTS staging")
                
                # Create ticket_sales table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS staging.ticket_sales (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        show_id VARCHAR(255) NOT NULL,
                        artist_name VARCHAR(255) NOT NULL,
                        venue_name VARCHAR(255) NOT NULL,
                        show_date DATE NOT NULL,
                        city_name VARCHAR(255) NOT NULL,
                        state_code VARCHAR(2) NOT NULL,
                        tickets_sold INTEGER NOT NULL,
                        cumulative_tickets_sold INTEGER NOT NULL,
                        revenue DECIMAL(10,2) NOT NULL,
                        cumulative_revenue DECIMAL(10,2) NOT NULL,
                        venue_capacity INTEGER NOT NULL,
                        sales_rate DECIMAL(5,2) NOT NULL,
                        days_until_show INTEGER NOT NULL,
                        artist_tier VARCHAR(50) NOT NULL,
                        average_ticket_price DECIMAL(10,2) NOT NULL,
                        tickets_remaining INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ticket_sales_show_id 
                    ON staging.ticket_sales(show_id)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ticket_sales_timestamp 
                    ON staging.ticket_sales(timestamp)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ticket_sales_show_date 
                    ON staging.ticket_sales(show_date)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ticket_sales_artist_name 
                    ON staging.ticket_sales(artist_name)
                """)
                
            logger.info("✅ Ticket sales table created/verified successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create ticket sales table: {e}")
            return False
    
    def _insert_ticket_sale(self, sale_event: Dict[str, Any]) -> bool:
        """
        Insert a ticket sale event into PostgreSQL.
        
        Args:
            sale_event: Deserialized sale event dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure timestamp is valid
            timestamp_str = sale_event.get('timestamp')
            if isinstance(timestamp_str, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except Exception:
                    timestamp = datetime.now(UTC)
            else:
                timestamp = datetime.now(UTC)
            
            # Parse show_date
            show_date_str = sale_event.get('show_date')
            if isinstance(show_date_str, str):
                try:
                    show_date = datetime.fromisoformat(show_date_str.split('T')[0]).date()
                except Exception:
                    show_date = datetime.now().date()
            else:
                show_date = datetime.now().date()
            
            with (
                psycopg.connect(self.postgres_dsn, autocommit=True) as conn,
                conn.cursor() as cur,
            ):
                cur.execute(
                    """
                    INSERT INTO staging.ticket_sales (
                        timestamp, show_id, artist_name, venue_name, show_date,
                        city_name, state_code, tickets_sold, cumulative_tickets_sold,
                        revenue, cumulative_revenue, venue_capacity, sales_rate,
                        days_until_show, artist_tier, average_ticket_price, tickets_remaining
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        timestamp,
                        sale_event.get('show_id'),
                        sale_event.get('artist_name'),
                        sale_event.get('venue_name'),
                        show_date,
                        sale_event.get('city_name'),
                        sale_event.get('state_code'),
                        sale_event.get('tickets_sold'),
                        sale_event.get('cumulative_tickets_sold'),
                        sale_event.get('revenue'),
                        sale_event.get('cumulative_revenue'),
                        sale_event.get('venue_capacity'),
                        sale_event.get('sales_rate'),
                        sale_event.get('days_until_show'),
                        sale_event.get('artist_tier'),
                        sale_event.get('average_ticket_price'),
                        sale_event.get('tickets_remaining'),
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to insert ticket sale: {e}", exc_info=True)
            return False
    
    def process_message(self, msg) -> bool:
        """
        Process a single Kafka message.
        
        Args:
            msg: Kafka message object
            
        Returns:
            bool: True if processed successfully
        """
        try:
            # Deserialize message value
            sale_event = deserialize_json(msg.value())
            
            # Insert into PostgreSQL
            if self._insert_ticket_sale(sale_event):
                artist_name = sale_event.get('artist_name', 'Unknown')
                tickets_sold = sale_event.get('tickets_sold', 0)
                logger.info(
                    f"✅ Inserted sale for {artist_name} - "
                    f"{tickets_sold} tickets at {sale_event.get('venue_name', 'Unknown')}"
                )
                return True
            else:
                logger.error("Failed to insert sale event")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False
    
    def run(self):
        """Run the consumer, processing messages continuously"""
        # Subscribe to topic
        self.subscribe([self.topic_name])
        
        rows_written = 0
        messages_processed = 0
        
        logger.info("Starting to consume messages...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                msg = self.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                # Process message
                if self.process_message(msg):
                    rows_written += 1
                    messages_processed += 1
                    
                    # Commit offset after successful processing
                    self.commit(msg, asynchronous=False)
                    
                    if messages_processed % 10 == 0:
                        logger.info(
                            f"Progress: {messages_processed} messages processed, "
                            f"{rows_written} rows written"
                        )
                else:
                    messages_processed += 1
                    # Don't commit on failure - will retry
                    logger.warning(f"Message {messages_processed} failed, will retry")
        
        except KeyboardInterrupt:
            logger.info(
                f"Shutdown. Final stats: {messages_processed} messages processed, "
                f"{rows_written} rows written"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.close()
            logger.info("Consumer closed")


def main():
    """Main entry point"""
    consumer = PostgresConsumer()
    consumer.run()


if __name__ == "__main__":
    main()


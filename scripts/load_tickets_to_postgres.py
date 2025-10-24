#!/usr/bin/env python3
"""
Load synthetic ticket sales data into Postgres
Handles table creation, data loading, and sync status tracking
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_postgres_connection():
    """Get Postgres connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DATABASE', 'fanalyze'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to Postgres: {e}")

def create_ticket_sales_table(conn):
    """Create ticket_sales table with sync tracking columns"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS ticket_sales (
        id SERIAL PRIMARY KEY,
        show_id VARCHAR(255) NOT NULL,
        sale_date DATE NOT NULL,
        tickets_sold INTEGER NOT NULL,
        cumulative_tickets_sold INTEGER NOT NULL,
        revenue DECIMAL(10,2) NOT NULL,
        cumulative_revenue DECIMAL(10,2) NOT NULL,
        sales_rate DECIMAL(5,2) NOT NULL,
        days_until_show INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sync_status VARCHAR(20) DEFAULT 'pending',
        synced_at TIMESTAMP,
        UNIQUE(show_id, sale_date)
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_ticket_sales_show_id ON ticket_sales(show_id);
    CREATE INDEX IF NOT EXISTS idx_ticket_sales_sale_date ON ticket_sales(sale_date);
    CREATE INDEX IF NOT EXISTS idx_ticket_sales_sync_status ON ticket_sales(sync_status);
    CREATE INDEX IF NOT EXISTS idx_ticket_sales_days_until_show ON ticket_sales(days_until_show);
    
    -- Create trigger to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    DROP TRIGGER IF EXISTS update_ticket_sales_updated_at ON ticket_sales;
    CREATE TRIGGER update_ticket_sales_updated_at
        BEFORE UPDATE ON ticket_sales
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    cursor = conn.cursor()
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("✅ Ticket sales table created/verified with sync tracking")
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise
    finally:
        cursor.close()

def create_analytics_views(conn):
    """Create useful analytics views for ticket sales data"""
    
    views_sql = """
    -- Daily sales summary
    CREATE OR REPLACE VIEW daily_sales_summary AS
    SELECT 
        sale_date,
        COUNT(DISTINCT show_id) as shows_with_sales,
        SUM(tickets_sold) as total_tickets_sold,
        SUM(revenue) as total_revenue,
        AVG(sales_rate) as avg_sales_rate,
        COUNT(*) as total_sales_events
    FROM ticket_sales
    GROUP BY sale_date
    ORDER BY sale_date;
    
    -- Show sales performance
    CREATE OR REPLACE VIEW show_sales_performance AS
    SELECT 
        show_id,
        MIN(sale_date) as first_sale_date,
        MAX(sale_date) as last_sale_date,
        MAX(cumulative_tickets_sold) as total_tickets_sold,
        MAX(cumulative_revenue) as total_revenue,
        MAX(sales_rate) as max_sales_rate,
        AVG(tickets_sold) as avg_daily_sales,
        COUNT(*) as days_with_sales,
        sync_status
    FROM ticket_sales
    GROUP BY show_id, sync_status
    ORDER BY total_revenue DESC;
    
    -- Sales velocity by days until show
    CREATE OR REPLACE VIEW sales_velocity_analysis AS
    SELECT 
        days_until_show,
        COUNT(*) as sales_events,
        AVG(tickets_sold) as avg_tickets_per_sale,
        AVG(sales_rate) as avg_sales_rate,
        SUM(tickets_sold) as total_tickets_sold,
        SUM(revenue) as total_revenue
    FROM ticket_sales
    GROUP BY days_until_show
    ORDER BY days_until_show;
    
    -- Sync status summary
    CREATE OR REPLACE VIEW sync_status_summary AS
    SELECT 
        sync_status,
        COUNT(*) as record_count,
        MIN(created_at) as oldest_record,
        MAX(created_at) as newest_record,
        COUNT(CASE WHEN synced_at IS NOT NULL THEN 1 END) as synced_count
    FROM ticket_sales
    GROUP BY sync_status
    ORDER BY record_count DESC;
    """
    
    cursor = conn.cursor()
    try:
        cursor.execute(views_sql)
        conn.commit()
        logger.info("✅ Analytics views created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating views: {e}")
        raise
    finally:
        cursor.close()

def load_ticket_sales_data(conn, csv_file_path):
    """Load ticket sales data from CSV into Postgres"""
    
    # Read CSV
    logger.info(f"📊 Reading ticket sales data from {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    if df.empty:
        logger.warning("⚠️ No data found in CSV file")
        return False
    
    logger.info(f"📈 Found {len(df)} ticket sales records")
    
    # Validate required columns
    required_columns = ['show_id', 'sale_date', 'tickets_sold', 'cumulative_tickets_sold', 
                      'revenue', 'cumulative_revenue', 'sales_rate', 'days_until_show']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"❌ Missing required columns: {missing_columns}")
        return False
    
    # Prepare data for insertion
    data_tuples = []
    for _, row in df.iterrows():
        try:
            data_tuples.append((
                str(row['show_id']),
                pd.to_datetime(row['sale_date']).date(),
                int(row['tickets_sold']),
                int(row['cumulative_tickets_sold']),
                float(row['revenue']),
                float(row['cumulative_revenue']),
                float(row['sales_rate']),
                int(row['days_until_show'])
            ))
        except Exception as e:
            logger.warning(f"⚠️ Skipping invalid row: {e}")
            continue
    
    if not data_tuples:
        logger.error("❌ No valid data to insert")
        return False
    
    # Insert data
    cursor = conn.cursor()
    try:
        # Clear existing data for these shows (if any)
        show_ids = df['show_id'].unique()
        placeholders = ','.join(['%s'] * len(show_ids))
        cursor.execute(f"DELETE FROM ticket_sales WHERE show_id IN ({placeholders})", show_ids)
        logger.info(f"🗑️ Cleared existing data for {len(show_ids)} shows")
        
        # Insert new data
        insert_sql = """
        INSERT INTO ticket_sales 
        (show_id, sale_date, tickets_sold, cumulative_tickets_sold, revenue, 
         cumulative_revenue, sales_rate, days_until_show, sync_status)
        VALUES %s
        ON CONFLICT (show_id, sale_date) DO UPDATE SET
            tickets_sold = EXCLUDED.tickets_sold,
            cumulative_tickets_sold = EXCLUDED.cumulative_tickets_sold,
            revenue = EXCLUDED.revenue,
            cumulative_revenue = EXCLUDED.cumulative_revenue,
            sales_rate = EXCLUDED.sales_rate,
            days_until_show = EXCLUDED.days_until_show,
            sync_status = 'updated',
            updated_at = CURRENT_TIMESTAMP
        """
        
        execute_values(cursor, insert_sql, data_tuples)
        conn.commit()
        
        logger.info(f"✅ Successfully loaded {len(data_tuples)} ticket sales records")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def validate_data_quality(conn):
    """Validate data quality and provide summary statistics"""
    
    cursor = conn.cursor()
    try:
        # Get basic statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT show_id) as unique_shows,
                MIN(sale_date) as earliest_sale,
                MAX(sale_date) as latest_sale,
                SUM(tickets_sold) as total_tickets,
                SUM(revenue) as total_revenue,
                AVG(sales_rate) as avg_sales_rate
            FROM ticket_sales
        """)
        
        stats = cursor.fetchone()
        
        # Get sync status summary
        cursor.execute("""
            SELECT sync_status, COUNT(*) 
            FROM ticket_sales 
            GROUP BY sync_status
        """)
        
        sync_stats = cursor.fetchall()
        
        logger.info("📊 Data Quality Summary:")
        logger.info(f"   Total records: {stats[0]:,}")
        logger.info(f"   Unique shows: {stats[1]:,}")
        logger.info(f"   Date range: {stats[2]} to {stats[3]}")
        logger.info(f"   Total tickets: {stats[4]:,}")
        logger.info(f"   Total revenue: ${stats[5]:,.2f}")
        logger.info(f"   Avg sales rate: {stats[6]:.2f}%")
        
        logger.info("📋 Sync Status Summary:")
        for status, count in sync_stats:
            logger.info(f"   {status}: {count:,} records")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating data: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main function to load ticket sales data into Postgres"""
    
    # Get CSV file path
    csv_file = 'data/raw/csv/synthetic_ticket_sales.csv'
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        logger.info("💡 Run generate_tickets.py first to create ticket sales data")
        return
    
    try:
        # Connect to Postgres
        logger.info("🔌 Connecting to Postgres...")
        conn = get_postgres_connection()
        
        # Create table with sync tracking
        logger.info("📋 Creating ticket sales table...")
        create_ticket_sales_table(conn)
        
        # Load data
        logger.info("📊 Loading ticket sales data...")
        success = load_ticket_sales_data(conn, csv_file)
        
        if success:
            # Create analytics views
            logger.info("📈 Creating analytics views...")
            create_analytics_views(conn)
            
            # Validate data quality
            logger.info("🔍 Validating data quality...")
            validate_data_quality(conn)
            
            logger.info("🎉 Ticket sales data loading complete!")
            logger.info("📊 You can now query the following tables/views:")
            logger.info("   - ticket_sales (raw data with sync tracking)")
            logger.info("   - daily_sales_summary")
            logger.info("   - show_sales_performance") 
            logger.info("   - sales_velocity_analysis")
            logger.info("   - sync_status_summary")
            logger.info("")
            logger.info("🔄 Next step: Run sync_tickets__postgres_to_snowflake.py to sync to Snowflake")
        else:
            logger.error("❌ Failed to load ticket sales data")
            
    except Exception as e:
        logger.error(f"❌ Error during loading: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick setup script for Postgres database
Creates the database and user for the ticket sales demo
"""

import os
import subprocess
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_postgres():
    """Set up Postgres database for the demo"""
    
    print("🗄️  Setting up Postgres database for ticket sales demo...")
    
    # Database configuration - connect to default 'postgres' database first
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',  # Connect to default database first
        'user': os.getenv('POSTGRES_USER_INGEST', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD_INGEST', 'password')
    }
    
    try:
        # Connect to Postgres (default database)
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Try to create database, but continue if it already exists
        print("📝 Creating database 'fanalyze'...")
        try:
            cur.execute("DROP DATABASE IF EXISTS fanalyze")
            cur.execute("CREATE DATABASE fanalyze")
            print("✅ Database 'fanalyze' created successfully")
        except Exception as e:
            print(f"⚠️  Database creation failed (may already exist): {e}")
            print("📝 Continuing with existing database...")
        
        # Close connection
        cur.close()
        conn.close()
        
        # Connect to fanalyze database (or use existing database)
        try:
            db_config['database'] = 'fanalyze'
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()
        except Exception as e:
            print(f"⚠️  Could not connect to 'fanalyze' database: {e}")
            print("📝 Using default database instead...")
            db_config['database'] = 'postgres'
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()
        
        # Create table
        print("📊 Creating ticket_sales table...")
        create_table_sql = """
        CREATE TABLE ticket_sales (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_ticket_sales_show_id ON ticket_sales(show_id);
        CREATE INDEX idx_ticket_sales_timestamp ON ticket_sales(timestamp);
        CREATE INDEX idx_ticket_sales_show_date ON ticket_sales(show_date);
        """
        
        cur.execute(create_table_sql)
        conn.commit()
        
        print("✅ Postgres setup complete!")
        print(f"   Database: fanalyze")
        print(f"   Host: localhost:5432")
        print(f"   User: postgres")
        print(f"   Table: ticket_sales")
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error connecting to Postgres: {e}")
        print("\n💡 Make sure Postgres is running:")
        print("   - Start PostgreSQL service")
        print("   - Check if port 5432 is available")
        print("   - Verify username/password")
        return False
    
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    
    return True

def test_connection():
    """Test the database connection"""
    
    print("\n🔍 Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='fanalyze',
            user='postgres',
            password='password'
        )
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ticket_sales")
        count = cur.fetchone()[0]
        
        print(f"✅ Connection successful!")
        print(f"   Current records in ticket_sales: {count}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 Postgres Setup for Ticket Sales Demo")
    print("=" * 50)
    
    if setup_postgres():
        test_connection()
        print("\n🎉 Setup complete! You can now run the demo pipeline.")
    else:
        print("\n❌ Setup failed. Please check your Postgres installation.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Complete Demo Pipeline: Real-time Streaming → Postgres → Snowflake
Perfect for demonstrating the full data flow for your test
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

class DemoPipeline:
    def __init__(self):
        self.demo_start_time = datetime.now()
        
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
    
    def print_step(self, step_num, title, description=""):
        """Print a step header"""
        print(f"\n📋 Step {step_num}: {title}")
        if description:
            print(f"   {description}")
        print("-" * 40)
    
    def run_command(self, command, description="", wait=True):
        """Run a command and show output"""
        if description:
            print(f"🔄 {description}")
        
        print(f"💻 Running: {' '.join(command)}")
        
        if wait:
            result = subprocess.run(command, capture_output=False)
            return result.returncode == 0
        else:
            # Run in background
            subprocess.Popen(command)
            return True
    
    def demo_1_streaming_only(self):
        """Demo 1: Just show the streaming data"""
        self.print_header("DEMO 1: Real-Time Ticket Sales Streaming")
        
        print("🎫 This shows live ticket sales happening across all future shows")
        print("⚡ We'll run at 20x speed for 2 minutes to see lots of activity")
        print("👀 Watch the sales build up in real-time!")
        
        input("\nPress Enter to start streaming demo...")
        
        self.run_command([
            sys.executable, 'scripts/stream_tickets.py',
            '--speed', '20',
            '--duration', '2',
            '--format', 'console'
        ], "Starting real-time ticket sales stream...")
    
    def demo_2_json_output(self):
        """Demo 2: Show JSON output for data pipelines"""
        self.print_header("DEMO 2: JSON Output for Data Pipelines")
        
        print("📄 This shows the same data in JSON format")
        print("🔗 Perfect for feeding into Kafka, databases, or other systems")
        print("📊 Each line is a complete ticket sale event")
        
        input("\nPress Enter to show JSON output...")
        
        self.run_command([
            sys.executable, 'scripts/stream_tickets.py',
            '--speed', '10',
            '--duration', '1',
            '--format', 'jsonl'
        ], "Generating JSON ticket sales data...")
    
    def demo_3_postgres_integration(self):
        """Demo 3: Stream to Postgres database"""
        self.print_header("DEMO 3: Streaming to Postgres Database")
        
        print("🗄️  This streams the ticket sales directly to a Postgres database")
        print("📝 Each sale event is written as it happens")
        print("📊 Perfect for real-time analytics and dashboards")
        
        print("\n⚠️  Note: Make sure Postgres is running on localhost:5432")
        print("   Database: fanalyze, User: postgres, Password: password")
        
        input("\nPress Enter to start Postgres streaming...")
        
        self.run_command([
            sys.executable, 'scripts/stream_to_postgres.py',
            '--duration', '3',
            '--speed', '15'
        ], "Streaming ticket sales to Postgres...")
    
    def demo_4_snowflake_transfer(self):
        """Demo 4: Transfer from Postgres to Snowflake"""
        self.print_header("DEMO 4: Postgres to Snowflake Transfer")
        
        print("❄️  This transfers all the ticket sales data from Postgres to Snowflake")
        print("🔄 Shows the complete data pipeline: Stream → Postgres → Snowflake")
        print("📈 Perfect for data warehousing and analytics")
        
        input("\nPress Enter to transfer data to Snowflake...")
        
        self.run_command([
            sys.executable, 'scripts/postgres_to_snowflake.py'
        ], "Transferring data from Postgres to Snowflake...")
    
    def demo_5_monitoring(self):
        """Demo 5: Show monitoring and statistics"""
        self.print_header("DEMO 5: Data Monitoring and Statistics")
        
        print("📊 Let's check what data we have in each system:")
        
        # Check Postgres stats
        print("\n🗄️  Postgres Statistics:")
        self.run_command([
            sys.executable, '-c', '''
import psycopg2
conn = psycopg2.connect(host="localhost", port=5432, database="fanalyze", user="postgres", password="password")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as total_sales, COUNT(DISTINCT show_id) as unique_shows, SUM(tickets_sold) as total_tickets, SUM(revenue) as total_revenue FROM ticket_sales")
result = cur.fetchone()
print(f"Total sales events: {result[0]:,}")
print(f"Unique shows: {result[1]}")
print(f"Total tickets sold: {result[2]:,}")
print(f"Total revenue: ${result[3]:,.2f}")
cur.close()
conn.close()
'''
        ], "Checking Postgres data...")
        
        # Check Snowflake stats
        print("\n❄️  Snowflake Statistics:")
        self.run_command([
            sys.executable, '-c', '''
import sys
from pathlib import Path
sys.path.append(str(Path(".") / "config"))
from api_config import get_snowflake_connection
conn = get_snowflake_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as total_sales, COUNT(DISTINCT show_id) as unique_shows, SUM(tickets_sold) as total_tickets, SUM(revenue) as total_revenue FROM fan_staging.ticket_sales_stream")
result = cur.fetchone()
print(f"Total sales events: {result[0]:,}")
print(f"Unique shows: {result[1]}")
print(f"Total tickets sold: {result[2]:,}")
print(f"Total revenue: ${result[3]:,.2f}")
cur.close()
conn.close()
'''
        ], "Checking Snowflake data...")
    
    def run_full_demo(self):
        """Run the complete demo pipeline"""
        self.print_header("COMPLETE DEMO PIPELINE")
        
        print("🎯 This demo shows the complete data flow:")
        print("   1. Real-time ticket sales streaming")
        print("   2. JSON output for data pipelines")
        print("   3. Postgres database integration")
        print("   4. Snowflake data warehouse transfer")
        print("   5. Monitoring and statistics")
        
        print(f"\n⏰ Demo started at: {self.demo_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all demos
        self.demo_1_streaming_only()
        self.demo_2_json_output()
        self.demo_3_postgres_integration()
        self.demo_4_snowflake_transfer()
        self.demo_5_monitoring()
        
        # Final summary
        self.print_header("DEMO COMPLETE!")
        
        demo_duration = datetime.now() - self.demo_start_time
        print(f"⏱️  Total demo time: {demo_duration}")
        print("\n🎉 You've successfully demonstrated:")
        print("   ✅ Real-time data streaming")
        print("   ✅ Database integration")
        print("   ✅ Data warehouse pipeline")
        print("   ✅ End-to-end data flow")
        
        print("\n💡 Perfect for your test next week!")
    
    def show_menu(self):
        """Show the demo menu"""
        while True:
            self.print_header("TICKET SALES DEMO MENU")
            
            print("Choose a demo to run:")
            print("1. 🎫 Real-time streaming only")
            print("2. 📄 JSON output demo")
            print("3. 🗄️  Postgres integration")
            print("4. ❄️  Snowflake transfer")
            print("5. 📊 Monitoring & statistics")
            print("6. 🚀 Complete pipeline demo")
            print("7. ❌ Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                self.demo_1_streaming_only()
            elif choice == '2':
                self.demo_2_json_output()
            elif choice == '3':
                self.demo_3_postgres_integration()
            elif choice == '4':
                self.demo_4_snowflake_transfer()
            elif choice == '5':
                self.demo_5_monitoring()
            elif choice == '6':
                self.run_full_demo()
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")
            
            input("\nPress Enter to return to menu...")

def main():
    """Main function"""
    demo = DemoPipeline()
    demo.show_menu()

if __name__ == "__main__":
    main()

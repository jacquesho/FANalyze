#!/usr/bin/env python3
"""
Streaming-only demo for ticket sales
Perfect for demonstrating real-time data without database setup
"""

import sys
import subprocess


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)


def print_step(step_num, title, description=""):
    """Print a step header"""
    print(f"\n📋 Step {step_num}: {title}")
    if description:
        print(f"   {description}")
    print("-" * 40)


def run_streaming_demo():
    """Run the streaming demo without database setup"""

    print_header("REAL-TIME TICKET SALES STREAMING DEMO")

    print("🎫 This demo shows live ticket sales happening across all future shows")
    print("⚡ We'll run at different speeds to show various scenarios")
    print("👀 Watch the sales build up in real-time!")

    print("\n🎯 Demo Scenarios:")
    print("1. 🚀 Fast demo (20x speed, 2 minutes) - Shows lots of activity")
    print("2. 📄 JSON output (10x speed, 1 minute) - Shows data format")
    print("3. 🎪 Real-time simulation (1x speed, 30 seconds) - Shows realistic timing")
    print("4. 🎯 Limited events (50x speed, 50 events) - Shows controlled output")

    while True:
        print("\n" + "=" * 40)
        print("Choose a demo scenario:")
        print("1. Fast demo (20x speed, 2 minutes)")
        print("2. JSON output (10x speed, 1 minute)")
        print("3. Real-time simulation (1x speed, 30 seconds)")
        print("4. Limited events (50x speed, 50 events)")
        print("5. Custom demo")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            print_step(1, "Fast Demo", "20x speed, 2 minutes - Shows lots of activity")
            print("🚀 Starting fast demo...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "20",
                    "--duration",
                    "2",
                    "--format",
                    "console",
                ]
            )

        elif choice == "2":
            print_step(2, "JSON Output Demo", "10x speed, 1 minute - Shows data format")
            print("📄 Starting JSON output demo...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "10",
                    "--duration",
                    "1",
                    "--format",
                    "jsonl",
                ]
            )

        elif choice == "3":
            print_step(
                3,
                "Real-time Simulation",
                "1x speed, 30 seconds - Shows realistic timing",
            )
            print("⏰ Starting real-time simulation...")
            print("   (This will be slow - perfect for showing realistic timing)")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "1",
                    "--duration",
                    "0.5",  # 30 seconds
                    "--format",
                    "console",
                ]
            )

        elif choice == "4":
            print_step(
                4,
                "Limited Events Demo",
                "50x speed, 50 events - Shows controlled output",
            )
            print("🎯 Starting limited events demo...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "50",
                    "--max-events",
                    "50",
                    "--format",
                    "console",
                ]
            )

        elif choice == "5":
            print_step(5, "Custom Demo", "Configure your own demo")
            print("🎛️  Custom demo configuration:")

            speed = (
                input("Enter speed multiplier (1-100, default 10): ").strip() or "10"
            )
            duration = input("Enter duration in minutes (default 1): ").strip() or "1"
            format_choice = (
                input("Output format (console/jsonl, default console): ").strip()
                or "console"
            )

            print(
                f"\n🚀 Starting custom demo: {speed}x speed, {duration} minutes, {format_choice} format..."
            )
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    speed,
                    "--duration",
                    duration,
                    "--format",
                    format_choice,
                ]
            )

        elif choice == "6":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please enter 1-6.")

        input("\nPress Enter to return to menu...")


def show_demo_info():
    """Show information about the demo"""

    print_header("DEMO INFORMATION")

    print("🎯 What This Demo Shows:")
    print("✅ Real-time ticket sales streaming")
    print("✅ Multiple shows selling simultaneously")
    print("✅ Realistic sales patterns and timing")
    print("✅ Cumulative sales tracking")
    print("✅ Revenue calculations")
    print("✅ Sales velocity based on show characteristics")

    print("\n📊 Key Features:")
    print("• Speed control (1x = real-time, 10x = 10x faster)")
    print("• Multiple output formats (console, JSON)")
    print("• Realistic sales patterns")
    print("• Artist tier impact on sales")
    print("• Venue size impact on sales")
    print("• Time-based sales velocity")

    print("\n🎪 Perfect for Demonstrating:")
    print("• Real-time data processing")
    print("• Streaming data architectures")
    print("• Data pipeline concepts")
    print("• Scalable data systems")
    print("• Real-world data patterns")

    print("\n💡 Demo Tips:")
    print("• Use fast speeds (20x+) for quick demos")
    print("• Use JSON format to show data structure")
    print("• Use real-time (1x) to show realistic timing")
    print("• Show cumulative sales building up")
    print("• Point out different artist tiers and venues")


def main():
    """Main function"""

    print_header("TICKET SALES STREAMING DEMO")

    print("🎫 Welcome to the Real-Time Ticket Sales Demo!")
    print("This demo shows live ticket sales happening across all future shows.")

    while True:
        print("\n" + "=" * 40)
        print("Choose an option:")
        print("1. 🎪 Run streaming demo")
        print("2. ℹ️  Show demo information")
        print("3. ❌ Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            run_streaming_demo()
        elif choice == "2":
            show_demo_info()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-3.")

        if choice in ["1", "2"]:
            input("\nPress Enter to return to main menu...")


if __name__ == "__main__":
    main()

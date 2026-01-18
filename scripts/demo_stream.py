#!/usr/bin/env python3
"""
Demo script for real-time ticket sales streaming
Shows different ways to use the stream_tickets.py script
"""

import subprocess
import sys


def run_demo():
    """Run a demo of the ticket sales stream"""

    print("🎫 Real-time Ticket Sales Stream Demo")
    print("=" * 50)

    print("\n1. Basic console output (10x speed, 2 minutes):")
    print(
        "   Command: python scripts/stream_tickets.py --speed 10 --duration 2 --format console"
    )

    print("\n2. JSON Lines output (5x speed, 1 minute):")
    print(
        "   Command: python scripts/stream_tickets.py --speed 5 --duration 1 --format jsonl"
    )

    print("\n3. Limited events (20x speed, max 50 events):")
    print(
        "   Command: python scripts/stream_tickets.py --speed 20 --max-events 50 --format console"
    )

    print("\n4. Continuous streaming (real-time):")
    print("   Command: python scripts/stream_tickets.py --format console")

    print("\n" + "=" * 50)
    print("Choose a demo to run:")
    print("1. Fast demo (2 minutes, 10x speed)")
    print("2. JSON output demo (1 minute, 5x speed)")
    print("3. Limited events demo (50 events, 20x speed)")
    print("4. Continuous streaming (real-time)")
    print("5. Exit")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            print("\n🚀 Running fast demo (2 minutes, 10x speed)...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "10",
                    "--duration",
                    "2",
                    "--format",
                    "console",
                ]
            )
            break

        elif choice == "2":
            print("\n📄 Running JSON output demo (1 minute, 5x speed)...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "5",
                    "--duration",
                    "1",
                    "--format",
                    "jsonl",
                ]
            )
            break

        elif choice == "3":
            print("\n🎯 Running limited events demo (50 events, 20x speed)...")
            subprocess.run(
                [
                    sys.executable,
                    "scripts/stream_tickets.py",
                    "--speed",
                    "20",
                    "--max-events",
                    "50",
                    "--format",
                    "console",
                ]
            )
            break

        elif choice == "4":
            print("\n⏰ Starting continuous streaming (real-time)...")
            print("Press Ctrl+C to stop")
            subprocess.run(
                [sys.executable, "scripts/stream_tickets.py", "--format", "console"]
            )
            break

        elif choice == "5":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    run_demo()

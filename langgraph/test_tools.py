#!/usr/bin/env python3
"""
Simple test script for FANalyze agent tools
Run this to verify tools are working correctly
"""

from tools import query_show_data, query_ticket_sales


def test_show_tool():
    """Test query_show_data tool"""
    print("\n" + "=" * 60)
    print("Testing query_show_data tool")
    print("=" * 60)

    # Test 1: Query future shows
    print("\n1. Query future shows:")
    result = query_show_data.invoke({"show_type": "future", "limit": 5})
    print(result)

    # Test 2: Query past shows
    print("\n2. Query past shows:")
    result = query_show_data.invoke({"show_type": "past", "limit": 5})
    print(result)


def test_ticket_sales_tool():
    """Test query_ticket_sales tool"""
    print("\n" + "=" * 60)
    print("Testing query_ticket_sales tool")
    print("=" * 60)

    # Test 1: Query recent ticket sales
    print("\n1. Query recent ticket sales (last 24 hours):")
    result = query_ticket_sales.invoke({"hours": 24, "limit": 5})
    print(result)

    # Test 2: Query ticket sales for specific artist
    print("\n2. Query ticket sales for Metallica:")
    result = query_ticket_sales.invoke(
        {"artist_name": "Metallica", "hours": 168, "limit": 5}
    )
    print(result)


if __name__ == "__main__":
    print("🧪 Testing FANalyze Agent Tools\n")

    try:
        test_show_tool()
        test_ticket_sales_tool()
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()

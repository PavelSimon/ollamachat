#!/usr/bin/env python3
"""
Simple test script for internet search functionality
"""

from search_service import search_service

def test_search():
    """Test the search functionality"""
    print("Testing Internet Search Service")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "Python programming language",
        "Current weather",
        "Latest news technology"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 40)
        
        try:
            result = search_service.search_and_format(query, max_results=3)
            print(result)
            print("✅ Search successful")
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print("\n" + "=" * 50)
    print("Search test completed!")

if __name__ == "__main__":
    test_search()
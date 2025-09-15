#!/usr/bin/env python3
"""
Test script to demonstrate expiry date caching functionality
"""
from findexpiry import find_exp, is_cache_valid, clear_expiry_cache, force_expiry_recalculation
import time

def test_caching():
    """Test the caching functionality"""
    print("🧪 Testing Expiry Date Caching System")
    print("=" * 50)
    
    # Check initial cache status
    print("\n1. Checking initial cache status...")
    if is_cache_valid():
        print("✅ Cache is valid")
    else:
        print("❌ Cache is invalid or missing")
    
    # Clear cache and test first run
    print("\n2. Clearing cache and testing first calculation...")
    clear_expiry_cache()
    
    start_time = time.time()
    find_exp()
    first_run_time = time.time() - start_time
    print(f"⏱️  First run (no cache): {first_run_time:.2f} seconds")
    
    # Test second run (should use cache)
    print("\n3. Testing second calculation (should use cache)...")
    start_time = time.time()
    find_exp()
    second_run_time = time.time() - start_time
    print(f"⏱️  Second run (with cache): {second_run_time:.2f} seconds")
    
    # Calculate speedup
    if first_run_time > 0:
        speedup = first_run_time / second_run_time
        print(f"🚀 Speedup: {speedup:.1f}x faster with cache!")
    
    # Check cache status again
    print("\n4. Final cache status...")
    if is_cache_valid():
        print("✅ Cache is valid and working")
    else:
        print("❌ Cache is not working properly")

if __name__ == "__main__":
    test_caching()

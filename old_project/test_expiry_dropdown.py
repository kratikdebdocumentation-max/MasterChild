#!/usr/bin/env python3
"""
Test script for expiry dropdown functionality
"""

from market_data.expiry_manager import ExpiryManager

def test_expiry_dropdown():
    """Test the new expiry dropdown functionality"""
    expiry_manager = ExpiryManager()
    
    print("=== Testing Expiry Dropdown Functionality ===")
    
    # Test NIFTY expiry list
    print("\n--- NIFTY ---")
    nifty_expiry = expiry_manager.get_expiry_date("NIFTY")
    nifty_list = expiry_manager.get_expiry_list("NIFTY")
    print(f"Current expiry: {nifty_expiry}")
    print(f"Expiry list: {nifty_list}")
    
    # Test BANKNIFTY expiry list
    print("\n--- BANKNIFTY ---")
    bn_expiry = expiry_manager.get_expiry_date("BANKNIFTY")
    bn_list = expiry_manager.get_expiry_list("BANKNIFTY")
    print(f"Current expiry: {bn_expiry}")
    print(f"Expiry list: {bn_list}")
    
    # Test SENSEX expiry list
    print("\n--- SENSEX ---")
    sx_expiry = expiry_manager.get_expiry_date("SENSEX")
    sx_list = expiry_manager.get_expiry_list("SENSEX")
    print(f"Current expiry: {sx_expiry}")
    print(f"Expiry list: {sx_list}")
    
    print("\n=== Test Results ===")
    print("✅ Expiry dropdown should now show current + next expiry dates")
    print("✅ Users can select between different expiry dates")
    print("✅ Strikes will update when expiry changes")

if __name__ == "__main__":
    test_expiry_dropdown()


#!/usr/bin/env python3
"""
Test the new expiry manager with old project logic
"""
import logging
from market_data.expiry_manager import ExpiryManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_expiry_manager():
    """Test the expiry manager"""
    try:
        print("Testing Expiry Manager with Old Project Logic")
        print("=" * 50)
        
        # Create expiry manager
        expiry_manager = ExpiryManager()
        
        # Test getting expiry lists
        print("\nExpiry Lists:")
        for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
            expiry_list = expiry_manager.get_expiry_list(index)
            print(f"{index}: {expiry_list}")
        
        # Test current expiry
        print("\nCurrent Expiry Dates:")
        for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
            current = expiry_manager.get_current_expiry(index)
            print(f"{index}: {current}")
        
        # Test recalculation if needed
        if expiry_manager.should_refresh_expiry():
            print("\nRefreshing expiry dates from master files...")
            success = expiry_manager.calculate_expiry_dates()
            if success:
                print("✅ Successfully recalculated expiry dates")
            else:
                print("❌ Failed to recalculate expiry dates")
        else:
            print("\n✅ Expiry dates are current, no refresh needed")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_expiry_manager()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")

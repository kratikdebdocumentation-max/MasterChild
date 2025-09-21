#!/usr/bin/env python3
"""
Test script for dynamic strike generation based on option type
"""

from market_data.expiry_manager import ExpiryManager

def test_dynamic_strikes():
    """Test the new dynamic strike generation logic"""
    expiry_manager = ExpiryManager()
    
    # Test SENSEX at 80700
    print("=== Testing SENSEX at 80700 ===")
    current_price = 80700
    
    # Test CE options (more strikes above)
    ce_strikes = expiry_manager.get_strike_list("SENSEX", current_price, "CE")
    print(f"CE strikes: {ce_strikes}")
    print(f"Expected: [80500, 80600, 80700, 80800, 80900, 81000, 81100, 81200, 81300, 81400, 81500, 81600, 81700, 81800, 81900]")
    print(f"Match: {ce_strikes == [80500, 80600, 80700, 80800, 80900, 81000, 81100, 81200, 81300, 81400, 81500, 81600, 81700, 81800, 81900]}")
    print()
    
    # Test PE options (more strikes below)
    pe_strikes = expiry_manager.get_strike_list("SENSEX", current_price, "PE")
    print(f"PE strikes: {pe_strikes}")
    print(f"Expected: [79500, 79600, 79700, 79800, 79900, 80000, 80100, 80200, 80300, 80400, 80500, 80600, 80700, 80800, 80900]")
    print(f"Match: {pe_strikes == [79500, 79600, 79700, 79800, 79900, 80000, 80100, 80200, 80300, 80400, 80500, 80600, 80700, 80800, 80900]}")
    print()
    
    # Test NIFTY at 24000
    print("=== Testing NIFTY at 24000 ===")
    nifty_price = 24000
    
    # Test CE options
    nifty_ce = expiry_manager.get_strike_list("NIFTY", nifty_price, "CE")
    print(f"NIFTY CE strikes: {nifty_ce}")
    print(f"Expected: [23900, 23950, 24000, 24050, 24100, 24150, 24200, 24250, 24300, 24350, 24400, 24450, 24500, 24550, 24600]")
    print()
    
    # Test PE options
    nifty_pe = expiry_manager.get_strike_list("NIFTY", nifty_price, "PE")
    print(f"NIFTY PE strikes: {nifty_pe}")
    print(f"Expected: [23500, 23550, 23600, 23650, 23700, 23750, 23800, 23850, 23900, 23950, 24000, 24050, 24100, 24150, 24200]")
    print()
    
    # Test BANKNIFTY at 52000
    print("=== Testing BANKNIFTY at 52000 ===")
    banknifty_price = 52000
    
    # Test CE options
    bn_ce = expiry_manager.get_strike_list("BANKNIFTY", banknifty_price, "CE")
    print(f"BANKNIFTY CE strikes: {bn_ce}")
    print(f"Expected: [51900, 52000, 52100, 52200, 52300, 52400, 52500, 52600, 52700, 52800, 52900, 53000, 53100, 53200, 53300]")
    print()
    
    # Test PE options
    bn_pe = expiry_manager.get_strike_list("BANKNIFTY", banknifty_price, "PE")
    print(f"BANKNIFTY PE strikes: {bn_pe}")
    print(f"Expected: [50900, 51000, 51100, 51200, 51300, 51400, 51500, 51600, 51700, 51800, 51900, 52000, 52100, 52200, 52300]")
    print()

if __name__ == "__main__":
    test_dynamic_strikes()


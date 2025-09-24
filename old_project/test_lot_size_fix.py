#!/usr/bin/env python3
"""
Test script to verify the lot size fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_data.symbol_manager import SymbolManager
from logger import applicationLogger

def test_lot_size_fix():
    """Test the new lot size method"""
    print("Testing lot size fix...")
    
    # Initialize symbol manager
    symbol_manager = SymbolManager()
    
    # Test getting lot sizes for each index
    indices = ["NIFTY", "BANKNIFTY", "SENSEX"]
    
    for index in indices:
        print(f"\nTesting {index}:")
        lot_size = symbol_manager.get_lot_size_for_index(index)
        if lot_size:
            print(f"  ✓ Found lot size: {lot_size}")
            # Generate quantity options
            quantities = symbol_manager.get_quantity_options(lot_size)
            print(f"  ✓ Generated quantities: {quantities[:5]}...")  # Show first 5
        else:
            print(f"  ✗ Lot size not found for {index}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_lot_size_fix()

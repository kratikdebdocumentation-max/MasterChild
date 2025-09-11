"""
Simple test for WebSocket subscription
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from market_data.symbol_manager import SymbolManager
from logger import applicationLogger

def test_simple_subscription():
    """Test simple WebSocket subscription"""
    try:
        print("Starting simple subscription test...")
        
        # Initialize managers
        account_manager = AccountManager()
        websocket_manager = WebSocketManager(account_manager, None, None)
        symbol_manager = SymbolManager()
        
        # Login to master account
        print("Logging in to master account...")
        success, client_name = account_manager.login_account(1)
        if not success:
            print(f"Failed to login: {client_name}")
            return
        
        print(f"Logged in successfully: {client_name}")
        
        # Get API
        api = account_manager.get_api(1)
        if not api:
            print("No API available")
            return
        
        print(f"API obtained: {type(api)}")
        
        # Test symbol
        trading_symbol = "SENSEX2591181400CE"
        token = symbol_manager.get_token(trading_symbol)
        exchange = 'BFO'
        
        print(f"Testing symbol: {trading_symbol}")
        print(f"Token: {token}")
        print(f"Exchange: {exchange}")
        
        if not token:
            print("No token found")
            return
        
        # Setup WebSocket with simple callbacks
        def order_callback(tick_data):
            print(f"Order: {tick_data}")
        
        def quote_callback(tick_data):
            print(f"Quote: {tick_data}")
            if isinstance(tick_data, dict) and 'lp' in tick_data:
                print(f"Price: {tick_data['lp']}")
        
        def open_callback():
            print("WebSocket opened")
        
        # Start WebSocket
        print("Starting WebSocket...")
        api.start_websocket(
            order_update_callback=order_callback,
            subscribe_callback=quote_callback,
            socket_open_callback=open_callback
        )
        
        # Wait for connection
        import time
        time.sleep(2)
        
        # Test subscription
        print("Testing subscription...")
        success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        if success:
            print("Subscription successful!")
            print("Waiting for price updates...")
            
            # Wait for updates
            for i in range(15):
                time.sleep(1)
                print(f"Waiting... {i+1}/15")
        else:
            print("Subscription failed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_simple_subscription()

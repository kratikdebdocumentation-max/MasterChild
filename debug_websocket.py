"""
Debug WebSocket functionality for live prices
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from market_data.symbol_manager import SymbolManager
from market_data.expiry_manager import ExpiryManager
from logger import applicationLogger

def test_websocket_subscription():
    """Test WebSocket subscription functionality"""
    try:
        print("🔧 Starting WebSocket debug test")
        applicationLogger.info("🔧 Starting WebSocket debug test")
        
        # Initialize managers
        account_manager = AccountManager()
        websocket_manager = WebSocketManager(account_manager, None, None)
        symbol_manager = SymbolManager()
        expiry_manager = ExpiryManager()
        
        # Login to master account
        print("🔧 Logging in to master account...")
        applicationLogger.info("🔧 Logging in to master account...")
        success, client_name = account_manager.login_account(1)
        if not success:
            print(f"❌ Failed to login: {client_name}")
            applicationLogger.error(f"❌ Failed to login: {client_name}")
            return
        
        print(f"✅ Logged in successfully: {client_name}")
        applicationLogger.info(f"✅ Logged in successfully: {client_name}")
        
        # Get API
        api = account_manager.get_api(1)
        if not api:
            applicationLogger.error("❌ No API available")
            return
        
        applicationLogger.info(f"✅ API obtained: {type(api)}")
        
        # Test symbol generation
        applicationLogger.info("🔧 Testing symbol generation...")
        
        # Test SENSEX symbol
        index = "SENSEX"
        expiry = "11SEP25"  # Today's expiry
        strike = "81400"
        option = "CE"
        
        if index == "SENSEX":
            # Generate SENSEX symbol
            day = expiry[:2]
            month = expiry[2:5]
            year = expiry[5:]
            
            month_num = datetime.strptime(month, '%b').month
            year_full = 2000 + int(year)
            day_num = int(day)
            
            trading_symbol = f"SENSEX{year}{month_num:d}{day_num:02d}{strike}{option}"
        else:
            trading_symbol = f"{index}{expiry}{option}{strike}"
        
        applicationLogger.info(f"✅ Generated trading symbol: {trading_symbol}")
        
        # Get token for the symbol
        applicationLogger.info("🔧 Getting token for symbol...")
        token = symbol_manager.get_token(trading_symbol)
        applicationLogger.info(f"✅ Token: {token}")
        
        if not token:
            applicationLogger.error("❌ No token found for symbol")
            return
        
        # Determine exchange
        exchange = 'BFO' if 'SENSEX' in trading_symbol else 'NFO'
        applicationLogger.info(f"✅ Exchange: {exchange}")
        
        # Setup WebSocket with debug callbacks
        applicationLogger.info("🔧 Setting up WebSocket with debug callbacks...")
        
        def order_update_callback(tick_data):
            applicationLogger.info(f"📋 Order update: {tick_data}")
        
        def quote_update_callback(tick_data):
            applicationLogger.info(f"📊 Quote update: {tick_data}")
            applicationLogger.info(f"📊 Quote type: {type(tick_data)}")
            if isinstance(tick_data, dict):
                applicationLogger.info(f"📊 Quote keys: {list(tick_data.keys())}")
                if 'lp' in tick_data:
                    applicationLogger.info(f"📊 Last price: {tick_data['lp']}")
                if 'tsym' in tick_data:
                    applicationLogger.info(f"📊 Symbol: {tick_data['tsym']}")
        
        def socket_open_callback():
            applicationLogger.info("🔌 WebSocket opened")
        
        # Start WebSocket
        applicationLogger.info("🔧 Starting WebSocket...")
        api.start_websocket(
            order_update_callback=order_update_callback,
            subscribe_callback=quote_update_callback,
            socket_open_callback=socket_open_callback
        )
        
        # Wait a moment for connection
        import time
        time.sleep(2)
        
        # Test subscription
        applicationLogger.info("🔧 Testing subscription...")
        success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        if success:
            applicationLogger.info("✅ Subscription successful!")
            applicationLogger.info("🔧 Waiting for price updates...")
            
            # Wait for updates
            for i in range(10):
                time.sleep(1)
                applicationLogger.info(f"⏰ Waiting... {i+1}/10")
        else:
            applicationLogger.error("❌ Subscription failed!")
        
    except Exception as e:
        applicationLogger.error(f"❌ Error in test: {e}")
        import traceback
        applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_websocket_subscription()

#!/usr/bin/env python3
"""
Test script to demonstrate enhanced websocket logging functionality
This script will show websocket responses in the logs after subscribing to a symbol
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from trading.order_manager import OrderManager
from logger import applicationLogger

def test_websocket_logging():
    """
    Test the enhanced websocket logging by subscribing to a symbol
    and showing the quote responses in the logs
    """
    try:
        applicationLogger.info("=" * 60)
        applicationLogger.info("🧪 STARTING WEBSOCKET LOGGING TEST")
        applicationLogger.info("=" * 60)
        
        # Initialize managers
        account_manager = AccountManager()
        order_manager = OrderManager()
        websocket_manager = WebSocketManager(account_manager, order_manager)
        
        # Test with Master account (Account 1)
        account_num = 1
        applicationLogger.info(f"🔧 Testing with Account {account_num}")
        
        # Login to account
        applicationLogger.info("🔐 Logging into account...")
        success, client_name = account_manager.login_account(account_num)
        
        if not success:
            applicationLogger.error(f"❌ Failed to login: {client_name}")
            return False
        
        applicationLogger.info(f"✅ Successfully logged in as: {client_name}")
        
        # Get API instance
        api = account_manager.get_api(account_num)
        if not api:
            applicationLogger.error("❌ No API available")
            return False
        
        applicationLogger.info("✅ API instance obtained")
        
        # Connect websocket feed
        applicationLogger.info("🔌 Connecting websocket feed...")
        websocket_connected = websocket_manager.connect_feed(account_num)
        
        if not websocket_connected:
            applicationLogger.error("❌ Failed to connect websocket feed")
            return False
        
        applicationLogger.info("✅ Websocket feed connected")
        
        # Wait for websocket to be ready
        applicationLogger.info("⏳ Waiting for websocket to be ready...")
        time.sleep(3)
        
        # Test subscription to a common symbol (NIFTY 50)
        exchange = "NSE"
        token = "26000"  # NIFTY 50 token
        symbol = "NIFTY 50"
        
        applicationLogger.info(f"🔌 Testing subscription to {symbol}")
        applicationLogger.info(f"🔌 Exchange: {exchange}, Token: {token}")
        
        # Subscribe to symbol
        subscription_success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        if subscription_success:
            applicationLogger.info(f"✅ Successfully subscribed to {symbol}")
            applicationLogger.info("📊 Now waiting for quote responses...")
            applicationLogger.info("📊 Check the log files for detailed quote data!")
            applicationLogger.info("📊 Log files location: logs/")
            applicationLogger.info("📊 Look for files: Log_Master1_WS_*.log and applicationLogger_*.log")
            
            # Wait for quote updates
            applicationLogger.info("⏳ Waiting for quote updates (30 seconds)...")
            for i in range(30):
                time.sleep(1)
                if i % 5 == 0:  # Log every 5 seconds
                    applicationLogger.info(f"⏰ Waiting for quotes... {i+1}/30 seconds")
            
            # Unsubscribe
            applicationLogger.info(f"🔌 Unsubscribing from {symbol}")
            unsubscribe_success = websocket_manager.unsubscribe_from_symbol(api, exchange, token)
            
            if unsubscribe_success:
                applicationLogger.info(f"✅ Successfully unsubscribed from {symbol}")
            else:
                applicationLogger.warning(f"⚠️ Unsubscription may have failed for {symbol}")
                
        else:
            applicationLogger.error(f"❌ Failed to subscribe to {symbol}")
            return False
        
        applicationLogger.info("=" * 60)
        applicationLogger.info("✅ WEBSOCKET LOGGING TEST COMPLETED")
        applicationLogger.info("=" * 60)
        applicationLogger.info("📋 Check the following log files for detailed websocket responses:")
        applicationLogger.info("📋 - logs/Log_Master1_WS_*.log (for quote updates)")
        applicationLogger.info("📋 - logs/applicationLogger_*.log (for general application logs)")
        applicationLogger.info("=" * 60)
        
        return True
        
    except Exception as e:
        applicationLogger.error(f"❌ Error in websocket logging test: {e}")
        import traceback
        applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Websocket Logging Test...")
    print("📋 This test will demonstrate enhanced websocket logging")
    print("📋 Check the logs/ directory for detailed websocket responses")
    print("=" * 60)
    
    success = test_websocket_logging()
    
    if success:
        print("✅ Test completed successfully!")
        print("📋 Check the log files for websocket responses")
    else:
        print("❌ Test failed! Check the logs for details")

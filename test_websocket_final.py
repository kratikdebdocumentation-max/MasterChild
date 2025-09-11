#!/usr/bin/env python3
"""
Final test to check websocket subscription and quote logging
This test will wait longer and check for actual quote responses
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from trading.order_manager import OrderManager
from logger import applicationLogger

def test_websocket_final():
    """
    Final test for websocket subscription and quote logging
    """
    try:
        applicationLogger.info("=" * 60)
        applicationLogger.info("FINAL WEBSOCKET TEST")
        applicationLogger.info("=" * 60)
        
        # Initialize managers
        account_manager = AccountManager()
        order_manager = OrderManager()
        websocket_manager = WebSocketManager(account_manager, order_manager)
        
        # Test with Master account (Account 1)
        account_num = 1
        applicationLogger.info(f"Testing with Account {account_num}")
        
        # Ensure login
        api = account_manager.get_api(account_num)
        if not api:
            applicationLogger.info("No API available, attempting login...")
            success, client_name = account_manager.login_account(account_num)
            if not success:
                applicationLogger.error(f"Login failed: {client_name}")
                return False
            else:
                applicationLogger.info(f"Login successful: {client_name}")
                api = account_manager.get_api(account_num)
        else:
            applicationLogger.info("API already available")
        
        # Test websocket connection
        applicationLogger.info("Testing websocket connection...")
        try:
            websocket_connected = websocket_manager.connect_feed(account_num)
            if websocket_connected:
                applicationLogger.info("Websocket feed connected successfully")
            else:
                applicationLogger.error("Failed to connect websocket feed")
                return False
        except Exception as e:
            applicationLogger.error(f"Websocket connection error: {e}")
            return False
        
        # Wait for connection to stabilize
        applicationLogger.info("Waiting for websocket to stabilize...")
        time.sleep(5)
        
        # Test subscription to a simple symbol
        exchange = "NSE"
        token = "26000"  # NIFTY 50
        symbol = "NIFTY 50"
        
        applicationLogger.info(f"Testing subscription to {symbol}")
        applicationLogger.info(f"Exchange: {exchange}, Token: {token}")
        
        # Subscribe
        applicationLogger.info("Attempting subscription...")
        subscription_success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        applicationLogger.info(f"Subscription result: {subscription_success}")
        
        # Wait for quote updates regardless of subscription result
        applicationLogger.info("Waiting for quote updates (30 seconds)...")
        applicationLogger.info("Check the log files for quote responses:")
        applicationLogger.info(f"- logs/Log_Master1_WS_{time.strftime('%Y-%m-%d')}.log")
        applicationLogger.info(f"- logs/applicationLogger_{time.strftime('%Y-%m-%d')}.log")
        
        quote_count = 0
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                applicationLogger.info(f"Waiting for quotes... {i+1}/30 seconds")
        
        # Check if we received any quotes
        applicationLogger.info("Checking for quote responses in logs...")
        
        # Try to subscribe to a different symbol to test
        applicationLogger.info("Trying a different symbol...")
        exchange2 = "NSE"
        token2 = "22"  # INFY
        symbol2 = "INFY"
        
        applicationLogger.info(f"Testing subscription to {symbol2}")
        subscription_success2 = websocket_manager.subscribe_to_symbol(api, exchange2, token2)
        applicationLogger.info(f"Second subscription result: {subscription_success2}")
        
        # Wait a bit more
        applicationLogger.info("Waiting for more quote updates (15 seconds)...")
        for i in range(15):
            time.sleep(1)
            if i % 3 == 0:
                applicationLogger.info(f"Waiting... {i+1}/15 seconds")
        
        # Unsubscribe
        applicationLogger.info(f"Unsubscribing from {symbol}")
        unsubscribe_success = websocket_manager.unsubscribe_from_symbol(api, exchange, token)
        applicationLogger.info(f"Unsubscribe result: {unsubscribe_success}")
        
        applicationLogger.info(f"Unsubscribing from {symbol2}")
        unsubscribe_success2 = websocket_manager.unsubscribe_from_symbol(api, exchange2, token2)
        applicationLogger.info(f"Second unsubscribe result: {unsubscribe_success2}")
        
        applicationLogger.info("=" * 60)
        applicationLogger.info("FINAL WEBSOCKET TEST COMPLETED")
        applicationLogger.info("=" * 60)
        applicationLogger.info("Check the log files for any quote responses that may have been received")
        
        return True
        
    except Exception as e:
        applicationLogger.error(f"Error in final websocket test: {e}")
        import traceback
        applicationLogger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Starting Final Websocket Test...")
    print("This test will check websocket subscription and quote logging")
    print("=" * 60)
    
    success = test_websocket_final()
    
    if success:
        print("Test completed!")
        print("Check the log files for websocket responses")
    else:
        print("Test failed! Check the logs for details")

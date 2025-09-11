#!/usr/bin/env python3
"""
Simple test to check websocket subscription and logging without emojis
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from trading.order_manager import OrderManager
from logger import applicationLogger

def test_simple_websocket():
    """
    Simple test for websocket subscription and logging
    """
    try:
        applicationLogger.info("=" * 60)
        applicationLogger.info("SIMPLE WEBSOCKET TEST")
        applicationLogger.info("=" * 60)
        
        # Initialize managers
        account_manager = AccountManager()
        order_manager = OrderManager()
        websocket_manager = WebSocketManager(account_manager, order_manager)
        
        # Test with Master account (Account 1)
        account_num = 1
        applicationLogger.info(f"Testing with Account {account_num}")
        
        # Check if already logged in
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
        
        # Check API authentication status
        applicationLogger.info("Checking API authentication...")
        try:
            # Try to get user profile to verify authentication
            profile = api.get_user_profile()
            if profile:
                applicationLogger.info(f"API is authenticated. Profile: {profile}")
            else:
                applicationLogger.warning("API profile is None - may not be authenticated")
        except Exception as e:
            applicationLogger.error(f"API authentication check failed: {e}")
            applicationLogger.info("Attempting to re-login...")
            success, client_name = account_manager.login_account(account_num)
            if not success:
                applicationLogger.error(f"Re-login failed: {client_name}")
                return False
            else:
                applicationLogger.info(f"Re-login successful: {client_name}")
        
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
        time.sleep(3)
        
        # Test subscription to a simple symbol
        exchange = "NSE"
        token = "26000"  # NIFTY 50
        symbol = "NIFTY 50"
        
        applicationLogger.info(f"Testing subscription to {symbol}")
        applicationLogger.info(f"Exchange: {exchange}, Token: {token}")
        
        # Subscribe
        subscription_success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        if subscription_success:
            applicationLogger.info(f"Subscription successful for {symbol}")
            
            # Wait for quote updates
            applicationLogger.info("Waiting for quote updates (20 seconds)...")
            applicationLogger.info("Check the log files for quote responses:")
            applicationLogger.info(f"- logs/Log_Master1_WS_{time.strftime('%Y-%m-%d')}.log")
            applicationLogger.info(f"- logs/applicationLogger_{time.strftime('%Y-%m-%d')}.log")
            
            for i in range(20):
                time.sleep(1)
                if i % 5 == 0:
                    applicationLogger.info(f"Waiting for quotes... {i+1}/20 seconds")
            
            # Unsubscribe
            applicationLogger.info(f"Unsubscribing from {symbol}")
            unsubscribe_success = websocket_manager.unsubscribe_from_symbol(api, exchange, token)
            if unsubscribe_success:
                applicationLogger.info(f"Unsubscribed from {symbol}")
            else:
                applicationLogger.warning(f"Unsubscription failed for {symbol}")
                
        else:
            applicationLogger.error(f"Subscription failed for {symbol}")
            return False
        
        applicationLogger.info("=" * 60)
        applicationLogger.info("SIMPLE WEBSOCKET TEST COMPLETED")
        applicationLogger.info("=" * 60)
        
        return True
        
    except Exception as e:
        applicationLogger.error(f"Error in simple websocket test: {e}")
        import traceback
        applicationLogger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Starting Simple Websocket Test...")
    print("This test will check websocket subscription and logging")
    print("=" * 60)
    
    success = test_simple_websocket()
    
    if success:
        print("Test completed successfully!")
        print("Check the log files for websocket responses")
    else:
        print("Test failed! Check the logs for details")

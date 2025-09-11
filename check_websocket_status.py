#!/usr/bin/env python3
"""
Diagnostic script to check websocket subscription status and troubleshoot logging issues
"""

import sys
import time
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading.account_manager import AccountManager
from trading.websocket_manager import WebSocketManager
from trading.order_manager import OrderManager
from logger import applicationLogger, master1WSLogger, child2WSLogger

def check_websocket_status():
    """
    Check websocket subscription status and troubleshoot logging issues
    """
    try:
        applicationLogger.info("=" * 80)
        applicationLogger.info("🔍 WEBSOCKET STATUS DIAGNOSTIC")
        applicationLogger.info("=" * 80)
        
        # Initialize managers
        account_manager = AccountManager()
        order_manager = OrderManager()
        websocket_manager = WebSocketManager(account_manager, order_manager)
        
        # Check Master account (Account 1)
        account_num = 1
        applicationLogger.info(f"🔧 Checking Account {account_num} (Master)")
        
        # Check if logged in
        api = account_manager.get_api(account_num)
        if not api:
            applicationLogger.error("❌ No API available - Account not logged in")
            applicationLogger.info("🔐 Attempting to login...")
            success, client_name = account_manager.login_account(account_num)
            if not success:
                applicationLogger.error(f"❌ Login failed: {client_name}")
                return False
            else:
                applicationLogger.info(f"✅ Login successful: {client_name}")
                api = account_manager.get_api(account_num)
        
        # Check API methods
        applicationLogger.info("🔍 Checking API methods...")
        if hasattr(api, 'subscribe'):
            applicationLogger.info("✅ API has subscribe method")
        else:
            applicationLogger.error("❌ API does not have subscribe method")
            applicationLogger.info(f"Available methods: {[m for m in dir(api) if not m.startswith('_')]}")
            return False
        
        # Check websocket connection
        applicationLogger.info("🔍 Checking websocket connection...")
        try:
            # Try to get websocket status (if available)
            if hasattr(api, 'get_websocket_status'):
                status = api.get_websocket_status()
                applicationLogger.info(f"WebSocket Status: {status}")
            else:
                applicationLogger.info("No websocket status method available")
        except Exception as e:
            applicationLogger.warning(f"Could not check websocket status: {e}")
        
        # Test websocket connection
        applicationLogger.info("🔌 Testing websocket connection...")
        websocket_connected = websocket_manager.connect_feed(account_num)
        
        if websocket_connected:
            applicationLogger.info("✅ Websocket feed connected successfully")
        else:
            applicationLogger.error("❌ Failed to connect websocket feed")
            return False
        
        # Wait for connection to stabilize
        applicationLogger.info("⏳ Waiting for websocket to stabilize...")
        time.sleep(3)
        
        # Test subscription to a simple symbol
        exchange = "NSE"
        token = "26000"  # NIFTY 50
        symbol = "NIFTY 50"
        
        applicationLogger.info(f"🔌 Testing subscription to {symbol}")
        applicationLogger.info(f"🔌 Exchange: {exchange}, Token: {token}")
        
        # Subscribe
        subscription_success = websocket_manager.subscribe_to_symbol(api, exchange, token)
        
        if subscription_success:
            applicationLogger.info(f"✅ Subscription successful for {symbol}")
            
            # Wait for quote updates
            applicationLogger.info("📊 Waiting for quote updates (15 seconds)...")
            applicationLogger.info("📊 Check the following log files:")
            applicationLogger.info(f"📊 - logs/Log_Master1_WS_{datetime.now().strftime('%Y-%m-%d')}.log")
            applicationLogger.info(f"📊 - logs/applicationLogger_{datetime.now().strftime('%Y-%m-%d')}.log")
            
            quote_received = False
            for i in range(15):
                time.sleep(1)
                if i % 3 == 0:
                    applicationLogger.info(f"⏰ Waiting for quotes... {i+1}/15 seconds")
            
            # Check if we received any quotes
            if not quote_received:
                applicationLogger.warning("⚠️ No quote updates received in 15 seconds")
                applicationLogger.info("🔍 Possible issues:")
                applicationLogger.info("1. Market might be closed")
                applicationLogger.info("2. Symbol might not be valid")
                applicationLogger.info("3. Websocket callback might not be working")
                applicationLogger.info("4. Check log files for any error messages")
            
            # Unsubscribe
            applicationLogger.info(f"🔌 Unsubscribing from {symbol}")
            unsubscribe_success = websocket_manager.unsubscribe_from_symbol(api, exchange, token)
            if unsubscribe_success:
                applicationLogger.info(f"✅ Unsubscribed from {symbol}")
            else:
                applicationLogger.warning(f"⚠️ Unsubscription failed for {symbol}")
                
        else:
            applicationLogger.error(f"❌ Subscription failed for {symbol}")
            return False
        
        # Check log files
        applicationLogger.info("📋 Checking log files...")
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            applicationLogger.info(f"📋 Found {len(log_files)} log files:")
            for log_file in sorted(log_files):
                file_path = os.path.join(log_dir, log_file)
                file_size = os.path.getsize(file_path)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                applicationLogger.info(f"📋 - {log_file} ({file_size} bytes, modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            applicationLogger.error("❌ Logs directory not found")
        
        applicationLogger.info("=" * 80)
        applicationLogger.info("✅ DIAGNOSTIC COMPLETED")
        applicationLogger.info("=" * 80)
        
        return True
        
    except Exception as e:
        applicationLogger.error(f"❌ Error in diagnostic: {e}")
        import traceback
        applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def check_recent_logs():
    """
    Check recent log entries for websocket activity
    """
    try:
        applicationLogger.info("📋 Checking recent log entries...")
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            applicationLogger.error("❌ Logs directory not found")
            return
        
        # Find today's log files
        today = datetime.now().strftime('%Y-%m-%d')
        log_files = []
        
        for file in os.listdir(log_dir):
            if file.endswith('.log') and today in file:
                log_files.append(os.path.join(log_dir, file))
        
        if not log_files:
            applicationLogger.warning(f"⚠️ No log files found for today ({today})")
            return
        
        applicationLogger.info(f"📋 Found {len(log_files)} log files for today")
        
        # Check each log file for websocket activity
        for log_file in log_files:
            applicationLogger.info(f"📋 Checking {os.path.basename(log_file)}...")
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    websocket_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['websocket', 'subscribe', 'quote', '📊', '🔌'])]
                    
                    if websocket_lines:
                        applicationLogger.info(f"📋 Found {len(websocket_lines)} websocket-related entries")
                        # Show last 5 websocket entries
                        for line in websocket_lines[-5:]:
                            applicationLogger.info(f"📋 {line.strip()}")
                    else:
                        applicationLogger.warning(f"⚠️ No websocket activity found in {os.path.basename(log_file)}")
                        
            except Exception as e:
                applicationLogger.error(f"❌ Error reading {log_file}: {e}")
                
    except Exception as e:
        applicationLogger.error(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    print("🔍 Starting Websocket Status Check...")
    print("=" * 80)
    
    # Check recent logs first
    check_recent_logs()
    
    print("\n" + "=" * 80)
    
    # Run diagnostic
    success = check_websocket_status()
    
    if success:
        print("✅ Diagnostic completed successfully!")
        print("📋 Check the log files for detailed information")
    else:
        print("❌ Diagnostic failed! Check the logs for details")

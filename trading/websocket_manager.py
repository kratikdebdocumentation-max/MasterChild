"""
WebSocket management for real-time data feeds
"""
import threading
import logging
import time
from typing import Callable, Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for all accounts"""
    
    def __init__(self, account_manager, order_manager=None, simple_order_manager=None):
        self.account_manager = account_manager
        self.order_manager = order_manager
        self.simple_order_manager = simple_order_manager
        self.live_price_callback = None
        self.order_status_callback = None
        self.buy_order_completed_callback = None
        self.sell_order_completed_callback = None
        self.pnl_update_callback = None
        self.order_state_callback = None
        self.order_rejection_callback = None
        
        # Retry logic properties
        self.connection_status = {}  # Track connection status for each account
        self.retry_attempts = {}    # Track retry attempts for each account
        self.max_retry_attempts = 5  # Maximum retry attempts
        self.base_retry_delay = 5    # Base delay in seconds
        self.max_retry_delay = 300   # Maximum delay in seconds (5 minutes)
        self.retry_threads = {}      # Track retry threads
        self.connection_monitor_thread = None
        self.monitor_active = False
    
    def setup_websocket_callbacks(self, account_num: int):
        """Setup WebSocket callbacks for a specific account"""
        
        def order_update_callback(tick_data):
            """Handle order updates"""
            logger.info(f"Order update for account {account_num}: {tick_data}")
            
            # Process order update in a separate thread
            thread = threading.Thread(target=self._process_order_update, args=(tick_data, account_num))
            thread.start()
            
            # Update order status display
            if self.order_status_callback:
                try:
                    status = tick_data.get('status', 'Unknown')
                    trantype = tick_data.get('trantype', 'Unknown')
                    reporttype = tick_data.get('reporttype', 'Unknown')
                    rejreason = tick_data.get('rejreason', '')
                    price = tick_data.get('prc', '')
                    
                    # Format status message with custom descriptions
                    logger.info(f"Order status debug - status: '{status}', reporttype: '{reporttype}', trantype: '{trantype}', price: '{price}'")
                    
                    if status.upper() == 'OPEN' and reporttype.lower() == 'new':
                        if trantype.upper() == 'B':
                            status_message = f"Buy Order Open @ {price}" if price else "Buy Order Open"
                        elif trantype.upper() == 'S':
                            status_message = f"Sell Order Open @ {price}" if price else "Sell Order Open"
                        else:
                            status_message = f"Order Open @ {price}" if price else "Order Open"
                    elif status.upper() == 'OPEN' and reporttype.lower() == 'modify':
                        status_message = "Order Modified"
                    elif status.upper() == 'COMPLETE':
                        # Format based on transaction type
                        if trantype.upper() == 'B':
                            status_message = f"Buy Order Complete @ {price}" if price else "Buy Order Complete"
                        elif trantype.upper() == 'S':
                            status_message = f"Sell Order Complete @ {price}" if price else "Sell Order Complete"
                        else:
                            status_message = f"Order Complete @ {price}" if price else "Order Complete"
                        
                        # Check if this is a buy order completion - ONLY for successfully filled orders
                        if trantype.upper() == 'B' and self.buy_order_completed_callback:
                            try:
                                symbol = tick_data.get('tsym', '')
                                price_float = float(price) if price else 0.0
                                
                                # Additional validation: Check if order was actually filled (not rejected)
                                # Look for rejection reason in the tick data
                                rejreason = tick_data.get('rejreason', '')
                                
                                if not rejreason:  # No rejection reason = successfully filled
                                    self.buy_order_completed_callback(account_num, symbol, price_float)
                                    logger.info(f"Buy order successfully completed for account {account_num}: {symbol} @ {price_float}")
                                else:
                                    logger.warning(f"Buy order marked as COMPLETE but has rejection reason: {rejreason} - NOT calling completion callback")
                                    
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error processing buy order completion: {e}")
                        
                        # Check if this is a sell order completion
                        if trantype.upper() == 'S' and self.sell_order_completed_callback:
                            try:
                                symbol = tick_data.get('tsym', '')
                                price_float = float(price) if price else 0.0
                                self.sell_order_completed_callback(account_num, symbol, price_float)
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error processing sell order completion: {e}")
                    elif status.upper() == 'CANCELLED':
                        status_message = "Order Cancelled"
                    elif status.upper() == 'REJECTED':
                        status_message = f"Order Rejected: {rejreason}" if rejreason else "Order Rejected"
                        
                        # Handle order rejection - specifically check for buy order rejections
                        if self.order_rejection_callback and trantype.upper() == 'B':
                            try:
                                symbol = tick_data.get('tsym', '')
                                rejection_reason = rejreason if rejreason else "Unknown reason"
                                self.order_rejection_callback(account_num, symbol, rejection_reason)
                            except Exception as e:
                                logger.error(f"Error processing buy order rejection: {e}")
                    else:
                        # Fallback to custom format instead of original
                        if trantype.upper() == 'B':
                            status_message = f"Buy Order {status} @ {price}" if price else f"Buy Order {status}"
                        elif trantype.upper() == 'S':
                            status_message = f"Sell Order {status} @ {price}" if price else f"Sell Order {status}"
                        else:
                            status_message = f"Order {status} @ {price}" if price else f"Order {status}"
                    
                    self.order_status_callback(account_num, status_message, trantype)
                except Exception as e:
                    logger.error(f"Error updating order status: {e}")
        
        def quote_update_callback(tick_data):
            """Handle quote updates - only for master account (account 1)"""
            
            # Update WebSocket health tracking
            if hasattr(self, 'websocket_health_callback') and self.websocket_health_callback:
                try:
                    self.websocket_health_callback(account_num)
                except Exception as e:
                    logger.error(f"Error updating WebSocket health: {e}")
            
            # Only handle live price updates for master account (account 1)
            if account_num == 1 and 'lp' in tick_data and self.live_price_callback:
                try:
                    live_price = float(tick_data['lp'])
                    self.live_price_callback(live_price)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing live price: {e}")
            elif account_num != 1:
                logger.info(f"Quote update received for child account {account_num} - not processing live price")
        
        def socket_open_callback():
            """Handle socket open"""
            logger.info(f"WebSocket is now open for Account {account_num}")
        
        return order_update_callback, quote_update_callback, socket_open_callback
    
    def set_live_price_callback(self, callback: Callable[[float], None]):
        """Set callback for live price updates"""
        self.live_price_callback = callback
    
    def set_order_status_callback(self, callback: Callable[[int, str, str], None]):
        """Set callback for order status updates"""
        self.order_status_callback = callback
    
    def set_buy_order_completed_callback(self, callback: Callable[[int, str, float], None]):
        """Set callback for when buy orders are completed"""
        self.buy_order_completed_callback = callback
    
    def set_sell_order_completed_callback(self, callback: Callable[[int, str, float], None]):
        """Set callback for when sell orders are completed"""
        self.sell_order_completed_callback = callback
    
    def set_pnl_update_callback(self, callback: Callable[[int], None]):
        """Set callback for PnL updates"""
        self.pnl_update_callback = callback
    
    def set_order_state_callback(self, callback: Callable[[int, str, str, str], None]):
        """Set callback for order state updates"""
        self.order_state_callback = callback
    
    def set_order_rejection_callback(self, callback: Callable[[int, str, str], None]):
        """Set callback for order rejection updates"""
        self.order_rejection_callback = callback
    
    def set_websocket_health_callback(self, callback: Callable[[int], None]):
        """Set callback for WebSocket health updates"""
        self.websocket_health_callback = callback
    
    def _process_order_update(self, tick_data: Dict[str, Any], account_num: int):
        """Process order update data"""
        try:
            # Handle order update using simple order manager if available
            if self.simple_order_manager:
                order_id = tick_data.get('norenordno', '')
                status = tick_data.get('status', '')
                rejreason = tick_data.get('rejreason', '')
                
                if order_id and status:
                    self.simple_order_manager.update_order_status(account_num, order_id, status, rejreason)
            elif self.order_manager:
                # Fallback to original order manager
                self.order_manager.handle_order_update(tick_data)
            
            # Process order status updates
            self._process_order_status(tick_data, account_num)
            
            # Update PnL if callback is set
            if self.pnl_update_callback:
                try:
                    self.pnl_update_callback(account_num)
                except Exception as e:
                    logger.error(f"Error updating PnL for account {account_num}: {e}")
            
            # Update order state for cross-account coordination
            if self.order_state_callback:
                try:
                    status = tick_data.get('status', '')
                    reporttype = tick_data.get('reporttype', '')
                    trantype = tick_data.get('trantype', '')
                    if status and reporttype and trantype:
                        self.order_state_callback(account_num, status, reporttype, trantype)
                except Exception as e:
                    logger.error(f"Error updating order state for account {account_num}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing order update for account {account_num}: {e}")
    
    def _process_order_status(self, tick_data: Dict[str, Any], account_num: int):
        """Process order status and update UI accordingly"""
        # This will be implemented when we integrate with the GUI
        # For now, just log the status
        status = tick_data.get('status')
        report_type = tick_data.get('reporttype')
        trantype = tick_data.get('trantype')
        
        if status and report_type and trantype:
            logger.info(f"Account {account_num} - {trantype} {status} {report_type}")
    
    def connect_feed(self, account_num: int) -> bool:
        """
        Connect WebSocket feed for an account
        
        Args:
            account_num: Account number
            
        Returns:
            bool: True if successful
        """
        try:
            api = self.account_manager.get_api(account_num)
            if not api:
                logger.error(f"No API available for account {account_num}")
                return False
            
            order_callback, quote_callback, open_callback = self.setup_websocket_callbacks(account_num)
            
            api.start_websocket(
                order_update_callback=order_callback,
                subscribe_callback=quote_callback,
                socket_open_callback=open_callback
            )
            
            # Mark connection as established
            self.mark_connection_established(account_num)
            return True
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket for account {account_num}: {e}")
            # Mark connection as lost to trigger retry
            self.mark_connection_lost(account_num)
            return False
    
    def subscribe_to_symbol(self, api, exchange: str, token: str) -> bool:
        """
        Subscribe to a symbol for real-time updates
        
        Args:
            api: API instance
            exchange: Exchange name
            token: Symbol token
            
        Returns:
            bool: True if successful
        """
        try:
            websocket_token = f'{exchange}|{token}'
            api.subscribe(websocket_token)
            logger.info(f"Subscribed to token: {websocket_token}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to symbol: {e}")
            return False
    
    def unsubscribe_from_symbol(self, api, exchange: str, token: str) -> bool:
        """
        Unsubscribe from a symbol
        
        Args:
            api: API instance
            exchange: Exchange name
            token: Symbol token
            
        Returns:
            bool: True if successful
        """
        try:
            websocket_token = f'{exchange}|{token}'
            api.unsubscribe(websocket_token)
            logger.info(f"Unsubscribed from token: {websocket_token}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from symbol: {e}")
            return False
    
    def start_connection_monitoring(self):
        """Start connection monitoring thread"""
        if self.monitor_active:
            return
            
        self.monitor_active = True
        self.connection_monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self.connection_monitor_thread.start()
        logger.info("WebSocket connection monitoring started")
    
    def stop_connection_monitoring(self):
        """Stop connection monitoring"""
        self.monitor_active = False
        if self.connection_monitor_thread:
            self.connection_monitor_thread.join(timeout=1)
        logger.info("WebSocket connection monitoring stopped")
    
    def _monitor_connections(self):
        """Monitor websocket connections and handle reconnections"""
        while self.monitor_active:
            try:
                for account_num in [1, 2]:  # Master and Child accounts
                    if account_num in self.connection_status:
                        status = self.connection_status[account_num]
                        if status == "disconnected" and account_num not in self.retry_threads:
                            logger.info(f"Account {account_num} is disconnected, starting retry process")
                            self._start_retry_process(account_num)
                
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _start_retry_process(self, account_num: int):
        """Start retry process for a disconnected account"""
        if account_num in self.retry_threads:
            return  # Already retrying
        
        retry_thread = threading.Thread(target=self._retry_connection, args=(account_num,), daemon=True)
        self.retry_threads[account_num] = retry_thread
        retry_thread.start()
    
    def _retry_connection(self, account_num: int):
        """Retry websocket connection with exponential backoff"""
        attempt = 0
        
        while attempt < self.max_retry_attempts and self.monitor_active:
            try:
                attempt += 1
                self.retry_attempts[account_num] = attempt
                
                # Calculate delay with exponential backoff
                delay = min(self.base_retry_delay * (2 ** (attempt - 1)), self.max_retry_delay)
                logger.info(f"Retry attempt {attempt}/{self.max_retry_attempts} for account {account_num} in {delay} seconds")
                
                time.sleep(delay)
                
                if not self.monitor_active:
                    break
                
                # Attempt reconnection
                logger.info(f"Attempting to reconnect account {account_num}...")
                success = self.connect_feed(account_num)
                
                if success:
                    logger.info(f"Successfully reconnected account {account_num}")
                    self.connection_status[account_num] = "connected"
                    self.retry_attempts[account_num] = 0
                    break
                else:
                    logger.warning(f"Reconnection attempt {attempt} failed for account {account_num}")
                    
            except Exception as e:
                logger.error(f"Error in retry attempt {attempt} for account {account_num}: {e}")
        
        # Clean up retry thread
        if account_num in self.retry_threads:
            del self.retry_threads[account_num]
        
        if attempt >= self.max_retry_attempts:
            logger.error(f"Max retry attempts reached for account {account_num}. Manual intervention required.")
            self.connection_status[account_num] = "failed"
    
    def mark_connection_lost(self, account_num: int):
        """Mark connection as lost and trigger retry process"""
        logger.warning(f"WebSocket connection lost for account {account_num}")
        self.connection_status[account_num] = "disconnected"
        
        # Notify order status callback about network failure
        if self.order_status_callback:
            try:
                self.order_status_callback(account_num, "NETWORK FAIL - EXIT Manual", "NETWORK_ERROR")
            except Exception as e:
                logger.error(f"Error notifying order status callback: {e}")
        
        # Start retry process if monitoring is active
        if self.monitor_active and account_num not in self.retry_threads:
            self._start_retry_process(account_num)
    
    def mark_connection_established(self, account_num: int):
        """Mark connection as established"""
        logger.info(f"WebSocket connection established for account {account_num}")
        self.connection_status[account_num] = "connected"
        self.retry_attempts[account_num] = 0
        
        # Notify order status callback about connection restored
        if self.order_status_callback:
            try:
                self.order_status_callback(account_num, "CONNECTION RESTORED", "NETWORK_RESTORED")
            except Exception as e:
                logger.error(f"Error notifying order status callback: {e}")
        
        # Clean up any retry thread
        if account_num in self.retry_threads:
            del self.retry_threads[account_num]
    
    def get_connection_status(self, account_num: int) -> str:
        """Get connection status for an account"""
        return self.connection_status.get(account_num, "unknown")
    
    def is_connected(self, account_num: int) -> bool:
        """Check if account is connected"""
        return self.connection_status.get(account_num) == "connected"

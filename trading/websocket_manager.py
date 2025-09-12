"""
WebSocket management for real-time data feeds
"""
import threading
from typing import Callable, Dict, Any
from logger import childWSLogger, master1WSLogger, applicationLogger

class WebSocketManager:
    """Manages WebSocket connections for all accounts"""
    
    def __init__(self, account_manager, order_manager):
        self.account_manager = account_manager
        self.order_manager = order_manager
        self.loggers = {
            1: master1WSLogger,
            2: childWSLogger
        }
        self.live_price_callback = None
        self.order_status_callback = None
        self.buy_order_completed_callback = None
        self.sell_order_completed_callback = None
    
    def setup_websocket_callbacks(self, account_num: int):
        """Setup WebSocket callbacks for a specific account"""
        
        def order_update_callback(tick_data):
            """Handle order updates"""
            logger = self.loggers.get(account_num, applicationLogger)
            logger.info(tick_data)
            
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
                    # Debug logging to see actual values
                    applicationLogger.info(f"Order status debug - status: '{status}', reporttype: '{reporttype}', trantype: '{trantype}', price: '{price}'")
                    
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
                        
                        # Check if this is a buy order completion
                        if trantype.upper() == 'B' and self.buy_order_completed_callback:
                            try:
                                symbol = tick_data.get('tsym', '')
                                price_float = float(price) if price else 0.0
                                self.buy_order_completed_callback(account_num, symbol, price_float)
                            except (ValueError, TypeError) as e:
                                applicationLogger.error(f"Error processing buy order completion: {e}")
                        
                        # Check if this is a sell order completion
                        if trantype.upper() == 'S' and self.sell_order_completed_callback:
                            try:
                                symbol = tick_data.get('tsym', '')
                                price_float = float(price) if price else 0.0
                                self.sell_order_completed_callback(account_num, symbol, price_float)
                            except (ValueError, TypeError) as e:
                                applicationLogger.error(f"Error processing sell order completion: {e}")
                    elif status.upper() == 'CANCELLED':
                        status_message = "Order Cancelled"
                    elif status.upper() == 'REJECTED':
                        status_message = f"Order Rejected: {rejreason}" if rejreason else "Order Rejected"
                    else:
                        # Fallback to custom format instead of original
                        if trantype.upper() == 'B':
                            status_message = f"Buy Order {status} @ {price}" if price else f"Buy Order {status}"
                        elif trantype.upper() == 'S':
                            status_message = f"Sell Order {status} @ {price}" if price else f"Sell Order {status}"
                        else:
                            status_message = f"Order {status} @ {price}" if price else f"Order {status}"
                    
                    self.order_status_callback(account_num, status_message)
                except Exception as e:
                    applicationLogger.error(f"Error updating order status: {e}")
        
        def quote_update_callback(tick_data):
            """Handle quote updates - only for master account (account 1)"""
            print(f"Quote Received for Account {account_num}: {tick_data}")
            
            # Only handle live price updates for master account (account 1)
            if account_num == 1 and 'lp' in tick_data and self.live_price_callback:
                try:
                    live_price = float(tick_data['lp'])
                    self.live_price_callback(live_price)
                except (ValueError, TypeError) as e:
                    applicationLogger.error(f"Error parsing live price: {e}")
            elif account_num != 1:
                applicationLogger.info(f"Quote update received for child account {account_num} - not processing live price")
        
        def socket_open_callback():
            """Handle socket open"""
            print(f"WebSocket is now open for Account {account_num}")
        
        return order_update_callback, quote_update_callback, socket_open_callback
    
    def set_live_price_callback(self, callback: Callable[[float], None]):
        """Set callback for live price updates"""
        self.live_price_callback = callback
    
    def set_order_status_callback(self, callback: Callable[[int, str], None]):
        """Set callback for order status updates"""
        self.order_status_callback = callback
    
    def set_buy_order_completed_callback(self, callback: Callable[[int, str, float], None]):
        """Set callback for when buy orders are completed"""
        self.buy_order_completed_callback = callback
    
    def set_sell_order_completed_callback(self, callback: Callable[[int, str, float], None]):
        """Set callback for when sell orders are completed"""
        self.sell_order_completed_callback = callback
    
    def _process_order_update(self, tick_data: Dict[str, Any], account_num: int):
        """Process order update data"""
        try:
            # Handle order update
            self.order_manager.handle_order_update(tick_data)
            
            # Process order status updates
            self._process_order_status(tick_data, account_num)
            
        except Exception as e:
            applicationLogger.error(f"Error processing order update for account {account_num}: {e}")
    
    def _process_order_status(self, tick_data: Dict[str, Any], account_num: int):
        """Process order status and update UI accordingly"""
        # This will be implemented when we integrate with the GUI
        # For now, just log the status
        status = tick_data.get('status')
        report_type = tick_data.get('reporttype')
        trantype = tick_data.get('trantype')
        
        if status and report_type and trantype:
            applicationLogger.info(f"Account {account_num} - {trantype} {status} {report_type}")
    
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
                return False
            
            order_callback, quote_callback, open_callback = self.setup_websocket_callbacks(account_num)
            
            api.start_websocket(
                order_update_callback=order_callback,
                subscribe_callback=quote_callback,
                socket_open_callback=open_callback
            )
            
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error connecting WebSocket for account {account_num}: {e}")
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
            applicationLogger.info(f"Subscribed to token: {websocket_token}")
            return True
        except Exception as e:
            applicationLogger.error(f"Error subscribing to symbol: {e}")
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
            applicationLogger.info(f"Unsubscribed from token: {websocket_token}")
            return True
        except Exception as e:
            applicationLogger.error(f"Error unsubscribing from symbol: {e}")
            return False

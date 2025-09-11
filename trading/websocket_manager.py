"""
WebSocket management for real-time data feeds
"""
import threading
from typing import Callable, Dict, Any
from logger import child2WSLogger, master1WSLogger, applicationLogger
from utils.telegram_notifications import send_sos_message

class WebSocketManager:
    """Manages WebSocket connections for all accounts"""
    
    def __init__(self, account_manager, order_manager, main_window=None):
        self.account_manager = account_manager
        self.order_manager = order_manager
        self.main_window = main_window  # Reference to main window for button updates
        self.loggers = {
            1: master1WSLogger,
            2: child2WSLogger
        }
    
    def setup_websocket_callbacks(self, account_num: int):
        """Setup WebSocket callbacks for a specific account"""
        
        def order_update_callback(tick_data):
            """Handle order updates"""
            logger = self.loggers.get(account_num, applicationLogger)
            logger.info(tick_data)
            
            # Process order update in a separate thread
            thread = threading.Thread(target=self._process_order_update, args=(tick_data, account_num))
            thread.start()
        
        def quote_update_callback(tick_data):
            """Handle quote updates"""
            logger = self.loggers.get(account_num, applicationLogger)
            
            # Log the raw quote data
            logger.info(f"[QUOTE] WebSocket Quote Response for Account {account_num}: {tick_data}")
            logger.info(f"[QUOTE] Quote Data Type: {type(tick_data)}")
            
            if isinstance(tick_data, dict):
                # Log specific quote fields for better debugging
                logger.info(f"[QUOTE] Symbol (tsym): {tick_data.get('tsym', 'N/A')}")
                logger.info(f"[QUOTE] Exchange (e): {tick_data.get('e', 'N/A')}")
                logger.info(f"[QUOTE] Token (tk): {tick_data.get('tk', 'N/A')}")
                logger.info(f"[QUOTE] Last Price (lp): {tick_data.get('lp', 'N/A')}")
                logger.info(f"[QUOTE] Open Price (o): {tick_data.get('o', 'N/A')}")
                logger.info(f"[QUOTE] High Price (h): {tick_data.get('h', 'N/A')}")
                logger.info(f"[QUOTE] Low Price (l): {tick_data.get('l', 'N/A')}")
                logger.info(f"[QUOTE] Close Price (c): {tick_data.get('c', 'N/A')}")
                logger.info(f"[QUOTE] Volume (v): {tick_data.get('v', 'N/A')}")
                logger.info(f"[QUOTE] Percentage Change (pc): {tick_data.get('pc', 'N/A')}")
                logger.info(f"[QUOTE] Average Price (ap): {tick_data.get('ap', 'N/A')}")
                logger.info(f"[QUOTE] Message Type (t): {tick_data.get('t', 'N/A')}")
            else:
                logger.warning(f"[QUOTE] Quote data is not a dictionary: {tick_data}")
            
            # Also print to console for immediate feedback
            print(f"Quote Received for Account {account_num}: {tick_data}")
        
        def socket_open_callback():
            """Handle socket open"""
            logger = self.loggers.get(account_num, applicationLogger)
            logger.info(f"[WS] WebSocket connection opened for Account {account_num}")
            print(f"WebSocket is now open for Account {account_num}")
        
        return order_update_callback, quote_update_callback, socket_open_callback
    
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
        try:
            # Get the appropriate button for this account
            button = self._get_order_status_button(account_num)
            if not button:
                applicationLogger.warning(f"No button found for account {account_num}")
                return
            
            # Determine entity name for logging
            entity = f"Account{account_num}"
            if account_num == 1:
                entity = "Master"
            elif account_num == 2:
                entity = "Child"
            
            # Debug logging
            applicationLogger.info(f"Processing order status for {entity}, button: {button is not None}")
            applicationLogger.info(f"Order data: status={tick_data.get('status')}, reporttype={tick_data.get('reporttype')}, trantype={tick_data.get('trantype')}")
            
            # Process the order using the comprehensive logic
            self.process_order(tick_data, entity, button)
            
        except Exception as e:
            applicationLogger.error(f"Error processing order status for account {account_num}: {e}")
            import traceback
            applicationLogger.error(f"Traceback: {traceback.format_exc()}")
    
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
            
            # Log subscription attempt
            applicationLogger.info(f"[SUBSCRIBE] Attempting to subscribe to: {websocket_token}")
            applicationLogger.info(f"[SUBSCRIBE] Exchange: {exchange}, Token: {token}")
            applicationLogger.info(f"[SUBSCRIBE] API Type: {type(api)}")
            
            # Perform subscription
            result = api.subscribe(websocket_token)
            
            # Log subscription result
            applicationLogger.info(f"[SUBSCRIBE] Subscription result: {result}")
            applicationLogger.info(f"[SUBSCRIBE] Subscription result type: {type(result)}")
            
            if result:
                applicationLogger.info(f"[SUBSCRIBE] Successfully subscribed to: {websocket_token}")
                applicationLogger.info(f"[SUBSCRIBE] WebSocket will now send quote updates for this symbol")
            else:
                applicationLogger.warning(f"[SUBSCRIBE] Subscription returned False for: {websocket_token}")
            
            return bool(result)
            
        except Exception as e:
            applicationLogger.error(f"[ERROR] Error subscribing to symbol {exchange}|{token}: {e}")
            import traceback
            applicationLogger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
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
            
            # Log unsubscription attempt
            applicationLogger.info(f"[WS] Attempting to unsubscribe from: {websocket_token}")
            
            # Perform unsubscription
            result = api.unsubscribe(websocket_token)
            
            # Log unsubscription result
            applicationLogger.info(f"[WS] Unsubscription result: {result}")
            
            if result:
                applicationLogger.info(f"[SUCCESS] Successfully unsubscribed from: {websocket_token}")
            else:
                applicationLogger.warning(f"[WARNING] Unsubscription returned False for: {websocket_token}")
            
            return bool(result)
            
        except Exception as e:
            applicationLogger.error(f"[ERROR] Error unsubscribing from symbol {exchange}|{token}: {e}")
            import traceback
            applicationLogger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            return False
    
    def _get_order_status_button(self, account_num: int):
        """Get the order status button for a specific account"""
        if not self.main_window:
            return None
        
        # Map account numbers to their corresponding buttons
        button_map = {
            1: getattr(self.main_window, 'master1_status_button', None),
            2: getattr(self.main_window, 'child2_status_button', None)
        }
        
        return button_map.get(account_num)
    
    def process_order(self, tick_data: Dict[str, Any], entity: str, button):
        """
        Process order updates with comprehensive status handling
        
        Args:
            tick_data: Order data from WebSocket
            entity: Entity name (Master1, Child2, etc.)
            button: Tkinter button to update
        """
        print(f" WS {entity} Data = {tick_data}")
        
        # Log to appropriate logger
        logger = self.loggers.get(1 if entity == "Master" else 
                                2 if entity == "Child" else 1)
        logger.info(f" WS {entity} Data = {tick_data}")

        # Check if it's an options order (NFO or BFO)
        exchange = tick_data.get('exch')
        if exchange not in ['NFO', 'BFO']:
            return

        status = tick_data.get('status')
        report_type = tick_data.get('reporttype')
        trantype = tick_data.get('trantype')

        # PENDING status handling
        if status == 'PENDING' and exchange in ['NFO', 'BFO']:
            if trantype == 'B':
                if report_type == 'NewAck':
                    applicationLogger.info(f"PLACE BUY ORDER for {entity}")
                elif report_type == 'ModAck':
                    applicationLogger.info(f"MODIFY BUY ORDER for {entity}")
                elif report_type == 'PendingCancel':
                    applicationLogger.info(f"Cancel BUY Order for {entity}")
            elif trantype == 'S':
                if report_type == 'NewAck':
                    applicationLogger.info(f"PLACE SELL ORDER for {entity}")
                elif report_type == 'ModAck':
                    applicationLogger.info(f"MODIFY SELL ORDER for {entity}")
                elif report_type == 'PendingCancel':
                    applicationLogger.info(f"Cancel SELL Order for {entity}")

        # OPEN status handling
        elif status == 'OPEN' and exchange in ['NFO', 'BFO']:
            if trantype == 'B':
                if report_type == 'New':
                    self.log_and_config_button(button, "#007bff", "Buy Open", f"Buy Order OPEN for {entity}")
                elif report_type == 'Replaced':
                    self.log_and_config_button(button, "#90EE90", "Buy Modified", f"BUY ORDER: OPEN/REPLACED for {entity}")
            elif trantype == 'S':
                if report_type == 'New':
                    self.log_and_config_button(button, "#90EE90", "Sell Open", f"SELL Order OPEN for {entity}")
                elif report_type == 'Replaced':
                    self.log_and_config_button(button, "#90EE90", "Sell Modified", f"SELL ORDER OPEN/REPLACED for {entity}")

        # COMPLETE status handling
        elif status == 'COMPLETE' and exchange in ['NFO', 'BFO']:
            if trantype == 'B' and report_type == 'Fill':
                self.log_and_config_button(button, "#fd7e14", "Buy Filled", f"BUY ORDER FILLED for {entity}")
                price = tick_data.get('prc')
                if price:
                    send_sos_message(f"Buy Order Filled @{price}")
            elif trantype == 'S' and report_type == 'Fill':
                self.log_and_config_button(button, "#90EE90", "Sell Complete", f"SELL ORDER FILLED for {entity}")
                price = tick_data.get('prc')
                if price:
                    send_sos_message(f"Sell Order Filled @{price}")

        # CANCELED status handling
        elif status == 'CANCELED' and exchange in ['NFO', 'BFO']:
            if trantype == 'B' and report_type == 'Canceled':
                self.log_and_config_button(button, "#90EE90", "Buy Cancelled", f"BUY ORDER Cancelled for {entity}")
            elif trantype == 'S' and report_type == 'Canceled':
                self.log_and_config_button(button, "red", "Sell Cancelled", f"SELL ORDER Cancelled for {entity}")

        # REJECTED status handling
        elif trantype == 'B' and report_type == 'Rejected':
            applicationLogger.info(f"Processing BUY REJECTED for {entity}")
            self.log_and_config_button(button, "#dc3545", "Buy Rejected", f"BUY ORDER Rejected for {entity}")
        elif trantype == 'S' and report_type == 'Rejected':
            applicationLogger.info(f"Processing SELL REJECTED for {entity}")
            self.log_and_config_button(button, "#dc3545", "Sell Rejected", f"SELL ORDER Rejected for {entity}")

    def log_and_config_button(self, button, color: str, text: str, log_message: str):
        """
        Update button appearance and log message
        
        Args:
            button: Tkinter button to update
            color: Background color for the button
            text: Text to display on the button
            log_message: Message to log
        """
        try:
            applicationLogger.info(f"log_and_config_button called: button={button is not None}, color={color}, text={text}")
            if button:
                button.config(bg=color, text=text)
                applicationLogger.info(f"Button updated successfully: {text}")
            else:
                applicationLogger.warning("Button is None, cannot update")
            applicationLogger.info(log_message)
        except Exception as e:
            applicationLogger.error(f"Error updating button: {e}")
            import traceback
            applicationLogger.error(f"Traceback: {traceback.format_exc()}")
    
    def subscribe_to_symbol(self, api, exchange: str, token: str):
        """Subscribe to a specific symbol for live price updates"""
        try:
            # Format: subscribe([instruments])
            # instruments format: "exchange|token"
            instrument = f"{exchange}|{token}"
            
            applicationLogger.info(f"[WS] WebSocket Subscribe - Exchange: {exchange}, Token: {token}")
            applicationLogger.info(f"[WS] WebSocket Subscribe - Instrument: {instrument}")
            applicationLogger.info(f"[WS] WebSocket Subscribe - API: {api}")
            applicationLogger.info(f"[WS] WebSocket Subscribe - API Type: {type(api)}")
            
            # Check if API has subscribe method
            if hasattr(api, 'subscribe'):
                applicationLogger.info(f"[SUCCESS] API has subscribe method")
            else:
                applicationLogger.error(f"[ERROR] API does not have subscribe method")
                applicationLogger.info(f"[ERROR] API methods: {dir(api)}")
                return False
            
            # Subscribe to touchline data
            applicationLogger.info(f"[WS] Calling api.subscribe('{instrument}')")
            success = api.subscribe(instrument)
            
            applicationLogger.info(f"[WS] Subscribe result: {success}")
            applicationLogger.info(f"[WS] Subscribe result type: {type(success)}")
            
            if success:
                applicationLogger.info(f"[SUCCESS] Subscribed to {instrument} for live price updates")
                return True
            else:
                applicationLogger.error(f"[ERROR] Failed to subscribe to {instrument}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"[ERROR] Error subscribing to symbol {exchange}|{token}: {e}")
            import traceback
            applicationLogger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            return False
    
    def unsubscribe_from_symbol(self, api, exchange: str, token: str):
        """Unsubscribe from a specific symbol"""
        try:
            # Format: unsubscribe(instrument)
            instrument = f"{exchange}|{token}"
            
            applicationLogger.info(f"[WS] WebSocket Unsubscribe - Instrument: {instrument}")
            success = api.unsubscribe(instrument)
            
            applicationLogger.info(f"[WS] Unsubscribe result: {success}")
            
            if success:
                applicationLogger.info(f"[SUCCESS] Unsubscribed from {instrument}")
                return True
            else:
                applicationLogger.error(f"[ERROR] Failed to unsubscribe from {instrument}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"[ERROR] Error unsubscribing from symbol {exchange}|{token}: {e}")
            import traceback
            applicationLogger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            return False
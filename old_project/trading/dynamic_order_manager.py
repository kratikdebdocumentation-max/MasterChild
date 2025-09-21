"""
Dynamic Order Management for Buy and Sell orders
Fast approach without ACK waiting - broker handles rejections automatically
"""
import time
import threading
from typing import Dict, Any, Optional, List
from logger import applicationLogger

class DynamicOrderManager:
    """
    Manages dynamic order adjustments for both Buy and Sell orders
    Uses fast approach without waiting for ACK - broker rejects if order is completed
    """
    
    def __init__(self):
        self.order_configs = {
            'buy': {
                'max_attempts': 5,           # More attempts for buy orders
                'min_interval': 2000,        # 2 seconds between attempts (slower)
                'max_wait_time': 10000,      # 10 seconds overall (longer)
                'buffer_levels': [0.0, 0.0, 0.0, 0.1, 0.2],  # Keep original price longer
                'market_threshold': 5.0,     # 5% drop = market order (more conservative)
                'description': 'Buy order - 5 attempts then market'
            },
            'target': {
                'max_attempts': 3,
                'min_interval': 1000,        # 1 second between attempts
                'max_wait_time': 5000,       # 5 seconds overall
                'buffer_levels': [0.0, 0.1, 0.2, 0.5],  # 0%, 0.1%, 0.2%, 0.5%
                'market_threshold': 2.0,     # 2% drop = market order
                'description': 'Target order - 3 attempts then market'
            },
            'stop_loss': {
                'max_attempts': 3,
                'min_interval': 1000,        # 1 second between attempts
                'max_wait_time': 3000,       # 3 seconds overall (faster for SL)
                'buffer_levels': [0.0, 0.2, 0.5, 1.0],  # 0%, 0.2%, 0.5%, 1.0%
                'market_threshold': 3.0,     # 3% drop = market order
                'description': 'Stop loss - 3 attempts then market'
            },
            'trailing_target': {
                'max_attempts': 3,
                'min_interval': 1000,        # 1 second between attempts
                'max_wait_time': 5000,       # 5 seconds overall
                'buffer_levels': [0.0, 0.1, 0.2, 0.5],  # 0%, 0.1%, 0.2%, 0.5%
                'market_threshold': 2.0,     # 2% drop = market order
                'description': 'Trailing target - 3 attempts then market'
            }
        }
        
        # Track active dynamic orders
        self.active_orders = {}
        self.lock = threading.Lock()
    
    def execute_dynamic_buy_order(self, api, order_id: str, trigger_price: float, 
                                 quantity: int, symbol: str, exchange: str) -> bool:
        """
        Execute dynamic buy order management
        
        Args:
            api: API instance
            order_id: Order ID to modify
            trigger_price: Original trigger price
            quantity: Order quantity
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            
        Returns:
            bool: True if order was filled, False if converted to market
        """
        return self._execute_dynamic_order(api, order_id, trigger_price, quantity, 
                                         symbol, exchange, 'buy')
    
    def execute_dynamic_target_order(self, api, order_id: str, trigger_price: float, 
                                   quantity: int, symbol: str, exchange: str) -> bool:
        """
        Execute dynamic target order management (sell order)
        
        Args:
            api: API instance
            order_id: Order ID to modify
            trigger_price: Original trigger price
            quantity: Order quantity
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            
        Returns:
            bool: True if order was filled, False if converted to market
        """
        return self._execute_dynamic_order(api, order_id, trigger_price, quantity, 
                                         symbol, exchange, 'target')
    
    def execute_dynamic_stop_loss_order(self, api, order_id: str, trigger_price: float, 
                                      quantity: int, symbol: str, exchange: str) -> bool:
        """
        Execute dynamic stop loss order management (sell order)
        
        Args:
            api: API instance
            order_id: Order ID to modify
            trigger_price: Original trigger price
            quantity: Order quantity
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            
        Returns:
            bool: True if order was filled, False if converted to market
        """
        return self._execute_dynamic_order(api, order_id, trigger_price, quantity, 
                                         symbol, exchange, 'stop_loss')
    
    def execute_dynamic_trailing_target_order(self, api, order_id: str, trigger_price: float, 
                                            quantity: int, symbol: str, exchange: str) -> bool:
        """
        Execute dynamic trailing target order management (sell order)
        
        Args:
            api: API instance
            order_id: Order ID to modify
            trigger_price: Original trigger price
            quantity: Order quantity
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            
        Returns:
            bool: True if order was filled, False if converted to market
        """
        return self._execute_dynamic_order(api, order_id, trigger_price, quantity, 
                                         symbol, exchange, 'trailing_target')
    
    def _execute_dynamic_order(self, api, order_id: str, trigger_price: float, 
                             quantity: int, symbol: str, exchange: str, order_type: str) -> bool:
        """
        Core dynamic order management logic
        
        Args:
            api: API instance
            order_id: Order ID to modify
            trigger_price: Original trigger price
            quantity: Order quantity
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            order_type: Type of order (buy/target/stop_loss/trailing_target)
            
        Returns:
            bool: True if order was filled, False if converted to market
        """
        config = self.order_configs[order_type]
        start_time = time.time()
        attempt_count = 0
        last_attempt_time = 0
        
        # Track this order as active
        with self.lock:
            self.active_orders[order_id] = {
                'order_type': order_type,
                'start_time': start_time,
                'trigger_price': trigger_price
            }
        
        applicationLogger.info(f"Starting dynamic order management for {order_type} order {order_id} at price {trigger_price}")
        
        try:
            while time.time() - start_time < config['max_wait_time']:
                current_time = time.time()
                
                # Check if order is filled
                if self._is_order_filled(api, order_id):
                    applicationLogger.info(f"Order {order_id} filled successfully")
                    return True
                
                # Check if enough time has passed since last attempt
                if current_time - last_attempt_time < config['min_interval']:
                    time.sleep(0.1)
                    continue
                
                # Check if we should convert to market order
                if attempt_count >= config['max_attempts']:
                    applicationLogger.info(f"Order {order_id} reached max attempts ({config['max_attempts']}), converting to market order")
                    self._convert_to_market_order(api, order_id, symbol, exchange, quantity)
                    return False
                
                # Get current market price
                current_price = self._get_live_price(api, symbol)
                if current_price is None:
                    applicationLogger.warning(f"Could not get live price for {symbol}, keeping original price")
                    # If we can't get live price, keep the original trigger price
                    current_price = trigger_price
                
                # Calculate new price based on current market conditions
                new_price = self._calculate_dynamic_price(trigger_price, current_price, 
                                                        attempt_count, config)
                
                if new_price is None:
                    # Price dropped too much, convert to market order
                    applicationLogger.info(f"Price dropped significantly for order {order_id}, converting to market order")
                    self._convert_to_market_order(api, order_id, symbol, exchange, quantity)
                    return False
                
                # Send modification immediately (no ACK waiting)
                success = self._modify_order_fast(api, order_id, new_price, symbol, exchange, quantity)
                
                if success:
                    applicationLogger.info(f"Order {order_id} modified (attempt {attempt_count + 1}): {new_price}")
                    attempt_count += 1
                    last_attempt_time = current_time
                else:
                    applicationLogger.warning(f"Failed to modify order {order_id}, will retry")
                
                time.sleep(0.1)  # Small delay before next check
        
        except Exception as e:
            applicationLogger.error(f"Error in dynamic order management for {order_id}: {e}")
        
        finally:
            # Remove from active orders
            with self.lock:
                self.active_orders.pop(order_id, None)
        
        return False
    
    def _calculate_dynamic_price(self, trigger_price: float, current_price: float, 
                               attempt_count: int, config: Dict[str, Any]) -> Optional[float]:
        """
        Calculate dynamic price based on current market conditions
        
        Args:
            trigger_price: Original trigger price
            current_price: Current market price
            attempt_count: Number of attempts made
            config: Order configuration
            
        Returns:
            float: New price for order, None if should convert to market
        """
        # If current price is not available, keep the original trigger price
        if current_price is None:
            applicationLogger.warning(f"Current price not available for order, keeping trigger price: {trigger_price}")
            return trigger_price
        
        # Calculate price deviation
        deviation = abs(trigger_price - current_price) / trigger_price * 100
        
        # Check if price dropped too much (market order threshold)
        if deviation >= config['market_threshold']:
            applicationLogger.info(f"Price deviation {deviation:.2f}% exceeds threshold {config['market_threshold']}%, converting to market order")
            return None  # Signal to convert to market order
        
        # Get buffer level based on attempt count
        if attempt_count < len(config['buffer_levels']):
            buffer_percentage = config['buffer_levels'][attempt_count]
        else:
            buffer_percentage = config['buffer_levels'][-1]  # Use last buffer level
        
        # Calculate new price with buffer
        if buffer_percentage == 0.0:
            # Use exact trigger price
            return trigger_price
        else:
            # Apply buffer to current price
            buffer_amount = current_price * (buffer_percentage / 100)
            new_price = current_price - buffer_amount
            return round(new_price, 2)
    
    def _modify_order_fast(self, api, order_id: str, new_price: float, 
                          symbol: str, exchange: str, quantity: int) -> bool:
        """
        Modify order immediately without waiting for ACK
        
        Args:
            api: API instance
            order_id: Order ID to modify
            new_price: New price for order
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            quantity: Order quantity
            
        Returns:
            bool: True if modification was sent successfully
        """
        try:
            result = api.modify_order(
                exchange=exchange,
                tradingsymbol=symbol,
                orderno=order_id,
                newquantity=quantity,
                newprice_type='LMT',
                newprice=new_price
            )
            
            # Check if modification was successful
            if result and result.get('stat') == 'Ok':
                return True
            else:
                applicationLogger.warning(f"Order modification failed: {result}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"Error modifying order {order_id}: {e}")
            return False
    
    def _convert_to_market_order(self, api, order_id: str, symbol: str, 
                               exchange: str, quantity: int) -> bool:
        """
        Convert order to market order
        
        Args:
            api: API instance
            order_id: Order ID to convert
            symbol: Trading symbol
            exchange: Exchange (BFO/NFO)
            quantity: Order quantity
            
        Returns:
            bool: True if conversion was successful
        """
        try:
            result = api.modify_order(
                exchange=exchange,
                tradingsymbol=symbol,
                orderno=order_id,
                newquantity=quantity,
                newprice_type='MKT',
                newprice=0.0  # Market orders don't need price
            )
            
            if result and result.get('stat') == 'Ok':
                applicationLogger.info(f"Order {order_id} converted to market order successfully")
                return True
            else:
                applicationLogger.error(f"Failed to convert order {order_id} to market: {result}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"Error converting order {order_id} to market: {e}")
            return False
    
    def _is_order_filled(self, api, order_id: str) -> bool:
        """
        Check if order is filled
        
        Args:
            api: API instance
            order_id: Order ID to check
            
        Returns:
            bool: True if order is filled
        """
        try:
            # Get order book to check order status
            orders = api.get_order_book()
            
            if isinstance(orders, dict) and orders.get('stat') == 'Ok':
                order_data = orders.get('data', [])
            elif isinstance(orders, list):
                order_data = orders
            else:
                return False
            
            # Find the specific order
            for order in order_data:
                if order.get('norenordno') == order_id:
                    status = order.get('status', '').upper()
                    return status in ['COMPLETE', 'FILLED']
            
            return False
            
        except Exception as e:
            applicationLogger.error(f"Error checking order status for {order_id}: {e}")
            return False
    
    def _get_live_price(self, api, symbol: str) -> Optional[float]:
        """
        Get live price for symbol
        
        Args:
            api: API instance
            symbol: Trading symbol
            
        Returns:
            float: Current price, None if error
        """
        try:
            # Get live price from the main window's price feed
            # This will be set by the main window when starting dynamic management
            if hasattr(self, 'price_feed_callback') and self.price_feed_callback:
                return self.price_feed_callback(symbol)
            
            # Fallback: try to get price from API (if available)
            # This is a placeholder - in real implementation, you'd get price from your price feed
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting live price for {symbol}: {e}")
            return None
    
    def set_price_feed_callback(self, callback):
        """
        Set the price feed callback function
        
        Args:
            callback: Function that returns current price for a symbol
        """
        self.price_feed_callback = callback
    
    def get_active_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        Get currently active dynamic orders
        
        Returns:
            Dict of active orders
        """
        with self.lock:
            return self.active_orders.copy()
    
    def stop_order_management(self, order_id: str) -> bool:
        """
        Stop dynamic management for a specific order
        
        Args:
            order_id: Order ID to stop managing
            
        Returns:
            bool: True if order was found and stopped
        """
        with self.lock:
            if order_id in self.active_orders:
                del self.active_orders[order_id]
                applicationLogger.info(f"Stopped dynamic management for order {order_id}")
                return True
            return False

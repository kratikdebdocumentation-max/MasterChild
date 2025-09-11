"""
Order management for trading operations
"""
import threading
import pandas as pd
import os
from typing import List, Dict, Any, Optional
from config import Config
from logger import applicationLogger

class OrderManager:
    """Manages order operations and tracking"""
    
    def __init__(self):
        self.order_data = {}
        self.file_path = "orders.csv"
        self._initialize_order_dataframe()
    
    def _initialize_order_dataframe(self):
        """Initialize order DataFrame"""
        columns = ['norenordno', 'uid', 'actid', 'exch', 'tsym', 'trantype',
                  'qty', 'prc', 'pcode', 'remarks', 'status', 'reporttype',
                  'prctyp', 'ret', 'exchordid', 'dscqty', 'rejreason']
        
        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            try:
                self.df_orders = pd.read_csv(self.file_path, on_bad_lines='skip')
            except pd.errors.EmptyDataError:
                self.df_orders = pd.DataFrame(columns=columns)
            except Exception as e:
                applicationLogger.warning(f"Error loading orders CSV file: {e}")
                self.df_orders = pd.DataFrame(columns=columns)
        else:
            self.df_orders = pd.DataFrame(columns=columns)
    
    def place_buy_orders(self, apis: List, quantities: List[int], 
                        trading_symbol: str, price: float, 
                        active_accounts: List[bool]) -> List[Optional[str]]:
        """
        Place buy orders across multiple accounts
        
        Args:
            apis: List of API instances
            quantities: List of quantities for each account
            trading_symbol: Trading symbol
            price: Order price
            active_accounts: List of active account flags
            
        Returns:
            List of order numbers
        """
        order_numbers = [None] * len(apis)
        lock = threading.Lock()
        
        def place_order(api, qty, index):
            try:
                # Determine correct exchange for options
                if 'SENSEX' in trading_symbol:
                    exchange = 'BFO'
                else:
                    exchange = 'NFO'
                
                # Log all parameters being sent to API
                order_params = {
                    'buy_or_sell': 'B',
                    'product_type': 'I',
                    'exchange': exchange,
                    'tradingsymbol': trading_symbol,
                    'quantity': qty,
                    'discloseqty': 0,
                    'price_type': 'LMT',  # Use LMT for limit orders, MKT for market orders
                    'price': price,
                    'trigger_price': None,
                    'retention': Config.RETENTION,
                    'amo': 'NO',
                    'remarks': None
                }
                
                applicationLogger.info(f"Placing order with parameters: {order_params}")
                
                # Place order directly as per API documentation
                order_place = api.place_order(
                    buy_or_sell=order_params['buy_or_sell'],
                    product_type=order_params['product_type'],
                    exchange=order_params['exchange'],
                    tradingsymbol=order_params['tradingsymbol'],
                    quantity=order_params['quantity'],
                    discloseqty=order_params['discloseqty'],
                    price_type=order_params['price_type'],
                    price=order_params['price'],
                    trigger_price=order_params['trigger_price'],
                    retention=order_params['retention'],
                    amo=order_params['amo'],
                    remarks=order_params['remarks']
                )
                
                applicationLogger.info(f"API response: {order_place}")
                applicationLogger.info(f"API response type: {type(order_place)}")
                
                if order_place and 'norenordno' in order_place:
                    norenordno = order_place.get('norenordno')
                    with lock:
                        order_numbers[index] = norenordno
                    applicationLogger.info(f"Buy order placed successfully: {order_place}")
                else:
                    applicationLogger.error(f"Order placement failed: {order_place}")
                    if order_place:
                        applicationLogger.error(f"Response keys: {order_place.keys() if hasattr(order_place, 'keys') else 'No keys'}")
                    
            except Exception as e:
                applicationLogger.error(f"Error placing buy order: {e}")
                import traceback
                applicationLogger.error(f"Traceback: {traceback.format_exc()}")
        
        # Create and start threads for placing orders
        threads = []
        for i, (api, qty, is_active) in enumerate(zip(apis, quantities, active_accounts)):
            if is_active:
                thread = threading.Thread(target=place_order, args=(api, qty, i))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return order_numbers
    
    def place_sell_orders(self, apis: List, quantities: List[int], 
                         trading_symbol: str, price: float, 
                         active_accounts: List[bool]) -> List[Optional[str]]:
        """
        Place sell orders across multiple accounts
        
        Args:
            apis: List of API instances
            quantities: List of quantities for each account
            trading_symbol: Trading symbol
            price: Order price
            active_accounts: List of active account flags
            
        Returns:
            List of order numbers
        """
        order_numbers = [None] * len(apis)
        lock = threading.Lock()
        
        def place_order(api, qty, index):
            try:
                # Determine correct exchange for options
                if 'SENSEX' in trading_symbol:
                    exchange = 'BFO'
                else:
                    exchange = 'NFO'
                
                order_place = api.place_order(
                    buy_or_sell='S',
                    product_type='I',
                    exchange=exchange,
                    tradingsymbol=trading_symbol,
                    quantity=qty,
                    discloseqty=0,
                    price_type='LMT',  # Use LMT for limit orders, MKT for market orders
                    price=price,
                    trigger_price=None,
                    retention=Config.RETENTION,
                    amo='NO',
                    remarks=None
                )
                
                if order_place and 'norenordno' in order_place:
                    norenordno = order_place.get('norenordno')
                    with lock:
                        order_numbers[index] = norenordno
                    applicationLogger.info(f"Sell order placed successfully: {order_place}")
                else:
                    applicationLogger.error(f"Sell order placement failed: {order_place}")
                    
            except Exception as e:
                applicationLogger.error(f"Error placing sell order: {e}")
        
        # Create and start threads for placing orders
        threads = []
        for i, (api, qty, is_active) in enumerate(zip(apis, quantities, active_accounts)):
            if is_active:
                thread = threading.Thread(target=place_order, args=(api, qty, i))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return order_numbers
    
    def place_exit_orders(self, apis: List, quantities: List[int], 
                         trading_symbol: str, price: float, 
                         active_accounts: List[bool]) -> List[Optional[str]]:
        """
        Place exit orders across multiple accounts
        
        Args:
            apis: List of API instances
            quantities: List of quantities for each account
            trading_symbol: Trading symbol
            price: Order price
            active_accounts: List of active account flags
            
        Returns:
            List of order numbers
        """
        order_numbers = [None] * len(apis)
        lock = threading.Lock()
        
        def place_order(api, qty, index):
            try:
                # Determine correct exchange for options
                if 'SENSEX' in trading_symbol:
                    exchange = 'BFO'
                else:
                    exchange = 'NFO'
                
                order_place = api.place_order(
                    buy_or_sell='S',
                    product_type='I',
                    exchange=exchange,
                    tradingsymbol=trading_symbol,
                    quantity=qty,
                    discloseqty=0,
                    price_type='LMT',  # Use LMT for limit orders, MKT for market orders
                    price=price,
                    trigger_price=None,
                    retention=Config.RETENTION,
                    amo='NO',
                    remarks=None
                )
                
                if order_place and 'norenordno' in order_place:
                    norenordno = order_place.get('norenordno')
                    with lock:
                        order_numbers[index] = norenordno
                    applicationLogger.info(f"Exit order placed successfully: {order_place}")
                else:
                    applicationLogger.error(f"Exit order placement failed: {order_place}")
                    
            except Exception as e:
                applicationLogger.error(f"Error placing exit order: {e}")
        
        # Create and start threads for placing orders
        threads = []
        for i, (api, qty, is_active) in enumerate(zip(apis, quantities, active_accounts)):
            if is_active:
                thread = threading.Thread(target=place_order, args=(api, qty, i))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return order_numbers
    
    def cancel_orders(self, apis: List, order_numbers: List[str], 
                     active_accounts: List[bool]) -> None:
        """
        Cancel orders across multiple accounts
        
        Args:
            apis: List of API instances
            order_numbers: List of order numbers to cancel
            active_accounts: List of active account flags
        """
        def cancel_order(api, order_no):
            try:
                api.cancel_order(orderno=order_no)
                applicationLogger.info(f"Order {order_no} cancelled successfully")
            except Exception as e:
                applicationLogger.error(f"Error cancelling order {order_no}: {e}")
        
        threads = []
        for i, (api, order_no, is_active) in enumerate(zip(apis, order_numbers, active_accounts)):
            if is_active and order_no:
                thread = threading.Thread(target=cancel_order, args=(api, order_no))
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()
    
    def modify_orders(self, apis: List, order_numbers: List[str], 
                     quantities: List[int], trading_symbol: str, 
                     price: float, active_accounts: List[bool]) -> None:
        """
        Modify orders across multiple accounts
        
        Args:
            apis: List of API instances
            order_numbers: List of order numbers to modify
            quantities: List of new quantities
            trading_symbol: Trading symbol
            price: New price
            active_accounts: List of active account flags
        """
        def modify_order(api, order_no, qty):
            try:
                # Determine correct exchange for options
                if 'SENSEX' in trading_symbol:
                    exchange = 'BFO'
                else:
                    exchange = 'NFO'
                
                api.modify_order(
                    exchange=exchange,
                    tradingsymbol=trading_symbol,
                    orderno=order_no,
                    newquantity=qty,
                    newprice_type=Config.PRICE_TYPE,
                    newprice=price
                )
                applicationLogger.info(f"Order {order_no} modified successfully")
            except Exception as e:
                applicationLogger.error(f"Error modifying order {order_no}: {e}")
        
        threads = []
        for i, (api, order_no, qty, is_active) in enumerate(zip(apis, order_numbers, quantities, active_accounts)):
            if is_active and order_no:
                thread = threading.Thread(target=modify_order, args=(api, order_no, qty))
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()
    
    def handle_order_update(self, order: Dict[str, Any]) -> None:
        """
        Handle order update and save to CSV
        
        Args:
            order: Order data dictionary
        """
        order_number = order['norenordno']
        
        # Check if the order already exists in the DataFrame
        if order_number in self.df_orders['norenordno'].values:
            # Update the existing order
            applicationLogger.info(f"Updating order {order_number}")
            self.df_orders.loc[self.df_orders['norenordno'] == order_number] = order
        else:
            # Add the new order
            applicationLogger.info(f"New order received: {order_number}")
            self.df_orders = pd.concat([self.df_orders, pd.DataFrame([order])], ignore_index=True)
        
        # Write the updated DataFrame to a CSV file
        self.df_orders.to_csv(self.file_path, index=False)
        applicationLogger.info(f"Order data saved to {self.file_path}")
    
    def get_order_book(self, api) -> List[Dict[str, Any]]:
        """
        Get order book for an account
        
        Args:
            api: API instance
            
        Returns:
            List of orders
        """
        try:
            return api.get_order_book()
        except Exception as e:
            applicationLogger.error(f"Error fetching order book: {e}")
            return []

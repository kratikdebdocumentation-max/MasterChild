"""
Simplified Order Management - No Complex Coordination
Uses account_states.csv for all tracking
"""
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from logger import applicationLogger

class SimpleOrderManager:
    """Simplified order manager with no complex coordination"""
    
    def __init__(self):
        self.account_states_file = "account_states.csv"
        self._initialize_account_states()
    
    def _initialize_account_states(self):
        """Initialize account states CSV if it doesn't exist"""
        if not os.path.exists(self.account_states_file):
            with open(self.account_states_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'account_id', 'account_name', 'login_status', 'api_connected', 
                    'blocked', 'rejected_blocked', 'order_id', 'order_status', 
                    'order_symbol', 'order_side', 'order_qty', 'order_price', 
                    'last_updated'
                ])
                # Initialize with default values
                writer.writerow([1, 'Master', 0, 0, 0, 0, '', '', '', '', 0, 0.0, ''])
                writer.writerow([2, 'Child', 0, 0, 0, 0, '', '', '', '', 0, 0.0, ''])
    
    def _read_account_states(self) -> List[Dict[str, Any]]:
        """Read account states from CSV"""
        states = []
        try:
            with open(self.account_states_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to appropriate types
                    row['account_id'] = int(row['account_id'])
                    row['login_status'] = int(row['login_status'])
                    row['api_connected'] = int(row['api_connected'])
                    row['blocked'] = int(row['blocked'])
                    row['rejected_blocked'] = int(row['rejected_blocked'])
                    row['order_qty'] = int(row['order_qty']) if row['order_qty'] else 0
                    row['order_price'] = float(row['order_price']) if row['order_price'] else 0.0
                    states.append(row)
        except Exception as e:
            applicationLogger.error(f"Error reading account states: {e}")
        return states
    
    def _write_account_states(self, states: List[Dict[str, Any]]):
        """Write account states to CSV"""
        try:
            with open(self.account_states_file, 'w', newline='') as f:
                if states:
                    fieldnames = states[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(states)
        except Exception as e:
            applicationLogger.error(f"Error writing account states: {e}")
    
    def is_account_blocked(self, account_id: int) -> bool:
        """Check if account is blocked (trading or rejection)"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                return bool(state['blocked'] or state['rejected_blocked'])
        return False
    
    def block_account(self, account_id: int, reason: str, is_rejection: bool = False):
        """Block an account with reason"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                if is_rejection:
                    state['rejected_blocked'] = 1
                else:
                    state['blocked'] = 1
                state['last_updated'] = datetime.now().isoformat()
                break
        self._write_account_states(states)
        applicationLogger.info(f"Account {account_id} blocked: {reason}")
    
    def unblock_account(self, account_id: int, unblock_rejection: bool = False):
        """Unblock an account"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                if unblock_rejection:
                    state['rejected_blocked'] = 0
                else:
                    state['blocked'] = 0
                state['last_updated'] = datetime.now().isoformat()
                break
        self._write_account_states(states)
        applicationLogger.info(f"Account {account_id} unblocked")
    
    def place_order(self, account_id: int, api, trading_symbol: str, 
                   quantity: int, price: float, side: str = 'B') -> Optional[str]:
        """Place order for a single account"""
        try:
            # Check if account is blocked
            if self.is_account_blocked(account_id):
                applicationLogger.warning(f"Account {account_id} is blocked, cannot place order")
                return None
            
            # Determine exchange and product type
            if 'SENSEX' in trading_symbol:
                exchange = 'BFO'
                product_type = 'M'
            else:
                exchange = 'NFO'
                product_type = 'I'
            
            # Place order
            order_params = {
                'buy_or_sell': side,
                'product_type': product_type,
                'exchange': exchange,
                'tradingsymbol': trading_symbol,
                'quantity': quantity,
                'discloseqty': 0,
                'price_type': 'LMT',
                'price': price,
                'trigger_price': None,
                'retention': 'DAY',
                'amo': 'NO',
                'remarks': None
            }
            
            applicationLogger.info(f"Placing order for account {account_id}: {order_params}")
            order_response = api.place_order(**order_params)
            
            if order_response and 'norenordno' in order_response:
                order_id = order_response['norenordno']
                self._update_order_info(account_id, order_id, trading_symbol, side, quantity, price, 'PENDING')
                applicationLogger.info(f"Order placed successfully for account {account_id}: {order_id}")
                return order_id
            else:
                applicationLogger.error(f"Order placement failed for account {account_id}: {order_response}")
                return None
                
        except Exception as e:
            applicationLogger.error(f"Error placing order for account {account_id}: {e}")
            return None
    
    def _update_order_info(self, account_id: int, order_id: str, symbol: str, 
                          side: str, qty: int, price: float, status: str):
        """Update order information in account states"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                state['order_id'] = order_id
                state['order_status'] = status
                state['order_symbol'] = symbol
                state['order_side'] = side
                state['order_qty'] = qty
                state['order_price'] = price
                state['last_updated'] = datetime.now().isoformat()
                break
        self._write_account_states(states)
    
    def update_order_status(self, account_id: int, order_id: str, status: str, reason: str = ""):
        """Update order status and handle rejections"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id and state['order_id'] == order_id:
                state['order_status'] = status
                state['last_updated'] = datetime.now().isoformat()
                
                # Handle rejections
                if status == 'REJECTED':
                    self.block_account(account_id, reason, is_rejection=True)
                    applicationLogger.warning(f"Account {account_id} blocked due to order rejection: {reason}")
                break
        self._write_account_states(states)
    
    def cancel_order(self, account_id: int, api, order_id: str) -> bool:
        """Cancel order for a single account"""
        try:
            # Check if order is in modifiable state
            states = self._read_account_states()
            current_status = None
            for state in states:
                if state['account_id'] == account_id and state['order_id'] == order_id:
                    current_status = state['order_status']
                    break
            
            if current_status != 'PENDING':
                applicationLogger.warning(f"Cannot cancel order {order_id} for account {account_id}: status is {current_status}")
                return False
            
            # Cancel order
            cancel_response = api.cancel_order(orderno=order_id)
            
            if cancel_response and cancel_response.get('stat') == 'Ok':
                self._update_order_info(account_id, order_id, '', '', 0, 0.0, 'CANCELLED')
                applicationLogger.info(f"Order {order_id} cancelled successfully for account {account_id}")
                return True
            else:
                applicationLogger.error(f"Failed to cancel order {order_id} for account {account_id}: {cancel_response}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"Error cancelling order for account {account_id}: {e}")
            return False
    
    def modify_order(self, account_id: int, api, order_id: str, new_qty: int, new_price: float) -> bool:
        """Modify order for a single account"""
        try:
            # Check if order is in modifiable state
            states = self._read_account_states()
            current_status = None
            symbol = ''
            for state in states:
                if state['account_id'] == account_id and state['order_id'] == order_id:
                    current_status = state['order_status']
                    symbol = state['order_symbol']
                    break
            
            if current_status != 'PENDING':
                applicationLogger.warning(f"Cannot modify order {order_id} for account {account_id}: status is {current_status}")
                return False
            
            # Determine exchange
            exchange = 'BFO' if 'SENSEX' in symbol else 'NFO'
            
            # Modify order
            modify_response = api.modify_order(
                exchange=exchange,
                tradingsymbol=symbol,
                orderno=order_id,
                newquantity=new_qty,
                newprice_type='LMT',
                newprice=new_price
            )
            
            if modify_response and modify_response.get('stat') == 'Ok':
                self._update_order_info(account_id, order_id, symbol, '', new_qty, new_price, 'PENDING')
                applicationLogger.info(f"Order {order_id} modified successfully for account {account_id}")
                return True
            else:
                applicationLogger.error(f"Failed to modify order {order_id} for account {account_id}: {modify_response}")
                return False
                
        except Exception as e:
            applicationLogger.error(f"Error modifying order for account {account_id}: {e}")
            return False
    
    def get_account_order_info(self, account_id: int) -> Dict[str, Any]:
        """Get current order information for an account"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                return {
                    'order_id': state['order_id'],
                    'order_status': state['order_status'],
                    'order_symbol': state['order_symbol'],
                    'order_side': state['order_side'],
                    'order_qty': state['order_qty'],
                    'order_price': state['order_price'],
                    'blocked': bool(state['blocked']),
                    'rejected_blocked': bool(state['rejected_blocked'])
                }
        return {}
    
    def clear_order_info(self, account_id: int):
        """Clear order information for an account"""
        states = self._read_account_states()
        for state in states:
            if state['account_id'] == account_id:
                state['order_id'] = ''
                state['order_status'] = ''
                state['order_symbol'] = ''
                state['order_side'] = ''
                state['order_qty'] = 0
                state['order_price'] = 0.0
                state['last_updated'] = datetime.now().isoformat()
                break
        self._write_account_states(states)

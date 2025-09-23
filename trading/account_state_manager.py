"""
Simplified Account State Management System
Only essential methods for Master-Child GUI
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AccountStateManager:
    """Simplified account state manager with only essential methods"""
    
    def __init__(self, csv_file_path: str = "account_state.csv"):
        self.csv_file_path = csv_file_path
        self.df_states = None
        self._initialize_states()
    
    def _initialize_states(self):
        """Initialize account states from CSV or create default"""
        try:
            if os.path.exists(self.csv_file_path):
                self.df_states = pd.read_csv(self.csv_file_path)
                logger.info(f"Loaded account states from {self.csv_file_path}")
            else:
                self._create_default_states()
                logger.info(f"Created new account states file: {self.csv_file_path}")
        except Exception as e:
            logger.error(f"Error initializing account states: {e}")
            self._create_default_states()
    
    def _create_default_states(self):
        """Create default account states"""
        default_data = {
            'account_id': [1, 2],
            'account_name': ['Master', 'Child'],
            'login_status': [1, 0],  # 1 = logged in, 0 = not logged in
            'can_order': [1, 0],  # 1 = can order, 0 = cannot order
            'reason': ['Master account always logged in', 'Not logged in'],
            'last_updated': [datetime.now().isoformat(), datetime.now().isoformat()],
            'current_order_id': ['', ''],
            'current_symbol': ['', ''],
            'current_quantity': ['', ''],
            'current_price': ['', ''],
            'filled_quantity': [0, 0],  # Track actual filled quantity
            'can_exit': [0, 0]  # 1 = can exit position, 0 = no position to exit
        }
        
        self.df_states = pd.DataFrame(default_data)
        self._save_to_csv()
    
    def _save_to_csv(self):
        """Save states to CSV file"""
        try:
            self.df_states.to_csv(self.csv_file_path, index=False)
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def get_account_status(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account status by ID"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                row = self.df_states.loc[mask].iloc[0]
                return {
                    'account_id': row['account_id'],
                    'account_name': row['account_name'],
                    'login_status': int(row['login_status']),
                    'can_order': int(row['can_order']),
                    'reason': row['reason'],
                    'last_updated': row['last_updated'],
                    'current_order_id': row['current_order_id'],
                    'current_symbol': row['current_symbol'],
                    'current_quantity': row['current_quantity'],
                    'current_price': row['current_price']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting account status for {account_id}: {e}")
            return None
    
    def update_login_status(self, account_id: int, login_status: int, reason: str) -> bool:
        """Update account login status"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'login_status'] = login_status
                self.df_states.loc[mask, 'reason'] = reason
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Updated {account_name} (ID: {account_id}) login_status to '{login_status}': {reason}")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error updating account {account_id} login status: {e}")
            return False
    
    def update_can_order(self, account_id: int, can_order: int, reason: str) -> bool:
        """Update account can_order status"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'can_order'] = can_order
                self.df_states.loc[mask, 'reason'] = reason
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Updated {account_name} (ID: {account_id}) can_order to '{can_order}': {reason}")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error updating account {account_id} can_order: {e}")
            return False
    
    def update_order_info(self, account_id: int, order_id: str, symbol: str, quantity, price) -> bool:
        """Update account order information"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'current_order_id'] = order_id
                self.df_states.loc[mask, 'current_symbol'] = symbol
                
                # Handle empty strings and convert to appropriate types
                if quantity == "" or quantity is None:
                    self.df_states.loc[mask, 'current_quantity'] = 0.0
                else:
                    self.df_states.loc[mask, 'current_quantity'] = float(quantity)
                
                if price == "" or price is None:
                    self.df_states.loc[mask, 'current_price'] = 0.0
                else:
                    self.df_states.loc[mask, 'current_price'] = float(price)
                
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Updated {account_name} (ID: {account_id}) order info: {order_id} {symbol} {quantity}@{price}")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error updating account {account_id} order info: {e}")
            return False
    
    def get_login_status(self, account_id: int) -> int:
        """Get login status for account (1 = logged in, 0 = not logged in)"""
        status = self.get_account_status(account_id)
        if not status:
            return 0
        return status['login_status']
    
    def get_can_order(self, account_id: int) -> int:
        """Get can_order status for account (1 = can order, 0 = cannot order)"""
        status = self.get_account_status(account_id)
        if not status:
            return 0
        return status['can_order']
    
    def update_filled_quantity(self, account_id: int, filled_qty: int) -> bool:
        """Update filled quantity for account"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'filled_quantity'] = filled_qty
                self.df_states.loc[mask, 'can_exit'] = 1 if filled_qty > 0 else 0
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Updated {account_name} (ID: {account_id}) filled_quantity: {filled_qty}")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error updating account {account_id} filled quantity: {e}")
            return False
    
    def get_filled_quantity(self, account_id: int) -> int:
        """Get filled quantity for account"""
        status = self.get_account_status(account_id)
        if not status:
            return 0
        return int(status.get('filled_quantity', 0))
    
    def get_can_exit(self, account_id: int) -> int:
        """Get can_exit status for account (1 = can exit, 0 = no position)"""
        status = self.get_account_status(account_id)
        if not status:
            return 0
        return int(status.get('can_exit', 0))
    
    def reset_position_data(self, account_id: int) -> bool:
        """Reset position data after exit"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'filled_quantity'] = 0
                self.df_states.loc[mask, 'can_exit'] = 0
                self.df_states.loc[mask, 'current_order_id'] = ''
                self.df_states.loc[mask, 'current_symbol'] = ''
                self.df_states.loc[mask, 'current_quantity'] = ''
                self.df_states.loc[mask, 'current_price'] = ''
                # Clear exit order info as well
                self.df_states.loc[mask, 'exit_order_number'] = ''
                self.df_states.loc[mask, 'exit_order_type'] = ''
                self.df_states.loc[mask, 'exit_price'] = ''
                self.df_states.loc[mask, 'exit_quantity'] = ''
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Reset position data for {account_name} (ID: {account_id})")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error resetting position data for account {account_id}: {e}")
            return False
    
    def update_exit_order_info(self, account_id: int, order_number: str, order_type: str, price: float, quantity: int) -> bool:
        """Update exit order information"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'exit_order_number'] = order_number
                self.df_states.loc[mask, 'exit_order_type'] = order_type
                self.df_states.loc[mask, 'exit_price'] = float(price)
                self.df_states.loc[mask, 'exit_quantity'] = int(quantity)
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Updated {account_name} (ID: {account_id}) exit order info: {order_number} {order_type} {quantity}@{price}")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error updating account {account_id} exit order info: {e}")
            return False
    
    def get_exit_order_number(self, account_id: int) -> str:
        """Get exit order number for account"""
        status = self.get_account_status(account_id)
        if not status:
            return ""
        return str(status.get('exit_order_number', ''))
    
    def get_exit_order_info(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get complete exit order information for account"""
        status = self.get_account_status(account_id)
        if not status:
            return None
        
        exit_order_number = str(status.get('exit_order_number', ''))
        if not exit_order_number or exit_order_number.strip() == '':
            return None
            
        return {
            'order_number': exit_order_number,
            'order_type': str(status.get('exit_order_type', '')),
            'price': float(status.get('exit_price', 0)),
            'quantity': int(status.get('exit_quantity', 0))
        }
    
    def clear_exit_order_info(self, account_id: int) -> bool:
        """Clear exit order information"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'exit_order_number'] = ''
                self.df_states.loc[mask, 'exit_order_type'] = ''
                self.df_states.loc[mask, 'exit_price'] = ''
                self.df_states.loc[mask, 'exit_quantity'] = ''
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                self._save_to_csv()
                
                account_name = self.df_states.loc[mask, 'account_name'].iloc[0]
                logger.info(f"Cleared exit order info for {account_name} (ID: {account_id})")
                return True
            else:
                logger.error(f"Account {account_id} not found in states")
                return False
        except Exception as e:
            logger.error(f"Error clearing exit order info for account {account_id}: {e}")
            return False
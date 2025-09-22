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
            'current_price': ['', '']
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
    
    def update_order_info(self, account_id: int, order_id: str, symbol: str, quantity: int, price: float) -> bool:
        """Update account order information"""
        try:
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'current_order_id'] = order_id
                self.df_states.loc[mask, 'current_symbol'] = symbol
                self.df_states.loc[mask, 'current_quantity'] = quantity
                self.df_states.loc[mask, 'current_price'] = price
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

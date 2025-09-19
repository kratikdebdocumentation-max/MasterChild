"""
Account State Management System
Centralized state management for Master and Child accounts
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from logger import applicationLogger

class AccountStateManager:
    """Manages account states with CSV persistence and in-memory cache"""
    
    def __init__(self, csv_file_path: str = "account_states.csv", reset_on_startup: bool = False):
        self.csv_file_path = csv_file_path
        self.cache = {}  # In-memory cache for fast access
        self.df_states = None
        self.reset_on_startup = reset_on_startup
        self._initialize_states()
    
    def _initialize_states(self):
        """Initialize account states from CSV or create default"""
        try:
            # Reset CSV on startup if enabled
            if self.reset_on_startup and os.path.exists(self.csv_file_path):
                applicationLogger.info(f"Resetting account states on startup: {self.csv_file_path}")
                self._create_default_states()
            elif os.path.exists(self.csv_file_path):
                self.df_states = pd.read_csv(self.csv_file_path)
                applicationLogger.info(f"Loaded account states from {self.csv_file_path}")
            else:
                # Create default states
                self._create_default_states()
                applicationLogger.info(f"Created new account states file: {self.csv_file_path}")
            
            # Populate cache
            self._update_cache()
            
            # Ensure Master account is always active
            self.ensure_master_always_active()
            
        except Exception as e:
            applicationLogger.error(f"Error initializing account states: {e}")
            self._create_default_states()
            self._update_cache()
            # Ensure Master account is always active even after error recovery
            self.ensure_master_always_active()
    
    def _create_default_states(self):
        """Create default account states"""
        default_data = {
            'account_id': [1, 2],
            'account_name': ['Master', 'Child'],
            'login_status': ['logged_in', 'not_logged_in'],  # Separate login status
            'order_status': ['ready', 'ready'],  # Order status (ready, blocked, etc.)
            'quantity': [0, 0],  # Current position quantity
            'reason': ['Master account always logged in', 'Not logged in'],
            'order_number': [None, None],
            'last_updated': [datetime.now().isoformat(), datetime.now().isoformat()]
        }
        
        self.df_states = pd.DataFrame(default_data)
        self._save_to_csv()
    
    def _update_cache(self):
        """Update in-memory cache from DataFrame"""
        try:
            for _, row in self.df_states.iterrows():
                account_id = int(row['account_id'])
                self.cache[account_id] = {
                    'account_name': row['account_name'],
                    'login_status': row['login_status'],
                    'order_status': row['order_status'],
                    'quantity': int(row['quantity']) if pd.notna(row['quantity']) else 0,
                    'reason': row['reason'],
                    'order_number': row['order_number'],
                    'last_updated': row['last_updated']
                }
        except Exception as e:
            applicationLogger.error(f"Error updating cache: {e}")
    
    def _save_to_csv(self):
        """Save current states to CSV file"""
        try:
            self.df_states.to_csv(self.csv_file_path, index=False)
            applicationLogger.debug(f"Account states saved to {self.csv_file_path}")
        except Exception as e:
            applicationLogger.error(f"Error saving account states to CSV: {e}")
    
    def get_account_status(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account status from cache"""
        return self.cache.get(account_id)
    
    def update_account_status(self, account_id: int, status: str, reason: str, 
                            order_number: Optional[str] = None) -> bool:
        """
        Update account status (legacy method - now updates order_status)
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            status: New status (active, inactive) - maps to order_status
            reason: Reason for the status change
            order_number: Order number that caused the status change (optional)
        
        Returns:
            bool: True if update successful, False otherwise
        """
        # Map legacy status to order_status
        order_status = 'ready' if status == 'active' else 'blocked'
        return self.update_order_status(account_id, order_status, reason, order_number)
    
    def update_login_status(self, account_id: int, login_status: str, reason: str) -> bool:
        """
        Update account login status
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            login_status: New login status (logged_in, not_logged_in)
            reason: Reason for the status change
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate account_id
            if account_id not in [1, 2]:
                applicationLogger.error(f"Invalid account_id: {account_id}")
                return False
            
            # Update DataFrame
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'login_status'] = login_status
                self.df_states.loc[mask, 'reason'] = reason
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
            else:
                applicationLogger.error(f"Account {account_id} not found in states")
                return False
            
            # Update cache
            self._update_cache()
            
            # Save to CSV
            self._save_to_csv()
            
            account_name = self.cache[account_id]['account_name']
            applicationLogger.info(f"Updated {account_name} (ID: {account_id}) login status to '{login_status}': {reason}")
            
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error updating account {account_id} login status: {e}")
            return False
    
    def update_order_status(self, account_id: int, order_status: str, reason: str, 
                           order_number: Optional[str] = None) -> bool:
        """
        Update account order status
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            order_status: New order status (ready, blocked, etc.)
            reason: Reason for the status change
            order_number: Order number that caused the status change (optional)
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate account_id
            if account_id not in [1, 2]:
                applicationLogger.error(f"Invalid account_id: {account_id}")
                return False
            
            # Update DataFrame
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'order_status'] = order_status
                self.df_states.loc[mask, 'reason'] = reason
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
                
                if order_number:
                    # Handle case where order_number might be a list
                    if isinstance(order_number, list):
                        order_number = order_number[0] if order_number else None
                    if order_number:
                        self.df_states.loc[mask, 'order_number'] = order_number
            else:
                applicationLogger.error(f"Account {account_id} not found in states")
                return False
            
            # Update cache
            self._update_cache()
            
            # Save to CSV
            self._save_to_csv()
            
            account_name = self.cache[account_id]['account_name']
            applicationLogger.info(f"Updated {account_name} (ID: {account_id}) order status to '{order_status}': {reason}")
            
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error updating account {account_id} order status: {e}")
            return False
    
    def update_quantity(self, account_id: int, quantity: int, reason: str) -> bool:
        """
        Update account quantity
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            quantity: New quantity (positive for long, negative for short, 0 for flat)
            reason: Reason for the quantity change
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate account_id
            if account_id not in [1, 2]:
                applicationLogger.error(f"Invalid account_id: {account_id}")
                return False
            
            # Update DataFrame
            mask = self.df_states['account_id'] == account_id
            if mask.any():
                self.df_states.loc[mask, 'quantity'] = quantity
                self.df_states.loc[mask, 'reason'] = reason
                self.df_states.loc[mask, 'last_updated'] = datetime.now().isoformat()
            else:
                applicationLogger.error(f"Account {account_id} not found in states")
                return False
            
            # Update cache
            self._update_cache()
            
            # Save to CSV
            self._save_to_csv()
            
            account_name = self.cache[account_id]['account_name']
            applicationLogger.info(f"Updated {account_name} (ID: {account_id}) quantity to {quantity}: {reason}")
            
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error updating account {account_id} quantity: {e}")
            return False
    
    def get_quantity(self, account_id: int) -> int:
        """Get current quantity for account"""
        status = self.get_account_status(account_id)
        if not status:
            return 0
        return status.get('quantity', 0)
    
    def add_quantity(self, account_id: int, quantity_change: int, reason: str) -> bool:
        """
        Add to current quantity (for order fills)
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            quantity_change: Quantity to add (positive for buy, negative for sell)
            reason: Reason for the quantity change
        
        Returns:
            bool: True if update successful, False otherwise
        """
        current_quantity = self.get_quantity(account_id)
        new_quantity = current_quantity + quantity_change
        return self.update_quantity(account_id, new_quantity, reason)
    
    def is_position_flat(self, account_id: int) -> bool:
        """Check if account has flat position (quantity = 0)"""
        return self.get_quantity(account_id) == 0
    
    def is_position_long(self, account_id: int) -> bool:
        """Check if account has long position (quantity > 0)"""
        return self.get_quantity(account_id) > 0
    
    def is_position_short(self, account_id: int) -> bool:
        """Check if account has short position (quantity < 0)"""
        return self.get_quantity(account_id) < 0
    
    def get_position_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get position summary for all accounts"""
        summary = {}
        for account_id in [1, 2]:
            status = self.get_account_status(account_id)
            if status:
                quantity = status.get('quantity', 0)
                summary[status['account_name']] = {
                    'account_id': account_id,
                    'quantity': quantity,
                    'position_type': 'Long' if quantity > 0 else 'Short' if quantity < 0 else 'Flat',
                    'login_status': status['login_status'],
                    'order_status': status['order_status'],
                    'can_trade': self.can_place_orders(account_id)
                }
        return summary
    
    def can_place_orders(self, account_id: int) -> bool:
        """Check if account can place orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        # Account can place orders if both logged in and order status is ready
        return (status.get('login_status') == 'logged_in' and 
                status.get('order_status') == 'ready')
    
    def can_modify_orders(self, account_id: int) -> bool:
        """Check if account can modify orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return (status.get('login_status') == 'logged_in' and 
                status.get('order_status') == 'ready')
    
    def can_exit_orders(self, account_id: int) -> bool:
        """Check if account can place exit orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return (status.get('login_status') == 'logged_in' and 
                status.get('order_status') == 'ready')
    
    def get_active_accounts(self) -> List[int]:
        """Get list of accounts that can place orders"""
        active_accounts = []
        for account_id in [1, 2]:
            if self.can_place_orders(account_id):
                active_accounts.append(account_id)
        return active_accounts
    
    def get_accounts_for_modify(self) -> List[int]:
        """Get list of accounts that can modify orders"""
        modify_accounts = []
        for account_id in [1, 2]:
            if self.can_modify_orders(account_id):
                modify_accounts.append(account_id)
        return modify_accounts
    
    def get_accounts_for_exit(self) -> List[int]:
        """Get list of accounts that can place exit orders"""
        exit_accounts = []
        for account_id in [1, 2]:
            if self.can_exit_orders(account_id):
                exit_accounts.append(account_id)
        return exit_accounts
    
    def is_account_blocked(self, account_id: int) -> bool:
        """Check if account is blocked (order status is blocked)"""
        status = self.get_account_status(account_id)
        if not status:
            return True
        return status['order_status'] == 'blocked'
    
    def get_blocked_accounts(self) -> List[int]:
        """Get list of blocked accounts"""
        blocked_accounts = []
        for account_id in [1, 2]:
            if self.is_account_blocked(account_id):
                blocked_accounts.append(account_id)
        return blocked_accounts
    
    def is_account_inactive(self, account_id: int) -> bool:
        """Check if account is inactive (order status is blocked)"""
        status = self.get_account_status(account_id)
        if not status:
            return True
        return status['order_status'] == 'blocked'
    
    def is_account_logged_in(self, account_id: int) -> bool:
        """Check if account is logged in"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return status['login_status'] == 'logged_in'
    
    def reset_account(self, account_id: int) -> bool:
        """Reset account to active state"""
        return self.update_account_status(account_id, 'active', 'Account reset to active')
    
    def reset_all_accounts(self) -> bool:
        """Reset all accounts to default states (clean slate)"""
        try:
            self._create_default_states()
            self._update_cache()
            applicationLogger.info("All accounts reset to default states")
            return True
        except Exception as e:
            applicationLogger.error(f"Error resetting all accounts: {e}")
            return False
    
    def reset_trading_blocks(self, account_manager=None) -> bool:
        """Reset only trading-related blocks while preserving actual login status"""
        try:
            # Use provided account manager or create new one
            if account_manager is None:
                from trading.account_manager import AccountManager
                account_manager = AccountManager()
            
            # Check actual login status for each account
            master_logged_in = account_manager.accounts.get(1, {}).get('active', False)
            child_logged_in = account_manager.accounts.get(2, {}).get('active', False)
            
            applicationLogger.info(f"Login status check - Master: {master_logged_in}, Child: {child_logged_in}")
            
            # Reset Master account - update login status and reset order status to ready
            if master_logged_in:
                self.update_login_status(1, 'logged_in', 'Master account logged in')
                self.update_order_status(1, 'ready', 'Master account reset after trading block')
                applicationLogger.info("Master account reset to ready (was logged in)")
            else:
                self.update_login_status(1, 'not_logged_in', 'Master not logged in')
                self.update_order_status(1, 'ready', 'Master account reset after trading block')
                applicationLogger.info("Master account set to not logged in but order status ready")
            
            # Reset Child account - update login status and reset order status to ready
            if child_logged_in:
                self.update_login_status(2, 'logged_in', 'Child account logged in')
                self.update_order_status(2, 'ready', 'Child account reset after trading block')
                applicationLogger.info("Child account reset to ready (was logged in)")
            else:
                self.update_login_status(2, 'not_logged_in', 'Child not logged in')
                self.update_order_status(2, 'ready', 'Child account reset after trading block')
                applicationLogger.info("Child account set to not logged in but order status ready")
            
            applicationLogger.info("Trading blocks reset while preserving actual login status")
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error resetting trading blocks: {e}")
            # Fallback to original behavior if error occurs
            return self.reset_all_accounts()
    
    def get_all_states(self) -> Dict[int, Dict[str, Any]]:
        """Get all account states (for debugging)"""
        return self.cache.copy()
    
    def ensure_master_always_active(self):
        """Ensure Master account is always logged in (hardcoded requirement)"""
        try:
            master_status = self.get_account_status(1)
            if not master_status or master_status['login_status'] != 'logged_in':
                self.update_login_status(1, 'logged_in', 'Master account always logged in')
                applicationLogger.info("Master account set to always logged in state")
        except Exception as e:
            applicationLogger.error(f"Error ensuring master account is logged in: {e}")
    
    def print_states(self):
        """Print current states (for debugging)"""
        print("\n=== Account States ===")
        for account_id in [1, 2]:
            status = self.get_account_status(account_id)
            if status:
                print(f"Account {account_id} ({status['account_name']}):")
                print(f"  Login Status: {status['login_status']}")
                print(f"  Order Status: {status['order_status']}")
                print(f"  Quantity: {status.get('quantity', 0)}")
                print(f"  Reason: {status['reason']}")
                print(f"  Can trade: {self.can_place_orders(account_id)}")
                print(f"  Order number: {status.get('order_number', 'None')}")
                print(f"  Last updated: {status['last_updated']}")
                print()

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
    
    def __init__(self, csv_file_path: str = "account_states.csv", reset_on_startup: bool = True):
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
            'status': ['active', 'inactive'],  # Master always active, Child inactive
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
                    'status': row['status'],
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
        Update account status
        
        Args:
            account_id: Account ID (1 for Master, 2 for Child)
            status: New status (active, inactive)
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
                self.df_states.loc[mask, 'status'] = status
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
            applicationLogger.info(f"Updated {account_name} (ID: {account_id}) status to '{status}': {reason}")
            
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error updating account {account_id} status: {e}")
            return False
    
    def can_place_orders(self, account_id: int) -> bool:
        """Check if account can place orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return status.get('status') == 'active'
    
    def can_modify_orders(self, account_id: int) -> bool:
        """Check if account can modify orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return status.get('status') == 'active'
    
    def can_exit_orders(self, account_id: int) -> bool:
        """Check if account can place exit orders"""
        status = self.get_account_status(account_id)
        if not status:
            return False
        return status.get('status') == 'active'
    
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
        """Check if account is blocked (inactive)"""
        status = self.get_account_status(account_id)
        if not status:
            return True
        return status['status'] == 'inactive'
    
    def get_blocked_accounts(self) -> List[int]:
        """Get list of blocked accounts"""
        blocked_accounts = []
        for account_id in [1, 2]:
            if self.is_account_blocked(account_id):
                blocked_accounts.append(account_id)
        return blocked_accounts
    
    def is_account_inactive(self, account_id: int) -> bool:
        """Check if account is inactive (blocked due to rejection)"""
        status = self.get_account_status(account_id)
        if not status:
            return True
        return status['status'] == 'inactive'
    
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
    
    def get_all_states(self) -> Dict[int, Dict[str, Any]]:
        """Get all account states (for debugging)"""
        return self.cache.copy()
    
    def ensure_master_always_active(self):
        """Ensure Master account is always active (hardcoded requirement)"""
        try:
            master_status = self.get_account_status(1)
            if not master_status or master_status['status'] != 'active':
                self.update_account_status(1, 'active', 'Master account always logged in')
                applicationLogger.info("Master account set to always active state")
        except Exception as e:
            applicationLogger.error(f"Error ensuring master account is active: {e}")
    
    def print_states(self):
        """Print current states (for debugging)"""
        print("\n=== Account States ===")
        for account_id in [1, 2]:
            status = self.get_account_status(account_id)
            if status:
                print(f"Account {account_id} ({status['account_name']}): {status['status']} - {status['reason']}")
                print(f"  Can trade: {status['status'] == 'active'}")
                print(f"  Order number: {status.get('order_number', 'None')}")
                print(f"  Last updated: {status['last_updated']}")
                print()

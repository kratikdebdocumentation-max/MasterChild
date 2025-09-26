"""
Account management for multiple trading accounts
"""
import pyotp
from retrying import retry
from api_helper import ShoonyaApiPy
from config import Config
# Telegram functionality removed
from logger import childWSLogger, master1WSLogger, applicationLogger

class AccountManager:
    """Manages multiple trading accounts"""
    
    def __init__(self):
        self.accounts = {}
        self.credentials = Config.get_all_credentials()
        self._initialize_accounts()
    
    def _initialize_accounts(self):
        """Initialize all trading accounts"""
        for account_num, creds in self.credentials.items():
            try:
                api = ShoonyaApiPy()
                twoFA = pyotp.TOTP(creds['factor2']).now()
                
                self.accounts[account_num] = {
                    'api': api,
                    'credentials': creds,
                    'twoFA': twoFA,
                    'active': account_num == 1,  # Master account is always active
                    'client_name': None
                }
            except Exception as e:
                print(f"Error initializing account {account_num}: {e}")
    
    @retry(stop_max_attempt_number=2, wait_fixed=10000)
    def login_account(self, account_num: int) -> tuple[bool, str]:
        """
        Login to a specific account
        
        Args:
            account_num: Account number (1-2)
            
        Returns:
            tuple: (success, client_name)
        """
        if account_num not in self.accounts:
            return False, "Account not found"
        
        account = self.accounts[account_num]
        creds = account['credentials']
        
        try:
            # Generate fresh 2FA code
            fresh_twoFA = pyotp.TOTP(creds['factor2']).now()
            applicationLogger.info(f"Generated fresh 2FA for account {account_num}: {fresh_twoFA}")
            
            # Log login attempt details
            applicationLogger.info(f"Attempting login for account {account_num} with userid: {creds['username']}")
            
            login_status = account['api'].login(
                userid=creds['username'],
                password=creds['pwd'],
                twoFA=fresh_twoFA,
                vendor_code=creds['vc'],
                api_secret=creds['app_key'],
                imei=creds['imei']
            )
            
            # Log the raw response for debugging
            applicationLogger.info(f"Login response for account {account_num}: {login_status}")
            applicationLogger.info(f"Login response type: {type(login_status)}")
            
            if login_status and 'uname' in login_status:
                client_name = login_status.get('uname')
                account['client_name'] = client_name
                account['active'] = True
                
                # Log success
                if account_num == 1:
                    master1WSLogger.info(f"Login Successful!, Welcome {client_name} - Master ACCOUNT")
                else:
                    childWSLogger.info(f"Login Successful!, Welcome {client_name} - Child{account_num} ACCOUNT")
                
                return True, client_name
            else:
                error_msg = f"Login failed for account {account_num}: Invalid response - {login_status}"
                applicationLogger.error(error_msg)
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Login failed for account {account_num}: {e}"
            applicationLogger.error(error_msg)
            # Log additional details for JSON parsing errors
            if "Expecting value" in str(e) or "JSON" in str(e):
                applicationLogger.error(f"JSON parsing error detected. Check if broker API is responding correctly.")
                applicationLogger.error(f"Account {account_num} credentials: userid={creds['username']}, vc={creds['vc']}")
            return False, error_msg
    
    def get_account(self, account_num: int) -> dict:
        """Get account information"""
        return self.accounts.get(account_num, {})
    
    def is_account_active(self, account_num: int) -> bool:
        """Check if account is active"""
        return self.accounts.get(account_num, {}).get('active', False)
    
    def get_api(self, account_num: int) -> ShoonyaApiPy:
        """Get API instance for account"""
        return self.accounts.get(account_num, {}).get('api')
    
    def get_all_active_accounts(self) -> list:
        """Get list of all active account numbers"""
        return [num for num, account in self.accounts.items() if account.get('active', False)]
    
    def logout_account(self, account_num: int) -> tuple[bool, str]:
        """
        Block account from sending orders while keeping it active for PnL
        
        Args:
            account_num: Account number to block
            
        Returns:
            tuple: (success, message)
        """
        if account_num not in self.accounts:
            return False, "Account not found"
        
        try:
            # Mark account as blocked instead of logging out
            self.accounts[account_num]['blocked'] = True
            self.accounts[account_num]['active'] = False  # Block from sending orders
            
            client_name = self.accounts[account_num].get('client_name', f'Account {account_num}')
            applicationLogger.info(f"Account {account_num} ({client_name}) blocked from sending orders - PnL monitoring continues")
            
            return True, f"Account {client_name} blocked from sending orders. PnL monitoring continues."
            
        except Exception as e:
            error_msg = f"Error blocking account {account_num}: {e}"
            applicationLogger.error(error_msg)
            return False, error_msg
    
    def is_account_blocked(self, account_num: int) -> bool:
        """Check if account is blocked from sending orders"""
        return self.accounts.get(account_num, {}).get('blocked', False)
    
    def unblock_account(self, account_num: int) -> tuple[bool, str]:
        """
        Unblock account to allow sending orders again
        
        Args:
            account_num: Account number to unblock
            
        Returns:
            tuple: (success, message)
        """
        if account_num not in self.accounts:
            return False, "Account not found"
        
        try:
            # Unblock account (remove blocked flag but don't change active status)
            self.accounts[account_num]['blocked'] = False
            # Don't set active = True here - active status should be based on actual login status
            
            client_name = self.accounts[account_num].get('client_name', f'Account {account_num}')
            applicationLogger.info(f"Account {account_num} ({client_name}) unblocked - Orders allowed again")
            
            return True, f"Account {client_name} unblocked. Orders allowed again."
            
        except Exception as e:
            error_msg = f"Error unblocking account {account_num}: {e}"
            applicationLogger.error(error_msg)
            return False, error_msg
    
    def get_trade_book(self, account_num: int) -> tuple[bool, list, str]:
        """
        Get trade book for a specific account using get_trade_book API
        
        Args:
            account_num: Account number to check trade book for
            
        Returns:
            tuple: (success, trade_book_list, message)
        """
        if account_num not in self.accounts:
            return False, [], "Account not found"
        
        account = self.accounts[account_num]
        api = account.get('api')
        
        if not api:
            return False, [], "API not available for account"
        
        if not account.get('active', False):
            return False, [], "Account not logged in"
        
        try:
            trade_book = api.get_trade_book()
            
            if trade_book is None:
                return True, [], "No trade book data found"
            
            # Filter for successful trades only
            valid_trades = []
            if isinstance(trade_book, list):
                for trade in trade_book:
                    if isinstance(trade, dict) and trade.get('stat') == 'Ok':
                        valid_trades.append(trade)
            
            client_name = account.get('client_name', f'Account {account_num}')
            applicationLogger.info(f"Trade book retrieved for {client_name}: {len(valid_trades)} trades found")
            
            return True, valid_trades, f"Trade book retrieved for {client_name}"
            
        except Exception as e:
            error_msg = f"Error retrieving trade book for account {account_num}: {e}"
            applicationLogger.error(error_msg)
            return False, [], error_msg
    
    def check_all_positions(self) -> tuple[bool, dict, str]:
        """
        Check positions for all active accounts using trade book
        
        Returns:
            tuple: (has_open_positions, positions_by_account, summary_message)
        """
        all_positions = {}
        total_open_positions = 0
        
        for account_num, account in self.accounts.items():
            if account.get('active', False):
                success, trade_book, message = self.get_trade_book(account_num)
                if success and trade_book:
                    # Process trade book to find open positions
                    open_positions = self._extract_open_positions_from_trade_book(trade_book)
                    all_positions[account_num] = {
                        'client_name': account.get('client_name', f'Account {account_num}'),
                        'positions': open_positions,
                        'count': len(open_positions)
                    }
                    total_open_positions += len(open_positions)
                else:
                    applicationLogger.warning(f"Could not retrieve trade book for account {account_num}: {message}")
        
        has_open_positions = total_open_positions > 0
        
        if has_open_positions:
            summary = f"Found {total_open_positions} open position(s) across {len(all_positions)} account(s)"
        else:
            summary = "No open positions found"
        
        return has_open_positions, all_positions, summary
    
    def _extract_open_positions_from_trade_book(self, trade_book_data):
        """Extract open positions from trade book data"""
        try:
            symbol_groups = {}
            
            # Group transactions by symbol
            for trade in trade_book_data:
                symbol = trade.get('tsym', 'Unknown')
                trantype = trade.get('trantype', 'Unknown')
                
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = {'buy': [], 'sell': []}
                
                if trantype == 'B':  # Buy
                    symbol_groups[symbol]['buy'].append(trade)
                elif trantype == 'S':  # Sell
                    symbol_groups[symbol]['sell'].append(trade)
            
            # Calculate net positions
            open_positions = []
            for symbol, transactions in symbol_groups.items():
                buy_qty = sum(int(trade.get('flqty', 0)) for trade in transactions.get('buy', []))
                sell_qty = sum(int(trade.get('flqty', 0)) for trade in transactions.get('sell', []))
                
                net_qty = buy_qty - sell_qty
                
                # Only include if there's an open position (net_qty > 0)
                if net_qty > 0:
                    # Calculate average buy price
                    avg_buy_price = 0.0
                    if transactions.get('buy'):
                        total_buy_value = sum(float(trade.get('flprc', 0)) * int(trade.get('flqty', 0)) for trade in transactions['buy'])
                        avg_buy_price = total_buy_value / buy_qty if buy_qty > 0 else 0.0
                    
                    open_positions.append({
                        'symbol': symbol,
                        'net_qty': net_qty,
                        'avg_buy_price': avg_buy_price
                    })
            
            return open_positions
            
        except Exception as e:
            applicationLogger.error(f"Error extracting open positions from trade book: {e}")
            return []
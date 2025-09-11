"""
Account management for multiple trading accounts
"""
import pyotp
from retrying import retry
from api_helper import ShoonyaApiPy
from config import Config
from utils.telegram_notifications import send_sos_message
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
            
            login_status = account['api'].login(
                userid=creds['username'],
                password=creds['pwd'],
                twoFA=fresh_twoFA,
                vendor_code=creds['vc'],
                api_secret=creds['app_key'],
                imei=creds['imei']
            )
            
            if login_status and 'uname' in login_status:
                client_name = login_status.get('uname')
                account['client_name'] = client_name
                account['active'] = True
                
                # Log success
                if account_num == 1:
                    master1WSLogger.info(f"Login Successful!, Welcome {client_name} - Master ACCOUNT")
                else:
                    child_logger = globals()[f'child{account_num}WSLogger']
                    child_logger.info(f"Login Successful!, Welcome {client_name} - Child{account_num} ACCOUNT")
                
                return True, client_name
            else:
                error_msg = f"Login failed for account {account_num}: Invalid response - {login_status}"
                applicationLogger.error(error_msg)
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Login failed for account {account_num}: {e}"
            applicationLogger.error(error_msg)
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

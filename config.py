"""
Configuration settings for Master-Child Trading System
"""

class Config:
    """Configuration class for application settings"""
    
    # Trading settings
    EXCHANGE = "NSE"
    PRICE_TYPE = "LMT"  # Default order type (LMT for limit, MKT for market)
    RETENTION = "DAY"
    
    # Account settings
    ACTIVE_CHILD_ACCOUNTS = [2]  # Child accounts to activate
    
    # API settings
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # GUI settings
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 350
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Trading intervals
    STRIKE_INTERVALS = {
        "NIFTY": 50,
        "BANKNIFTY": 100,
        "SENSEX": 100
    }
    
    # Default quantities
    DEFAULT_QUANTITIES = {
        "NIFTY": 25,
        "BANKNIFTY": 15,
        "SENSEX": 10
    }
    
    # Index tokens
    INDEX_TOKENS = {
        'SENSEX': {'token': '1', 'exchange': 'BSE', 'name': 'BSE SENSEX'},
        'NIFTY': {'token': '26000', 'exchange': 'NSE', 'name': 'NIFTY 50'},
        'BANKNIFTY': {'token': '26009', 'exchange': 'NSE', 'name': 'NIFTY BANK'}
    }
    
    # Telegram functionality removed
    
    @classmethod
    def get_strike_interval(cls, instrument: str) -> int:
        """Get strike interval for an instrument"""
        return cls.STRIKE_INTERVALS.get(instrument, 100)
    
    @classmethod
    def get_default_quantity(cls, instrument: str) -> int:
        """Get default quantity for an instrument"""
        return cls.DEFAULT_QUANTITIES.get(instrument, 10)
    
    @classmethod
    def get_index_info(cls, index_name: str) -> dict:
        """Get index information"""
        return cls.INDEX_TOKENS.get(index_name, {})
    
    @classmethod
    def get_all_credentials(cls) -> dict:
        """Load all credentials from JSON files"""
        import json
        import os
        
        credentials = {}
        credential_files = [
            'credentials1.json',
            'credentials2.json'
        ]
        
        # Get the directory where this config.py file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        for i, filename in enumerate(credential_files, 1):
            # Use absolute path to ensure we're looking in the right directory
            file_path = os.path.join(current_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as file:
                        creds = json.load(file)
                        credentials[i] = creds
                        print(f"Successfully loaded {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"Warning: {filename} not found at {file_path}")
        
        return credentials
    
    @classmethod
    def load_configuration_csv(cls, csv_file_path: str = "configuration.csv") -> dict:
        """Load configuration from CSV file"""
        import csv
        import os
        
        config = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, csv_file_path)
        
        if not os.path.exists(file_path):
            print(f"Warning: Configuration file {csv_file_path} not found at {file_path}")
            return config
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    setting_name = row.get('setting_name', '').strip()
                    value = row.get('value', '').strip()
                    if setting_name and value:
                        # Convert numeric values
                        try:
                            config[setting_name] = int(value)
                        except ValueError:
                            config[setting_name] = value
            print(f"Successfully loaded configuration from {csv_file_path}")
        except Exception as e:
            print(f"Error loading configuration from {csv_file_path}: {e}")
        
        return config
    
    @classmethod
    def get_lot_size(cls, index_name: str, config: dict = None) -> int:
        """Get lot size for an index from configuration"""
        if config is None:
            config = cls.load_configuration_csv()
        
        lot_size_mapping = {
            'SENSEX': 'sensex_lot_size',
            'NIFTY': 'nifty_lot_size', 
            'BANKNIFTY': 'banknifty_lot_size'
        }
        
        setting_name = lot_size_mapping.get(index_name)
        if setting_name and setting_name in config:
            return config[setting_name]
        
        # Default fallback values
        default_lot_sizes = {
            'SENSEX': 20,
            'NIFTY': 75,
            'BANKNIFTY': 35
        }
        return default_lot_sizes.get(index_name, 25)
    
    @classmethod
    def generate_quantity_options(cls, index_name: str, max_multiple: int = 10, config: dict = None) -> list:
        """Generate quantity options as multiples of lot size"""
        lot_size = cls.get_lot_size(index_name, config)
        quantities = []
        
        for i in range(1, max_multiple + 1):
            quantity = lot_size * i
            quantities.append(str(quantity))
        
        return quantities
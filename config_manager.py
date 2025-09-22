"""
Configuration Manager for Master-Child GUI
Handles reading and parsing configuration settings
"""
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration settings from CSV file"""
    
    def __init__(self, config_file: str = "configuration.csv"):
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from CSV file"""
        try:
            if os.path.exists(self.config_file):
                df = pd.read_csv(self.config_file)
                for _, row in df.iterrows():
                    setting_name = row['setting_name']
                    value = row['value']
                    self.config[setting_name] = value
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(f"Configuration file {self.config_file} not found")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def get_setting(self, setting_name: str, default_value=None):
        """Get a configuration setting value"""
        return self.config.get(setting_name, default_value)
    
    def get_child_lots_config(self):
        """Get child lots configuration"""
        return self.get_setting('child_lots', 'min')
    
    def get_index_lot_size(self, index: str) -> int:
        """Get minimum lot size for an index"""
        if index == "SENSEX":
            return int(self.get_setting('sensex_lot_size', 20))
        elif index == "NIFTY":
            return int(self.get_setting('nifty_lot_size', 75))
        elif index == "BANKNIFTY":
            return int(self.get_setting('banknifty_lot_size', 35))
        else:
            return int(self.get_setting('nifty_lot_size', 75))  # Default to NIFTY
    
    def calculate_child_quantity(self, master_quantity: int, index: str) -> int:
        """
        Calculate child quantity based on configuration
        
        Args:
            master_quantity: Master account quantity
            index: Trading index (SENSEX, NIFTY, BANKNIFTY)
            
        Returns:
            int: Calculated child quantity
        """
        try:
            child_lots_config = self.get_child_lots_config()
            
            if child_lots_config == "min":
                # Use minimum lot size for the index
                child_quantity = self.get_index_lot_size(index)
                logger.info(f"Child lots set to minimum for {index}: {child_quantity}")
            else:
                # Use as multiplier
                multiplier = float(child_lots_config)
                child_quantity = int(master_quantity * multiplier)
                logger.info(f"Child lots calculated as {master_quantity} × {multiplier} = {child_quantity}")
            
            return child_quantity
            
        except Exception as e:
            logger.error(f"Error calculating child quantity: {e}")
            # Fallback to minimum lot size
            return self.get_index_lot_size(index)

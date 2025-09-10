"""
Expiry date management for options
"""
import glob
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from logger import applicationLogger

class ExpiryManager:
    """Manages expiry dates for different instruments"""
    
    def __init__(self):
        self.expiry_dates = {}
        self._load_expiry_dates()
    
    def _load_expiry_dates(self):
        """Load expiry dates from files"""
        try:
            # Load NIFTY expiry
            with open('data/nf_expiry_dates.txt', 'r') as file:
                nf_exp_date = file.read().strip()
                self.expiry_dates['NIFTY'] = self._format_expiry_date(nf_exp_date)
            
            # Load BANKNIFTY expiry
            with open('data/bn_expiry_dates.txt', 'r') as file:
                bn_exp_date = file.read().strip()
                self.expiry_dates['BANKNIFTY'] = self._format_expiry_date(bn_exp_date)
            
            # Load SENSEX expiry
            with open('data/sx_expiry_dates.txt', 'r') as file:
                sx_exp_date = file.read().strip()
                self.expiry_dates['SENSEX'] = self._format_expiry_date(sx_exp_date)
                
        except Exception as e:
            applicationLogger.error(f"Error loading expiry dates: {e}")
    
    def _format_expiry_date(self, date_str: str) -> str:
        """Format expiry date to required format"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d%b%y').upper()
        except Exception as e:
            applicationLogger.error(f"Error formatting date {date_str}: {e}")
            return ""
    
    def get_expiry_date(self, instrument: str) -> str:
        """
        Get expiry date for an instrument
        
        Args:
            instrument: Instrument name (NIFTY, BANKNIFTY, SENSEX)
            
        Returns:
            Formatted expiry date
        """
        return self.expiry_dates.get(instrument, "")
    
    def get_strike_list(self, instrument: str, current_price: float) -> list:
        """
        Get strike price list for an instrument
        
        Args:
            instrument: Instrument name
            current_price: Current price
            
        Returns:
            List of strike prices around the current price
        """
        try:
            if instrument == "NIFTY":
                # NIFTY strikes with 50 point intervals
                # Round to nearest 50
                base_strike = round(current_price / 50) * 50
                strikes = [base_strike + (50 * i) for i in range(-7, 8)]
                return sorted(strikes)
                
            elif instrument == "BANKNIFTY":
                # BANKNIFTY strikes with 100 point intervals
                # Round to nearest 100
                base_strike = round(current_price / 100) * 100
                strikes = [base_strike + (100 * i) for i in range(-7, 8)]
                return sorted(strikes)
                
            elif instrument == "SENSEX":
                # SENSEX strikes with 100 point intervals
                # Round to nearest 100 (like the example: 81425.15 -> 81400)
                base_strike = round(current_price / 100) * 100
                strikes = [base_strike + (100 * i) for i in range(-7, 8)]
                return sorted(strikes)
            else:
                return []
                
        except Exception as e:
            applicationLogger.error(f"Error generating strike list for {instrument}: {e}")
            return []
    
    def get_quantity_list(self, instrument: str) -> list:
        """
        Get quantity list for an instrument
        
        Args:
            instrument: Instrument name
            
        Returns:
            List of quantities
        """
        try:
            if instrument == "NIFTY":
                return [25 * i for i in range(1, 10)]
            elif instrument == "BANKNIFTY":
                return [15 * i for i in range(1, 10)]
            elif instrument == "SENSEX":
                return [10 * i for i in range(1, 10)]
            else:
                return []
        except Exception as e:
            applicationLogger.error(f"Error generating quantity list for {instrument}: {e}")
            return []

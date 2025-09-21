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
        self.expiry_lists = {}  # Store lists of expiry dates for each instrument
        self.current_expiry = {}  # Store current expiry dates
        self.next_expiry = {}     # Store next expiry dates
        self._load_expiry_dates()
    
    def _load_expiry_dates(self):
        """Load current and next expiry dates from files"""
        try:
            # Load NIFTY expiry (current,next)
            with open('data/nf_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.current_expiry['NIFTY'] = self._format_expiry_date(current) if current else ""
                    self.next_expiry['NIFTY'] = self._format_expiry_date(next_date) if next_date else ""
                    self.expiry_dates['NIFTY'] = self.current_expiry['NIFTY']  # For backward compatibility
                else:
                    # Fallback for old format
                    self.expiry_dates['NIFTY'] = self._format_expiry_date(content)
                    self.current_expiry['NIFTY'] = self.expiry_dates['NIFTY']
                    self.next_expiry['NIFTY'] = ""
            
            # Load BANKNIFTY expiry (current,next)
            with open('data/bn_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.current_expiry['BANKNIFTY'] = self._format_expiry_date(current) if current else ""
                    self.next_expiry['BANKNIFTY'] = self._format_expiry_date(next_date) if next_date else ""
                    self.expiry_dates['BANKNIFTY'] = self.current_expiry['BANKNIFTY']  # For backward compatibility
                else:
                    # Fallback for old format
                    self.expiry_dates['BANKNIFTY'] = self._format_expiry_date(content)
                    self.current_expiry['BANKNIFTY'] = self.expiry_dates['BANKNIFTY']
                    self.next_expiry['BANKNIFTY'] = ""
            
            # Load SENSEX expiry (current,next)
            with open('data/sx_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.current_expiry['SENSEX'] = self._format_expiry_date(current) if current else ""
                    self.next_expiry['SENSEX'] = self._format_expiry_date(next_date) if next_date else ""
                    self.expiry_dates['SENSEX'] = self.current_expiry['SENSEX']  # For backward compatibility
                else:
                    # Fallback for old format
                    self.expiry_dates['SENSEX'] = self._format_expiry_date(content)
                    self.current_expiry['SENSEX'] = self.expiry_dates['SENSEX']
                    self.next_expiry['SENSEX'] = ""
                
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
    
    def get_expiry_list(self, instrument: str) -> list:
        """
        Get list of available expiry dates for an instrument (current + next)
        
        Args:
            instrument: Instrument name (NIFTY, BANKNIFTY, SENSEX)
            
        Returns:
            List of formatted expiry dates
        """
        # Get current and next expiry from loaded data
        current_expiry = self.current_expiry.get(instrument, "")
        next_expiry = self.next_expiry.get(instrument, "")
        
        # Return both current and next expiry
        return [current_expiry, next_expiry]
    
    def get_strike_list(self, instrument: str, current_price: float, option_type: str = None) -> list:
        """
        Get strike price list for an instrument based on option type
        
        Args:
            instrument: Instrument name
            current_price: Current price
            option_type: Option type (CE/PE) - if None, uses balanced distribution
            
        Returns:
            List of strike prices around the current price
        """
        try:
            if instrument == "NIFTY":
                # NIFTY strikes with 50 point intervals
                # Round to nearest 50
                base_strike = round(current_price / 50) * 50
                if option_type == "CE":
                    # CE: More strikes above current price (2 below, 12 above)
                    strikes = [base_strike + (50 * i) for i in range(-2, 13)]
                elif option_type == "PE":
                    # PE: More strikes below current price (12 below, 2 above)
                    strikes = [base_strike + (50 * i) for i in range(-12, 3)]
                else:
                    # Default: Balanced distribution (7 below, 7 above)
                    strikes = [base_strike + (50 * i) for i in range(-7, 8)]
                return sorted(strikes)
                
            elif instrument == "BANKNIFTY":
                # BANKNIFTY strikes with 100 point intervals
                # Round to nearest 100
                base_strike = round(current_price / 100) * 100
                if option_type == "CE":
                    # CE: More strikes above current price (2 below, 12 above)
                    strikes = [base_strike + (100 * i) for i in range(-2, 13)]
                elif option_type == "PE":
                    # PE: More strikes below current price (12 below, 2 above)
                    strikes = [base_strike + (100 * i) for i in range(-12, 3)]
                else:
                    # Default: Balanced distribution (7 below, 7 above)
                    strikes = [base_strike + (100 * i) for i in range(-7, 8)]
                return sorted(strikes)
                
            elif instrument == "SENSEX":
                # SENSEX strikes with 100 point intervals
                # Round to nearest 100 (like the example: 81425.15 -> 81400)
                base_strike = round(current_price / 100) * 100
                if option_type == "CE":
                    # CE: More strikes above current price (2 below, 12 above)
                    strikes = [base_strike + (100 * i) for i in range(-2, 13)]
                elif option_type == "PE":
                    # PE: More strikes below current price (12 below, 2 above)
                    strikes = [base_strike + (100 * i) for i in range(-12, 3)]
                else:
                    # Default: Balanced distribution (7 below, 7 above)
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
                return [20 * i for i in range(1, 10)]  # SENSEX lot size is 20
            else:
                return []
        except Exception as e:
            applicationLogger.error(f"Error generating quantity list for {instrument}: {e}")
            return []

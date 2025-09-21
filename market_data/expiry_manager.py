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
    
    def get_expiry_list(self, instrument: str) -> list:
        """
        Get list of available expiry dates for an instrument (current + next)
        
        Args:
            instrument: Instrument name (NIFTY, BANKNIFTY, SENSEX)
            
        Returns:
            List of formatted expiry dates
        """
        try:
            # For SENSEX, use the enhanced calculation from findexpiry.py
            if instrument == "SENSEX":
                from findexpiry import get_sensex_expiry_dates
                sensex_dates = get_sensex_expiry_dates()
                
                if not sensex_dates or len(sensex_dates) < 2:
                    applicationLogger.warning(f"Not enough SENSEX expiry dates found. Found: {len(sensex_dates) if sensex_dates else 0}")
                    return [self.expiry_dates.get(instrument, "")]
                
                # Convert to the required format (25SEP25, 01OCT25)
                current_date = datetime.strptime(sensex_dates[0][0], '%d-%b-%Y')
                next_date = datetime.strptime(sensex_dates[1][0], '%d-%b-%Y')
                
                current_formatted = current_date.strftime('%d%b%y').upper()
                next_formatted = next_date.strftime('%d%b%y').upper()
                
                return [current_formatted, next_formatted]
            
            # For BANKNIFTY, use the actual NFO file data
            elif instrument == "BANKNIFTY":
                banknifty_dates = self._get_banknifty_expiry_dates()
                
                if not banknifty_dates or len(banknifty_dates) < 2:
                    applicationLogger.warning(f"Not enough BANKNIFTY expiry dates found. Found: {len(banknifty_dates) if banknifty_dates else 0}")
                    return [self.expiry_dates.get(instrument, "")]
                
                # Convert to the required format (30SEP25, 28OCT25)
                current_date = datetime.strptime(banknifty_dates[0][0], '%d-%b-%Y')
                next_date = datetime.strptime(banknifty_dates[1][0], '%d-%b-%Y')
                
                current_formatted = current_date.strftime('%d%b%y').upper()
                next_formatted = next_date.strftime('%d%b%y').upper()
                
                return [current_formatted, next_formatted]
            
            # For other instruments, use the original method
            current_expiry = self.expiry_dates.get(instrument, "")
            if not current_expiry:
                return []
            
            # Calculate next expiry (add 7 days for weekly options)
            current_date = datetime.strptime(current_expiry, '%d%b%y')
            next_date = current_date + timedelta(days=7)
            next_expiry = next_date.strftime('%d%b%y').upper()
            
            return [current_expiry, next_expiry]
            
        except Exception as e:
            applicationLogger.error(f"Error generating expiry list for {instrument}: {e}")
            return [self.expiry_dates.get(instrument, "")]
    
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
    
    def _get_banknifty_expiry_dates(self):
        """
        Get all BANKNIFTY expiry dates from NFO file in chronological order
        
        Returns:
            List of tuples: (expiry_date_str, day_of_week, symbol_count)
        """
        import os
        from collections import defaultdict
        
        # Find the latest NFO file
        nfo_files = [f for f in os.listdir('data') if f.startswith('NFO_symbols.txt_') and f.endswith('.txt')]
        if not nfo_files:
            applicationLogger.warning("No NFO files found")
            return []
        
        latest_nfo = sorted(nfo_files)[-1]
        nfo_file_path = os.path.join('data', latest_nfo)
        
        if not os.path.exists(nfo_file_path):
            applicationLogger.warning(f"NFO file not found: {nfo_file_path}")
            return []
        
        expiry_counts = defaultdict(int)
        
        try:
            with open(nfo_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        # Check if it's a BANKNIFTY option
                        if 'BANKNIFTY' in parts[4]:  # TradingSymbol column
                            expiry_date = parts[5]  # Expiry column
                            expiry_counts[expiry_date] += 1
            
            # Convert to list of tuples and sort chronologically
            expiry_list = []
            for expiry_date, count in expiry_counts.items():
                try:
                    date_obj = datetime.strptime(expiry_date, '%d-%b-%Y')
                    day_of_week = date_obj.strftime('%A')
                    expiry_list.append((expiry_date, day_of_week, count))
                except ValueError:
                    continue
            
            # Sort by date
            expiry_list.sort(key=lambda x: datetime.strptime(x[0], '%d-%b-%Y'))
            return expiry_list
            
        except Exception as e:
            applicationLogger.error(f"Error reading NFO file for BANKNIFTY expiry dates: {e}")
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

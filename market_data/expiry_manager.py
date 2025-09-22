"""
Expiry Date Manager - Based on Old Project Logic
Calculates expiry dates from master files using the same logic as the old project
"""
import os
import json
import glob
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

class ExpiryManager:
    """Expiry date manager using master file logic from old project"""
    
    def __init__(self):
        self.expiry_dates = {
            'NIFTY': {'current': '', 'next': ''},
            'BANKNIFTY': {'current': '', 'next': ''},
            'SENSEX': {'current': '', 'next': ''}
        }
        self._load_cached_expiry()
    
    def _load_cached_expiry(self):
        """Load cached expiry dates from files"""
        try:
            # Try to load from JSON cache first
            cache_file = 'data/expiry_cache.json'
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                today = datetime.now().strftime('%Y-%m-%d')
                if cache_data.get('date') == today and cache_data.get('expiry_dates'):
                    self.expiry_dates = cache_data['expiry_dates']
                    logger.info("Loaded cached expiry dates from today")
                    return
            
            # Try to load from individual text files
            self._load_from_text_files()
            
        except Exception as e:
            logger.error(f"Error loading cached expiry: {e}")
    
    def _load_from_text_files(self):
        """Load expiry dates from individual text files (old project format)"""
        try:
            # Load NIFTY expiry (current,next format)
            with open('data/nf_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.expiry_dates['NIFTY'] = {
                        'current': current.strip(),
                        'next': next_date.strip()
                    }
            
            # Load BANKNIFTY expiry (current,next format)
            with open('data/bn_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.expiry_dates['BANKNIFTY'] = {
                        'current': current.strip(),
                        'next': next_date.strip()
                    }
            
            # Load SENSEX expiry (current,next format)
            with open('data/sx_expiry_dates.txt', 'r') as file:
                content = file.read().strip()
                if ',' in content:
                    current, next_date = content.split(',', 1)
                    self.expiry_dates['SENSEX'] = {
                        'current': current.strip(),
                        'next': next_date.strip()
                    }
            
            logger.info("Loaded expiry dates from text files")
            
        except Exception as e:
            logger.error(f"Error loading from text files: {e}")
    
    def get_expiry_list(self, index: str) -> List[str]:
        """Get expiry list for dropdown (current and next)"""
        try:
            if index in self.expiry_dates:
                current = self.expiry_dates[index]['current']
                next_date = self.expiry_dates[index]['next']
                
                # Convert YYYY-MM-DD to DDMMMYY format for display
                if current and next_date:
                    current_formatted = self._format_for_display(current)
                    next_formatted = self._format_for_display(next_date)
                    return [current_formatted, next_formatted]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting expiry list for {index}: {e}")
            return []
    
    def _format_for_display(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to DDMMMYY for display"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d%b%y').upper()
        except:
            return date_str
    
    def get_current_expiry(self, index: str) -> str:
        """Get current expiry date for an index"""
        current = self.expiry_dates.get(index, {}).get('current', '')
        return self._format_for_display(current) if current else ''
    
    def calculate_expiry_dates(self) -> bool:
        """Calculate expiry dates from master files using old project logic"""
        try:
            logger.info("Calculating expiry dates from master files...")
            
            # Calculate NIFTY and BANKNIFTY from NFO file
            nifty_expiry, banknifty_expiry = self._calculate_nifty_banknifty_expiry()
            
            # Calculate SENSEX from BFO file
            sensex_expiry = self._calculate_sensex_expiry()
            
            # Update expiry dates
            if nifty_expiry:
                self.expiry_dates['NIFTY'] = {
                    'current': nifty_expiry[0],
                    'next': nifty_expiry[1]
                }
            
            if banknifty_expiry:
                self.expiry_dates['BANKNIFTY'] = {
                    'current': banknifty_expiry[0],
                    'next': banknifty_expiry[1]
                }
            
            if sensex_expiry:
                self.expiry_dates['SENSEX'] = {
                    'current': sensex_expiry[0],
                    'next': sensex_expiry[1]
                }
            
            # Save the calculated dates
            self._save_expiry_dates()
            logger.info("Successfully calculated and saved expiry dates")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating expiry dates: {e}")
            return False
    
    def _calculate_nifty_banknifty_expiry(self) -> Tuple[Tuple[str, str], Tuple[str, str]]:
        """Calculate NIFTY and BANKNIFTY expiry dates from NFO file"""
        try:
            # Find latest NFO file
            nfo_files = glob.glob('data/NFO_symbols.txt_*.txt')
            if not nfo_files:
                raise FileNotFoundError("No NFO files found")
            
            latest_nfo = sorted(nfo_files)[-1]
            logger.info(f"Using NFO file: {latest_nfo}")
            
            # Read NFO file
            df = pd.read_csv(latest_nfo)
            
            # Get NIFTY dates
            nifty_df = df[df['Symbol'] == 'NIFTY']
            nifty_dates = sorted(nifty_df['Expiry'].unique())
            
            # Get BANKNIFTY dates  
            banknifty_df = df[df['Symbol'] == 'BANKNIFTY']
            banknifty_dates = sorted(banknifty_df['Expiry'].unique())
            
            # Convert to datetime and sort
            nifty_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in nifty_dates])
            banknifty_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in banknifty_dates])
            
            # Get current and next (first two dates)
            nifty_current = nifty_dates[0].strftime('%Y-%m-%d')
            nifty_next = nifty_dates[1].strftime('%Y-%m-%d')
            
            banknifty_current = banknifty_dates[0].strftime('%Y-%m-%d')
            banknifty_next = banknifty_dates[1].strftime('%Y-%m-%d')
            
            logger.info(f"NIFTY - Current: {nifty_current}, Next: {nifty_next}")
            logger.info(f"BANKNIFTY - Current: {banknifty_current}, Next: {banknifty_next}")
            
            return (nifty_current, nifty_next), (banknifty_current, banknifty_next)
            
        except Exception as e:
            logger.error(f"Error calculating NIFTY/BANKNIFTY expiry: {e}")
            return None, None
    
    def _calculate_sensex_expiry(self) -> Tuple[str, str]:
        """Calculate SENSEX expiry dates from BFO file using BSXOPT symbol"""
        try:
            # Find latest BFO file
            bfo_files = glob.glob('data/BFO_symbols.txt_*.txt')
            if not bfo_files:
                raise FileNotFoundError("No BFO files found")
            
            latest_bfo = sorted(bfo_files)[-1]
            logger.info(f"Using BFO file: {latest_bfo}")
            
            # Read BFO file
            df = pd.read_csv(latest_bfo)
            
            # Look for BSXOPT symbol (not SX50OPT) - same as old project
            sensex_df = df[df['Symbol'] == 'BSXOPT']
            
            if sensex_df.empty:
                logger.warning("No BSXOPT symbols found in BFO file")
                return None
            
            sensex_dates = sorted(sensex_df['Expiry'].unique())
            
            # Convert to datetime and sort
            sensex_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in sensex_dates])
            
            # Get current and next (first two dates)
            sensex_current = sensex_dates[0].strftime('%Y-%m-%d')
            sensex_next = sensex_dates[1].strftime('%Y-%m-%d')
            
            logger.info(f"SENSEX - Current: {sensex_current}, Next: {sensex_next}")
            
            return (sensex_current, sensex_next)
            
        except Exception as e:
            logger.error(f"Error calculating SENSEX expiry: {e}")
            return None
    
    def _save_expiry_dates(self):
        """Save expiry dates to files and cache"""
        try:
            # Save to individual text files (old project format)
            with open('data/nf_expiry_dates.txt', 'w') as f:
                nifty = self.expiry_dates['NIFTY']
                f.write(f"{nifty['current']},{nifty['next']}")
            
            with open('data/bn_expiry_dates.txt', 'w') as f:
                banknifty = self.expiry_dates['BANKNIFTY']
                f.write(f"{banknifty['current']},{banknifty['next']}")
            
            with open('data/sx_expiry_dates.txt', 'w') as f:
                sensex = self.expiry_dates['SENSEX']
                f.write(f"{sensex['current']},{sensex['next']}")
            
            # Save to JSON cache
            cache_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'expiry_dates': self.expiry_dates
            }
            
            with open('data/expiry_cache.json', 'w') as f:
                json.dump(cache_data, f)
            
            logger.info("Saved expiry dates to files and cache")
            
        except Exception as e:
            logger.error(f"Error saving expiry dates: {e}")
    
    def should_refresh_expiry(self) -> bool:
        """Check if expiry dates need refresh (not from today)"""
        try:
            cache_file = 'data/expiry_cache.json'
            if not os.path.exists(cache_file):
                return True
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            today = datetime.now().strftime('%Y-%m-%d')
            return cache_data.get('date') != today
            
        except Exception as e:
            logger.error(f"Error checking refresh status: {e}")
            return True

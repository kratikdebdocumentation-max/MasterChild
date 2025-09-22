"""
Simple Expiry Date Manager
Minimal implementation for options expiry date management
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from logger import applicationLogger

class SimpleExpiryManager:
    """Simple expiry date manager with daily caching"""
    
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
                    applicationLogger.info("Loaded cached expiry dates from today")
                    return
            
            # Try to load from individual text files
            self._load_from_text_files()
            
        except Exception as e:
            applicationLogger.error(f"Error loading cached expiry: {e}")
    
    def _load_from_text_files(self):
        """Load expiry dates from individual text files"""
        try:
            # File mappings
            files = {
                'NIFTY': 'data/nf_expiry_dates.txt',
                'BANKNIFTY': 'data/bn_expiry_dates.txt',
                'SENSEX': 'data/sx_expiry_dates.txt'
            }
            
            for index, file_path in files.items():
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if ',' in content:
                            current, next_date = content.split(',', 1)
                            self.expiry_dates[index] = {
                                'current': self._format_expiry_date(current.strip()),
                                'next': self._format_expiry_date(next_date.strip())
                            }
                        else:
                            # Single date format
                            self.expiry_dates[index] = {
                                'current': self._format_expiry_date(content),
                                'next': ''
                            }
            
            applicationLogger.info("Loaded expiry dates from text files")
            
        except Exception as e:
            applicationLogger.error(f"Error loading from text files: {e}")
    
    def _format_expiry_date(self, date_str: str) -> str:
        """Format expiry date to DDMMMYY format"""
        try:
            if not date_str:
                return ""
            
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%d%b%y').upper()
                except ValueError:
                    continue
            
            # If no format matches, return as is
            return date_str.upper()
            
        except Exception as e:
            applicationLogger.error(f"Error formatting date {date_str}: {e}")
            return ""
    
    def _save_expiry_dates(self):
        """Save expiry dates to both individual files and JSON cache"""
        try:
            # Save to individual text files
            files = {
                'NIFTY': 'data/nf_expiry_dates.txt',
                'BANKNIFTY': 'data/bn_expiry_dates.txt',
                'SENSEX': 'data/sx_expiry_dates.txt'
            }
            
            for index, file_path in files.items():
                current = self.expiry_dates[index]['current']
                next_date = self.expiry_dates[index]['next']
                
                with open(file_path, 'w') as f:
                    if next_date:
                        f.write(f"{current},{next_date}")
                    else:
                        f.write(current)
            
            # Save to JSON cache
            cache_file = 'data/expiry_cache.json'
            cache_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'expiry_dates': self.expiry_dates
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            applicationLogger.info("Saved expiry dates to cache files")
            
        except Exception as e:
            applicationLogger.error(f"Error saving expiry dates: {e}")
    
    def get_expiry_list(self, index: str) -> List[str]:
        """Get list of available expiry dates for dropdown"""
        try:
            if index not in self.expiry_dates:
                return []
            
            current = self.expiry_dates[index]['current']
            next_date = self.expiry_dates[index]['next']
            
            # Return both current and next expiry (formatted for dropdown)
            expiry_list = []
            if current:
                # Format the date for display in dropdown
                formatted_current = self._format_expiry_date(current)
                expiry_list.append(formatted_current)
            if next_date and next_date != current:
                # Format the date for display in dropdown
                formatted_next = self._format_expiry_date(next_date)
                expiry_list.append(formatted_next)
            
            return expiry_list
            
        except Exception as e:
            applicationLogger.error(f"Error getting expiry list for {index}: {e}")
            return []
    
    def get_current_expiry(self, index: str) -> str:
        """Get current expiry date (formatted)"""
        current = self.expiry_dates.get(index, {}).get('current', '')
        return self._format_expiry_date(current) if current else ''
    
    def calculate_expiry_dates(self) -> bool:
        """Calculate current and next expiry dates (simplified logic)"""
        try:
            applicationLogger.info("Calculating expiry dates...")
            
            # Get current date
            today = datetime.now()
            
            # Calculate expiry dates for each index
            for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
                try:
                    current_expiry, next_expiry = self._calculate_expiry_for_index(index, today)
                    self.expiry_dates[index] = {
                        'current': self._format_expiry_date(current_expiry),
                        'next': self._format_expiry_date(next_expiry)
                    }
                    applicationLogger.info(f"{index} - Current: {current_expiry}, Next: {next_expiry}")
                except Exception as e:
                    applicationLogger.error(f"Error calculating expiry for {index}: {e}")
            
            # Save the calculated dates
            self._save_expiry_dates()
            applicationLogger.info("Successfully calculated and saved expiry dates")
            return True
            
        except Exception as e:
            applicationLogger.error(f"Error calculating expiry dates: {e}")
            return False
    
    def _calculate_expiry_for_index(self, index: str, today: datetime) -> tuple:
        """Calculate current and next expiry for an index (simplified)"""
        try:
            # Simplified logic: assume monthly expiry on last Thursday
            # This is a basic implementation - in real scenario, you'd use proper option chain data
            
            # Find last Thursday of current month
            current_month = today.replace(day=1)
            next_month = (current_month + timedelta(days=32)).replace(day=1)
            
            # Find last Thursday of current month
            last_day = next_month - timedelta(days=1)
            last_thursday = last_day - timedelta(days=(last_day.weekday() + 3) % 7)
            
            # If last Thursday has passed, use next month's last Thursday
            if last_thursday < today:
                next_month_last_day = (next_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                next_month_last_thursday = next_month_last_day - timedelta(days=(next_month_last_day.weekday() + 3) % 7)
                current_expiry = last_thursday.strftime('%Y-%m-%d')
                next_expiry = next_month_last_thursday.strftime('%Y-%m-%d')
            else:
                current_expiry = last_thursday.strftime('%Y-%m-%d')
                # Next expiry is next month's last Thursday
                next_month_last_day = (next_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                next_month_last_thursday = next_month_last_day - timedelta(days=(next_month_last_day.weekday() + 3) % 7)
                next_expiry = next_month_last_thursday.strftime('%Y-%m-%d')
            
            return current_expiry, next_expiry
            
        except Exception as e:
            applicationLogger.error(f"Error calculating expiry for {index}: {e}")
            # Fallback: use simple monthly calculation
            current_expiry = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            next_expiry = (today + timedelta(days=37)).strftime('%Y-%m-%d')
            return current_expiry, next_expiry
    
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
            applicationLogger.error(f"Error checking expiry refresh: {e}")
            return True

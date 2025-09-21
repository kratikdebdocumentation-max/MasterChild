"""
Index price management for strike calculation
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from logger import applicationLogger

class IndexPriceManager:
    """Manages index prices for strike calculation with file-first approach"""
    
    def __init__(self):
        self.index_prices = {}
        self._load_index_prices()
    
    def _load_index_prices(self):
        """Load index prices from files with file-first approach"""
        try:
            # Step 1: Try to load from text files first
            if self._load_from_text_files():
                applicationLogger.info("Loaded index prices from text files")
                return
            
            # Step 2: Try to load from cache file
            if self._load_from_cache_file():
                applicationLogger.info("Loaded index prices from cache file")
                return
            
            # Step 3: Initialize with empty prices (will be fetched when needed)
            applicationLogger.info("No cached index prices found, will fetch when needed")
            self.index_prices = {
                'NIFTY': 0.0,
                'BANKNIFTY': 0.0,
                'SENSEX': 0.0
            }
                
        except Exception as e:
            applicationLogger.error(f"Error loading index prices: {e}")
            self.index_prices = {
                'NIFTY': 0.0,
                'BANKNIFTY': 0.0,
                'SENSEX': 0.0
            }
    
    def _load_from_text_files(self):
        """Try to load index prices from existing text files"""
        try:
            # Check if index price file exists and is from today
            price_file = 'data/index_prices.txt'
            
            if not os.path.exists(price_file):
                return False
            
            # Check if file was modified today
            today = datetime.today().strftime('%Y-%m-%d')
            file_time = datetime.fromtimestamp(os.path.getmtime(price_file))
            if file_time.strftime('%Y-%m-%d') != today:
                return False
            
            # Load prices from file
            with open(price_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return False
                
                # Parse format: NIFTY:25000,BANKNIFTY:75000,SENSEX:80000
                prices = {}
                for pair in content.split(','):
                    if ':' in pair:
                        index, price = pair.split(':', 1)
                        try:
                            prices[index] = float(price)
                        except ValueError:
                            return False
                
                # Validate all required indices are present
                required_indices = ['NIFTY', 'BANKNIFTY', 'SENSEX']
                if all(index in prices for index in required_indices):
                    self.index_prices = prices
                    return True
                
            return False
            
        except Exception as e:
            applicationLogger.error(f"Error loading from text files: {e}")
            return False
    
    def _load_from_cache_file(self):
        """Try to load index prices from cache file"""
        try:
            cache_file = 'data/index_prices_cache.json'
            
            if not os.path.exists(cache_file):
                return False
                
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            today = datetime.today().strftime('%Y-%m-%d')
            if cache_data.get('date') == today and cache_data.get('prices'):
                self.index_prices = cache_data['prices']
                return True
                
            return False
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            applicationLogger.error(f"Cache file issue: {e}")
            return False
    
    def get_index_price(self, index: str) -> float:
        """
        Get cached index price
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, SENSEX)
            
        Returns:
            Cached index price or 0.0 if not available
        """
        return self.index_prices.get(index, 0.0)
    
    def update_index_price(self, index: str, price: float):
        """
        Update index price and save to files
        
        Args:
            index: Index name
            price: New price
        """
        try:
            self.index_prices[index] = price
            self._save_index_prices()
            applicationLogger.info(f"Updated {index} price to {price}")
        except Exception as e:
            applicationLogger.error(f"Error updating {index} price: {e}")
    
    def update_all_prices(self, prices: Dict[str, float]):
        """
        Update all index prices at once
        
        Args:
            prices: Dictionary of index prices
        """
        try:
            self.index_prices.update(prices)
            self._save_index_prices()
            applicationLogger.info(f"Updated all index prices: {prices}")
        except Exception as e:
            applicationLogger.error(f"Error updating all prices: {e}")
    
    def _save_index_prices(self):
        """Save index prices to files"""
        try:
            # Save to text file
            price_file = 'data/index_prices.txt'
            with open(price_file, 'w') as f:
                price_strings = [f"{index}:{price}" for index, price in self.index_prices.items()]
                f.write(','.join(price_strings))
            
            # Save to cache file
            cache_data = {
                'date': datetime.today().strftime('%Y-%m-%d'),
                'prices': self.index_prices
            }
            
            with open('data/index_prices_cache.json', 'w') as f:
                json.dump(cache_data, f)
            
            applicationLogger.info("Saved index prices to files")
            
        except Exception as e:
            applicationLogger.error(f"Error saving index prices: {e}")
    
    def has_valid_prices(self) -> bool:
        """Check if we have valid cached prices for all indices"""
        required_indices = ['NIFTY', 'BANKNIFTY', 'SENSEX']
        return all(
            index in self.index_prices and 
            self.index_prices[index] > 0 
            for index in required_indices
        )
    
    def should_refresh_prices(self) -> bool:
        """Check if prices need to be refreshed (not from today or invalid)"""
        try:
            # Check if we have valid prices
            if not self.has_valid_prices():
                return True
            
            # Check if price file exists and is from today
            price_file = 'data/index_prices.txt'
            if not os.path.exists(price_file):
                return True
            
            today = datetime.today().strftime('%Y-%m-%d')
            file_time = datetime.fromtimestamp(os.path.getmtime(price_file))
            if file_time.strftime('%Y-%m-%d') != today:
                return True
            
            return False
            
        except Exception as e:
            applicationLogger.error(f"Error checking if refresh needed: {e}")
            return True
    
    def clear_cache(self):
        """Clear all cached index prices"""
        try:
            # Clear in-memory prices
            self.index_prices = {
                'NIFTY': 0.0,
                'BANKNIFTY': 0.0,
                'SENSEX': 0.0
            }
            
            # Remove files
            files_to_remove = [
                'data/index_prices.txt',
                'data/index_prices_cache.json'
            ]
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            applicationLogger.info("Cleared all index price cache")
            
        except Exception as e:
            applicationLogger.error(f"Error clearing cache: {e}")

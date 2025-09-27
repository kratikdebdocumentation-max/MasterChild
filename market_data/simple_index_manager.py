"""
Simple Index Price Manager
Minimal implementation for NIFTY, BANKNIFTY, SENSEX price management
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional
from logger import applicationLogger

class SimpleIndexManager:
    """Simple index price manager with daily caching"""
    
    def __init__(self):
        self.index_prices = {'NIFTY': 0.0, 'BANKNIFTY': 0.0, 'SENSEX': 0.0}
        self.index_tokens = {
            'SENSEX': {'token': '1', 'exchange': 'BSE', 'name': 'BSE SENSEX'},
            'NIFTY': {'token': '26000', 'exchange': 'NSE', 'name': 'NIFTY 50'},
            'BANKNIFTY': {'token': '26009', 'exchange': 'NSE', 'name': 'NIFTY BANK'}
        }
        self.strike_intervals = {'NIFTY': 50, 'BANKNIFTY': 100, 'SENSEX': 100}
        self._load_cached_prices()
    
    def _load_cached_prices(self):
        """Load cached prices from file if available and from today"""
        try:
            cache_file = 'data/index_prices_cache.json'
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                today = datetime.now().strftime('%Y-%m-%d')
                if cache_data.get('date') == today and cache_data.get('prices'):
                    self.index_prices = cache_data['prices']
                    applicationLogger.info("Loaded cached index prices from today")
                    return
            
            # Try to load from simple text file
            text_file = 'data/index_prices.txt'
            if os.path.exists(text_file):
                with open(text_file, 'r') as f:
                    content = f.read().strip()
                    # Parse format: NIFTY:25000.0,BANKNIFTY:75000.0,SENSEX:80000.0
                    for pair in content.split(','):
                        if ':' in pair:
                            index, price = pair.split(':')
                            if index in self.index_prices:
                                self.index_prices[index] = float(price)
                    applicationLogger.info("Loaded index prices from text file")
                    return
            
            applicationLogger.info("No cached index prices found, will fetch when needed")
            
        except Exception as e:
            applicationLogger.error(f"Error loading cached prices: {e}")
    
    def _save_prices(self):
        """Save prices to both text and JSON files"""
        try:
            # Save to text file (simple format)
            text_file = 'data/index_prices.txt'
            with open(text_file, 'w') as f:
                price_strings = [f"{index}:{price}" for index, price in self.index_prices.items()]
                f.write(','.join(price_strings))
            
            # Save to JSON cache with date
            cache_file = 'data/index_prices_cache.json'
            cache_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'prices': self.index_prices
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            applicationLogger.info("Saved index prices to cache files")
            
        except Exception as e:
            applicationLogger.error(f"Error saving prices: {e}")
    
    def get_index_price(self, index: str) -> float:
        """Get cached index price"""
        return self.index_prices.get(index, 0.0)
    
    def fetch_index_prices(self, api) -> bool:
        """Fetch current index prices from API"""
        try:
            applicationLogger.info("Fetching index prices from API...")
            prices = {}
            
            for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
                try:
                    price = self._get_index_price_from_api(api, index)
                    if price and price > 0:
                        prices[index] = price
                        applicationLogger.info(f"Fetched {index} price: {price}")
                    else:
                        applicationLogger.warning(f"Could not fetch price for {index}")
                except Exception as e:
                    applicationLogger.error(f"Error fetching {index} price: {e}")
            
            if prices:
                self.index_prices.update(prices)
                self._save_prices()
                applicationLogger.info("Successfully updated all index prices")
                return True
            else:
                applicationLogger.warning("No index prices could be fetched")
                return False
                
        except Exception as e:
            applicationLogger.error(f"Error fetching index prices: {e}")
            return False
    
    def _get_index_price_from_api(self, api, index: str) -> Optional[float]:
        """Get index price from API"""
        try:
            if index not in self.index_tokens:
                return None
            
            index_info = self.index_tokens[index]
            applicationLogger.info(f"Fetching {index} price from {index_info['exchange']}")
            
            # Get quotes for the index
            quotes = api.get_quotes(index_info['exchange'], index_info['token'])
            if quotes and 'lp' in quotes:
                price = float(quotes['lp'])
                if price > 0:
                    return price
            
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting {index} price from API: {e}")
            return None
    
    def get_strike_list(self, index: str, current_price: float, option_type: str = None) -> list:
        """Generate strike list around current price based on option type"""
        try:
            if index not in self.strike_intervals:
                return []
            
            interval = self.strike_intervals[index]
            
            # Round to nearest interval
            rounded_price = round(current_price / interval) * interval
            
            # Generate strikes based on option type
            strikes = []
            if option_type == "CE":
                # CE: 2 below + current + 20 above (biased towards higher strikes)
                for i in range(-2, 21):
                    strike = rounded_price + (i * interval)
                    strikes.append(int(strike))
                # Ensure CE strikes are sorted in descending order
                strikes.sort(reverse=True)
                # Add arrow prefix to current strike
                strikes = [f"→ {strike}" if strike == rounded_price else str(strike) for strike in strikes]
            elif option_type == "PE":
                # PE: 20 below + current + 2 above (biased towards lower strikes)
                for i in range(-20, 3):
                    strike = rounded_price + (i * interval)
                    strikes.append(int(strike))
                # Ensure PE strikes are sorted in ascending order
                strikes.sort()
                # Add arrow prefix to current strike
                strikes = [f"→ {strike}" if strike == rounded_price else str(strike) for strike in strikes]
            else:
                # Default: 7 below + current + 7 above (balanced distribution)
                for i in range(-7, 8):
                    strike = rounded_price + (i * interval)
                    strikes.append(int(strike))
                # Ensure default strikes are sorted in ascending order
                strikes.sort()
                # Add arrow prefix to current strike
                strikes = [f"→ {strike}" if strike == rounded_price else str(strike) for strike in strikes]
            
            return strikes
            
        except Exception as e:
            applicationLogger.error(f"Error generating strikes for {index}: {e}")
            return []
    
    def should_refresh_prices(self) -> bool:
        """Check if prices need refresh (not from today)"""
        try:
            cache_file = 'data/index_prices_cache.json'
            if not os.path.exists(cache_file):
                return True
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            today = datetime.now().strftime('%Y-%m-%d')
            return cache_data.get('date') != today
            
        except Exception as e:
            applicationLogger.error(f"Error checking price refresh: {e}")
            return True

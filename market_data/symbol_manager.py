"""
Symbol and market data management
"""
import pandas as pd
import glob
from datetime import datetime
from typing import Optional, List, Dict, Any
from logger import applicationLogger

class SymbolManager:
    """Manages symbol data and market information"""
    
    def __init__(self):
        self.symbol_data = {}
        self.latest_files = {}
        self._load_latest_symbol_files()
    
    def _load_latest_symbol_files(self):
        """Load the latest symbol files"""
        try:
            # Find latest NFO file
            nfo_files = glob.glob("data/NFO_symbols.txt_*.txt")
            if nfo_files:
                files_with_dates = [(file, datetime.strptime(file.split('_')[-1].split('.txt')[0], "%Y-%m-%d")) 
                                  for file in nfo_files]
                latest_nfo = sorted(files_with_dates, key=lambda x: x[1], reverse=True)[0][0]
                self.latest_files['NFO'] = latest_nfo
                self.symbol_data['NFO'] = pd.read_csv(latest_nfo)
            
            # Find latest BFO file
            bfo_files = glob.glob("data/BFO_symbols.txt_*.txt")
            if bfo_files:
                files_with_dates = [(file, datetime.strptime(file.split('_')[-1].split('.txt')[0], "%Y-%m-%d")) 
                                  for file in bfo_files]
                latest_bfo = sorted(files_with_dates, key=lambda x: x[1], reverse=True)[0][0]
                self.latest_files['BFO'] = latest_bfo
                self.symbol_data['BFO'] = pd.read_csv(latest_bfo)
                
        except Exception as e:
            applicationLogger.error(f"Error loading symbol files: {e}")
    
    def get_token(self, trading_symbol: str) -> Optional[str]:
        """
        Get token for a trading symbol
        
        Args:
            trading_symbol: Trading symbol
            
        Returns:
            Token string or None
        """
        try:
            applicationLogger.info(f"Getting token for trading symbol: {trading_symbol}")
            
            # Check if it's a SENSEX symbol
            if "SENSEX" in trading_symbol:
                # For new format symbols, use them directly
                if 'BFO' in self.symbol_data:
                    row = self.symbol_data['BFO'][self.symbol_data['BFO']['TradingSymbol'] == trading_symbol]
                    if not row.empty:
                        token = str(row.iloc[0]['Token'])
                        applicationLogger.info(f"Found token for {trading_symbol}: {token}")
                        return token
                    else:
                        applicationLogger.error(f"No token found for {trading_symbol}")
                        # Try to find similar symbols for debugging
                        similar_symbols = self.symbol_data['BFO'][self.symbol_data['BFO']['TradingSymbol'].str.contains('SENSEX')]['TradingSymbol'].unique()
                        applicationLogger.info(f"Available SENSEX symbols (first 10): {similar_symbols[:10]}")
                        
                        # Fallback to old conversion method for backward compatibility
                        try:
                            bfo_trading_symbol = self._convert_sensex_format(trading_symbol)
                            applicationLogger.info(f"Trying converted SENSEX symbol: {trading_symbol} -> {bfo_trading_symbol}")
                            
                            row = self.symbol_data['BFO'][self.symbol_data['BFO']['TradingSymbol'] == bfo_trading_symbol]
                            if not row.empty:
                                token = str(row.iloc[0]['Token'])
                                applicationLogger.info(f"Found token for converted symbol {bfo_trading_symbol}: {token}")
                                return token
                        except Exception as e:
                            applicationLogger.error(f"Error in fallback conversion: {e}")
            else:
                # Check NFO symbols
                if 'NFO' in self.symbol_data:
                    row = self.symbol_data['NFO'][self.symbol_data['NFO']['TradingSymbol'] == trading_symbol]
                    if not row.empty:
                        token = str(row.iloc[0]['Token'])
                        applicationLogger.info(f"Found NFO token for {trading_symbol}: {token}")
                        return token
                    else:
                        applicationLogger.error(f"No token found for {trading_symbol}")
                        # Let's check what symbols are available
                        available_symbols = self.symbol_data['NFO']['TradingSymbol'].unique()
                        applicationLogger.info(f"Available NFO symbols (first 10): {available_symbols[:10]}")
            
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting token for {trading_symbol}: {e}")
            import traceback
            applicationLogger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _convert_sensex_format(self, input_str: str) -> str:
        """Convert SENSEX symbol format"""
        import calendar
        from datetime import datetime, timedelta
        
        def is_last_friday(date):
            """Check if the given date is the last Friday of the month."""
            year = date.year
            month = date.month
            last_day = calendar.monthrange(year, month)[1]
            last_date = datetime(year, month, last_day)
            last_friday = last_date - timedelta(days=(last_date.weekday() - 4) % 7)
            return date == last_friday
        
        parts = input_str.split('SENSEX')
        if len(parts) < 2:
            raise ValueError("Invalid input format")
        
        details = parts[1]
        date_part = details[:7]  # e.g., 27DEC24 or 03JAN25
        strike_price = details[7:-2]  # e.g., 78000
        ce_pe = details[-2:]  # CE or PE
        
        day = int(date_part[:2])
        month_str = date_part[2:5].upper()
        year = int(date_part[5:])
        
        month = datetime.strptime(month_str, "%b").month
        date_obj = datetime(2000 + year, month, day)
        
        if is_last_friday(date_obj):
            output = f"SENSEX{year}{month_str}{strike_price}{ce_pe}"
        else:
            output = f"SENSEX{year}{month}{day:02d}{strike_price}{ce_pe}"
        
        return output
    
    def get_quotes(self, api, exchange: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get quotes for a symbol
        
        Args:
            api: API instance
            exchange: Exchange name
            token: Symbol token
            
        Returns:
            Quote data or None
        """
        try:
            return api.get_quotes(exchange=exchange, token=token)
        except Exception as e:
            applicationLogger.error(f"Error getting quotes for {exchange}|{token}: {e}")
            return None
    
    def get_latest_price(self, api, trading_symbol: str) -> Optional[float]:
        """
        Get latest price for a trading symbol
        
        Args:
            api: API instance
            trading_symbol: Trading symbol
            
        Returns:
            Latest price or None
        """
        try:
            # Determine exchange
            if 'SENSEX' in trading_symbol:
                exchange = 'BFO'
            else:
                exchange = 'NFO'
            
            # Get token
            token = self.get_token(trading_symbol)
            if not token:
                return None
            
            # Get quotes
            quotes = self.get_quotes(api, exchange, token)
            if quotes:
                return float(quotes.get('lp', 0))
            
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting latest price for {trading_symbol}: {e}")
            return None
    
    def get_index_price(self, api, index_name: str) -> Optional[float]:
        """
        Get latest price for an index
        
        Args:
            api: API instance
            index_name: Index name (SENSEX, NIFTY, BANKNIFTY)
            
        Returns:
            Latest index price or None
        """
        try:
            # Index tokens mapping
            index_tokens = {
                'SENSEX': {'token': '1', 'exchange': 'BSE', 'name': 'BSE SENSEX'},
                'NIFTY': {'token': '26000', 'exchange': 'NSE', 'name': 'NIFTY 50'},
                'BANKNIFTY': {'token': '26009', 'exchange': 'NSE', 'name': 'NIFTY BANK'}
            }
            
            if index_name not in index_tokens:
                applicationLogger.error(f"Unknown index: {index_name}")
                return None
            
            index_info = index_tokens[index_name]
            
            # Get quotes for the index
            quotes = self.get_quotes(api, index_info['exchange'], index_info['token'])
            if quotes:
                price = float(quotes.get('lp', 0))
                applicationLogger.info(f"Fetched {index_name} price: {price}")
                return price
            
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting index price for {index_name}: {e}")
            return None

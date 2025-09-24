import glob
import os
import json
from datetime import datetime, timedelta


def find_exp():
    """Calculate expiry dates with file-first approach for maximum efficiency"""
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Step 1: Try to load from existing text files first
    if _load_from_text_files():
        print("✅ Loaded expiry dates from existing text files")
        return
    
    # Step 2: Try to load from cache file
    if _load_from_cache_file(today):
        print("✅ Loaded expiry dates from cache file")
        return
    
    # Step 3: Only if both above fail, calculate from master files
    print("⚠️  Text files and cache not available, calculating from master files...")
    _calculate_from_master_files()


def _load_from_text_files():
    """Try to load expiry dates from existing text files"""
    try:
        # Check if all required text files exist and are from today
        text_files = [
            'data/nf_expiry_dates.txt',
            'data/bn_expiry_dates.txt', 
            'data/sx_expiry_dates.txt'
        ]
        
        today = datetime.today().strftime('%Y-%m-%d')
        
        for file_path in text_files:
            if not os.path.exists(file_path):
                return False
            
            # Check if file was modified today
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time.strftime('%Y-%m-%d') != today:
                return False
            
            # Check if file has valid content (current,next format)
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if ',' not in content or len(content.split(',')) != 2:
                    return False
        
        print("📁 All text files exist and are current")
        return True
        
    except Exception as e:
        print(f"Error checking text files: {e}")
        return False


def _load_from_cache_file(today):
    """Try to load expiry dates from cache file"""
    try:
        cache_file = 'data/expiry_cache.json'
        
        if not os.path.exists(cache_file):
            return False
            
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            
        if cache_data.get('date') == today and cache_data.get('expiry_dates'):
            print("📁 Loading from cache file...")
            _save_cached_expiry_dates(cache_data['expiry_dates'])
            return True
            
        return False
        
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Cache file issue: {e}")
        return False


def _calculate_from_master_files():
    """Calculate expiry dates from master files (fallback only)"""
    # Find the latest files based on today's date
    date_str = datetime.today().strftime('%Y-%m-%d')
    nfo_files = glob.glob(f'data/NFO_symbols.txt_{date_str}.txt')
    bfo_files = glob.glob(f'data/BFO_symbols.txt_{date_str}.txt')

    # Initialize sets to hold expiry dates
    nifty_dates = set()
    banknifty_dates = set()
    sensex_dates = set()

    # Process NFO files for NIFTY and BANKNIFTY
    for nfo_file in nfo_files:
        with open(nfo_file, 'r') as file:
            for line in file:
                values = line.strip().split(',')
                if values[3] == 'NIFTY':
                    nifty_dates.add(values[5])
                elif values[3] == 'BANKNIFTY':
                    banknifty_dates.add(values[5])

    # Process BFO files for SENSEX
    for bfo_file in bfo_files:
        with open(bfo_file, 'r') as file:
            for line in file:
                values = line.strip().split(',')
                if values[3] == 'BSXOPT':
                    sensex_dates.add(values[5])

    # Convert dates to datetime objects and sort them
    nifty_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in nifty_dates])
    banknifty_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in banknifty_dates])
    sensex_dates = sorted([datetime.strptime(date, '%d-%b-%Y') for date in sensex_dates])

    def find_current_and_next_expiry(dates):
        """Find current and next expiry dates from sorted list"""
        if len(dates) < 2:
            raise ValueError(f"Not enough expiry dates found. Found: {len(dates)}, Required: 2")
        
        # Get first two dates (current and next)
        current_date = dates[0]
        next_date = dates[1]
        
        return current_date, next_date

    # Get current and next expiry for each instrument
    nifty_current, nifty_next = find_current_and_next_expiry(nifty_dates)
    banknifty_current, banknifty_next = find_current_and_next_expiry(banknifty_dates)
    sensex_current, sensex_next = find_current_and_next_expiry(sensex_dates)

    # Format dates to 'YYYY-MM-DD'
    nifty_current = nifty_current.strftime('%Y-%m-%d')
    nifty_next = nifty_next.strftime('%Y-%m-%d')
    banknifty_current = banknifty_current.strftime('%Y-%m-%d')
    banknifty_next = banknifty_next.strftime('%Y-%m-%d')
    sensex_current = sensex_current.strftime('%Y-%m-%d')
    sensex_next = sensex_next.strftime('%Y-%m-%d')

    # Print the expiry dates
    print('Current and Next expiry for:')
    print('NIFTY - Current:', nifty_current, 'Next:', nifty_next)
    print('BANKNIFTY - Current:', banknifty_current, 'Next:', banknifty_next)
    print('SENSEX - Current:', sensex_current, 'Next:', sensex_next)

    # Prepare expiry dates dictionary for caching
    expiry_dates = {
        'nifty': {'current': nifty_current, 'next': nifty_next},
        'banknifty': {'current': banknifty_current, 'next': banknifty_next},
        'sensex': {'current': sensex_current, 'next': sensex_next}
    }
    
    # Save to cache file for future use
    cache_data = {
        'date': datetime.today().strftime('%Y-%m-%d'),
        'expiry_dates': expiry_dates
    }
    
    try:
        with open('data/expiry_cache.json', 'w') as f:
            json.dump(cache_data, f)
        print("Expiry dates cached for faster future startup...")
    except Exception as e:
        print(f"Warning: Could not save cache file: {e}")
    
    # Save the dates to individual files in data folder
    _save_cached_expiry_dates(expiry_dates)


def _save_cached_expiry_dates(expiry_dates):
    """Save cached expiry dates to individual files"""
    try:
        # Save current and next expiry dates for each instrument
        for instrument, dates in expiry_dates.items():
            current = dates.get('current', '')
            next_date = dates.get('next', '')
            
            if instrument == 'nifty':
                with open('data/nf_expiry_dates.txt', 'w') as f:
                    f.write(f"{current},{next_date}")
                with open('data/expiry_dates.txt', 'w') as f:
                    f.write(f"{current},{next_date}")
            elif instrument == 'banknifty':
                with open('data/bn_expiry_dates.txt', 'w') as f:
                    f.write(f"{current},{next_date}")
            elif instrument == 'sensex':
                with open('data/sx_expiry_dates.txt', 'w') as f:
                    f.write(f"{current},{next_date}")
        
        print("✅ Saved current and next expiry dates for NIFTY, BANKNIFTY, and SENSEX")
        
    except Exception as e:
        print(f"Error saving expiry date files: {e}")


def _save_enhanced_expiry_calculations():
    """Save enhanced expiry calculations to individual files"""
    try:
        # Save SENSEX enhanced calculation
        sensex_dates = get_sensex_expiry_dates()
        if sensex_dates and len(sensex_dates) >= 2:
            current_date = datetime.strptime(sensex_dates[0][0], '%d-%b-%Y')
            with open('data/sx_expiry_dates.txt', 'w') as f:
                f.write(current_date.strftime('%Y-%m-%d'))
            print(f"Enhanced SENSEX expiry saved: {current_date.strftime('%Y-%m-%d')}")
        
        # Save BANKNIFTY enhanced calculation
        banknifty_dates = _get_banknifty_expiry_dates()
        if banknifty_dates and len(banknifty_dates) >= 2:
            current_date = datetime.strptime(banknifty_dates[0][0], '%d-%b-%Y')
            with open('data/bn_expiry_dates.txt', 'w') as f:
                f.write(current_date.strftime('%Y-%m-%d'))
            print(f"Enhanced BANKNIFTY expiry saved: {current_date.strftime('%Y-%m-%d')}")
            
    except Exception as e:
        print(f"Error saving enhanced expiry calculations: {e}")


def _get_banknifty_expiry_dates():
    """Get all BANKNIFTY expiry dates from NFO file in chronological order"""
    import os
    from collections import defaultdict
    
    # Find the latest NFO file
    nfo_files = [f for f in os.listdir('data') if f.startswith('NFO_symbols.txt_') and f.endswith('.txt')]
    if not nfo_files:
        print("No NFO files found for BANKNIFTY")
        return []
    
    latest_nfo = sorted(nfo_files)[-1]
    nfo_file_path = os.path.join('data', latest_nfo)
    
    if not os.path.exists(nfo_file_path):
        print(f"NFO file not found: {nfo_file_path}")
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
        print(f"Error reading NFO file for BANKNIFTY expiry dates: {e}")
        return []


def clear_expiry_cache():
    """Clear the expiry cache to force recalculation"""
    cache_file = 'data/expiry_cache.json'
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Expiry cache cleared. Next startup will recalculate expiry dates.")


def is_cache_valid():
    """Check if the expiry cache is valid for today"""
    cache_file = 'data/expiry_cache.json'
    today = datetime.today().strftime('%Y-%m-%d')
    
    if not os.path.exists(cache_file):
        return False
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            return cache_data.get('date') == today and cache_data.get('expiry_dates')
    except (json.JSONDecodeError, KeyError):
        return False


def force_expiry_recalculation():
    """Force recalculation from master files (bypasses file-first logic)"""
    print("🔄 Forcing recalculation from master files...")
    clear_expiry_cache()
    _calculate_from_master_files()


def should_recalculate_expiry():
    """Check if expiry dates need to be recalculated"""
    try:
        # Check if text files exist and are current
        if _load_from_text_files():
            return False
        
        # Check if cache exists and is current
        today = datetime.today().strftime('%Y-%m-%d')
        if _load_from_cache_file(today):
            return False
        
        # Need to recalculate
        return True
        
    except Exception as e:
        print(f"Error checking if recalculation needed: {e}")
        return True


def get_sensex_expiry_dates(bfo_file_path=None):
    """
    Get all SENSEX expiry dates from BFO file in chronological order
    This function is called only once per day due to caching in find_exp()
    
    Args:
        bfo_file_path: Path to BFO file (if None, uses today's file)
        
    Returns:
        List of tuples: (expiry_date_str, day_of_week, symbol_count)
    """
    if bfo_file_path is None:
        today = datetime.today().strftime('%Y-%m-%d')
        bfo_file_path = f'data/BFO_symbols.txt_{today}.txt'
    
    if not os.path.exists(bfo_file_path):
        print(f"Warning: BFO file not found at {bfo_file_path}")
        return []
    
    from collections import defaultdict
    expiry_counts = defaultdict(int)
    
    try:
        with open(bfo_file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) >= 6:
                    # Check if it's a SENSEX option (BSXOPT only, exclude SX50OPT)
                    if 'SENSEX' in parts[4] and not parts[4].startswith('SENSEX50'):  # TradingSymbol column
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
        print(f"Error reading BFO file for SENSEX expiry dates: {e}")
        return []

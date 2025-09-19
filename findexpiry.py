import glob
import os
import json
from datetime import datetime, timedelta


def find_exp():
    """Calculate expiry dates with caching for faster startup"""
    # Check if we have valid cached expiry dates
    cache_file = 'data/expiry_cache.json'
    today = datetime.today().strftime('%Y-%m-%d')
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                if cache_data.get('date') == today and cache_data.get('expiry_dates'):
                    print("Using cached expiry dates for faster startup...")
                    _save_cached_expiry_dates(cache_data['expiry_dates'])
                    return
        except (json.JSONDecodeError, KeyError):
            print("Cache file corrupted, recalculating expiry dates...")
    
    # Find the latest files based on today's date
    date_str = today
    nfo_files = glob.glob(f'data/NFO_symbols.txt_{date_str}.txt')
    mcx_files = glob.glob(f'data/MCX_symbols.txt_{date_str}.txt')
    bfo_files = glob.glob(f'data/BFO_symbols.txt_{date_str}.txt')

    # Initialize sets to hold expiry dates
    finnifty_dates = set()
    nifty_dates = set()
    banknifty_dates = set()
    midcpnifty_dates = set()
    crude_dates = set()
    sensex_dates = set()
    bankex_dates = set()

    # Process NFO files
    for nfo_file in nfo_files:
        with open(nfo_file, 'r') as file:
            for line in file:
                values = line.strip().split(',')
                if values[3] == 'FINNIFTY':
                    finnifty_dates.add(values[5])
                elif values[3] == 'NIFTY':
                    nifty_dates.add(values[5])
                elif values[3] == 'BANKNIFTY':
                    banknifty_dates.add(values[5])
                elif values[3] == 'MIDCPNIFTY':
                    midcpnifty_dates.add(values[5])

    # Process MCX files
    for mcx_file in mcx_files:
        with open(mcx_file, 'r') as file:
            for line in file:
                values = line.strip().split(',')
                if values[4] == 'CRUDEOIL':
                    crude_dates.add(values[6])

    # Process BFO files
    for bfo_file in bfo_files:
        with open(bfo_file, 'r') as file:
            for line in file:
                values = line.strip().split(',')
                if values[3] == 'BSXOPT':
                    sensex_dates.add(values[5])
                elif values[3] == 'BKXOPT':
                    bankex_dates.add(values[5])
    
    # Enhanced SENSEX expiry calculation - get all dates and find the earliest
    sensex_earliest_date = None
    sensex_all_dates = get_sensex_expiry_dates()
    
    if sensex_all_dates:
        print("📅 All SENSEX Expiry Dates from BFO File (Sorted)")
        print("Here are all the SENSEX expiry dates found in the BFO file, sorted chronologically:")
        print("2025 Expiry Dates:")
        
        for expiry_date, day_of_week, count in sensex_all_dates:
            print(f"{expiry_date} ({day_of_week}) - {count} symbols")
        
        # Get the earliest date for the main calculation
        if sensex_all_dates:
            earliest_date_str = sensex_all_dates[0][0]
            sensex_earliest_date = datetime.strptime(earliest_date_str, '%d-%b-%Y')
            print(f"\nUsing earliest SENSEX expiry: {earliest_date_str} ({sensex_earliest_date.strftime('%A')})")

    # Convert dates to datetime objects
    finnifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in finnifty_dates]
    nifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in nifty_dates]
    banknifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in banknifty_dates]
    midcpnifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in midcpnifty_dates]
    crude_dates = [datetime.strptime(date, '%d-%b-%Y') for date in crude_dates]
    # Use the enhanced SENSEX calculation result
    sensex_dates = [sensex_earliest_date] if sensex_earliest_date else []
    bankex_dates = [datetime.strptime(date, '%d-%b-%Y') for date in bankex_dates]

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    futdate = datetime.today() + timedelta(days=32)

    def find_min_date(dates):
        min_date = None
        for date in dates:
            if date < futdate and date >= today:
                if min_date is None or date < min_date:
                    min_date = date
        return min_date

    finnifty_min_date = find_min_date(finnifty_dates)
    nifty_min_date = find_min_date(nifty_dates)
    banknifty_min_date = find_min_date(banknifty_dates)
    midcpnifty_min_date = find_min_date(midcpnifty_dates)
    sensex_min_date = find_min_date(sensex_dates)
    bankex_min_date = find_min_date(bankex_dates)

    futdate = datetime.today() + timedelta(days=30)
    crude_min_date = find_min_date(crude_dates)

    # Format dates to 'YYYY-MM-DD'
    if finnifty_min_date: finnifty_min_date = finnifty_min_date.strftime('%Y-%m-%d')
    if nifty_min_date: nifty_min_date = nifty_min_date.strftime('%Y-%m-%d')
    if banknifty_min_date: banknifty_min_date = banknifty_min_date.strftime('%Y-%m-%d')
    if midcpnifty_min_date: midcpnifty_min_date = midcpnifty_min_date.strftime('%Y-%m-%d')
    if crude_min_date: crude_min_date = crude_min_date.strftime('%Y-%m-%d')
    if sensex_min_date: sensex_min_date = sensex_min_date.strftime('%Y-%m-%d')
    if bankex_min_date: bankex_min_date = bankex_min_date.strftime('%Y-%m-%d')

    # Print the expiry dates
    print('Current expiry for:')
    print('FINNIFTY:', finnifty_min_date)
    print('NIFTY:', nifty_min_date)
    print('BANKNIFTY:', banknifty_min_date)
    print('MIDCPNIFTY:', midcpnifty_min_date)
    print('SENSEX:', sensex_min_date)
    print('BANKEX:', bankex_min_date)
    print('CRUDE:', crude_min_date)

    # Prepare expiry dates dictionary for caching
    expiry_dates = {
        'finnifty': finnifty_min_date,
        'nifty': nifty_min_date,
        'banknifty': banknifty_min_date,
        'midcpnifty': midcpnifty_min_date,
        'crude': crude_min_date,
        'sensex': sensex_min_date,
        'bankex': bankex_min_date
    }
    
    # Save to cache file for future use
    cache_data = {
        'date': today,
        'expiry_dates': expiry_dates
    }
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        print("Expiry dates cached for faster future startup...")
    except Exception as e:
        print(f"Warning: Could not save cache file: {e}")
    
    # Save the dates to individual files in data folder
    _save_cached_expiry_dates(expiry_dates)


def _save_cached_expiry_dates(expiry_dates):
    """Save cached expiry dates to individual files"""
    try:
        with open('data/fn_expiry_dates.txt', 'w') as f:
            if expiry_dates['finnifty']: f.write(expiry_dates['finnifty'])
        with open('data/nf_expiry_dates.txt', 'w') as f:
            if expiry_dates['nifty']: f.write(expiry_dates['nifty'])
        with open('data/expiry_dates.txt', 'w') as f:
            if expiry_dates['nifty']: f.write(expiry_dates['nifty'])
        with open('data/bn_expiry_dates.txt', 'w') as f:
            if expiry_dates['banknifty']: f.write(expiry_dates['banknifty'])
        with open('data/md_expiry_dates.txt', 'w') as f:
            if expiry_dates['midcpnifty']: f.write(expiry_dates['midcpnifty'])
        with open('data/co_expiry_dates.txt', 'w') as f:
            if expiry_dates['crude']: f.write(expiry_dates['crude'])
        with open('data/sx_expiry_dates.txt', 'w') as f:
            if expiry_dates['sensex']: f.write(expiry_dates['sensex'])
        with open('data/bx_expiry_dates.txt', 'w') as f:
            if expiry_dates['bankex']: f.write(expiry_dates['bankex'])
        
        # Save enhanced calculations for SENSEX and BANKNIFTY
        _save_enhanced_expiry_calculations()
        
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
    """Force recalculation of expiry dates even if cache exists"""
    clear_expiry_cache()
    find_exp()


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
                    # Check if it's a SENSEX option (BSXOPT or SX50OPT)
                    if 'SENSEX' in parts[4]:  # TradingSymbol column
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

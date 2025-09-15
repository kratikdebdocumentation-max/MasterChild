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

    # Convert dates to datetime objects
    finnifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in finnifty_dates]
    nifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in nifty_dates]
    banknifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in banknifty_dates]
    midcpnifty_dates = [datetime.strptime(date, '%d-%b-%Y') for date in midcpnifty_dates]
    crude_dates = [datetime.strptime(date, '%d-%b-%Y') for date in crude_dates]
    sensex_dates = [datetime.strptime(date, '%d-%b-%Y') for date in sensex_dates]
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
    except Exception as e:
        print(f"Error saving expiry date files: {e}")


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

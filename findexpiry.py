import glob
from datetime import datetime, timedelta


def find_exp():
    # Find the latest files based on today's date
    date_str = datetime.today().strftime('%Y-%m-%d')

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

    # Save the dates to files in data folder
    with open('data/fn_expiry_dates.txt', 'w') as f:
        if finnifty_min_date: f.write(finnifty_min_date)
    with open('data/nf_expiry_dates.txt', 'w') as f:
        if nifty_min_date: f.write(nifty_min_date)
    with open('data/expiry_dates.txt', 'w') as f:
        if nifty_min_date: f.write(nifty_min_date)
    with open('data/bn_expiry_dates.txt', 'w') as f:
        if banknifty_min_date: f.write(banknifty_min_date)
    with open('data/md_expiry_dates.txt', 'w') as f:
        if midcpnifty_min_date: f.write(midcpnifty_min_date)
    with open('data/co_expiry_dates.txt', 'w') as f:
        if crude_min_date: f.write(crude_min_date)
    with open('data/sx_expiry_dates.txt', 'w') as f:
        if sensex_min_date: f.write(sensex_min_date)
    with open('data/bx_expiry_dates.txt', 'w') as f:
        if bankex_min_date: f.write(bankex_min_date)

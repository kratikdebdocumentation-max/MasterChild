import os
import requests
import zipfile
from datetime import datetime

root = 'https://api.shoonya.com/'
masters = ['NSE_symbols.txt.zip', 'NFO_symbols.txt.zip', 'MCX_symbols.txt.zip', 'BFO_symbols.txt.zip']

current_date = datetime.now().strftime("_%Y-%m-%d")


def downloadFileMaster():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    for zip_file in masters:
        base_name = zip_file.replace('.zip', '')
        todays_file = f"data/{base_name}{current_date}.txt"

        if os.path.exists(todays_file):
            print(f"File for today already exists: {todays_file}. Skipping download.")
            continue

        print(f'Downloading {zip_file}')
        url = root + zip_file
        try:
            r = requests.get(url, allow_redirects=True)
            r.raise_for_status()  # Raise exception if response code is not 200
            with open(zip_file, 'wb') as f:
                f.write(r.content)

            with zipfile.ZipFile(zip_file, 'r') as z:
                z.extractall()
                extracted_file = z.namelist()[0]  # Assume there's only one file in the zip
                os.rename(extracted_file, todays_file)
                print(f"Extracted and renamed to: {todays_file}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {zip_file}: {e}")
        except zipfile.BadZipFile:
            print(f"Error extracting {zip_file}: Invalid zip file")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if os.path.exists(zip_file):
                os.remove(zip_file)
                print(f'Removed: {zip_file}')


def get_latest_expiry_date_from_file(file_path, instrument):
    try:
        with open(file_path, 'r') as file:
            data = file.readlines()

        # Filter data for the specified instrument
        instrument_data = [line.split(",") for line in data if line.split(",")[3] == instrument]

        # Extract expiry dates and convert them to datetime objects
        expiry_dates = [datetime.strptime(entry[5].strip(), "%d-%b-%Y") for entry in instrument_data]

        # Find the latest expiry date
        latest_expiry_date = min(expiry_dates)

        return latest_expiry_date
    except Exception as e:
        print(f"Error reading data from file: {e}")
        return None


# Get the latest NFO symbols file
downloadFileMaster()
nfo_file = max(
    (file for file in os.listdir('data') if file.startswith('NFO_symbols') and file.endswith('.txt')),
    key=lambda f: datetime.strptime(f.split('_')[-1].replace('.txt', ''), '%Y-%m-%d')
)
nfo_file = os.path.join('data', nfo_file)  # Add data folder path

global latest_expiry_NF
global latest_expiry_BN

latest_expiry_NF = get_latest_expiry_date_from_file(nfo_file, "NIFTY")
latest_expiry_BN = get_latest_expiry_date_from_file(nfo_file, "BANKNIFTY")


# Functions to format expiry dates
def getBNExpiry():
    date_object = datetime.strptime(str(latest_expiry_BN), "%Y-%m-%d %H:%M:%S")
    formatted_BN = date_object.strftime("%d%b%y").upper()
    return formatted_BN


def getNFExpiry():
    date_object = datetime.strptime(str(latest_expiry_NF), "%Y-%m-%d %H:%M:%S")
    formatted_NF = date_object.strftime("%d%b%y").upper()
    return formatted_NF

#df = getNFExpiry()
#print(df)

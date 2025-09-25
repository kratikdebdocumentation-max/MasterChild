"""
Master File Downloader for Trading System
Downloads symbol master files from Shoonya API
"""
import os
import requests
import zipfile
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)

# API configuration
ROOT_URL = 'https://api.shoonya.com/'
MASTER_FILES = ['NSE_symbols.txt.zip', 'NFO_symbols.txt.zip', 'MCX_symbols.txt.zip', 'BFO_symbols.txt.zip']

def download_master_files():
    """
    Download master symbol files from Shoonya API
    Only downloads if today's files don't exist
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        current_date = datetime.now().strftime("_%Y-%m-%d")
        downloaded_files = []
        
        for zip_file in MASTER_FILES:
            base_name = zip_file.replace('.zip', '')
            todays_file = f"data/{base_name}{current_date}.txt"

            if os.path.exists(todays_file):
                logger.info(f"File for today already exists: {todays_file}. Skipping download.")
                continue

            logger.info(f'Downloading {zip_file}...')
            url = ROOT_URL + zip_file
            
            try:
                # Download the file
                response = requests.get(url, allow_redirects=True, timeout=30)
                response.raise_for_status()
                
                # Save zip file temporarily
                with open(zip_file, 'wb') as f:
                    f.write(response.content)

                # Extract and rename
                with zipfile.ZipFile(zip_file, 'r') as z:
                    z.extractall()
                    extracted_file = z.namelist()[0]  # Assume there's only one file in the zip
                    os.rename(extracted_file, todays_file)
                    logger.info(f"Extracted and renamed to: {todays_file}")
                    downloaded_files.append(todays_file)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error downloading {zip_file}: {e}")
            except zipfile.BadZipFile:
                logger.error(f"Error extracting {zip_file}: Invalid zip file")
            except Exception as e:
                logger.error(f"An unexpected error occurred with {zip_file}: {e}")
            finally:
                # Clean up temporary zip file
                if os.path.exists(zip_file):
                    os.remove(zip_file)
                    logger.debug(f'Removed temporary file: {zip_file}')
        
        if downloaded_files:
            logger.info(f"Successfully downloaded {len(downloaded_files)} master files")
        else:
            logger.info("All master files are up to date")
            
        return len(downloaded_files) > 0
        
    except Exception as e:
        logger.error(f"Error in download_master_files: {e}")
        return False

def should_download_master_files():
    """
    Check if master files need to be downloaded
    Returns True if files are older than 1 day or missing
    """
    try:
        current_date = datetime.now().strftime("_%Y-%m-%d")
        
        for zip_file in MASTER_FILES:
            base_name = zip_file.replace('.zip', '')
            todays_file = f"data/{base_name}{current_date}.txt"
            
            if not os.path.exists(todays_file):
                logger.info(f"Master file missing: {todays_file}")
                return True
                
        logger.info("All master files are current")
        return False
        
    except Exception as e:
        logger.error(f"Error checking master files: {e}")
        return True

def cleanup_old_master_files(days_to_keep=3):
    """
    Clean up old master files, keep only the latest N days
    """
    try:
        cleaned_files = 0
        current_date = datetime.now()
        
        for zip_file in MASTER_FILES:
            base_name = zip_file.replace('.zip', '')
            pattern = f"data/{base_name}_*.txt"
            
            # Find all matching files
            import glob
            files = glob.glob(pattern)
            
            if not files:
                continue
                
            # Sort by date (newest first)
            files.sort(key=lambda f: datetime.strptime(f.split('_')[-1].replace('.txt', ''), '%Y-%m-%d'), reverse=True)
            
            # Delete files older than days_to_keep
            for file_path in files:
                try:
                    # Extract date from filename
                    file_date_str = file_path.split('_')[-1].replace('.txt', '')
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    
                    # Calculate days difference
                    days_old = (current_date - file_date).days
                    
                    if days_old > days_to_keep:
                        os.remove(file_path)
                        logger.info(f"Deleted old master file: {os.path.basename(file_path)} (age: {days_old} days)")
                        cleaned_files += 1
                    else:
                        logger.debug(f"Keeping file: {os.path.basename(file_path)} (age: {days_old} days)")
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {cleaned_files} old master files deleted")
        return cleaned_files
        
    except Exception as e:
        logger.error(f"Error cleaning up old master files: {e}")
        return 0

def get_latest_master_file(file_type):
    """
    Get the latest master file for a specific type (NFO, BFO, etc.)
    """
    try:
        pattern = f"data/{file_type}_symbols_*.txt"
        import glob
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Return the newest file
        latest_file = max(files, key=lambda f: datetime.strptime(f.split('_')[-1].replace('.txt', ''), '%Y-%m-%d'))
        return latest_file
        
    except Exception as e:
        logger.error(f"Error getting latest {file_type} file: {e}")
        return None

if __name__ == "__main__":
    # Test the downloader
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testing master file downloader...")
    
    # Check if download is needed
    if should_download_master_files():
        print("Downloading fresh master files...")
        success = download_master_files()
        if success:
            print("[SUCCESS] Master files downloaded successfully")
        else:
            print("[ERROR] Failed to download master files")
    else:
        print("[SUCCESS] Master files are up to date")
    
    # Cleanup old files
    print("Cleaning up old files...")
    cleaned = cleanup_old_master_files()
    print(f"Cleaned up {cleaned} old files")

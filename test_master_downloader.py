#!/usr/bin/env python3
"""
Test script for master file downloader
"""
import logging
from master_file_downloader import download_master_files, should_download_master_files, cleanup_old_master_files

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_master_downloader():
    """Test the master file downloader"""
    try:
        print("🧪 Testing Master File Downloader")
        print("=" * 50)
        
        # Test 1: Check if download is needed
        print("\n1. Checking if download is needed...")
        needs_download = should_download_master_files()
        print(f"   Download needed: {needs_download}")
        
        # Test 2: Download master files
        print("\n2. Downloading master files...")
        success = download_master_files()
        print(f"   Download success: {success}")
        
        # Test 3: Check again after download
        print("\n3. Checking again after download...")
        needs_download_after = should_download_master_files()
        print(f"   Download needed: {needs_download_after}")
        
        # Test 4: Cleanup old files
        print("\n4. Cleaning up old files...")
        cleaned = cleanup_old_master_files()
        print(f"   Files cleaned: {cleaned}")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_master_downloader()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")

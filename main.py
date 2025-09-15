"""
Main entry point for Master-Child Trading GUI System
"""
import sys
import os
from findexpiry import find_exp, clear_expiry_cache, force_expiry_recalculation, is_cache_valid
from downloadMasters_v0 import downloadFileMaster
from gui.main_window import MainWindow
from logger import applicationLogger

def initialize_system():
    """Initialize the trading system"""
    try:
        # Download master files (with timeout handling)
        applicationLogger.info("Downloading master files...")
        downloadFileMaster()
        
        # Find expiry dates
        applicationLogger.info("Finding expiry dates...")
        find_exp()
        
        applicationLogger.info("System initialization completed successfully")
        return True
        
    except Exception as e:
        applicationLogger.error(f"Error during system initialization: {e}")
        return False

def initialize_system_async():
    """Initialize the trading system asynchronously (non-blocking)"""
    try:
        # Start master file download in background
        applicationLogger.info("Starting master file download in background...")
        import threading
        download_thread = threading.Thread(target=downloadFileMaster, daemon=True)
        download_thread.start()
        
        # Find expiry dates (now with caching - very fast if cached)
        applicationLogger.info("Finding expiry dates (with caching)...")
        find_exp()
        
        applicationLogger.info("System initialization completed (downloads in background)")
        return True
        
    except Exception as e:
        applicationLogger.error(f"Error during system initialization: {e}")
        return False

def show_cache_status():
    """Show the status of expiry cache"""
    if is_cache_valid():
        print("✅ Expiry cache is valid - startup will be fast")
    else:
        print("⚠️  Expiry cache is invalid or missing - will recalculate on startup")

def clear_cache():
    """Clear all caches for fresh calculation"""
    clear_expiry_cache()
    print("🗑️  All caches cleared - next startup will recalculate everything")

def main():
    """Main application entry point"""
    try:
        # Initialize system (use async version for faster startup)
        if not initialize_system_async():
            print("Failed to initialize system. Please check logs for details.")
            sys.exit(1)
        
        # Create and run main window
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        applicationLogger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        applicationLogger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

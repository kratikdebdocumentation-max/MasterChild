"""
Main entry point for Master-Child Trading GUI System
"""
import sys
import os
from findexpiry import find_exp
from downloadMasters_v0 import downloadFileMaster
from gui.main_window import MainWindow
from logger import applicationLogger

def initialize_system():
    """Initialize the trading system"""
    try:
        # Download master files
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

def main():
    """Main application entry point"""
    try:
        # Initialize system
        if not initialize_system():
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

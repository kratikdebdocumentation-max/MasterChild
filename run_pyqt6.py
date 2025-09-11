"""
Launcher for PyQt6 Trading Application
"""
import sys
import os
import subprocess

def install_requirements():
    """Install PyQt6 requirements"""
    try:
        print("Installing PyQt6 requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_pyqt6.txt"])
        print("Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 Starting Modern PyQt6 Trading Application...")
    
    # Check if requirements are installed
    try:
        import PyQt6
        print("✅ PyQt6 is already installed")
    except ImportError:
        print("❌ PyQt6 not found. Installing requirements...")
        if not install_requirements():
            print("Failed to install requirements. Please install manually:")
            print("pip install -r requirements_pyqt6.txt")
            return
    
    # Run the PyQt6 application
    try:
        from pyqt6_app.main import main as run_app
        run_app()
    except Exception as e:
        print(f"Error running application: {e}")
        print("Make sure all requirements are installed correctly.")

if __name__ == "__main__":
    main()

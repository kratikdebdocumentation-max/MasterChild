# Master-Child Trading GUI - Setup Instructions

## Prerequisites

### 1. Python Installation
- Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
- **IMPORTANT**: During installation, check "Add Python to PATH"
- Verify installation by opening Command Prompt and typing: `python --version`

### 2. System Requirements
- Windows 10/11
- Internet connection (for downloading dependencies)
- At least 2GB free disk space

## Quick Setup (Recommended)

### Method 1: Using the Batch File (Easiest)
1. **Download/Clone** the Master-Child GUI project to your computer
2. **Navigate** to the project folder in Windows Explorer
3. **Double-click** `run_master_child_gui.bat`
4. The batch file will automatically:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Start the application

### Method 2: Manual Setup
If the batch file doesn't work, follow these manual steps:

#### Step 1: Open Command Prompt
- Press `Win + R`, type `cmd`, press Enter
- Navigate to the project folder:
  ```cmd
  cd C:\path\to\MasterChild_GUI
  ```

#### Step 2: Create Virtual Environment
```cmd
python -m venv trading_env
```

#### Step 3: Activate Virtual Environment
```cmd
trading_env\Scripts\activate
```

#### Step 4: Install Dependencies
```cmd
pip install -r requirements.txt
```

#### Step 5: Run the Application
```cmd
python main.py
```

## Configuration

### 1. Credentials Setup
Before first use, you need to set up your trading credentials:

1. **Copy** one of the credential files:
   - `credentials1.json` (for Master account)
   - `credentials2.json` (for Child account)
   - `credentials3.json` (for additional account)

2. **Edit** the credential file with your details:
   ```json
   {
       "userid": "YOUR_USER_ID",
       "password": "YOUR_PASSWORD",
       "totp_secret": "YOUR_TOTP_SECRET",
       "vendor_code": "YOUR_VENDOR_CODE",
       "api_secret": "YOUR_API_SECRET",
       "imei": "YOUR_IMEI"
   }
   ```

### 2. Settings Configuration
- The application will create `config/settings.json` automatically
- You can modify default settings in this file if needed

## Troubleshooting

### Common Issues

#### 1. "Python is not recognized"
- **Solution**: Reinstall Python and make sure to check "Add Python to PATH"
- **Alternative**: Add Python to PATH manually in System Environment Variables

#### 2. "pip is not recognized"
- **Solution**: Install Python with pip included (default option)
- **Alternative**: Use `python -m pip` instead of `pip`

#### 3. "Module not found" errors
- **Solution**: Make sure virtual environment is activated
- **Check**: Run `pip list` to see installed packages

#### 4. "Permission denied" errors
- **Solution**: Run Command Prompt as Administrator
- **Alternative**: Check if antivirus is blocking the application

#### 5. Application crashes on startup
- **Check**: Ensure all credential files are properly configured
- **Check**: Verify internet connection
- **Check**: Look at logs in the `logs` folder for error details

### Getting Help

#### Log Files
- Application logs: `logs/applicationLogger_YYYY-MM-DD.log`
- WebSocket logs: `logs/Log_Master1_WS_YYYY-MM-DD.log`
- Child WebSocket logs: `logs/Log_Child_WS_YYYY-MM-DD.log`

#### Debug Mode
To run with debug information:
```cmd
python main.py --debug
```

## File Structure

```
MasterChild_GUI/
├── run_master_child_gui.bat    # Windows batch launcher
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── config/
│   └── settings.json          # Application settings
├── credentials1.json           # Master account credentials
├── credentials2.json           # Child account credentials
├── credentials3.json           # Additional account credentials
├── data/                       # Market data and symbols
├── logs/                       # Application logs
├── gui/                        # GUI components
├── trading/                    # Trading logic
├── market_data/                # Market data management
└── utils/                      # Utility functions
```

## Security Notes

- **Never share** your credential files
- **Keep credentials secure** and don't commit them to version control
- **Use strong passwords** for your trading accounts
- **Enable 2FA** on your trading accounts

## Updates

To update the application:
1. Download the latest version
2. Replace the old files
3. Run `run_master_child_gui.bat` again
4. The batch file will handle dependency updates

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review log files for error details
3. Ensure all prerequisites are met
4. Verify your trading account credentials

---

**Note**: This application is for educational and personal use only. Always follow your broker's terms of service and local regulations.

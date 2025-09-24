# Master-Child Trading GUI - Quick Start

## 🚀 One-Click Launch

Simply **double-click** `run_master_child_gui.bat` to start the application!

## What the Batch File Does

The `run_master_child_gui.bat` file automatically:

1. ✅ **Checks Python installation**
2. ✅ **Creates virtual environment** (if not exists)
3. ✅ **Installs all dependencies**
4. ✅ **Creates necessary folders**
5. ✅ **Starts the application**

## Before First Run

1. **Install Python 3.8+** from [python.org](https://python.org)
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Configure your credentials**:
   - Edit `credentials1.json` with your Master account details
   - Edit `credentials2.json` with your Child account details

3. **Run the batch file**:
   - Double-click `run_master_child_gui.bat`
   - Wait for setup to complete (first time only)
   - Application will start automatically

## Troubleshooting

### If the batch file doesn't work:
1. **Check Python installation**: Open Command Prompt, type `python --version`
2. **Run as Administrator**: Right-click the batch file → "Run as administrator"
3. **Check internet connection**: Required for downloading dependencies

### If you get errors:
- Check the `SETUP_INSTRUCTIONS.md` file for detailed troubleshooting
- Look at log files in the `logs` folder
- Ensure your credential files are properly configured

## File Structure

```
MasterChild_GUI/
├── run_master_child_gui.bat    ← Double-click this to start!
├── main.py
├── requirements.txt
├── credentials1.json           ← Configure your Master account
├── credentials2.json           ← Configure your Child account
├── SETUP_INSTRUCTIONS.md       ← Detailed setup guide
└── README_BATCH.md            ← This file
```

## Need Help?

- 📖 **Detailed Setup**: See `SETUP_INSTRUCTIONS.md`
- 🔧 **Troubleshooting**: Check the troubleshooting section
- 📝 **Logs**: Check `logs` folder for error details

---

**Ready to trade? Just double-click the batch file! 🎯**

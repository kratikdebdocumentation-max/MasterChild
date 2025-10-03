#!/usr/bin/env python3
"""
Master-Child Trading GUI - Fresh Start
Recreated with the same UI as the original system
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
import threading
import time
import re
import os

# Import trading modules
from trading.account_manager import AccountManager
from trading.account_state_manager import AccountStateManager
from trading.websocket_manager import WebSocketManager
from config import Config
from config_manager import ConfigManager
from config_window import ConfigWindow

# Import market data modules
from market_data.simple_index_manager import SimpleIndexManager
from market_data.expiry_manager import ExpiryManager
from market_data.symbol_manager import SymbolManager

# Import master file downloader
from master_file_downloader import download_master_files, should_download_master_files, cleanup_old_master_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y-%m-%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CenteredConfirmationDialog:
    """Custom confirmation dialog that centers on parent window"""
    
    def __init__(self, parent, title, message, icon='question'):
        self.parent = parent
        self.result = None
        self.dialog = None
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        
        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create the dialog content
        self.create_widgets(message, icon)
        
        # Center the dialog on the parent window
        self.center_on_parent()
        
        # Focus on the dialog
        self.dialog.focus()
        
        # Wait for user response
        self.dialog.wait_window()
    
    def create_widgets(self, message, icon):
        """Create the dialog widgets"""
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon and message frame
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon (using text symbol for simplicity)
        icon_text = "?" if icon == 'question' else "!"
        icon_label = tk.Label(content_frame, text=icon_text, font=("Arial", 24, "bold"), 
                             fg="blue" if icon == 'question' else "orange")
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Message label
        message_label = tk.Label(content_frame, text=message, font=("Arial", 10), 
                                wraplength=400, justify=tk.LEFT)
        message_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Yes button
        yes_button = tk.Button(button_frame, text="Yes", command=self.yes_clicked, 
                              width=10, font=("Arial", 10, "bold"))
        yes_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # No button
        no_button = tk.Button(button_frame, text="No", command=self.no_clicked, 
                             width=10, font=("Arial", 10))
        no_button.pack(side=tk.RIGHT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.yes_clicked())
        self.dialog.bind('<Escape>', lambda e: self.no_clicked())
        
        # Set focus to Yes button
        yes_button.focus()
    
    def center_on_parent(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        
        # Get parent window geometry
        if self.parent and self.parent.winfo_exists():
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Get dialog size
            dialog_width = self.dialog.winfo_width()
            dialog_height = self.dialog.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            # Ensure dialog stays on screen
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            
            x = max(0, min(x, screen_width - dialog_width))
            y = max(0, min(y, screen_height - dialog_height))
            
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        else:
            # Fallback to screen center if parent is not available
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def yes_clicked(self):
        """Handle Yes button click"""
        self.result = True
        self.dialog.destroy()
    
    def no_clicked(self):
        """Handle No button click"""
        self.result = False
        self.dialog.destroy()
    
    @staticmethod
    def askyesno(parent, title, message, icon='question'):
        """Static method to show confirmation dialog"""
        dialog = CenteredConfirmationDialog(parent, title, message, icon)
        return dialog.result

class WebSocketErrorDialog:
    """Custom error dialog for websocket disconnection errors"""
    
    def __init__(self, parent, title, message, account_info=""):
        self.parent = parent
        self.dialog = None
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        
        # Make it modal and always on top
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.attributes('-topmost', True)
        
        # Create the dialog content
        self.create_widgets(message, account_info)
        
        # Center the dialog on the parent window
        self.center_on_parent()
        
        # Focus on the dialog
        self.dialog.focus()
        
        # Make it stay on top
        self.dialog.lift()
        self.dialog.focus_force()
    
    def create_widgets(self, message, account_info):
        """Create the dialog widgets"""
        # Main frame with red border for error
        main_frame = tk.Frame(self.dialog, padx=20, pady=20, relief=tk.RAISED, bd=2, bg='#ffebee')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title frame
        title_frame = tk.Frame(main_frame, bg='#ffebee')
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Error icon and title
        error_icon = tk.Label(title_frame, text="⚠", font=("Arial", 32, "bold"), 
                             fg="red", bg='#ffebee')
        error_icon.pack(side=tk.LEFT, padx=(0, 15))
        
        title_label = tk.Label(title_frame, text="WEBSOCKET DISCONNECTED", 
                              font=("Arial", 16, "bold"), fg="red", bg='#ffebee')
        title_label.pack(side=tk.LEFT)
        
        # Message frame
        message_frame = tk.Frame(main_frame, bg='#ffebee')
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Account info if available
        if account_info:
            account_label = tk.Label(message_frame, text=f"Account: {account_info}", 
                                   font=("Arial", 12, "bold"), fg="darkred", bg='#ffebee')
            account_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Main error message
        error_message = tk.Label(message_frame, text=message, font=("Arial", 12), 
                                wraplength=500, justify=tk.LEFT, fg="darkred", bg='#ffebee')
        error_message.pack(anchor=tk.W, pady=(0, 10))
        
        # Action instructions
        instructions = [
            "IMMEDIATE ACTION REQUIRED:",
            "1. RESTART the program immediately",
            "2. Check your internet connection",
            "3. Manage your positions quickly",
            "4. Do not place new orders until reconnected"
        ]
        
        for instruction in instructions:
            if instruction.startswith("IMMEDIATE"):
                color = "red"
                font_weight = "bold"
            else:
                color = "darkred"
                font_weight = "normal"
            
            inst_label = tk.Label(message_frame, text=instruction, font=("Arial", 11, font_weight), 
                                 fg=color, bg='#ffebee', anchor=tk.W)
            inst_label.pack(anchor=tk.W, pady=2)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#ffebee')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Action buttons
        restart_button = tk.Button(button_frame, text="RESTART APP", command=self.restart_clicked, 
                                  width=15, font=("Arial", 10, "bold"), bg='#f44336', fg='white',
                                  relief=tk.RAISED, bd=2)
        restart_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ok_button = tk.Button(button_frame, text="I UNDERSTAND", command=self.ok_clicked, 
                             width=15, font=("Arial", 10, "bold"), bg='#4CAF50', fg='white',
                             relief=tk.RAISED, bd=2)
        ok_button.pack(side=tk.RIGHT)
        
        # Bind Enter key to OK
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        
        # Set focus to OK button
        ok_button.focus()
    
    def center_on_parent(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        
        # Get parent window geometry
        if self.parent and self.parent.winfo_exists():
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Get dialog size
            dialog_width = self.dialog.winfo_width()
            dialog_height = self.dialog.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            # Ensure dialog stays on screen
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            
            x = max(0, min(x, screen_width - dialog_width))
            y = max(0, min(y, screen_height - dialog_height))
            
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        else:
            # Fallback to screen center if parent is not available
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok_clicked(self):
        """Handle OK button click"""
        self.dialog.destroy()
    
    def restart_clicked(self):
        """Handle Restart button click"""
        self.dialog.destroy()
        # Restart the application
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    @staticmethod
    def show_error(parent, title, message, account_info=""):
        """Static method to show error dialog"""
        dialog = WebSocketErrorDialog(parent, title, message, account_info)
        return dialog

class LogMonitor:
    """Monitor log files for WebSocket disconnection errors"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.running = False
        self.monitor_thread = None
        self.log_files = []
        self.file_positions = {}
        self.seen_errors = set()  # Track already shown errors to avoid duplicates
        self.startup_time = time.time()  # Track when monitoring started
        self.startup_delay = 60  # 1 minute delay before monitoring starts
        self.error_detected = False  # Flag to stop monitoring after first error
        
        # Load Telegram configuration
        self.telegram_config = self._load_telegram_config()
        self.telegram_bot_token = self.telegram_config.get('bot_token', '')
        self.telegram_channel_id = self.telegram_config.get('channel_id', '')
        self.telegram_enabled = self.telegram_config.get('enabled', False)
        
        # Error patterns to monitor
        self.error_patterns = [
            r"websocket run forever ended in exception",
            r"socket is already opened",
            r"WebSocket connection lost",
            r"Connection timeout",
            r"WebSocket error",
            r"websocket.*disconnect",
            r"websocket.*error",
            r"connection.*lost",
            r"connection.*failed"
        ]
        
        # Account patterns to extract account info
        self.account_patterns = [
            r"account\s*(\d+)",
            r"master.*account",
            r"child.*account",
            r"account.*(\d+)"
        ]
    
    def start_monitoring(self):
        """Start the log monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Log monitoring started")
    
    def stop_monitoring(self):
        """Stop the log monitoring thread"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("Log monitoring stopped")
    
    def is_monitoring(self):
        """Check if monitoring is currently active"""
        return self.running and self.monitor_thread and self.monitor_thread.is_alive()
    
    def reset_monitoring(self):
        """Reset monitoring state to allow monitoring to start again"""
        self.error_detected = False
        self.seen_errors.clear()
        self.file_positions.clear()
        logger.info("Log monitoring state reset")
    
    def restart_monitoring(self):
        """Restart monitoring after reset"""
        if not self.running:
            self.reset_monitoring()
            self.start_monitoring()
    
    def _load_telegram_config(self):
        """Load Telegram configuration from file"""
        try:
            import json
            config_file = 'telegram_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    logger.info("Telegram configuration loaded successfully")
                    return config
            else:
                logger.warning("Telegram config file not found, using defaults")
                return {'enabled': False, 'bot_token': '', 'channel_id': '', 'timeout': 10}
        except Exception as e:
            logger.error(f"Error loading Telegram configuration: {e}")
            return {'enabled': False, 'bot_token': '', 'channel_id': '', 'timeout': 10}
    
    def send_telegram_notification(self, error_message, account_info):
        """Send notification to Telegram channel"""
        if not self.telegram_enabled:
            return
        
        try:
            import requests
            
            # Format the message for Telegram
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"🚨 **WebSocket Error Alert** 🚨\n\n"
            message += f"**Account:** {account_info}\n"
            message += f"**Time:** {timestamp}\n"
            message += f"**Error:** `{error_message}`\n\n"
            message += f"⚠️ **Action Required:** Check your trading system immediately!"
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Message data
            data = {
                'chat_id': self.telegram_channel_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            # Send the message
            timeout = self.telegram_config.get('timeout', 10)
            response = requests.post(url, data=data, timeout=timeout)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
            else:
                logger.error(f"Failed to send Telegram notification: {response.status_code} - {response.text}")
                
        except ImportError:
            logger.error("Requests library not available for Telegram notifications")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def validate_telegram_config(self):
        """Validate Telegram configuration"""
        if not self.telegram_enabled:
            return False
        
        if not self.telegram_bot_token:
            return False
        
        if not self.telegram_channel_id:
            return False
        
        return True
    
    def send_order_completion_notification(self, account_id, symbol, price, quantity, trantype, status):
        """Send order completion notification to Telegram channel"""
        if not self.telegram_enabled:
            return
        
        try:
            import requests
            
            # Determine account name
            account_name = "MASTER" if account_id == 1 else "CHILD"
            
            # Determine order type and emoji
            order_type = "BUY" if trantype.upper() == 'B' else "SELL"
            emoji = "✅" if status == "COMPLETE" else "⚠️"
            
            # Format the message for Telegram
            message = f"{account_name} → {emoji} {order_type} ORDER COMPLETED\n\n"
            message += f"**Symbol:** `{symbol}`\n"
            message += f"**Price:** {price}\n"
            message += f"**Quantity:** {quantity}\n"
            message += f"**Status:** {status}\n"
            message += f"**Account:** {account_name} (ID: {account_id})"
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Message data
            data = {
                'chat_id': self.telegram_channel_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            # Send the message (non-blocking)
            timeout = self.telegram_config.get('timeout', 10)
            response = requests.post(url, data=data, timeout=timeout)
            
            if response.status_code == 200:
                logger.info(f"Order completion notification sent for {account_name} - {order_type} {symbol}")
            else:
                logger.error(f"Failed to send order completion notification: {response.status_code} - {response.text}")
                
        except ImportError:
            logger.error("Requests library not available for order completion notifications")
        except Exception as e:
            logger.error(f"Error sending order completion notification: {e}")
    
    def send_startup_notification(self):
        """Send startup welcome message to Telegram channel"""
        if not self.telegram_enabled:
            return
        
        try:
            import requests
            
            # Get current timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the welcome message
            message = f"🚀 **Trading System Started** 🚀\n\n"
            message += f"**Time:** {timestamp}\n"
            message += f"**Status:** Online and Ready\n"
            message += f"**Monitoring:** WebSocket Errors & Order Completions\n\n"
            message += f"✅ **Ready for Trading!**\n"
            message += f"📊 Order completions will be notified\n"
            message += f"⚠️ WebSocket errors will be alerted"
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Message data
            data = {
                'chat_id': self.telegram_channel_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            # Send the message
            timeout = self.telegram_config.get('timeout', 10)
            response = requests.post(url, data=data, timeout=timeout)
            
            if response.status_code == 200:
                logger.info("Startup notification sent successfully")
            else:
                logger.error(f"Failed to send startup notification: {response.status_code} - {response.text}")
                
        except ImportError:
            logger.error("Requests library not available for startup notification")
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
    
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        # Wait for startup delay before beginning monitoring
        while self.running and (time.time() - self.startup_time) < self.startup_delay:
            time.sleep(1)  # Check every second during startup delay
        
        if not self.running:
            return
            
        logger.info(f"Log monitoring active after {self.startup_delay} second startup delay")
        
        while self.running and not self.error_detected:
            try:
                self._check_log_files()
                time.sleep(5)  # Check every 5 seconds (balanced frequency)
            except Exception as e:
                logger.error(f"Error in log monitoring: {e}")
                time.sleep(10)  # Wait longer on error
        
        if self.error_detected:
            logger.info("Log monitoring stopped after first error detection")
        else:
            logger.info("Log monitoring stopped normally")
    
    def _check_log_files(self):
        """Check all log files for new errors"""
        if self.error_detected:
            return  # Don't check if error already detected
            
        try:
            # Get current log file
            current_log = f'logs/app_{datetime.now().strftime("%Y-%m-%d")}.log'
            logger.debug(f"Checking log file: {current_log}")
            
            # Check if file exists
            if not os.path.exists(current_log):
                logger.debug(f"Log file does not exist: {current_log}")
                return
            
            # Initialize file position if not exists
            if current_log not in self.file_positions:
                # Start from end of file to avoid reading old content
                with open(current_log, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # Seek to end
                    self.file_positions[current_log] = f.tell()
                logger.debug(f"Initialized file position for {current_log}: {self.file_positions[current_log]}")
                return
            
            # Read only new content
            with open(current_log, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.file_positions[current_log])
                new_content = f.read()
                self.file_positions[current_log] = f.tell()
            
            logger.debug(f"Read {len(new_content)} new characters from log file")
            
            # Check for error patterns only in new content
            if new_content.strip():
                logger.debug(f"Processing new content: {new_content[:200]}...")
                self._process_new_content(new_content, current_log)
                
        except Exception as e:
            logger.error(f"Error checking log files: {e}")
    
    def _process_new_content(self, content, log_file):
        """Process new log content for error patterns"""
        if self.error_detected:
            return  # Stop processing if error already detected
            
        lines = content.split('\n')
        
        for line in lines:
            if not line.strip() or self.error_detected:
                continue
            
            # Check for error patterns
            for pattern in self.error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Extract account info
                    account_info = self._extract_account_info(line)
                    
                    # Show error popup immediately
                    logger.error(f"WebSocket error detected: {line.strip()}")
                    logger.error(f"Pattern matched: {pattern}")
                    
                    # Send Telegram notification
                    self.send_telegram_notification(line.strip(), account_info)
                    
                    # Show popup directly on main thread (synchronous)
                    try:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        detailed_message = f"WebSocket connection error detected:\n\n{line.strip()}\n\nTime: {timestamp}\nLog: {os.path.basename(log_file)}"
                        
                        # Create and show dialog directly
                        WebSocketErrorDialog.show_error(
                            self.main_window.root,
                            "WebSocket Disconnection Error",
                            detailed_message,
                            account_info
                        )
                        logger.error("Error popup displayed successfully")
                    except Exception as e:
                        logger.error(f"Error showing popup: {e}")
                    
                    # Mark error as detected and stop monitoring
                    self.error_detected = True
                    logger.error("Stopping log monitoring after first error detection")
                    self.running = False
                    return  # Exit immediately after first error
    
    def _extract_account_info(self, line):
        """Extract account information from log line"""
        for pattern in self.account_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if "master" in pattern.lower():
                    return "Master Account"
                elif "child" in pattern.lower():
                    return f"Child Account {match.group(1) if match.groups() else ''}"
                elif match.groups():
                    account_num = match.group(1)
                    return "Master Account" if account_num == "1" else f"Child Account {account_num}"
        
        return "Unknown Account"
    
    def _show_error_popup(self, error_line, account_info, log_file):
        """Show error popup on main thread"""
        try:
            # Create detailed error message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            detailed_message = f"WebSocket connection error detected:\n\n{error_line}\n\nTime: {timestamp}\nLog: {os.path.basename(log_file)}"
            
            # Schedule popup on main thread
            self.main_window.root.after(0, self._display_error_popup, detailed_message, account_info)
            
        except Exception as e:
            logger.error(f"Error showing error popup: {e}")
    
    def _display_error_popup(self, message, account_info):
        """Display error popup on main thread"""
        try:
            WebSocketErrorDialog.show_error(
                self.main_window.root,
                "WebSocket Disconnection Error",
                message,
                account_info
            )
        except Exception as e:
            logger.error(f"Error displaying error popup: {e}")
    

class MainWindow:
    """Main application window - Recreated with original UI layout"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("***Kratik's Soft*** - Master Account Not Logged In")
        self.root.geometry("900x490")
        
        # Position the window at right bottom of screen
        self.center_window()
        
        # Initialize account management
        self.account_manager = AccountManager()
        self.account_state_manager = AccountStateManager("account_state.csv")
        self.config_manager = ConfigManager()
        
        # Reset account states to initial state on startup
        self.reset_account_states_on_startup()
        
        # Initialize market data managers
        self.index_manager = SimpleIndexManager()
        self.expiry_manager = ExpiryManager()
        self.symbol_manager = SymbolManager()
        
        # Initialize websocket manager
        self.websocket_manager = WebSocketManager(self.account_manager)
        
        # Setup websocket callbacks
        self.setup_websocket_callbacks()
        
        # Start websocket connection monitoring
        self.websocket_manager.start_connection_monitoring()
        
        # Initialize log monitor for WebSocket errors
        self.log_monitor = LogMonitor(self)
        self.log_monitor.start_monitoring()
        
        # Validate Telegram configuration and send welcome message
        if self.log_monitor.validate_telegram_config():
            logger.info("Telegram notifications enabled for order completions and WebSocket errors")
            # Send welcome message
            self.log_monitor.send_startup_notification()
        else:
            logger.warning("Telegram configuration invalid, notifications disabled")
        
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load configuration
        self.config = Config.load_configuration_csv()
        
        # Master account holder name
        self.master_account_name = tk.StringVar()
        self.master_account_name.set("Not Logged In")
        
        # Setup variables
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Setup logging
        self.setup_logging()
        
        # Download master files if needed
        self.download_master_files_if_needed()
        
        # Auto-login master account
        self.auto_login_master()
        
        # Initialize quantity dropdown with default values
        self.update_quantity_dropdown()
        
    def center_window(self):
        """Position the window at right bottom of the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = self.root.winfo_screenwidth() - width - 50  # 50 pixels from right edge
        y = self.root.winfo_screenheight() - height - 50  # 50 pixels from bottom edge
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def download_master_files_if_needed(self):
        """Download master files if they are missing or outdated"""
        try:
            logger.info("Checking master files...")
            
            # Check if download is needed
            if should_download_master_files():
                logger.info("Master files are missing or outdated, downloading fresh files...")
                
                # Download in a separate thread to avoid blocking UI
                def download_thread():
                    try:
                        success = download_master_files()
                        if success:
                            logger.info("[SUCCESS] Master files downloaded successfully")
                            # Clean up old files
                            cleanup_old_master_files()
                        else:
                            logger.warning("[WARNING] Failed to download some master files")
                    except Exception as e:
                        logger.error(f"Error downloading master files: {e}")
                
                # Start download in background
                threading.Thread(target=download_thread, daemon=True).start()
            else:
                logger.info("[SUCCESS] Master files are up to date")
                
        except Exception as e:
            logger.error(f"Error checking master files: {e}")
    
    def setup_variables(self):
        """Setup Tkinter variables"""
        # Index selection
        self.selected_index = tk.StringVar()
        self.expiry_value = tk.StringVar()
        self.selected_strike = tk.StringVar()
        self.selected_option = tk.StringVar()
        
        # Price variables
        self.price_value = tk.StringVar()
        self.price1_value = tk.StringVar()
        self.modify_buy_value = tk.StringVar()
        self.modify_exit_value = tk.StringVar()
        
        # Store original buy price for modify functionality
        self.original_buy_price = None
        
        # Flag to track if buy price field was manually cleared by user
        self.buy_price_manually_cleared = False
        
        # Track previous value to detect manual changes
        self.previous_price_value = ""

        self.sl_price_value = tk.StringVar()
        self.target_price_value = tk.StringVar()
        
        # Trailing stop loss variables
        self.trail_value = tk.StringVar()  # Single value field
        self.enable_trailing_value = tk.BooleanVar()
        self.trail_type_selected = tk.StringVar()  # "point" or "percent"
        self.trail_status_text = tk.StringVar()
        self.trail_status_text.set("Trailing Disabled")
        
        # Trailing mode variables
        self.trailing_active = False
        self.trailing_start_price = None
        self.trailing_high_price = None
        self.trailing_stop_price = None
        
        # Child account order blocking flag
        self.child_orders_blocked = False
        
        # Premium price variable for live updates
        self.premium_price_value = tk.StringVar()
        
        # Index LTP variable
        self.index_ltp_value = tk.StringVar()
        
        # Current trading symbol for order placement
        self.current_trading_symbol = None
        
        # Order state tracking
        self.order_states = {
            1: "PENDING",  # Master account order status
            2: "PENDING"   # Child account order status
        }
        
        # SL and Target monitoring variables (from old project)
        self.sl_monitoring_active = False
        self.target_monitoring_active = False
        self.sl_price_level = None
        self.target_price_level = None
        
        # Button state tracking for two-step confirmation
        self.sl_button_state = "ready"  # "ready", "showing_price", "confirmed"
        self.target_button_state = "ready"  # "ready", "showing_price", "confirmed"
        
        # Auto SL/Target system variables - load from configuration.csv
        try:
            sl_points = int(self.config_manager.get_setting('default_auto_sl', 20))
            target_points = int(self.config_manager.get_setting('default_auto_target', 30))
            self.sl_difference_from_buy = -sl_points  # SL points from buy price (negative)
            self.target_difference_from_buy = target_points  # Target points from buy price (positive)
            logger.info(f"SL/Target configuration loaded - SL: {sl_points} points, Target: {target_points} points")
            logger.info(f"Calculated differences - SL: {self.sl_difference_from_buy}, Target: {self.target_difference_from_buy}")
        except Exception as e:
            logger.error(f"Error loading SL/Target configuration: {e}")
            # Fallback to default values
            self.sl_difference_from_buy = -20
            self.target_difference_from_buy = 30
            logger.info(f"Using fallback values - SL: {self.sl_difference_from_buy}, Target: {self.target_difference_from_buy}")
        
        self.current_buy_order_open_value = None  # Track current buy order open value
        
        # SL/Target state tracking for distance maintenance during order modifications
        self.sl_target_states = {
            'sl_calculated': False,
            'target_calculated': False,
            'sl_active': False,
            'target_active': False,
            'sl_triggered': False,
            'target_triggered': False,
            'sl_price': None,
            'target_price': None,
            'sl_points': 0,
            'target_points': 0,
            'buy_price': None
        }
        
        # Timeout timer for order management
        self.timeout_timer = None
        
        self.index_ltp_value.set("--")
        
        # Order status variables
        self.master_order_status = tk.StringVar()
        self.child_order_status = tk.StringVar()
        self.master_order_status.set("Master Not Logged In")
        self.child_order_status.set("Child Not Logged In")
        
        # PnL variables
        self.master_pnl_value = tk.StringVar()
        self.child_pnl_value = tk.StringVar()
        self.master_pnl_value.set("")  # Hidden by default
        self.child_pnl_value.set("")   # Hidden by default
        
        
        # Cross-account coordination variables
        self.master_order_state = None  # PENDING, OPEN, FILLED, REJECTED, CANCELLED
        self.child_order_state = None
        
        # Master account state management
        self.master_account_blocked = False
        self.master_block_reason = ""
        
        # Child account state management
        self.child_account_blocked = False
        self.child_block_reason = ""
        
        # Account blocking due to order rejection
        self.master_account_rejected_blocked = False
        self.child_account_rejected_blocked = False
        
        # Price feed management for dynamic orders
        self.last_known_prices = {}  # Store last known price for each symbol
        self.order_coordination_active = False
        self.coordination_timer = None
        
        # WebSocket monitoring
        self.websocket_health = {1: True, 2: True}  # Track WebSocket health
        self.websocket_last_update = {1: None, 2: None}  # Track last update time
        self.websocket_health_timer = None
        
        # Quantity variables
        self.qty1_var = tk.StringVar()
        
        # Account display variables
        self.master1_value = tk.StringVar()
        self.child_value = tk.StringVar()
        
        # Order numbers
        self.order_numbers = {
            1: '', 2: ''
        }
        self.exit_order_numbers = {
            1: '', 2: ''
        }
        
        # Quantities
        self.quantities = {
            1: '', 2: ''
        }
        
        # Current websocket subscription
        self.current_subscription = None
    
    def create_widgets(self):
        """Create GUI widgets"""
        self.create_style()
        self.create_login_buttons()
        self.create_selection_frame()
        self.create_trading_frame()
        self.create_order_buttons()
        self.create_order_status_display()
        self.create_bottom_control_panel()
    
    def create_style(self):
        """Create custom styles"""
        self.style = ttk.Style()
        self.style.configure("TButton", padding=(10, 10))
        self.style.configure("GreenButton.TButton", background="green")
        self.style.configure("RedButton.TButton", background="red")
        
        # Login button styles with borders
        self.style.configure("LoginButton.TButton", 
                           background="SystemButtonFace",
                           relief="solid",
                           borderwidth=2)
        self.style.map("LoginButton.TButton",
                      background=[('active', 'lightblue')])
        
        # Green background and border for successful login
        self.style.configure("LoginSuccess.TButton",
                           background="green",
                           relief="solid",
                           borderwidth=3,
                           font=("Arial", 10, "bold"))
        self.style.map("LoginSuccess.TButton",
                      background=[('active', 'darkgreen')])
        
        # Red border for login error
        self.style.configure("LoginError.TButton",
                           background="SystemButtonFace", 
                           relief="solid",
                           borderwidth=3)
        self.style.map("LoginError.TButton",
                      background=[('active', 'lightcoral')])
        
        # Show PnL button style
        self.style.configure("VerifyButton.TButton",
                           background="orange",
                           relief="solid",
                           borderwidth=2,
                           font=("Arial", 9, "bold"))
        self.style.map("VerifyButton.TButton",
                      background=[('active', 'darkorange')])
    
    def create_login_buttons(self):
        """Create login buttons frame with integrated PnL display"""
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Child account login buttons
        self.login_button2 = ttk.Button(
            self.login_frame, text="Login Child Account", 
            command=lambda: self.login_account(2), 
            width=30, style="LoginButton.TButton"
        )
        self.login_button2.pack(side=tk.LEFT, padx=10)
        
        # Utility buttons (reduced size)
        self.release_button = ttk.Button(
            self.login_frame, text="RELEASE", 
            command=self.release_buttons, width=12
        )
        self.release_button.pack(side=tk.LEFT, padx=5)
        
        

        # Premium Price display (reduced size)
        tk.Label(self.login_frame, text="Premium Price:").pack(side=tk.LEFT, padx=5)
        self.premium_price_box = tk.Entry(
            self.login_frame, textvariable=self.premium_price_value, 
            width=12, state='readonly', font=('Helvetica', 10, 'bold')
        )
        self.premium_price_box.pack(side=tk.LEFT, padx=5)
        
        # Compact PnL display (hidden by default)
        # Master PnL
        self.master_pnl_label = tk.Label(self.login_frame, text="M PnL:", font=('Helvetica', 9, 'bold'))
        self.master_pnl_label.pack(side=tk.LEFT, padx=5)
        self.master_pnl_box = tk.Entry(
            self.login_frame, textvariable=self.master_pnl_value, 
            width=8, state='readonly', font=('Helvetica', 9, 'bold'),
            bg='lightblue'
        )
        self.master_pnl_box.pack(side=tk.LEFT, padx=2)
        
        # Child PnL
        self.child_pnl_label = tk.Label(self.login_frame, text="C PnL:", font=('Helvetica', 9, 'bold'))
        self.child_pnl_label.pack(side=tk.LEFT, padx=5)
        self.child_pnl_box = tk.Entry(
            self.login_frame, textvariable=self.child_pnl_value, 
            width=8, state='readonly', font=('Helvetica', 9, 'bold'),
            bg='lightgreen'
        )
        self.child_pnl_box.pack(side=tk.LEFT, padx=2)
        
        # Initially clear PnL display (but keep widgets visible)
        self.master_pnl_value.set("")
        self.child_pnl_value.set("")
        
        # Show PnL button
        self.verify_pnl_button = ttk.Button(
            self.login_frame, text="Show PnL", 
            command=self.verify_pnl_from_broker,
            width=12, style="VerifyButton.TButton",
            state='normal'  # Initially enabled
        )
        self.verify_pnl_button.pack(side=tk.LEFT, padx=10)
    
    def create_selection_frame(self):
        """Create instrument selection frame"""
        self.selection_frame = tk.Frame(self.root)
        self.selection_frame.pack(side=tk.TOP, pady=10)
        
        # Index selection
        tk.Label(self.selection_frame, text="Index:").grid(row=0, column=0, padx=10)
        index_options = ["BANKNIFTY", "NIFTY", "SENSEX"]
        self.index_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_index, 
            values=index_options, width=15
        )
        self.index_dropdown.grid(row=0, column=1, padx=10)
        self.selected_index.trace_add('write', self.update_selections)
        
        # Index LTP display (next to Index dropdown)
        tk.Label(self.selection_frame, text="Index LTP:").grid(row=0, column=2, padx=10)
        self.index_ltp_label = tk.Label(
            self.selection_frame, textvariable=self.index_ltp_value,
            font=('Helvetica', 10, 'bold'), fg="blue", width=10
        )
        self.index_ltp_label.grid(row=0, column=3, padx=5)
        
        # Expiry dropdown (shifted right)
        tk.Label(self.selection_frame, text="Expiry:").grid(row=0, column=4, padx=10)
        self.expiry_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.expiry_value, 
            values=[], width=12
        )
        self.expiry_dropdown.grid(row=0, column=5, padx=10)
        self.expiry_value.trace_add('write', self.on_expiry_selected)
        
        # Option type
        tk.Label(self.selection_frame, text="Option:").grid(row=0, column=6, padx=10)
        option_types = ["CE", "PE"]
        self.option_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_option, 
            values=option_types, width=5
        )
        self.option_dropdown.grid(row=0, column=7, padx=10)
        self.selected_option.trace_add('write', self.on_option_selected)
        
        # Strike selection
        tk.Label(self.selection_frame, text="Select Strike:").grid(row=0, column=8, padx=10)
        self.strike_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_strike, 
            width=15
        )
        self.strike_dropdown.grid(row=0, column=9, padx=10)
        self.selected_strike.trace_add('write', self.on_strike_selected)
    
    def create_trading_frame(self):
        """Create trading controls frame"""
        self.trading_frame = tk.Frame(self.root)
        self.trading_frame.pack(side=tk.TOP, pady=10)
        
        
        # Quantity selection (moved to right of Master Position)
        tk.Label(self.trading_frame, text="Qty").pack(side=tk.LEFT, padx=5)
        self.qty_dropdown = ttk.Combobox(
            self.trading_frame, textvariable=self.qty1_var, width=10, state="readonly"
        )
        self.qty_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Price display (moved to right of Qty)
        tk.Label(self.trading_frame, text="Price").pack(side=tk.LEFT, padx=5)
        self.price_box = tk.Entry(
            self.trading_frame, textvariable=self.price_value, width=10
        )
        self.price_box.pack(side=tk.LEFT, padx=5)
        
        # Bind events to detect manual clearing
        self.price_box.bind('<KeyPress>', self.on_price_box_key_press)
        self.price_box.bind('<FocusIn>', self.on_price_box_focus_in)
        self.price_box.bind('<KeyRelease>', self.on_price_box_key_release)
        
        # Add trace to detect value changes
        self.price_value.trace('w', self.on_price_value_changed)
        
        # Buy button
        self.buy_button = ttk.Button(
            self.trading_frame, text="BUY", 
            command=self.place_buy_orders, width=20, style="GreenButton.TButton"
        )
        self.buy_button.pack(side=tk.LEFT, padx=10)
        
        # Exit price
        self.price1_box = tk.Entry(
            self.trading_frame, textvariable=self.price1_value, width=10
        )
        self.price1_box.pack(side=tk.LEFT, padx=5)
        
        # Sell Order button
        self.exit_button = ttk.Button(
            self.trading_frame, text="SELL Order", 
            command=self.place_exit_orders, width=20, style="RedButton.TButton",
            state="disabled"
        )
        self.exit_button.pack(side=tk.LEFT, padx=10)

    def create_order_status_display(self):
        """Create order status display frame"""
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Master account order status
        master_status_label = tk.Label(
            self.status_frame, 
            text="Master Order Status:", 
            font=('Arial', 10, 'bold'),
            fg="darkgreen"
        )
        master_status_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        self.master_status_display = tk.Label(
            self.status_frame, 
            textvariable=self.master_order_status,
            font=('Arial', 10, 'bold'),
            fg="darkred",
            bg="lightyellow",
            width=30,
            relief="sunken",
            bd=1
        )
        self.master_status_display.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        # Child account order status
        child_status_label = tk.Label(
            self.status_frame, 
            text="Child Order Status:", 
            font=('Arial', 10, 'bold'),
            fg="darkgreen"
        )
        child_status_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        
        self.child_status_display = tk.Label(
            self.status_frame, 
            textvariable=self.child_order_status,
            font=('Arial', 10, 'bold'),
            fg="darkred",
            bg="lightyellow",
            width=30,
            relief="sunken",
            bd=1
        )
        self.child_status_display.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        # Cancel order buttons below Child Order Status
        self.cancel_master_buy_button = tk.Button(
            self.status_frame, text="Cancel Master Buy Order", 
            command=self.cancel_master_buy_order, width=20, height=1,
            state="disabled"
        )
        self.cancel_master_buy_button.grid(row=2, column=0, padx=10, pady=5)
        
        self.cancel_child_buy_button = tk.Button(
            self.status_frame, text="Cancel Child Buy Order", 
            command=self.cancel_child_buy_order, width=20, height=1,
            state="disabled"
        )
        self.cancel_child_buy_button.grid(row=2, column=1, padx=10, pady=5)
        
        # SL Price and Target Price controls (next to order status)
        # SL Price box first, then button
        self.sl_price_box = tk.Entry(
            self.status_frame, textvariable=self.sl_price_value, width=10
        )
        self.sl_price_box.grid(row=0, column=2, padx=5, pady=5)
        
        self.sl_price_button = tk.Button(
            self.status_frame, text="SL Price", 
            command=self.set_sl_price, width=20, height=1
        )
        self.sl_price_button.grid(row=0, column=3, padx=10, pady=5)
        
        # SL Monitoring status label
        self.sl_monitoring_label = tk.Label(
            self.status_frame, text="", 
            font=("Arial", 8), fg="green"
        )
        self.sl_monitoring_label.grid(row=0, column=4, padx=5, pady=5)
        
        # Target Price box first, then button
        self.target_price_box = tk.Entry(
            self.status_frame, textvariable=self.target_price_value, width=10
        )
        self.target_price_box.grid(row=1, column=2, padx=5, pady=5)
        
        self.target_price_button = tk.Button(
            self.status_frame, text="Target Price", 
            command=self.set_target_price, width=20, height=1
        )
        self.target_price_button.grid(row=1, column=3, padx=10, pady=5)
        
        # Trailing Stop Loss controls (compact design)
        # Trail Type dropdown
        self.trail_type_label = tk.Label(self.status_frame, text="Trail Type:")
        self.trail_type_label.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        self.trail_type_combo = ttk.Combobox(
            self.status_frame, textvariable=self.trail_type_selected,
            values=["Point", "Percent"], state="readonly", width=8
        )
        self.trail_type_combo.grid(row=2, column=3, padx=5, pady=5)
        self.trail_type_combo.bind("<<ComboboxSelected>>", self.on_trail_type_changed)
        
        # Trail value entry
        self.trail_value_box = tk.Entry(
            self.status_frame, textvariable=self.trail_value, width=8
        )
        self.trail_value_box.grid(row=2, column=4, padx=5, pady=5)
        
        # Enable button
        self.enable_trail_button = tk.Button(
            self.status_frame, text="Enable", 
            command=self.enable_trail, width=8, height=1,
            bg="lightgreen"
        )
        self.enable_trail_button.grid(row=2, column=5, padx=5, pady=5)
        
        # Disable button
        self.disable_trail_button = tk.Button(
            self.status_frame, text="Disable", 
            command=self.disable_trail, width=8, height=1,
            bg="lightcoral", state="disabled"
        )
        self.disable_trail_button.grid(row=3, column=5, padx=5, pady=5)
        
        # Status display (compact)
        self.trail_status_label = tk.Label(
            self.status_frame, textvariable=self.trail_status_text,
            font=("Arial", 8), fg="blue"
        )
        self.trail_status_label.grid(row=3, column=2, columnspan=3, padx=5, pady=2, sticky="w")
        
        # Real-time trailing stop display
        self.trailing_stop_display_label = tk.Label(
            self.status_frame, text="",
            font=("Arial", 8), fg="red"
        )
        self.trailing_stop_display_label.grid(row=4, column=2, columnspan=3, padx=5, pady=2, sticky="w")

    def create_order_buttons(self):
        """Create order management buttons"""
        self.order_frame = tk.Frame(self.root)
        self.order_frame.pack(side=tk.TOP, pady=10)
        
        # Broker Positions button (leftmost)
        self.child_position_button = tk.Button(
            self.order_frame, text="Broker Positions", 
            command=self.show_order_book, width=15, height=2,
            state="normal"
        )
        self.child_position_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Cancel Buy and Modify Buy (left side)
        self.cancel_buy_button = tk.Button(
            self.order_frame, text="Cancel Buy", 
            command=self.cancel_buy_orders, width=15, height=2,
            state="disabled"
        )
        self.cancel_buy_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Modify Buy box first, then button
        self.modify_buy_box = tk.Entry(
            self.order_frame, textvariable=self.modify_buy_value, width=10
        )
        self.modify_buy_box.grid(row=0, column=2, padx=5, pady=5)
        
        self.modify_buy_button = tk.Button(
            self.order_frame, text="Modify Buy", 
            command=self.modify_buy_orders, width=15, height=2,
            state="disabled"
        )
        self.modify_buy_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Cancel Exit and Modify Exit (right side)
        self.cancel_exit_button = tk.Button(
            self.order_frame, text="Cancel Exit", 
            command=self.cancel_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.cancel_exit_button.grid(row=0, column=4, padx=5, pady=5)
        
        # Modify Exit box first, then button
        self.modify_exit_box = tk.Entry(
            self.order_frame, textvariable=self.modify_exit_value, width=10
        )
        self.modify_exit_box.grid(row=0, column=5, padx=5, pady=5)
        
        self.modify_exit_button = tk.Button(
            self.order_frame, text="Modify Exit", 
            command=self.modify_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.modify_exit_button.grid(row=0, column=6, padx=5, pady=5)

    def create_bottom_control_panel(self):
        """Create bottom control panel with exit and logout buttons"""
        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Exit All Orders at Market Price
        self.exit_all_button = tk.Button(
            self.bottom_frame, text="Exit All Orders at Market Price", 
            command=self.exit_all_orders_market, width=25, height=2, state='disabled'
        )
        self.exit_all_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Exit Master Order at Market Price
        self.exit_master_button = tk.Button(
            self.bottom_frame, text="Exit Master Order at Market Price", 
            command=self.exit_master_orders_market, width=25, height=2, state='disabled'
        )
        self.exit_master_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Exit Child Order at Market Price
        self.exit_child_button = tk.Button(
            self.bottom_frame, text="Exit Child Order at Market Price", 
            command=self.exit_child_orders_market, width=25, height=2, state='disabled'
        )
        self.exit_child_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Child Account Logout
        self.child_logout_button = tk.Button(
            self.bottom_frame, text="Child Account Logout", 
            command=self.logout_child_account, width=25, height=2, state='disabled'
        )
        self.child_logout_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Configuration button
        self.config_button = tk.Button(
            self.bottom_frame, text="⚙️ Config", 
            command=self.open_configuration, width=12, height=2
        )
        self.config_button.grid(row=0, column=4, padx=5, pady=5)
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        import os
        os.makedirs("logs", exist_ok=True)
    
    def setup_websocket_callbacks(self):
        """Setup websocket callbacks for live price updates and order status"""
        # Set up live price callback
        self.websocket_manager.set_live_price_callback(self.update_live_price)
        
        # Set up order status callback
        self.websocket_manager.set_order_status_callback(self.update_order_status)
        
        # Set up buy order completed callback
        self.websocket_manager.set_buy_order_completed_callback(self.on_buy_order_completed)
        
        # Set up sell order completed callback
        self.websocket_manager.set_sell_order_completed_callback(self.on_sell_order_completed)
    
    def handle_websocket_error(self, account_num: int, error_message: str):
        """Handle websocket errors and trigger reconnection"""
        try:
            logger.error(f"WebSocket error for account {account_num}: {error_message}")
            
            # Check if it's a connection lost error
            if any(keyword in error_message.lower() for keyword in ['connection lost', '502 bad gateway', 'disconnected', 'closed']):
                logger.warning(f"WebSocket connection lost for account {account_num}, triggering reconnection")
                self.websocket_manager.mark_connection_lost(account_num)
            
        except Exception as e:
            logger.error(f"Error handling websocket error: {e}")
    
    def trigger_network_failure_display(self, account_num: int):
        """Manually trigger network failure display for testing"""
        try:
            logger.info(f"Manually triggering network failure display for account {account_num}")
            self.update_order_status(account_num, "NETWORK FAIL - EXIT Manual", "NETWORK_ERROR")
        except Exception as e:
            logger.error(f"Error triggering network failure display: {e}")
    
    def test_network_failure_master(self):
        """Test network failure display for master account"""
        self.trigger_network_failure_display(1)
    
    def test_network_failure_child(self):
        """Test network failure display for child account"""
        self.trigger_network_failure_display(2)
    
    def test_connection_restore_master(self):
        """Test connection restored display for master account"""
        self.update_order_status(1, "CONNECTION RESTORED", "NETWORK_RESTORED")
    
    def test_connection_restore_child(self):
        """Test connection restored display for child account"""
        self.update_order_status(2, "CONNECTION RESTORED", "NETWORK_RESTORED")
    
    def test_websocket_error_dialog(self):
        """Test WebSocket error dialog display"""
        try:
            logger.info("Testing WebSocket error dialog")
            WebSocketErrorDialog.show_error(
                self.root,
                "WebSocket Disconnection Error",
                "WebSocket connection error detected:\n\nwebsocket run forever ended in exception, socket is already opened\n\nTime: 2025-09-26 15:21:14\nLog: app_2025-09-26.log",
                "Master Account"
            )
        except Exception as e:
            logger.error(f"Error testing WebSocket error dialog: {e}")
    
    def disable_selection_row(self):
        """Disable all components in the selection row (Index, Index LTP, Expiry, Option, Strike)"""
        try:
            logger.info("Disabling selection row components")
            
            # Disable Index dropdown
            self.index_dropdown.config(state='disabled')
            
            # Disable Expiry dropdown
            self.expiry_dropdown.config(state='disabled')
            
            # Disable Option dropdown
            self.option_dropdown.config(state='disabled')
            
            # Disable Strike dropdown
            self.strike_dropdown.config(state='disabled')
            
            # Index LTP is already read-only (Label), so no need to disable
            
            logger.info("Selection row components disabled")
            
        except Exception as e:
            logger.error(f"Error disabling selection row: {e}")
    
    def enable_selection_row(self):
        """Enable all components in the selection row (Index, Index LTP, Expiry, Option, Strike)"""
        try:
            logger.info("Enabling selection row components")
            
            # Enable Index dropdown
            self.index_dropdown.config(state='normal')
            
            # Enable Expiry dropdown
            self.expiry_dropdown.config(state='normal')
            
            # Enable Option dropdown
            self.option_dropdown.config(state='normal')
            
            # Enable Strike dropdown
            self.strike_dropdown.config(state='normal')
            
            # Index LTP is already read-only (Label), so no need to enable
            
            logger.info("Selection row components enabled")
            
        except Exception as e:
            logger.error(f"Error enabling selection row: {e}")
    
    def get_websocket_status(self, account_num: int) -> str:
        """Get websocket connection status for an account"""
        try:
            return self.websocket_manager.get_connection_status(account_num)
        except Exception as e:
            logger.error(f"Error getting websocket status: {e}")
            return "unknown"
    
    def is_websocket_connected(self, account_num: int) -> bool:
        """Check if websocket is connected for an account"""
        try:
            return self.websocket_manager.is_connected(account_num)
        except Exception as e:
            logger.error(f"Error checking websocket connection: {e}")
            return False
    
    
    def on_closing(self):
        """Handle application closing"""
        try:
            logger.info("Application closing - cleaning up resources")
            
            # Stop log monitoring
            if hasattr(self, 'log_monitor'):
                self.log_monitor.stop_monitoring()
            
            # Stop websocket connection monitoring
            self.websocket_manager.stop_connection_monitoring()
            
            # Close the window
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during application closing: {e}")
            self.root.destroy()
    
    def update_live_price(self, live_price: float):
        """Update live price display and buy price box (first time only)"""
        try:
            # Always update Premium Price box (live updates)
            self.premium_price_value.set(f"{live_price:.2f}")
            
            # Debug logging
            current_price_value = self.price_value.get().strip()
            
            # Update Buy Price box ONLY if it's empty AND not manually cleared by user
            if not current_price_value and not self.buy_price_manually_cleared:
                self.price_value.set(f"{live_price:.2f}")
                logger.info(f"Initial buy price set: {live_price:.2f}")
            elif not current_price_value and self.buy_price_manually_cleared:
                logger.info("Buy price field is empty but manually cleared - NOT auto-filling")
            # Check SL/Target breaches if monitoring is active
            self.check_sl_target_breach(live_price)
            
            # Check trailing stop updates
            self.check_trailing_stop(live_price)
            
        except Exception as e:
            logger.error(f"Error updating live price: {e}")
    
    def check_sl_target_breach(self, live_price: float):
        """Check for SL/Target breaches - from old project"""
        try:
            # Check SL breach
            if self.sl_monitoring_active and self.sl_price_level is not None:
                if live_price <= self.sl_price_level:
                    # Stop both monitoring systems immediately to prevent duplicate triggers
                    self.sl_monitoring_active = False
                    self.target_monitoring_active = False
                    logger.info(f"SL BREACH DETECTED! Current price: {live_price}, SL: {self.sl_price_level}")
                    logger.info("Both SL and Target monitoring stopped due to SL breach")
                    self._trigger_sl_breach(live_price)
                else:
                    # Log comparison info periodically (every 10th check to avoid spam)
                    if not hasattr(self, '_sl_check_counter'):
                        self._sl_check_counter = 0
                    self._sl_check_counter += 1
                    if self._sl_check_counter % 10 == 0:
                        logger.info(f"SL Monitoring - Current: {live_price}, SL Level: {self.sl_price_level}, Gap: {live_price - self.sl_price_level:.2f}")
            
            # Check Target breach
            if self.target_monitoring_active and self.target_price_level is not None:
                if live_price >= self.target_price_level:
                    # Stop both monitoring systems immediately to prevent duplicate triggers
                    self.sl_monitoring_active = False
                    self.target_monitoring_active = False
                    logger.info(f"TARGET HIT! Current price: {live_price}, Target: {self.target_price_level}")
                    logger.info("Both SL and Target monitoring stopped due to Target breach")
                    self._trigger_target_breach(live_price)
                else:
                    # Log comparison info periodically (every 10th check to avoid spam)
                    if not hasattr(self, '_target_check_counter'):
                        self._target_check_counter = 0
                    self._target_check_counter += 1
                    if self._target_check_counter % 10 == 0:
                        logger.info(f"TARGET Monitoring - Current: {live_price}, Target Level: {self.target_price_level}, Gap: {self.target_price_level - live_price:.2f}")
                    
        except Exception as e:
            logger.error(f"Error checking SL/Target breaches: {e}")
    
    def _trigger_sl_breach(self, current_price: float):
        """Handle SL breach - place exit orders - from old project"""
        try:
            logger.info(f"SL BREACH DETECTED! Current price: {current_price}, SL: {self.sl_price_level}")
            
            # Stop both monitoring systems (already stopped in check_sl_target_breach, but ensure UI is updated)
            self.stop_sl_monitoring()
            self.stop_target_monitoring()
            
            # Update UI to show breach
            self.sl_price_button.config(text=f"SL TRIGGERED @{current_price:.2f}", bg="red", fg="white")
            self.target_price_button.config(text="Target Monitoring Stopped", bg="gray", fg="white")
            
            # Place exit orders (placeholder for now)
            self._place_exit_orders_for_breach("SL", current_price)
            
            logger.info("SL breach handled - both monitoring stopped, exit orders placed")
            
        except Exception as e:
            logger.error(f"Error handling SL breach: {e}")
    
    def _trigger_target_breach(self, current_price: float):
        """Handle Target breach - start trailing if enabled, otherwise exit"""
        try:
            logger.info(f"TARGET HIT! Current price: {current_price}, Target: {self.target_price_level}")
            
            # Stop both monitoring systems (already stopped in check_sl_target_breach, but ensure UI is updated)
            self.stop_sl_monitoring()
            self.stop_target_monitoring()
            
            # Update UI to show target hit
            self.target_price_button.config(text=f"TARGET HIT @{current_price:.2f}", bg="green", fg="white")
            self.sl_price_button.config(text="SL Monitoring Stopped", bg="gray", fg="white")
            
            # Check if trailing is enabled
            if self.enable_trailing_value.get():
                # Start trailing instead of exiting
                logger.info("Trailing is enabled - starting trailing mode")
                self.start_trailing_mode(current_price)
                logger.info("Target breach handled - both monitoring stopped, trailing mode started (no exit orders)")
            else:
                # Exit immediately (both monitoring already stopped above)
                self._place_exit_orders_for_breach("TARGET", current_price)
                logger.info("Target breach handled - both monitoring stopped, exit orders placed")
            
        except Exception as e:
            logger.error(f"Error handling Target breach: {e}")
    
    def _place_exit_orders_for_breach(self, breach_type: str, current_price: float):
        """Place exit orders when SL or Target is breached - PARALLEL EXECUTION"""
        try:
            logger.info(f"Placing exit orders for {breach_type} breach at price {current_price} - PARALLEL MODE")
            
            # Refresh state to ensure we have the latest values
            self.account_state_manager._initialize_states()
            
            # Debug: Check filled quantity status for both accounts
            master_filled_qty = self.account_state_manager.get_filled_quantity(1)
            child_filled_qty = self.account_state_manager.get_filled_quantity(2)
            master_active = self.account_manager.accounts[1]['active']
            child_active = self.account_manager.accounts[2]['active']
            
            logger.info(f"SL BREACH DEBUG - Master: active={master_active}, filled_qty={master_filled_qty}")
            logger.info(f"SL BREACH DEBUG - Child: active={child_active}, filled_qty={child_filled_qty}")
            
            # Get active accounts that have positions to exit
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_filled_quantity(account_id) > 0):
                    active_accounts.append(account_id)
            
            if not active_accounts:
                logger.warning("No active accounts with positions available for breach exit orders")
                return
            
            # Use silent market exit for SL/Target breaches (now parallel)
            self.exit_all_orders_market_silent()
            
            logger.info(f"EXIT ORDERS PLACED IN PARALLEL - {breach_type} breach at {current_price} for {len(active_accounts)} account(s)")
            
            # Update UI to show exit orders placed
            if breach_type == "SL":
                self.sl_price_button.config(text=f"SL EXIT @{current_price:.2f}")
            else:
                self.target_price_button.config(text=f"TARGET EXIT @{current_price:.2f}")
            
        except Exception as e:
            logger.error(f"Error placing exit orders for {breach_type} breach: {e}")
    
    def _check_if_all_monitoring_should_stop(self):
        """Check if all monitoring should stop (when either SL or Target is triggered)"""
        try:
            # Initialize sl_target_states if it doesn't exist
            if not hasattr(self, 'sl_target_states'):
                self.sl_target_states = {}
            
            sl_triggered = self.sl_target_states.get('sl_triggered', False)
            target_triggered = self.sl_target_states.get('target_triggered', False)
            
            # If either SL or Target is triggered, stop all monitoring
            if sl_triggered or target_triggered:
                self.sl_target_states['sl_active'] = False
                self.sl_target_states['target_active'] = False
                logger.info("All SL/Target monitoring stopped - one level was breached")
                
                # Update UI to show monitoring stopped
                if not sl_triggered:
                    self.sl_price_button.config(text="SL Monitoring Stopped", bg="gray")
                if not target_triggered:
                    self.target_price_button.config(text="Target Monitoring Stopped", bg="gray")
                    
        except Exception as e:
            logger.error(f"Error checking if monitoring should stop: {e}")
    
    def update_order_status(self, account_num: int, status_message: str, trantype: str = "Unknown"):
        """Update order status display and handle order state changes"""
        try:
            # Update UI display
            if account_num == 1:
                self.master_order_status.set(status_message)
            elif account_num == 2:
                self.child_order_status.set(status_message)
            
            # Handle network failure status specially
            if status_message == "NETWORK FAIL - EXIT Manual":
                logger.warning(f"Network failure detected for account {account_num} - Manual exit required")
                # Don't process this as a normal order status update
                return
            
            # Handle connection restored status
            if status_message == "CONNECTION RESTORED":
                logger.info(f"Network connection restored for account {account_num}")
                # Don't process this as a normal order status update
                return
            
            # Extract order status from message for state tracking
            status = self._extract_order_status(status_message)
            if status:
                self._on_order_status_update(account_num, status, trantype)
            
            logger.info(f"Order status updated for account {account_num}: {status_message}")
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
    
    def _extract_order_status(self, status_message: str) -> str:
        """Extract order status from status message"""
        try:
            status_message = status_message.upper()
            
            if "COMPLETE" in status_message:
                return "COMPLETE"
            elif "REJECTED" in status_message:
                return "REJECTED"
            elif "OPEN" in status_message:
                return "OPEN"
            elif "CANCELLED" in status_message:
                return "CANCELLED"
            elif "PENDING" in status_message:
                return "PENDING"
            else:
                return None
        except Exception as e:
            logger.error(f"Error extracting order status from '{status_message}': {e}")
            return None
    
    
    def on_sell_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle sell order completion"""
        try:
            logger.info(f"Sell order completed for account {account_num}: {symbol} @ {price}")
            # Additional logic can be added here for sell order completion
        except Exception as e:
            logger.error(f"Error handling sell order completion: {e}")
    
    def on_price_box_key_press(self, event):
        """Handle key press in price box to detect manual clearing"""
        try:
            # Store current value before key press
            self.previous_price_value = self.price_value.get()
            
            # Check if user is deleting/clearing content
            if event.keysym in ['BackSpace', 'Delete'] or event.char in ['\x08', '\x7f']:  # Backspace, Delete
                # Check if the field will be empty after this key press
                current_text = self.price_value.get()
                if len(current_text) <= 1:  # Will be empty or almost empty
                    self.buy_price_manually_cleared = True
                    logger.info("Buy price field manually cleared by user - auto-fill disabled")
        except Exception as e:
            logger.error(f"Error handling price box key press: {e}")
    
    def on_price_box_key_release(self, event):
        """Handle key release in price box"""
        try:
            # Check if user is actively editing (not just clicking)
            if event.keysym in ['BackSpace', 'Delete'] or event.char in ['\x08', '\x7f']:
                current_text = self.price_value.get()
                if len(current_text) == 0:  # Field is now empty
                    self.buy_price_manually_cleared = True
                    logger.info("Buy price field cleared by user - auto-fill disabled")
        except Exception as e:
            logger.error(f"Error handling price box key release: {e}")
    
    def on_price_value_changed(self, *args):
        """Handle price value changes via trace"""
        try:
            current_value = self.price_value.get()
            
            # If value changed from non-empty to empty, user manually cleared it
            if self.previous_price_value and not current_value:
                self.buy_price_manually_cleared = True
                logger.info("Buy price field value changed to empty - auto-fill disabled")
            
            # Update previous value
            self.previous_price_value = current_value
            
        except Exception as e:
            logger.error(f"Error handling price value change: {e}")
    
    def on_price_box_focus_in(self, event):
        """Handle focus in on price box"""
        try:
            # Store current value when focusing
            self.previous_price_value = self.price_value.get()
            logger.info(f"User focused on price box - current value: '{self.previous_price_value}'")
        except Exception as e:
            logger.error(f"Error handling price box focus in: {e}")
        
    # ===== BLANK FUNCTIONS - TO BE IMPLEMENTED =====
    
    def auto_login_master(self):
        """Auto-login master account on startup"""
        def login_thread():
            try:
                logger.info("Attempting auto-login for master account...")
                success, client_name = self.account_manager.login_account(1)
                
                if success:
                    # Update account state
                    self.account_state_manager.update_login_status(1, 1, "Master account auto-login successful")
                    self.account_state_manager.update_can_order(1, 1, "Master account ready for orders")
                    
                    # Connect websocket feed for master account
                    self.websocket_manager.connect_feed(1)
                    
                    # Refresh market data after successful login
                    self.refresh_market_data()
                    
                    # Update UI
                    self.root.after(0, self.update_master_login_ui, True, client_name)
                    logger.info(f"Master account auto-login successful: {client_name}")
                    
                else:
                    # Update UI to show login failed
                    self.root.after(0, self.update_master_login_ui, False, "Login Failed")
                    logger.error("Master account auto-login failed")
                    
            except Exception as e:
                logger.error(f"Error during master auto-login: {e}")
                self.root.after(0, self.update_master_login_ui, False, f"Error: {str(e)}")
        
        # Run login in separate thread to avoid blocking UI
        threading.Thread(target=login_thread, daemon=True).start()
    
    def update_master_login_ui(self, success, client_name):
        """Update UI after master login attempt"""
        if success:
            self.master_account_name.set(client_name)
            self.root.title(f"***Kratik's Soft*** - Master Account: {client_name}")
            self.master_order_status.set(f"{client_name} - Order Ready")
            # Update login button style
            self.login_button2.config(style="LoginButton.TButton")
        else:
            self.master_account_name.set("Login Failed")
            self.master_order_status.set(f"Master Login Failed: {client_name}")
            # Show error popup
            messagebox.showerror("Login Error", f"Master account login failed: {client_name}")
    
    def login_account(self, account_num):
        """Login to account"""
        if account_num == 1:
            # Master account - already handled by auto-login
            messagebox.showinfo("Info", "Master account login is automatic on startup")
            return
        
        # Child account login
        def login_thread():
            try:
                logger.info(f"Attempting login for child account {account_num}...")
                
                # Try login with retry mechanism
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Login attempt {attempt + 1}/{max_retries} for child account {account_num}")
                        success, client_name = self.account_manager.login_account(account_num)
                        
                        if success:
                            # Update account state
                            self.account_state_manager.update_login_status(account_num, 1, f"Child account {account_num} login successful")
                            self.account_state_manager.update_can_order(account_num, 1, f"Child account {account_num} ready for orders")
                            
                            # Connect websocket feed for child account
                            self.websocket_manager.connect_feed(account_num)
                            
                            # Update UI
                            self.root.after(0, self.update_child_login_ui, True, client_name)
                            logger.info(f"Child account login successful: {client_name}")
                            
                            return  # Success, exit retry loop
                        else:
                            logger.warning(f"Login attempt {attempt + 1} failed: {client_name}")
                            if attempt < max_retries - 1:
                                import time
                                time.sleep(2)  # Wait 2 seconds before retry
                            
                    except Exception as e:
                        logger.error(f"Login attempt {attempt + 1} error: {e}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2)  # Wait 2 seconds before retry
                
                # All retries failed
                self.root.after(0, self.update_child_login_ui, False, "Login Failed - All retries exhausted")
                logger.error(f"Child account login failed after {max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Error during child login: {e}")
                self.root.after(0, self.update_child_login_ui, False, f"Error: {str(e)}")
        
        # Run login in separate thread to avoid blocking UI
        threading.Thread(target=login_thread, daemon=True).start()
    
    def update_child_login_ui(self, success, client_name):
        """Update UI after child login attempt"""
        if success:
            self.child_order_status.set(f"{client_name} - Order Ready")
            # Update login button style
            self.login_button2.config(style="LoginSuccess.TButton", text=f"Child: {client_name}")
        else:
            self.child_order_status.set(f"Child Login Failed: {client_name}")
            # Show error popup
            messagebox.showerror("Login Error", f"Child account login failed: {client_name}")
            # Update login button style
            self.login_button2.config(style="LoginError.TButton", text="Login Child Account")
    
    def refresh_market_data(self):
        """Refresh index prices and expiry dates"""
        def refresh_thread():
            try:
                logger.info("Refreshing market data...")
                
                # Get master account API
                api = self.account_manager.get_api(1)
                if not api:
                    logger.warning("No API available for market data refresh")
                    return
                
                # Refresh index prices if needed
                if self.index_manager.should_refresh_prices():
                    logger.info("Refreshing index prices...")
                    self.index_manager.fetch_index_prices(api)
                else:
                    logger.info("Index prices are current, no refresh needed")
                
                # Refresh expiry dates if needed
                if self.expiry_manager.should_refresh_expiry():
                    logger.info("Refreshing expiry dates...")
                    self.expiry_manager.calculate_expiry_dates()
                else:
                    logger.info("Expiry dates are current, no refresh needed")
                
                # Update UI with current data
                self.root.after(0, self.update_market_data_ui)
                
            except Exception as e:
                logger.error(f"Error refreshing market data: {e}")
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def update_market_data_ui(self):
        """Update UI with current market data"""
        try:
            # Update index LTP display
            selected_index = self.selected_index.get()
            if selected_index:
                current_price = self.index_manager.get_index_price(selected_index)
                if current_price > 0:
                    self.index_ltp_value.set(f"{current_price:.2f}")
                else:
                    self.index_ltp_value.set("--")
            
            # Update expiry dropdown
            self.update_expiry_dropdown()
            
        except Exception as e:
            logger.error(f"Error updating market data UI: {e}")
    
    def update_expiry_dropdown(self):
        """Update expiry dropdown with current data"""
        try:
            selected_index = self.selected_index.get()
            if selected_index:
                expiry_list = self.expiry_manager.get_expiry_list(selected_index)
                self.expiry_dropdown['values'] = expiry_list
                if expiry_list:
                    self.expiry_value.set(expiry_list[0])  # Set first expiry as default
        except Exception as e:
            logger.error(f"Error updating expiry dropdown: {e}")
        
    def has_open_orders_or_monitoring(self):
        """Check if there are open buy orders or active SL/Target monitoring"""
        try:
            # Check for open buy orders
            master_has_open = self.order_states.get(1) == "OPEN"
            child_has_open = self.order_states.get(2) == "OPEN"
            
            # Check for active monitoring
            sl_monitoring = self.sl_monitoring_active
            target_monitoring = self.target_monitoring_active
            
            # Check if any monitoring is active in the states
            sl_active_in_states = self.sl_target_states.get('sl_active', False)
            target_active_in_states = self.sl_target_states.get('target_active', False)
            
            has_open_orders = master_has_open or child_has_open
            has_active_monitoring = sl_monitoring or target_monitoring or sl_active_in_states or target_active_in_states
            
            logger.info(f"Open orders check - Master: {master_has_open}, Child: {child_has_open}")
            logger.info(f"Monitoring check - SL: {sl_monitoring}, Target: {target_monitoring}, States SL: {sl_active_in_states}, States Target: {target_active_in_states}")
            
            return has_open_orders or has_active_monitoring
            
        except Exception as e:
            logger.error(f"Error checking open orders or monitoring: {e}")
            return False  # If we can't determine, assume safe to release

    def set_buy_price_box_state(self, state):
        """Control the buy price box state (disabled/normal)"""
        try:
            if state == "disabled":
                self.price_box.config(state="disabled", bg="lightgray")
                logger.info("Buy price box disabled")
            elif state == "normal":
                self.price_box.config(state="normal", bg="white")
                logger.info("Buy price box enabled")
            else:
                logger.warning(f"Invalid state for buy price box: {state}")
        except Exception as e:
            logger.error(f"Error setting buy price box state: {e}")
        
    def release_buttons(self):
        """Release button states - enable buy and sell order buttons"""
        try:
            # Check if there are open orders or active monitoring
            if self.has_open_orders_or_monitoring():
                messagebox.showwarning(
                    "Cannot Release", 
                    "Close Open Orders first!\n\nPlease cancel any open buy orders and stop SL/Target monitoring before releasing the system."
                )
                return
            
            logger.info("Release buttons clicked - resetting system for new orders")
            
            # 1. Reset account states - clear trading blocks while preserving login status
            self._reset_account_states()
            
            # 2. Clear order information for both accounts
            self._clear_order_information()
            
            # 3. Reset UI state - enable buttons and clear form fields
            self._reset_ui_state()
            
            # 4. Update order status displays
            self._update_order_status_displays()
            
            # 5. Stop any active monitoring
            self._stop_monitoring()
            
            # 6. Re-enable selection row components
            self.enable_selection_row()
            
            # 7. Update PnL button state (enable when no positions)
            self.update_verify_pnl_button_state()
            
            logger.info("System released - ready for new orders")
            messagebox.showinfo("System Released", "System has been reset and is ready for new orders")
            
        except Exception as e:
            logger.error(f"Error releasing buttons: {e}")
            messagebox.showerror("Error", f"Failed to release system: {str(e)}")
    
    def _reset_account_states(self):
        """Reset account states - clear trading blocks while preserving login status"""
        try:
            # Check actual login status for each account
            master_logged_in = self.account_manager.accounts.get(1, {}).get('active', False)
            child_logged_in = self.account_manager.accounts.get(2, {}).get('active', False)
            
            logger.info(f"Login status check - Master: {master_logged_in}, Child: {child_logged_in}")
            
            # Reset Master account - update login status and reset can_order to 1
            if master_logged_in:
                self.account_state_manager.update_login_status(1, 1, 'Master account logged in')
                self.account_state_manager.update_can_order(1, 1, 'Master account reset after trading block')
                logger.info("Master account reset to ready (was logged in)")
            else:
                self.account_state_manager.update_login_status(1, 0, 'Master not logged in')
                self.account_state_manager.update_can_order(1, 1, 'Master account reset after trading block')
                logger.info("Master account set to not logged in but can_order ready")
            
            # Reset Child account - update login status and reset can_order to 1
            if child_logged_in:
                self.account_state_manager.update_login_status(2, 1, 'Child account logged in')
                self.account_state_manager.update_can_order(2, 1, 'Child account reset after trading block')
                logger.info("Child account reset to ready (was logged in)")
            else:
                self.account_state_manager.update_login_status(2, 0, 'Child not logged in')
                self.account_state_manager.update_can_order(2, 1, 'Child account reset after trading block')
                logger.info("Child account set to not logged in but can_order ready")
            
            logger.info("Trading blocks reset while preserving login status")
            
        except Exception as e:
            logger.error(f"Error resetting account states: {e}")
            raise
    
    def _clear_order_information(self):
        """Clear order information for both accounts"""
        try:
            # Reset position data for Master account (includes filled_quantity)
            self.account_state_manager.reset_position_data(1)
            self.account_state_manager.clear_exit_order_info(1)
            logger.info("Position data and exit order info cleared for Master account")
            
            # Reset position data for Child account (includes filled_quantity)
            self.account_state_manager.reset_position_data(2)
            self.account_state_manager.clear_exit_order_info(2)
            logger.info("Position data and exit order info cleared for Child account")
            
        except Exception as e:
            logger.error(f"Error clearing order information: {e}")
            raise
    
    def _reset_ui_state(self):
        """Reset UI state - enable buttons and clear form fields"""
        try:
            # Enable buy button
            self.buy_button.config(state='normal', text="BUY")
            
            # Re-enable price box for new orders
            self.set_buy_price_box_state("normal")
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            # Reset manual clear flag for new orders
            self.buy_price_manually_cleared = False
            self.previous_price_value = ""
            logger.info("BUY button and Price box re-enabled for new orders - auto-fill re-enabled")
            
            # Disable buy-related buttons until new buy orders are placed
            self.cancel_buy_button.config(state='disabled', text="Cancel Buy")
            self.modify_buy_button.config(state='disabled', text="Modify Buy")
            self.cancel_master_buy_button.config(state='disabled', text="Cancel Master Buy Order")
            self.cancel_child_buy_button.config(state='disabled', text="Cancel Child Buy Order")
            
            # Disable exit-related buttons until new orders are placed
            self.exit_button.config(state='disabled', text="SELL Order")
            self.cancel_exit_button.config(state='disabled', text="Cancel Exit")
            self.modify_exit_button.config(state='disabled', text="Modify Exit")
            
            # Reset SL/Target controls
            self._reset_sl_target_controls()
            
            # Re-enable selection row components
            self.enable_selection_row()
            
            logger.info("Management buttons disabled until new orders are placed")
            
        except Exception as e:
            logger.error(f"Error resetting UI state: {e}")
            raise
    
    def _reset_sl_target_controls(self):
        """Reset SL/Target controls to initial state"""
        try:
            # Initialize sl_target_states if it doesn't exist
            if not hasattr(self, 'sl_target_states'):
                self.sl_target_states = {}
            
            # Reset state variables
            self.sl_target_states.update({
                'sl_calculated': False,
                'target_calculated': False,
                'sl_active': False,
                'target_active': False,
                'sl_triggered': False,
                'target_triggered': False,
                'sl_price': None,
                'target_price': None,
                'sl_points': 0,
                'target_points': 0,
                'buy_price': None
            })
            
            # Clear UI display
            self.sl_price_value.set("")
            self.target_price_value.set("")
            
            # Enable controls for new input
            self.sl_price_box.config(state="normal")
            self.target_price_box.config(state="normal")
            self.sl_price_button.config(state="normal", text="SL Price")
            self.target_price_button.config(state="normal", text="Target Price")
            self.sl_monitoring_label.config(text="", fg="green")
            
            # Reset trailing controls
            self._reset_trailing_controls()
            
            logger.info("SL/Target controls reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting SL/Target controls: {e}")
    
    def _reset_trailing_controls(self):
        """Reset trailing controls to initial state"""
        try:
            # Stop any active trailing monitoring
            self.stop_trailing_monitoring()
            
            # Reset trailing variables
            self.trailing_active = False
            self.trailing_start_price = None
            self.trailing_high_price = None
            self.trailing_stop_price = None
            
            # Reset trailing UI controls
            self.enable_trailing_value.set(False)
            self.trail_value.set("")
            self.trail_type_selected.set("")
            self.trail_status_text.set("Trailing Disabled")
            
            # Reset button states
            self.update_trail_button_states()
            
            # Clear trailing stop display
            self.trailing_stop_display_label.config(text="")
            
            logger.info("Trailing controls reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting trailing controls: {e}")
    
    def _update_order_status_displays(self):
        """Update order status displays based on account states"""
        try:
            # Update Master order status
            master_status = self.account_state_manager.get_account_status(1)
            if master_status and master_status.get('login_status') == 1:
                # Get client name from account manager
                master_client_name = self.account_manager.accounts[1].get('client_name', 'Master')
                self.master_order_status.set(f"{master_client_name} ready for orders")
            else:
                self.master_order_status.set("Master Not Logged In")
            
            # Update Child order status
            child_status = self.account_state_manager.get_account_status(2)
            if child_status and child_status.get('login_status') == 1:
                # Get client name from account manager
                child_client_name = self.account_manager.accounts[2].get('client_name', 'Child')
                self.child_order_status.set(f"{child_client_name} ready for orders")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            logger.info("Order status displays updated with client names")
            
        except Exception as e:
            logger.error(f"Error updating order status displays: {e}")
            raise
    
    def _stop_monitoring(self):
        """Stop any active monitoring"""
        try:
            # Reset order states
            self.order_states = {1: "PENDING", 2: "PENDING"}
            
            # Clear any timeout timers
            if hasattr(self, 'timeout_timer') and self.timeout_timer:
                self.timeout_timer.cancel()
                self.timeout_timer = None
            
            # Stop SL/Target monitoring
            if hasattr(self, 'sl_monitoring_active') and self.sl_monitoring_active:
                self.stop_sl_monitoring()
            if hasattr(self, 'target_monitoring_active') and self.target_monitoring_active:
                self.stop_target_monitoring()
            
            # Stop trailing monitoring
            if hasattr(self, 'trailing_active') and self.trailing_active:
                self.stop_trailing_monitoring()
            
            logger.info("Monitoring stopped and timers cleared")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            raise
        
    def verify_pnl_from_broker(self):
        """Verify PnL by fetching actual data from broker and show for 1 second"""
        try:
            logger.info("Verifying PnL from broker...")
            
            # Show PnL display
            self.show_pnl_display()
            
            pnl_found = False
            for account_num in [1, 2]:  # Master and child accounts
                account = self.account_manager.accounts.get(account_num, {})
                # Verify if account is active or blocked (both can show PnL)
                if account.get('active', False) or account.get('blocked', False):
                    api = self.account_manager.get_api(account_num)
                    if api:
                        # Get actual PnL from broker
                        broker_pnl = self.calculate_pnl(api)
                        
                        # Update PnL display
                        self.update_pnl_display(account_num, broker_pnl)
                        pnl_found = True
                        
                        status = "blocked" if account.get('blocked', False) else "active"
                        logger.info(f"Verified PnL for account {account_num} ({status}): {broker_pnl}")
            
            if not pnl_found:
                logger.warning("No active or blocked accounts found for PnL verification")
                # Set empty values to show that button was pressed
                self.master_pnl_value.set("No Data")
                self.child_pnl_value.set("No Data")
            
            # Log verification complete
            logger.info("PnL verification completed successfully")
            
            # Schedule hiding PnL display after 1 second
            self.root.after(1000, self.hide_pnl_display)
            
        except Exception as e:
            logger.error(f"Error verifying PnL from broker: {e}")
            # Show error in PnL display
            self.master_pnl_value.set("Error")
            self.child_pnl_value.set("Error")
            self.root.after(1000, self.hide_pnl_display)
    
    def calculate_pnl(self, api):
        """Calculate PnL for a given API account using positions"""
        try:
            ret = api.get_positions()
            if ret is None or not ret:
                return 0.0
            
            mtm = 0
            pnl = 0
            for i in ret:
                mtm += float(i.get('urmtom', 0))
                pnl += float(i.get('rpnl', 0))
            
            day_m2m = mtm + pnl
            return round(day_m2m, 2)
            
        except Exception as e:
            logger.error(f"Error calculating PnL: {e}")
            return 0.0
    
    def update_pnl_display(self, account_num, pnl_value):
        """Update PnL display for specific account"""
        try:
            if account_num == 1:  # Master account
                self.master_pnl_value.set(f"{pnl_value}")
            elif account_num == 2:  # Child account
                self.child_pnl_value.set(f"{pnl_value}")
        except Exception as e:
            logger.error(f"Error updating PnL display: {e}")
    
    def show_pnl_display(self):
        """Show PnL display (widgets are always visible, just ensure values are set)"""
        try:
            # Widgets are always visible, this method just ensures they're ready
            logger.debug("PnL display ready to show values")
        except Exception as e:
            logger.error(f"Error preparing PnL display: {e}")
    
    def hide_pnl_display(self):
        """Clear PnL display values"""
        try:
            self.master_pnl_value.set("")
            self.child_pnl_value.set("")
            logger.debug("PnL display values cleared")
        except Exception as e:
            logger.error(f"Error clearing PnL display: {e}")
    
    def update_verify_pnl_button_state(self):
        """Update Show PnL button state based on active positions"""
        try:
            # Check if any account has an active position (filled quantity > 0)
            has_active_position = any(
                self.account_state_manager.get_filled_quantity(account_num) > 0
                for account_num in [1, 2]
            )
            
            # Disable button if any position is active, enable otherwise
            if has_active_position:
                self.verify_pnl_button.config(state='disabled')
                logger.debug("Show PnL button disabled - active position detected")
            else:
                self.verify_pnl_button.config(state='normal')
                logger.debug("Show PnL button enabled - no active positions")
                
        except Exception as e:
            logger.error(f"Error updating Show PnL button state: {e}")
    
    def process_trade_book_data(self, trade_book_data):
        """Process trade book data and group transactions by symbol"""
        try:
            symbol_groups = {}
            
            for trade in trade_book_data:
                symbol = trade.get('tsym', 'Unknown')
                trantype = trade.get('trantype', 'Unknown')
                
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = {'buy': [], 'sell': []}
                
                if trantype == 'B':  # Buy
                    symbol_groups[symbol]['buy'].append(trade)
                elif trantype == 'S':  # Sell
                    symbol_groups[symbol]['sell'].append(trade)
            
            logger.info(f"Processed trade book data: {len(symbol_groups)} symbols found")
            return symbol_groups
            
        except Exception as e:
            logger.error(f"Error processing trade book data: {e}")
            return {}
    
    def calculate_net_position(self, symbol_transactions):
        """Calculate net position for a symbol"""
        try:
            buy_qty = sum(int(trade.get('flqty', 0)) for trade in symbol_transactions.get('buy', []))
            sell_qty = sum(int(trade.get('flqty', 0)) for trade in symbol_transactions.get('sell', []))
            
            net_qty = buy_qty - sell_qty
            
            # Calculate average buy price
            avg_buy_price = 0.0
            if symbol_transactions.get('buy'):
                total_buy_value = sum(float(trade.get('flprc', 0)) * int(trade.get('flqty', 0)) for trade in symbol_transactions['buy'])
                avg_buy_price = total_buy_value / buy_qty if buy_qty > 0 else 0.0
            
            return {
                'net_qty': net_qty,
                'buy_qty': buy_qty,
                'sell_qty': sell_qty,
                'avg_buy_price': avg_buy_price,
                'is_open': net_qty > 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating net position: {e}")
            return {'net_qty': 0, 'buy_qty': 0, 'sell_qty': 0, 'avg_buy_price': 0.0, 'is_open': False}
    
    def exit_position(self, symbol, qty):
        """Exit position by placing market sell order"""
        try:
            logger.info(f"Exit position called for {symbol} with quantity {qty}")
            
            # Get the broker position window as parent
            broker_window = self._get_broker_position_window()
            
            # Show confirmation popup
            result = CenteredConfirmationDialog.askyesno(
                broker_window,
                "Confirm Exit Position", 
                f"Are you sure you want to EXIT this position?\n\n"
                f"Symbol: {symbol}\n"
                f"Quantity: {qty}\n\n"
                f"This will place a MARKET SELL order to close the position.",
                icon='question'
            )
            
            if result:
                # Find which account has this position
                account_id = self._find_account_for_position(symbol, qty)
                
                if account_id:
                    # Get API for the account
                    api = self.account_manager.get_api(account_id)
                    account_name = "Master" if account_id == 1 else "Child"
                    
                    if api:
                        # Place market sell order to exit position
                        success = self._place_exit_order(api, symbol, int(qty), account_name)
                        
                        if success:
                            logger.info(f"Successfully placed exit order for {account_name}: {symbol} qty {qty}")
                            messagebox.showinfo("Position Exited", f"Market sell order for {symbol} (Qty: {qty}) has been placed successfully", parent=broker_window)
                            
                            # Refresh the broker position window
                            self.populate_trade_book_sections()
                        else:
                            logger.error(f"Failed to place exit order for {account_name}: {symbol}")
                            messagebox.showerror("Exit Failed", f"Failed to place exit order for {symbol}. Please try again.", parent=broker_window)
                    else:
                        logger.error(f"API not available for {account_name} account")
                        messagebox.showerror("Error", f"API not available for {account_name} account", parent=broker_window)
                else:
                    logger.error(f"Could not find account for position {symbol}")
                    messagebox.showerror("Error", f"Could not find account for position {symbol}", parent=broker_window)
            else:
                logger.info(f"Exit position cancelled for {symbol}")
                
        except Exception as e:
            logger.error(f"Error in exit position: {e}")
            broker_window = self._get_broker_position_window()
            messagebox.showerror("Error", f"Failed to exit position: {str(e)}", parent=broker_window)
    
    def _find_account_for_position(self, symbol, qty):
        """Find which account (1 or 2) has the given position"""
        try:
            # Check both accounts for the position
            for account_num in [1, 2]:
                success, trade_book_data, message = self.account_manager.get_trade_book(account_num)
                if success and trade_book_data:
                    symbol_groups = self.process_trade_book_data(trade_book_data)
                    if symbol in symbol_groups:
                        position_info = self.calculate_net_position(symbol_groups[symbol])
                        if position_info['is_open'] and position_info['net_qty'] == int(qty):
                            return account_num
            return None
        except Exception as e:
            logger.error(f"Error finding account for position {symbol}: {e}")
            return None
    
    def _place_exit_order(self, api, symbol, quantity, account_name):
        """Place market sell order to exit position"""
        try:
            logger.info(f"Placing market sell order for {account_name}: {symbol} qty {quantity}")
            
            # Determine exchange and product type based on symbol
            if 'SENSEX' in symbol:
                exchange = 'BFO'
                product_type = 'M'
            else:
                exchange = 'NFO'
                product_type = 'I'
            
            # Place market sell order
            result = api.place_order(
                buy_or_sell='S',
                product_type=product_type,
                exchange=exchange,
                tradingsymbol=symbol,
                quantity=str(quantity),
                discloseqty=0,
                price_type='MKT',
                price='0',
                trigger_price='0',
                retention='DAY',
                amo='NO',
                remarks=f'exit_position_{symbol}'
            )
            
            if result and 'norenordno' in result:
                order_id = result['norenordno']
                logger.info(f"Exit order placed successfully for {account_name}: Order ID {order_id}")
                return True
            else:
                logger.error(f"Failed to place exit order for {account_name}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error placing exit order for {account_name}: {e}")
            return False
    
    def cancel_order(self, order_id, symbol, qty, price):
        """Cancel open buy order"""
        try:
            logger.info(f"Cancel order called for Order ID: {order_id}, Symbol: {symbol}")
            
            # Get the broker position window as parent
            broker_window = self._get_broker_position_window()
            
            # Show confirmation popup
            result = CenteredConfirmationDialog.askyesno(
                broker_window,
                "Confirm Cancel Order", 
                f"Are you sure you want to CANCEL this order?\n\n"
                f"Order ID: {order_id}\n"
                f"Symbol: {symbol}\n"
                f"Quantity: {qty}\n"
                f"Price: {price}\n\n"
                f"This will cancel the pending buy order.",
                icon='question'
            )
            
            if result:
                # Find which account this order belongs to
                account_id = self._find_account_for_order(order_id)
                
                if account_id:
                    # Get API for the account
                    api = self.account_manager.get_api(account_id)
                    account_name = "Master" if account_id == 1 else "Child"
                    
                    if api:
                        # Cancel the order using API
                        cancel_response = api.cancel_order(orderno=order_id)
                        
                        if cancel_response and cancel_response.get('stat') == 'Ok':
                            logger.info(f"Successfully cancelled {account_name} order: {order_id}")
                            messagebox.showinfo("Order Cancelled", f"Order {order_id} for {symbol} has been cancelled successfully")
                            
                            # Refresh the broker position window
                            self.populate_trade_book_sections()
                        else:
                            logger.error(f"Failed to cancel {account_name} order {order_id}: {cancel_response}")
                            messagebox.showerror("Cancel Failed", f"Failed to cancel order {order_id}. Please try again.")
                    else:
                        logger.error(f"API not available for {account_name} account")
                        messagebox.showerror("Error", f"API not available for {account_name} account")
                else:
                    logger.error(f"Could not find account for order {order_id}")
                    messagebox.showerror("Error", f"Could not find account for order {order_id}")
            else:
                logger.info(f"Cancel order cancelled for Order ID: {order_id}")
                
        except Exception as e:
            logger.error(f"Error in cancel order: {e}")
            messagebox.showerror("Error", f"Failed to cancel order: {str(e)}")
    
    def _find_account_for_order(self, order_id):
        """Find which account (1 or 2) contains the given order ID"""
        try:
            # Check both accounts for the order
            for account_num in [1, 2]:
                success, order_book_data, message = self.account_manager.get_order_book(account_num)
                if success and order_book_data:
                    for order in order_book_data:
                        if order.get('norenordno') == order_id:
                            return account_num
            return None
        except Exception as e:
            logger.error(f"Error finding account for order {order_id}: {e}")
            return None
    
    def _get_broker_position_window(self):
        """Get the broker position window reference if it exists"""
        try:
            if hasattr(self, 'broker_position_window') and self.broker_position_window.winfo_exists():
                return self.broker_position_window
            return None
        except:
            return None
    
    def show_broker_position_info(self):
        """Show broker position information"""
        try:
            logger.info("Broker Positions button clicked - showing broker position information")
            
            account_num = 2
            filled_qty = self.account_state_manager.get_filled_quantity(account_num)
            account_status = self.account_state_manager.get_account_status(account_num)
            
            if filled_qty > 0:
                symbol = account_status.get('current_symbol', 'Unknown') if account_status else 'Unknown'
                price = account_status.get('current_price', 0.0) if account_status else 0.0
                position_text = f"Broker Position:\n{filled_qty} lots of {symbol} @ {price}"
            else:
                position_text = "Broker Position:\nNo position"
            
            messagebox.showinfo("Broker Positions", position_text)
            
        except Exception as e:
            logger.error(f"Error showing broker position information: {e}")
            messagebox.showerror("Error", f"Failed to retrieve broker position information: {str(e)}")
    
    def show_order_book(self):
        """Show trade book in a new window with Open Positions and Trade History sections"""
        try:
            logger.info("Trade Book button clicked - showing trade book")
            
            # Create new window
            self.broker_position_window = tk.Toplevel(self.root)
            self.broker_position_window.title("Trade Book & Position Status - Master & Child")
            self.broker_position_window.geometry("900x600")
            self.broker_position_window.resizable(True, True)
            
            # Position window at top left of screen
            self.broker_position_window.update_idletasks()
            width = self.broker_position_window.winfo_width()
            height = self.broker_position_window.winfo_height()
            x = 50  # 50 pixels from left edge
            y = 50  # 50 pixels from top edge
            self.broker_position_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Create main frame
            main_frame = tk.Frame(self.broker_position_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create Open Positions section
            positions_frame = tk.LabelFrame(main_frame, text="Open Positions (Exit Required)", font=("Arial", 12, "bold"))
            positions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create Treeview for Open Positions
            positions_columns = ('Account', 'Symbol', 'Net Qty', 'Avg Buy Price', 'Current Price', 'PnL', 'Action')
            self.positions_tree = ttk.Treeview(positions_frame, columns=positions_columns, show='headings', height=4)
            
            # Define column headings and widths for Positions
            for col in positions_columns:
                self.positions_tree.heading(col, text=col)
            
            self.positions_tree.column('Account', width=80)
            self.positions_tree.column('Symbol', width=200)
            self.positions_tree.column('Net Qty', width=80)
            self.positions_tree.column('Avg Buy Price', width=100)
            self.positions_tree.column('Current Price', width=100)
            self.positions_tree.column('PnL', width=100)
            self.positions_tree.column('Action', width=100)
            
            # Add scrollbar for Positions
            positions_scrollbar = ttk.Scrollbar(positions_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
            self.positions_tree.configure(yscrollcommand=positions_scrollbar.set)
            
            # Pack Positions tree and scrollbar
            self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            positions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create separator
            separator1 = tk.Frame(main_frame, height=2, bg="gray")
            separator1.pack(fill=tk.X, padx=10, pady=5)
            
            # Create Open Orders section
            orders_frame = tk.LabelFrame(main_frame, text="Open Orders (Cancel Required)", font=("Arial", 12, "bold"))
            orders_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create Treeview for Open Orders
            orders_columns = ('Account', 'Order ID', 'Symbol', 'Qty', 'Price', 'Type', 'Time', 'Action')
            self.orders_tree = ttk.Treeview(orders_frame, columns=orders_columns, show='headings', height=4)
            
            # Define column headings and widths for Orders
            for col in orders_columns:
                self.orders_tree.heading(col, text=col)
            
            self.orders_tree.column('Account', width=80)
            self.orders_tree.column('Order ID', width=120)
            self.orders_tree.column('Symbol', width=200)
            self.orders_tree.column('Qty', width=80)
            self.orders_tree.column('Price', width=100)
            self.orders_tree.column('Type', width=60)
            self.orders_tree.column('Time', width=120)
            self.orders_tree.column('Action', width=100)
            
            # Add scrollbar for Orders
            orders_scrollbar = ttk.Scrollbar(orders_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
            self.orders_tree.configure(yscrollcommand=orders_scrollbar.set)
            
            # Pack Orders tree and scrollbar
            self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create separator
            separator2 = tk.Frame(main_frame, height=2, bg="gray")
            separator2.pack(fill=tk.X, padx=10, pady=5)
            
            # Create Trade History section
            history_frame = tk.LabelFrame(main_frame, text="Trade History", font=("Arial", 12, "bold"))
            history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create Treeview for Trade History
            history_columns = ('Account', 'Symbol', 'Type', 'Qty', 'Fill Price', 'Fill Time', 'Status')
            self.history_tree = ttk.Treeview(history_frame, columns=history_columns, show='headings', height=6)
            
            # Define column headings and widths for History
            for col in history_columns:
                self.history_tree.heading(col, text=col)
            
            self.history_tree.column('Account', width=80)
            self.history_tree.column('Symbol', width=200)
            self.history_tree.column('Type', width=60)
            self.history_tree.column('Qty', width=80)
            self.history_tree.column('Fill Price', width=100)
            self.history_tree.column('Fill Time', width=120)
            self.history_tree.column('Status', width=80)
            
            # Add scrollbar for History
            history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
            self.history_tree.configure(yscrollcommand=history_scrollbar.set)
            
            # Pack History tree and scrollbar
            self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind click events for action buttons
            self.positions_tree.bind('<Button-1>', self.on_positions_click)
            self.orders_tree.bind('<Button-1>', self.on_orders_click)
            
            # Fetch and display trade book data for both accounts
            self.populate_trade_book_sections()
            
            # Add refresh button
            refresh_button = tk.Button(self.broker_position_window, text="Refresh All", 
                                    command=self.populate_trade_book_sections)
            refresh_button.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing order book: {e}")
            messagebox.showerror("Error", f"Failed to show order book: {str(e)}")
    
    def populate_trade_book_sections(self):
        """Populate both Open Positions and Trade History sections with data"""
        try:
            # Clear existing data from all trees
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Process data for both accounts
            all_positions = []
            all_orders = []
            all_history = []
            
            for account_num in [1, 2]:  # Master and Child
                account_name = "Master" if account_num == 1 else "Child"
                
                # Get trade book data
                success, trade_book_data, message = self.account_manager.get_trade_book(account_num)
                
                if success and trade_book_data:
                    # Process trade book data
                    symbol_groups = self.process_trade_book_data(trade_book_data)
                    
                    # Process each symbol
                    for symbol, transactions in symbol_groups.items():
                        # Calculate net position
                        position_info = self.calculate_net_position(transactions)
                        
                        # Add to positions if open
                        if position_info['is_open']:
                            all_positions.append({
                                'account': account_name,
                                'symbol': symbol,
                                'net_qty': position_info['net_qty'],
                                'avg_buy_price': position_info['avg_buy_price'],
                                'current_price': 0.0,  # TODO: Get current price
                                'pnl': 0.0,  # TODO: Calculate PnL
                                'account_num': account_num
                            })
                        
                        # Add all transactions to history
                        for trade in transactions.get('buy', []) + transactions.get('sell', []):
                            all_history.append({
                                'account': account_name,
                                'symbol': symbol,
                                'type': 'Buy' if trade.get('trantype') == 'B' else 'Sell',
                                'qty': trade.get('flqty', '0'),
                                'fill_price': trade.get('flprc', '0.00'),
                                'fill_time': trade.get('norentm', 'N/A'),
                                'status': 'COMPLETE',
                                'account_num': account_num
                            })
                else:
                    # No data or error
                    if not success:
                        all_history.append({
                            'account': account_name,
                            'symbol': f'Error: {message}',
                            'type': '',
                            'qty': '',
                            'fill_price': '',
                            'fill_time': '',
                            'status': '',
                            'account_num': account_num
                        })
                
                # Get order book data
                success, order_book_data, message = self.account_manager.get_order_book(account_num)
                
                if success and order_book_data:
                    # Process order book data for open buy orders
                    for order in order_book_data:
                        if (order.get('status') == 'OPEN' and 
                            order.get('trantype') == 'B' and 
                            order.get('stat') == 'Ok'):
                            
                            all_orders.append({
                                'account': account_name,
                                'order_id': order.get('norenordno', 'N/A'),
                                'symbol': order.get('tsym', 'N/A'),
                                'qty': order.get('qty', '0'),
                                'price': order.get('prc', '0.00'),
                                'type': 'Buy',
                                'time': order.get('norentm', 'N/A'),
                                'account_num': account_num
                            })
            
            # Populate positions tree
            for pos in all_positions:
                self.positions_tree.insert('', 'end', values=(
                    pos['account'],
                    pos['symbol'],
                    pos['net_qty'],
                    f"{pos['avg_buy_price']:.2f}",
                    f"{pos['current_price']:.2f}",
                    f"{pos['pnl']:.2f}",
                    "Exit"
                ))
            
            # Populate orders tree
            for order in all_orders:
                self.orders_tree.insert('', 'end', values=(
                    order['account'],
                    order['order_id'],
                    order['symbol'],
                    order['qty'],
                    order['price'],
                    order['type'],
                    order['time'],
                    "Cancel"
                ))
            
            # Populate history tree
            for trade in all_history:
                self.history_tree.insert('', 'end', values=(
                    trade['account'],
                    trade['symbol'],
                    trade['type'],
                    trade['qty'],
                    trade['fill_price'],
                    trade['fill_time'],
                    trade['status']
                ))
            
            # Show summary
            logger.info(f"Data populated: {len(all_positions)} open positions, {len(all_orders)} open orders, {len(all_history)} trade records")
                
        except Exception as e:
            logger.error(f"Error populating sections: {e}")
            # Show error in all sections
            self.positions_tree.insert('', 'end', values=(f'Error: {str(e)}', '', '', '', '', '', ''))
            self.orders_tree.insert('', 'end', values=(f'Error: {str(e)}', '', '', '', '', '', '', ''))
            self.history_tree.insert('', 'end', values=(f'Error: {str(e)}', '', '', '', '', '', ''))
    
    def on_positions_click(self, event):
        """Handle click on positions tree"""
        try:
            item = self.positions_tree.selection()[0] if self.positions_tree.selection() else None
            if item:
                values = self.positions_tree.item(item, 'values')
                if len(values) >= 7 and values[6] == "Exit":  # Action column
                    symbol = values[1]  # Symbol column
                    qty = values[2]    # Net Qty column
                    self.exit_position(symbol, qty)
        except Exception as e:
            logger.error(f"Error handling positions click: {e}")
    
    def on_orders_click(self, event):
        """Handle click on orders tree"""
        try:
            item = self.orders_tree.selection()[0] if self.orders_tree.selection() else None
            if item:
                values = self.orders_tree.item(item, 'values')
                if len(values) >= 8 and values[7] == "Cancel":  # Action column
                    order_id = values[1]  # Order ID column
                    symbol = values[2]    # Symbol column
                    qty = values[3]      # Qty column
                    price = values[4]    # Price column
                    self.cancel_order(order_id, symbol, qty, price)
        except Exception as e:
            logger.error(f"Error handling orders click: {e}")
    
    def populate_account_orders(self, account_num, tree, account_name):
        """Populate order book table for a specific account"""
        try:
            # Get API for this account
            api = self.account_manager.get_api(account_num)
            
            if api:
                ret = api.get_order_book()
                logger.info(f"{account_name} order book data: {ret}")
                
                if ret and isinstance(ret, list):
                    orders_found = False
                    for order in ret:
                        if isinstance(order, dict) and order.get('stat') == 'Ok':
                            orders_found = True
                            # Extract relevant information
                            order_id = order.get('norenordno', 'N/A')
                            symbol = order.get('tsym', 'N/A')
                            qty = order.get('qty', 'N/A')
                            trantype = order.get('trantype', 'N/A')
                            status = order.get('status', 'N/A')
                            
                            # Determine action based on status
                            action = 'N/A'
                            if status == 'OPEN':
                                action = 'Cancel'
                            elif status == 'COMPLETE':
                                action = 'View'
                            elif status == 'REJECTED':
                                action = 'View'
                            elif status == 'CANCELED':
                                action = 'View'
                            
                            # Insert row into tree
                            tree.insert('', 'end', values=(
                                order_id, symbol, qty, trantype, status, action
                            ))
                    
                    if not orders_found:
                        tree.insert('', 'end', values=('No orders found', '', '', '', '', ''))
                else:
                    # No orders or error
                    tree.insert('', 'end', values=('No orders found', '', '', '', '', ''))
            else:
                # API not available
                tree.insert('', 'end', values=('API not available', '', '', '', '', ''))
                
        except Exception as e:
            logger.error(f"Error populating {account_name} order book: {e}")
            tree.insert('', 'end', values=(f'Error: {str(e)}', '', '', '', '', ''))
        
    def update_selections(self, *args):
        """Update selections when index changes"""
        try:
            selected_index = self.selected_index.get()
            if selected_index:
                logger.info(f"Index selected: {selected_index}")
                
                # Clear existing option and strike selections when index changes
                self.selected_option.set("")  # Clear option dropdown
                self.selected_strike.set("")  # Clear strike dropdown
                logger.info("Option and strike selections cleared for new index")
                
                # Update index LTP
                current_price = self.index_manager.get_index_price(selected_index)
                if current_price > 0:
                    self.index_ltp_value.set(f"{current_price:.2f}")
                else:
                    self.index_ltp_value.set("--")
                
                # Update expiry dropdown
                self.update_expiry_dropdown()
                
                # Update strike dropdown (will be implemented later)
                self.update_strike_dropdown()
                
                # Update quantity dropdown based on selected index
                self.update_quantity_dropdown()
                
        except Exception as e:
            logger.error(f"Error updating selections: {e}")
    
    def update_strike_dropdown(self):
        """Update strike dropdown based on selected index, price, and option type"""
        try:
            selected_index = self.selected_index.get()
            selected_option = self.selected_option.get()
            
            if selected_index:
                current_price = self.index_manager.get_index_price(selected_index)
                if current_price > 0:
                    # Pass option type to get appropriate strike range
                    strikes = self.index_manager.get_strike_list(selected_index, current_price, selected_option)
                    self.strike_dropdown['values'] = strikes
                    # Don't auto-select any strike - let user choose from dropdown
                    logger.info(f"Strike dropdown populated with {len(strikes)} strikes for {selected_index} {selected_option}")
                else:
                    self.strike_dropdown['values'] = []
        except Exception as e:
            logger.error(f"Error updating strike dropdown: {e}")
    
    def update_quantity_dropdown(self):
        """Update quantity dropdown based on selected index lot size"""
        try:
            selected_index = self.selected_index.get()
            if selected_index:
                # Generate quantity options as multiples of lot size
                quantity_options = Config.generate_quantity_options(selected_index, max_multiple=10, config=self.config)
                self.qty_dropdown['values'] = quantity_options
                
                # Set default quantity (1x lot size)
                if quantity_options:
                    self.qty1_var.set(quantity_options[0])
                    logger.info(f"Updated quantity dropdown for {selected_index}: {quantity_options}")
                else:
                    self.qty1_var.set("")
            else:
                self.qty_dropdown['values'] = []
                self.qty1_var.set("")
        except Exception as e:
            logger.error(f"Error updating quantity dropdown: {e}")
    
    def reset_account_states_on_startup(self):
        """Reset all account states to initial state on program startup"""
        try:
            logger.info("Resetting account states to initial state on startup...")
            
            # Reset master account (ID: 1)
            self.account_state_manager.update_login_status(1, 0, "Program startup - master not logged in")
            self.account_state_manager.update_can_order(1, 0, "Program startup - master cannot place orders")
            
            # Reset child account (ID: 2)
            self.account_state_manager.update_login_status(2, 0, "Program startup - child not logged in")
            self.account_state_manager.update_can_order(2, 0, "Program startup - child cannot place orders")
            
            # Reset position data for both accounts on startup (includes filled_quantity)
            self.account_state_manager.reset_position_data(1)
            self.account_state_manager.reset_position_data(2)
            
            # Clear exit order information for both accounts on startup
            self.account_state_manager.clear_exit_order_info(1)
            self.account_state_manager.clear_exit_order_info(2)
            
            # Ensure selection row is enabled on startup
            self.enable_selection_row()
            logger.info("Position data and exit order info cleared on startup for both accounts")
            
            logger.info("Account states reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting account states: {e}")
    
        
    def on_expiry_selected(self, *args):
        """On expiry selected - TO BE IMPLEMENTED"""
        logger.info("On expiry selected called - Function not implemented yet")
        
    def on_option_selected(self, *args):
        """On option selected - update strike dropdown with appropriate range"""
        try:
            selected_option = self.selected_option.get()
            selected_index = self.selected_index.get()
            
            if selected_option and selected_index:
                logger.info(f"Option type changed to {selected_option}, updating strike dropdown")
                # Update strike dropdown with new option type
                self.update_strike_dropdown()
            else:
                logger.info(f"Option type changed to {selected_option}, but no index selected")
        except Exception as e:
            logger.error(f"Error handling option selection: {e}")
        
    def on_strike_selected(self, *args):
        """Handle strike selection - automatically subscribe and fetch price"""
        try:
            strike = self.selected_strike.get()
            # Remove arrow prefix if present (→ 24350 -> 24350)
            if strike.startswith("→ "):
                strike = strike[2:]
            index = self.selected_index.get()
            option = self.selected_option.get()
            expiry = self.expiry_value.get()
            
            # Only proceed if all required fields are selected
            if all([index, expiry, strike, option]):
                # Clear Buy Price box for new symbol selection
                self.price_value.set("")
                # Reset manual clear flag for new symbol
                self.buy_price_manually_cleared = False
                self.previous_price_value = ""
                logger.info("Buy price box cleared for new symbol selection - auto-fill re-enabled")
                
                # Generate trading symbol
                trading_symbol = self.concatenate_values()
                if trading_symbol:
                    # Store the trading symbol for order placement
                    self.current_trading_symbol = trading_symbol
                    logger.info(f"Trading symbol stored: {trading_symbol}")
                    
                    # Automatically fetch price and subscribe
                    self.auto_fetch_and_subscribe(trading_symbol)
                    logger.info(f"Strike selected: {strike}, trading symbol: {trading_symbol}")
                else:
                    logger.warning("Could not generate trading symbol")
            else:
                logger.info("Not all required fields selected for strike selection")
        except Exception as e:
            logger.error(f"Error in on_strike_selected: {e}")
    
    def concatenate_values(self):
        """Concatenate selected values to form trading symbol using old project logic"""
        try:
            index = self.selected_index.get()
            expiry = self.expiry_value.get()
            strike = self.selected_strike.get()
            # Remove arrow prefix if present (→ 24350 -> 24350)
            if strike.startswith("→ "):
                strike = strike[2:]
            option = self.selected_option.get()
            
            if all([index, expiry, strike, option]):
                if index == "SENSEX":
                    trading_symbol = self._generate_sensex_symbol(expiry, strike, option)
                else:
                    # Convert CE/PE to C/P for NIFTY and BANKNIFTY (old project logic)
                    if option == "CE":
                        option_type = "C"
                    elif option == "PE":
                        option_type = "P"
                    else:
                        option_type = option
                    
                    trading_symbol = f"{index}{expiry}{option_type}{strike}"
                
                logger.info(f"Generated trading symbol: {trading_symbol}")
                return trading_symbol
            else:
                logger.warning("Missing required fields for symbol generation")
                return None
        except Exception as e:
            logger.error(f"Error concatenating values: {e}")
            return None
    
    def auto_fetch_and_subscribe(self, trading_symbol):
        """Automatically fetch current price for selected symbol and subscribe to websocket"""
        try:
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                self.premium_price_value.set("No API")
                logger.warning("No API available for fetching price")
                return
            
            # Get current price using symbol manager
            price = self.symbol_manager.get_latest_price(api, trading_symbol)
            if price and price > 0:
                self.premium_price_value.set(f"{price:.2f}")
                logger.info(f"Fetched price for {trading_symbol}: {price}")
                
                # Subscribe to websocket for live updates
                self.subscribe_to_live_price(api, trading_symbol)
                logger.info(f"Auto-subscribed to {trading_symbol} at price {price}")
            else:
                self.premium_price_value.set("N/A")
                logger.warning(f"Could not fetch price for {trading_symbol}")
                
        except Exception as e:
            self.premium_price_value.set("Error")
            logger.error(f"Error in auto-fetch for {trading_symbol}: {e}")
    
    def subscribe_to_live_price(self, api, trading_symbol: str):
        """Subscribe to websocket for live price updates using master account (account 1) only"""
        try:
            # Determine exchange
            if 'SENSEX' in trading_symbol:
                exchange = 'BFO'
            else:
                exchange = 'NFO'
            
            # Get token from symbol manager
            token = self.symbol_manager.get_token(trading_symbol)
            if not token:
                logger.error(f"Could not get token for {trading_symbol}")
                return
            
            # Unsubscribe from previous subscription if exists
            if self.current_subscription:
                try:
                    api.unsubscribe(self.current_subscription)
                    logger.info(f"Unsubscribed from previous: {self.current_subscription}")
                except Exception as e:
                    logger.warning(f"Error unsubscribing from previous: {e}")
            
            # Subscribe to new symbol using master account's WebSocket (account 1)
            websocket_token = f'{exchange}|{token}'
            api.subscribe(websocket_token)
            self.current_subscription = websocket_token
            logger.info(f"Subscribed to live price feed via master account: {websocket_token}")
            
        except Exception as e:
            logger.error(f"Error subscribing to live price: {e}")
    
    def _generate_sensex_symbol(self, expiry: str, strike: str, option: str) -> str:
        """
        Generate SENSEX symbol based on expiry type using old project logic
        
        Format Rules:
        - Monthly expiry (last Thursday): SENSEX + YEAR + MONTH(3-letter) + STRIKE + OPTION
          Example: SENSEX25SEP91600PE
        - Weekly expiry: SENSEX + YEAR + MONTH(single char) + DAY + STRIKE + OPTION  
          Example: SENSEX2591890200PE
        
        Args:
            expiry: Expiry date in format like "11SEP25" or "25SEP25"
            strike: Strike price as string
            option: "CE" or "PE"
            
        Returns:
            Formatted SENSEX symbol
        """
        try:
            # Parse the expiry date
            # Format: "11SEP25" or "25SEP25"
            if len(expiry) == 7:  # Daily expiry like "11SEP25"
                day = expiry[:2]
                month = expiry[2:5]
                year = expiry[5:]
                
                # Convert to datetime to check if it's monthly expiry
                month_num = datetime.strptime(month, '%b').month
                year_full = 2000 + int(year)
                day_num = int(day)
                
                # Check if it's the last Thursday of the month (monthly expiry)
                last_thursday = self._get_last_thursday(year_full, month_num)
                
                if day_num == last_thursday.day:
                    # Monthly expiry format: SENSEX25SEP91600PE
                    return f"SENSEX{year}{month}{strike}{option}"
                else:
                    # Weekly expiry format: SENSEX2591890200PE
                    # Month encoding: 9=Sep, O=Oct, N=Nov, D=Dec
                    month_code = self._get_month_code(month_num)
                    return f"SENSEX{year}{month_code}{day_num:02d}{strike}{option}"
            else:
                # Fallback to original format
                return f"SENSEX{expiry}{strike}{option}"
                
        except Exception as e:
            logger.error(f"Error generating SENSEX symbol: {e}")
            # Fallback to original format
            return f"SENSEX{expiry}{strike}{option}"
    
    def _get_last_thursday(self, year: int, month: int) -> datetime:
        """Get the last Thursday of the month"""
        import calendar
        from datetime import timedelta
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        # Find the last Thursday
        days_back = (last_date.weekday() - 3) % 7
        if days_back == 0 and last_date.weekday() != 3:
            days_back = 7
        last_thursday = last_date - timedelta(days=days_back)
        
        return last_thursday
    
    def _get_month_code(self, month_num: int) -> str:
        """
        Get month code for SENSEX weekly expiry symbols
        
        Args:
            month_num: Month number (1-12)
            
        Returns:
            Single character month code: 9=Sep, O=Oct, N=Nov, D=Dec
        """
        month_codes = {
            1: '1',   # Jan
            2: '2',   # Feb  
            3: '3',   # Mar
            4: '4',   # Apr
            5: '5',   # May
            6: '6',   # Jun
            7: '7',   # Jul
            8: '8',   # Aug
            9: '9',   # Sep
            10: 'O',  # Oct
            11: 'N',  # Nov
            12: 'D'   # Dec
        }
        return month_codes.get(month_num, str(month_num))
        
    def place_buy_orders(self):
        """Place buy orders with validation and parallel execution"""
        try:
            # 1. Validate inputs
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            if not self.current_trading_symbol:
                messagebox.showerror("Error", "Please select all required fields (Index, Expiry, Strike, Option)")
                return
            
            if not self.price_value.get():
                messagebox.showerror("Error", "Please enter buy price")
                return
            
            # 2. Get trading parameters
            trading_symbol = self.current_trading_symbol
            price = float(self.price_value.get())
            master_quantity = int(self.qty1_var.get())
            
            # Get index for lot size calculation
            index = self.selected_index.get()
            
            logger.info(f"Placing buy orders for {trading_symbol} @ {price} master_qty {master_quantity}")
            
            # 3. Check active accounts and validate states
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                login_status = self.account_state_manager.get_login_status(account_id)
                can_order = self.account_state_manager.get_can_order(account_id)
                
                if login_status == 1 and can_order == 1:
                    active_accounts.append(account_id)
                    logger.info(f"Account {account_id} is active for order placement")
                else:
                    logger.warning(f"Account {account_id} not active - login: {login_status}, can_order: {can_order}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts found. Please login to accounts first.")
                return
            
            # 4. Initialize order state tracking
            self.order_states = {1: "PENDING", 2: "PENDING"}
            
            # 5. Disable selection row components to prevent changes during order execution
            self.disable_selection_row()
            
            # 5. Place orders in parallel
            self._place_orders_parallel(active_accounts, trading_symbol, price, master_quantity, index)
            
            # 6. Auto-set SL and Target based on buy order price
            self.auto_set_sl_target_from_buy_price(price)
            
            # 7. Disable buy button with price display and enable management buttons
            self.buy_button.config(state="disabled", text=f"Buy @{price}")
            self.set_buy_price_box_state("disabled")  # Disable price box when buy orders are placed
            
            # 8. Populate modify buy box with the buy order price
            self.modify_buy_value.set(str(price))
            logger.info(f"Modify buy box populated with price: {price}")
            
            self.cancel_buy_button.config(state="normal")
            self.modify_buy_button.config(state="normal")
            self.cancel_master_buy_button.config(state="normal")
            self.cancel_child_buy_button.config(state="normal")
            
            logger.info("Buy orders placed successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid price or quantity: {e}")
            logger.error(f"Value error in place_buy_orders: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to place buy orders: {e}")
            logger.error(f"Error in place_buy_orders: {e}")
    
    def _place_orders_parallel(self, active_accounts, trading_symbol, price, master_quantity, index):
        """Place orders in parallel for active accounts with different quantities"""
        import threading
        
        def place_single_order(account_id):
            try:
                api = self.account_manager.get_api(account_id)
                if not api:
                    logger.error(f"No API available for account {account_id}")
                    return
                
                # Calculate quantity based on account type
                if account_id == 1:  # Master account
                    quantity = master_quantity
                    logger.info(f"Master account quantity: {quantity}")
                else:  # Child account
                    quantity = self.config_manager.calculate_child_quantity(master_quantity, index)
                    logger.info(f"Child account quantity: {quantity} (master: {master_quantity}, index: {index})")
                
                # Determine exchange and product type
                if 'SENSEX' in trading_symbol:
                    exchange = 'BFO'
                    product_type = 'M'
                else:
                    exchange = 'NFO'
                    product_type = 'I'
                
                # Place order
                order_params = {
                    'buy_or_sell': 'B',
                    'product_type': product_type,
                    'exchange': exchange,
                    'tradingsymbol': trading_symbol,
                    'quantity': quantity,
                    'discloseqty': 0,
                    'price_type': 'LMT',
                    'price': price,
                    'trigger_price': None,
                    'retention': 'DAY',
                    'amo': 'NO',
                    'remarks': None
                }
                
                logger.info(f"Placing order for account {account_id}: {order_params}")
                order_response = api.place_order(**order_params)
                
                if order_response and 'norenordno' in order_response:
                    order_id = order_response['norenordno']
                    # Update account state with order info
                    self.account_state_manager.update_order_info(
                        account_id, order_id, trading_symbol, quantity, price
                    )
                    logger.info(f"Order placed successfully for account {account_id}: {order_id}")
                else:
                    logger.error(f"Order placement failed for account {account_id}: {order_response}")
                    
            except Exception as e:
                logger.error(f"Error placing order for account {account_id}: {e}")
        
        # Create and start threads for each active account
        threads = []
        for account_id in active_accounts:
            thread = threading.Thread(target=place_single_order, args=(account_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
    
    def auto_set_sl_target_from_buy_price(self, buy_open_value):
        """Automatically set SL and Target based on buy order open value - from old project"""
        try:
            logger.info(f"Starting auto SL/Target calculation for buy price: {buy_open_value}")
            
            if buy_open_value is None:
                logger.warning("Buy open value is None, skipping SL/Target calculation")
                return
                
            # Update current buy order open value
            self.current_buy_order_open_value = buy_open_value
            
            # Log the differences being used
            logger.info(f"Using differences - SL: {self.sl_difference_from_buy}, Target: {self.target_difference_from_buy}")
            
            # Calculate SL and Target based on stored differences
            sl_price = round(buy_open_value + self.sl_difference_from_buy, 2)
            # Ensure SL price never goes below 0
            if sl_price < 0:
                sl_price = 0.0
                logger.info(f"SL price calculated as negative ({buy_open_value + self.sl_difference_from_buy}), setting to 0")
            
            target_price = round(buy_open_value + self.target_difference_from_buy, 2)
            
            logger.info(f"Calculated prices - SL: {sl_price}, Target: {target_price}")
            
            # Set SL price
            self.sl_price_value.set(str(sl_price))
            self.sl_price_level = sl_price
            self.sl_button_state = "confirmed"
            self.sl_price_button.config(text=f"SL Set @{sl_price}", bg="orange", fg="white")
            
            # Set Target price
            self.target_price_value.set(str(target_price))
            self.target_price_level = target_price
            self.target_button_state = "confirmed"
            self.target_price_button.config(text=f"Target Set @{target_price}", bg="orange", fg="white")
            
            # Update sl_target_states for distance maintenance during buy order modifications
            sl_points = buy_open_value - sl_price  # Points difference for SL
            target_points = target_price - buy_open_value  # Points difference for Target
            
            self.sl_target_states.update({
                'sl_calculated': True,
                'target_calculated': True,
                'sl_price': sl_price,
                'target_price': target_price,
                'sl_points': sl_points,
                'target_points': target_points,
                'buy_price': buy_open_value
            })
            
            logger.info(f"UI values set - SL: {self.sl_price_value.get()}, Target: {self.target_price_value.get()}")
            logger.info(f"SL/Target points calculated - SL points: {sl_points}, Target points: {target_points}")
            
            # Start monitoring if buy orders are filled
            if self._are_buy_orders_filled():
                self.start_sl_monitoring(sl_price)
                self.start_target_monitoring(target_price)
                logger.info(f"Auto SL/Target set and monitoring started - SL: {sl_price}, Target: {target_price} (Buy Open: {buy_open_value})")
            else:
                logger.info(f"Auto SL/Target set - SL: {sl_price}, Target: {target_price} (Buy Open: {buy_open_value})")
                
        except Exception as e:
            logger.error(f"Error in auto_set_sl_target_from_buy_price: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _are_buy_orders_filled(self):
        """Check if buy orders are filled/completed - only returns True for actually filled orders"""
        try:
            # Check if accounts have actual filled positions (not just ability to order)
            master_filled_qty = self.account_state_manager.get_filled_quantity(1)
            child_filled_qty = self.account_state_manager.get_filled_quantity(2)
            
            logger.info(f"Buy orders filled check - Master: filled_qty={master_filled_qty}")
            logger.info(f"Buy orders filled check - Child: filled_qty={child_filled_qty}")
            
            # Only return True if at least one account has actual filled positions
            has_filled_positions = (master_filled_qty > 0) or (child_filled_qty > 0)
            
            logger.info(f"Buy orders filled result: {has_filled_positions}")
            return has_filled_positions
            
        except Exception as e:
            logger.error(f"Error checking if buy orders are filled: {e}")
            return False
    
    def set_sl_price(self):
        """Set SL price - from old project"""
        try:
            if not self.sl_price_value.get():
                messagebox.showerror("Error", "Please enter SL price")
                return
            
            new_sl_price = float(self.sl_price_value.get())
            
            # Ensure SL price is not negative
            if new_sl_price < 0:
                messagebox.showerror("Error", "SL price cannot be negative")
                return
            
            # Update state
            self.sl_price_level = new_sl_price
            self.sl_button_state = "confirmed"
            
            # Check if monitoring is currently active to maintain button color
            if self.sl_monitoring_active:
                # Keep RED color when monitoring is active
                self.sl_price_button.config(text=f"SL placed @{new_sl_price}", bg="red", fg="white")
                logger.info(f"SL price updated during active monitoring: {new_sl_price}")
            else:
                # Use orange color when not monitoring
                self.sl_price_button.config(text=f"SL Set @{new_sl_price}", bg="orange", fg="white")
            
            # Update sl_target_states with new SL points for proper distance maintenance during buy order modification
            # Use current price field value instead of stored buy order value for manual SL calculation
            current_buy_price = None
            if self.price_value.get().strip():
                try:
                    current_buy_price = float(self.price_value.get())
                except ValueError:
                    logger.warning("Invalid buy price in field - cannot calculate SL points")
            
            if current_buy_price:
                # Calculate new SL points based on current price field value
                new_sl_points = current_buy_price - new_sl_price
                
                # Update sl_target_states to maintain this distance during future buy order modifications
                if not hasattr(self, 'sl_target_states'):
                    self.sl_target_states = {}
                
                self.sl_target_states.update({
                    'sl_calculated': True,
                    'sl_price': new_sl_price,
                    'sl_points': new_sl_points,
                    'buy_price': current_buy_price
                })
                
                logger.info(f"Manual SL set - Price: {new_sl_price}, Points from buy: {new_sl_points}, Buy price: {current_buy_price}")
            else:
                logger.warning("No current buy price in field - SL points cannot be calculated for distance maintenance")
            
            # Check if buy orders are completed and start monitoring
            if self._are_buy_orders_filled():
                self.start_sl_monitoring(new_sl_price)
                logger.info(f"SL price confirmed and monitoring started: {new_sl_price} (buy orders are filled)")
            else:
                logger.info(f"SL price confirmed: {new_sl_price} (monitoring will start after buy order is filled)")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid SL price")
        except Exception as e:
            logger.error(f"Error setting SL price: {e}")
    
    def set_target_price(self):
        """Set Target price - from old project"""
        try:
            if not self.target_price_value.get():
                messagebox.showerror("Error", "Please enter Target price")
                return
            
            new_target_price = float(self.target_price_value.get())
            
            # Update state
            self.target_price_level = new_target_price
            self.target_button_state = "confirmed"
            
            # Check if monitoring is currently active to maintain button color
            if self.target_monitoring_active:
                # Keep GREEN color when monitoring is active
                self.target_price_button.config(text=f"Target placed @{new_target_price}", bg="green", fg="white")
                logger.info(f"Target price updated during active monitoring: {new_target_price}")
            else:
                # Use orange color when not monitoring
                self.target_price_button.config(text=f"Target Set @{new_target_price}", bg="orange", fg="white")
            
            # Update sl_target_states with new Target points for proper distance maintenance during buy order modification
            # Use current price field value instead of stored buy order value for manual Target calculation
            current_buy_price = None
            if self.price_value.get().strip():
                try:
                    current_buy_price = float(self.price_value.get())
                except ValueError:
                    logger.warning("Invalid buy price in field - cannot calculate Target points")
            
            if current_buy_price:
                # Calculate new Target points based on current price field value
                new_target_points = new_target_price - current_buy_price
                
                # Update sl_target_states to maintain this distance during future buy order modifications
                if not hasattr(self, 'sl_target_states'):
                    self.sl_target_states = {}
                
                self.sl_target_states.update({
                    'target_calculated': True,
                    'target_price': new_target_price,
                    'target_points': new_target_points,
                    'buy_price': current_buy_price
                })
                
                logger.info(f"Manual Target set - Price: {new_target_price}, Points from buy: {new_target_points}, Buy price: {current_buy_price}")
            else:
                logger.warning("No current buy price in field - Target points cannot be calculated for distance maintenance")
            
            # Check if buy orders are completed and start monitoring
            if self._are_buy_orders_filled():
                self.start_target_monitoring(new_target_price)
                logger.info(f"Target price confirmed and monitoring started: {new_target_price} (buy orders are filled)")
            else:
                logger.info(f"Target price confirmed: {new_target_price} (monitoring will start after buy order is filled)")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid Target price")
        except Exception as e:
            logger.error(f"Error setting Target price: {e}")
    
    def _timeout_handler(self, account_id):
        """Handle timeout for order completion"""
        try:
            logger.info(f"Timeout reached for account {account_id}, cancelling order")
            
            # Cancel the order for the specified account
            if account_id == 1:
                self.cancel_master_buy_order()
            else:
                self.cancel_child_buy_order()
                
        except Exception as e:
            logger.error(f"Error in timeout handler for account {account_id}: {e}")
    
    def _on_order_status_update(self, account_id: int, status: str, trantype: str = "Unknown"):
        """Handle order status updates from websocket"""
        try:
            # Update order state
            self.order_states[account_id] = status
            logger.info(f"Account {account_id} order status updated to: {status}")
            
            # CRITICAL DEBUG: Log detailed information about the status
            logger.info(f"DEBUG - Account {account_id} status: '{status}' (type: {type(status)})")
            logger.info(f"DEBUG - Current account can_order: {self.account_state_manager.get_can_order(account_id)}")
            logger.info(f"DEBUG - Transaction type: '{trantype}'")
            
            # Handle rejection - set can_order to 0
            if status == "REJECTED":
                self.account_state_manager.update_can_order(
                    account_id, 0, f"Order rejected for account {account_id}"
                )
                logger.info(f"Account {account_id} can_order set to 0 due to rejection")
            
            # Check for timeout scenario: one COMPLETE, other OPEN
            if status == "COMPLETE":
                other_account = 2 if account_id == 1 else 1
                if self.order_states[other_account] == "OPEN":
                    # Start 5-second timer for the OPEN order
                    import threading
                    self.timeout_timer = threading.Timer(5.0, self._timeout_handler, args=[other_account])
                    self.timeout_timer.start()
                    logger.info(f"Started 5-second timeout timer for account {other_account}")
            
            # If OPEN order completes before timeout, cancel timer
            elif status in ["COMPLETE", "REJECTED"] and self.timeout_timer:
                self.timeout_timer.cancel()
                self.timeout_timer = None
                logger.info("Timeout timer cancelled - order completed before timeout")
            
            # Send Telegram notification for any completed order
            if status == "COMPLETE":
                # Get order details for notification
                account_status = self.account_state_manager.get_account_status(account_id)
                if account_status:
                    symbol = account_status.get('current_symbol', '')
                    price = account_status.get('current_price', 0.0)
                    quantity = account_status.get('current_quantity', 0)
                    
                    # Send Telegram notification (non-blocking)
                    try:
                        self.log_monitor.send_order_completion_notification(
                            account_id, symbol, price, quantity, trantype, status
                        )
                    except Exception as e:
                        logger.error(f"Error sending order completion notification: {e}")
            
            # Activate SL/Target monitoring ONLY when BUY orders are completed
            if status == "COMPLETE" and trantype.upper() == 'B':
                # Get current symbol and price for the completed order
                account_status = self.account_state_manager.get_account_status(account_id)
                if account_status:
                    symbol = account_status.get('current_symbol', '')
                    price = account_status.get('current_price', 0.0)
                    
                    # Additional safety check: Only activate if account can still order (not rejected)
                    can_order = self.account_state_manager.get_can_order(account_id)
                    if can_order == 1:  # Account can still order = order was successful
                        self.on_buy_order_completed(account_id, symbol, price)
                        logger.info(f"SL/Target monitoring activated for account {account_id} - BUY order was successful")
                    else:
                        logger.warning(f"Order marked as COMPLETE but account {account_id} cannot order - likely rejected. NOT activating SL/Target monitoring")
            elif status == "COMPLETE" and trantype.upper() == 'S':
                logger.info(f"SELL order completed for account {account_id} - NOT activating SL/Target monitoring")
            elif status == "COMPLETE":
                logger.warning(f"Order completed for account {account_id} but unknown transaction type: '{trantype}' - NOT activating SL/Target monitoring")
                
        except Exception as e:
            logger.error(f"Error handling order status update for account {account_id}: {e}")
    
    def on_buy_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle buy order completion - track filled quantity and start monitoring"""
        try:
            logger.info(f"Buy order completed for account {account_num}: {symbol} @ {price}")
            
            # CRITICAL VALIDATION: Check if account can still order (not rejected)
            can_order = self.account_state_manager.get_can_order(account_num)
            if can_order == 0:
                logger.warning(f"Buy order completion called for account {account_num} but account cannot order - likely rejected. NOT activating SL/Target")
                return
            
            # ADDITIONAL VALIDATION: Check if account is active
            if not self.account_manager.accounts[account_num]['active']:
                logger.warning(f"Buy order completion called for account {account_num} but account is not active. NOT activating SL/Target")
                return
            
            # Get the filled quantity from account state (should be set during order placement)
            filled_qty = self.account_state_manager.get_filled_quantity(account_num)
            if filled_qty == 0:
                # Fallback: use the quantity from current order info if not set
                account_status = self.account_state_manager.get_account_status(account_num)
                if account_status and account_status.get('current_quantity'):
                    filled_qty = int(float(account_status['current_quantity']))
                    # Update filled quantity in state
                    self.account_state_manager.update_filled_quantity(account_num, filled_qty)
            
            # FINAL VALIDATION: Only proceed if we have actual filled quantity
            if filled_qty <= 0:
                logger.warning(f"Buy order completion called for account {account_num} but no filled quantity. NOT activating SL/Target")
                return
            
            logger.info(f"Account {account_num} filled quantity: {filled_qty} - VALID for SL/Target activation")
            
            # Check if SL and Target prices are set
            sl_price_text = self.sl_price_value.get().strip()
            target_price_text = self.target_price_value.get().strip()
            
            if sl_price_text:
                try:
                    sl_price = float(sl_price_text)
                    self.start_sl_monitoring(sl_price)
                    logger.info(f"SL monitoring started at: {sl_price}")
                except ValueError:
                    logger.warning("Invalid SL price format")
            
            if target_price_text:
                try:
                    target_price = float(target_price_text)
                    self.start_target_monitoring(target_price)
                    logger.info(f"Target monitoring started at: {target_price}")
                except ValueError:
                    logger.warning("Invalid Target price format")
            
            # Enable exit buttons based on accounts with positions
            # Refresh state to ensure we have latest values
            self.account_state_manager._initialize_states()  # Reload state from CSV
            self._update_exit_button_states()
            
            # Update PnL button state (disable when positions are active)
            self.update_verify_pnl_button_state()
                
            logger.info("Exit buttons and PnL button state updated after buy order completion")
            
        except Exception as e:
            logger.error(f"Error handling buy order completion: {e}")
    
    def _update_exit_button_states(self):
        """Update exit button states based on accounts with positions"""
        try:
            # Debug logging with more details
            master_filled_qty = self.account_state_manager.get_filled_quantity(1)
            child_filled_qty = self.account_state_manager.get_filled_quantity(2)
            logger.info(f"Exit button state update - Master: filled_qty={master_filled_qty}")
            logger.info(f"Exit button state update - Child: filled_qty={child_filled_qty}")
            
            # Enable general exit buttons if any account has position
            if master_filled_qty > 0 or child_filled_qty > 0:
                self.exit_button.config(state='normal')
                self.exit_all_button.config(state='normal')
                logger.info("SELL buttons ENABLED - at least one account has position")
            else:
                self.exit_button.config(state='disabled')
                self.exit_all_button.config(state='disabled')
                logger.info("SELL buttons DISABLED - no accounts have positions")
            
            # Enable individual exit buttons based on account positions
            if master_filled_qty > 0 and self.account_manager.accounts[1]['active']:
                self.exit_master_button.config(state='normal')
            else:
                self.exit_master_button.config(state='disabled')
                
            if child_filled_qty > 0 and self.account_manager.accounts[2]['active']:
                self.exit_child_button.config(state='normal')
            else:
                self.exit_child_button.config(state='disabled')
                
            
        except Exception as e:
            logger.error(f"Error updating exit button states: {e}")
    
    def start_websocket_health_monitoring(self):
        """Start monitoring WebSocket health"""
        try:
            import datetime
            current_time = datetime.datetime.now()
            
            # Update last update time for the account
            for account_id in [1, 2]:
                if self.account_manager.accounts[account_id]['active']:
                    self.websocket_last_update[account_id] = current_time
            
            # Start periodic health check (every 30 seconds)
            if not self.websocket_health_timer:
                self._schedule_websocket_health_check()
                
        except Exception as e:
            logger.error(f"Error starting WebSocket health monitoring: {e}")
    
    def _schedule_websocket_health_check(self):
        """Schedule the next WebSocket health check"""
        try:
            import threading
            self.websocket_health_timer = threading.Timer(30.0, self._check_websocket_health)
            self.websocket_health_timer.start()
        except Exception as e:
            logger.error(f"Error scheduling WebSocket health check: {e}")
    
    def _check_websocket_health(self):
        """Check WebSocket health and alert on failures"""
        try:
            import datetime
            current_time = datetime.datetime.now()
            alert_needed = False
            alert_message = "[WARNING] WEBSOCKET CONNECTION ISSUES DETECTED [WARNING]\n\n"
            
            for account_id in [1, 2]:
                if self.account_manager.accounts[account_id]['active']:
                    last_update = self.websocket_last_update.get(account_id)
                    
                    if last_update:
                        time_diff = (current_time - last_update).total_seconds()
                        
                        # Consider connection failed if no updates for 60 seconds
                        if time_diff > 60:
                            self.websocket_health[account_id] = False
                            account_name = "Master" if account_id == 1 else "Child"
                            alert_message += f"• {account_name} account: No data for {int(time_diff)} seconds\n"
                            alert_needed = True
                        else:
                            self.websocket_health[account_id] = True
            
            if alert_needed:
                alert_message += "\n🚫 AUTOMATED ACTIONS PAUSED 🚫\n"
                alert_message += "• Stop Loss monitoring may be affected\n"
                alert_message += "• Target monitoring may be affected\n"
                alert_message += "• Real-time price updates unavailable\n\n"
                alert_message += "Please check your internet connection and broker status."
                
                # Show alert popup
                messagebox.showwarning("WebSocket Connection Alert", alert_message)
                logger.critical("WebSocket health check failed - automated actions paused")
                
                # Pause SL/Target monitoring
                self.sl_monitoring_active = False
                self.target_monitoring_active = False
            
            # Schedule next check
            self._schedule_websocket_health_check()
            
        except Exception as e:
            logger.error(f"Error in WebSocket health check: {e}")
            # Continue monitoring even if there's an error
            self._schedule_websocket_health_check()
    
    def update_websocket_health(self, account_id: int):
        """Update WebSocket health timestamp for account"""
        try:
            import datetime
            self.websocket_last_update[account_id] = datetime.datetime.now()
            self.websocket_health[account_id] = True
        except Exception as e:
            logger.error(f"Error updating WebSocket health for account {account_id}: {e}")
    
    def start_sl_monitoring(self, sl_price):
        """Start monitoring Stop Loss price - from old project"""
        try:
            self.sl_monitoring_active = True
            self.sl_price_level = sl_price
            self.sl_price_button.config(text=f"SL placed @{sl_price}", bg="red", fg="white")
            self.sl_monitoring_label.config(text="Monitoring Activated", fg="green")
            logger.info(f"SL MONITORING ACTIVATED - Price: {sl_price} - Monitoring for price <= {sl_price}")
        except Exception as e:
            logger.error(f"Error starting SL monitoring: {e}")
    
    def start_target_monitoring(self, target_price):
        """Start monitoring Target price - from old project"""
        try:
            self.target_monitoring_active = True
            self.target_price_level = target_price
            self.target_price_button.config(text=f"Target placed @{target_price}", bg="green", fg="white")
            logger.info(f"TARGET MONITORING ACTIVATED - Price: {target_price} - Monitoring for price >= {target_price}")
        except Exception as e:
            logger.error(f"Error starting Target monitoring: {e}")
    
    def stop_sl_monitoring(self):
        """Stop SL monitoring - from old project"""
        try:
            self.sl_monitoring_active = False
            self.sl_price_level = None
            self.sl_button_state = "ready"
            self.sl_price_button.config(text="SL Price", bg="SystemButtonFace", fg="black")
            self.sl_monitoring_label.config(text="", fg="green")
            logger.info("SL monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping SL monitoring: {e}")
    
    def stop_target_monitoring(self):
        """Stop Target monitoring - from old project"""
        try:
            self.target_monitoring_active = False
            self.target_price_level = None
            self.target_button_state = "ready"
            self.target_price_button.config(text="Target Price", bg="SystemButtonFace", fg="black")
            logger.info("Target monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping Target monitoring: {e}")
    
    def _start_price_monitoring(self):
        """Start real-time price monitoring for SL/Target"""
        try:
            # The monitoring is already active through the live price callback
            # This method is called when SL/Target become active
            logger.info("Price monitoring started for SL/Target - monitoring live price feed")
            
            # The actual monitoring happens in _check_sl_target_breaches()
            # which is called from update_live_price() on every price update
            
        except Exception as e:
            logger.error(f"Error starting price monitoring: {e}")
        
    def place_exit_orders(self, order_type='LMT'):
        """Place exit orders across all active accounts
        
        Args:
            order_type: 'LMT' for limit orders, 'MKT' for market orders
        """
        try:
            # Check if exit button is disabled (orders already placed)
            if self.exit_button['state'] == 'disabled':
                messagebox.showwarning("Warning", "Exit orders already placed! Use RELEASE button to enable new orders.")
                return
                
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            # If exit price box is empty, populate with current LTP and return (don't place order yet)
            if not self.price1_value.get().strip():
                current_ltp = self.premium_price_value.get()
                if current_ltp:
                    self.price1_value.set(current_ltp)
                    logger.info(f"Exit price box populated with current LTP: {current_ltp}")
                    return  # Stop here - user needs to press button again to place order
                else:
                    messagebox.showerror("Error", "Please fetch current price first")
                    return
            
            price = float(self.price1_value.get())
            
            # Get active accounts that have positions to exit
            active_accounts = []
            account_data = {}
            
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_filled_quantity(account_id) > 0):
                    
                    # Get position details from account state
                    account_status = self.account_state_manager.get_account_status(account_id)
                    filled_qty = self.account_state_manager.get_filled_quantity(account_id)
                    
                    if account_status and account_status.get('current_symbol') and filled_qty > 0:
                        active_accounts.append(account_id)
                        account_data[account_id] = {
                            'symbol': account_status['current_symbol'],
                            'quantity': filled_qty,  # Use actual filled quantity
                            'order_id': account_status['current_order_id']
                        }
                        logger.info(f"Account {account_id} exit position: {account_status['current_symbol']} filled_qty={filled_qty}")
                    else:
                        logger.warning(f"Account {account_id} has no position to exit - filled_qty: {filled_qty}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts with positions available for exit orders")
                return
            
            logger.info(f"Placing exit orders for accounts: {active_accounts}")
            
            # Set quantities from account state data
            for account_id in active_accounts:
                self.quantities[account_id] = account_data[account_id]['quantity']
                logger.info(f"Account {account_id} quantity from state: {self.quantities[account_id]}")
            
            # Place orders for each active account in parallel
            order_numbers = self._place_exit_orders_parallel(active_accounts, account_data, price, order_type)
                
            # Store exit order numbers and update CSV
            for i, account_id in enumerate(active_accounts):
                if i < len(order_numbers) and order_numbers[i]:
                    self.exit_order_numbers[account_id] = order_numbers[i]
                    logger.info(f"Exit order placed for account {account_id}: {order_numbers[i]}")
                    
                    # Update exit order info in CSV
                    symbol = account_data[account_id]['symbol']
                    quantity = account_data[account_id]['quantity']
                    self.account_state_manager.update_exit_order_info(
                        account_id, 
                        order_numbers[i], 
                        order_type, 
                        price, 
                        quantity
                    )
            
            # Update UI state
            self.exit_button.config(state='disabled', text="Exit Orders Placed")
            self.cancel_exit_button.config(state='normal')
            self.modify_exit_button.config(state='normal')
            
            # Update order status displays
            for account_id in active_accounts:
                if account_id == 1:
                    self.master_order_status.set(f"Exit Order Placed: {self.exit_order_numbers[account_id]}")
                elif account_id == 2:
                    self.child_order_status.set(f"Exit Order Placed: {self.exit_order_numbers[account_id]}")
            
            messagebox.showinfo("Success", f"Exit orders placed successfully for {len(active_accounts)} account(s)")
            logger.info("Exit orders placed successfully")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            logger.error(f"Value error in place_exit_orders: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error placing exit orders: {e}")
            logger.error(f"Error in place_exit_orders: {e}")
        
    def modify_exit_orders(self):
        """Modify exit orders across all active accounts"""
        try:
            # If modify exit box is empty, populate with current LTP and return (don't place order yet)
            if not self.modify_exit_value.get().strip():
                current_ltp = self.premium_price_value.get()
                if current_ltp:
                    self.modify_exit_value.set(current_ltp)
                    logger.info(f"Modify Exit box populated with current LTP: {current_ltp}")
                    return  # Stop here - user needs to press button again to place order
                else:
                    messagebox.showerror("Error", "Please fetch current price first")
                    return
            
            price = float(self.modify_exit_value.get())
            
            # Get active accounts that can place orders, have positions, and have exit orders
            active_accounts = []
            account_data = {}
            
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_order(account_id) == 1 and
                    self.exit_order_numbers[account_id]):
                    
                    # Get position details from account state
                    account_status = self.account_state_manager.get_account_status(account_id)
                    if account_status and account_status.get('current_symbol') and account_status.get('current_quantity'):
                        active_accounts.append(account_id)
                        account_data[account_id] = {
                            'symbol': account_status['current_symbol'],
                            'quantity': int(account_status['current_quantity']),
                            'order_id': account_status['current_order_id']
                        }
                        logger.info(f"Account {account_id} position for modify: {account_status['current_symbol']} qty={account_status['current_quantity']}")
                    else:
                        logger.warning(f"Account {account_id} has no position data in account state")
            
            if not active_accounts:
                messagebox.showerror("Error", "No modifiable exit orders found")
                return
            
            logger.info(f"Modifying exit orders for accounts: {active_accounts}")
            
            # Modify orders in parallel using threading
            modified_orders = self._modify_exit_orders_parallel(active_accounts, account_data, price)
            
            # Update order status displays
            successful_modifications = 0
            for i, account_id in enumerate(active_accounts):
                if i < len(modified_orders) and modified_orders[i]:
                    successful_modifications += 1
                    if account_id == 1:
                        self.master_order_status.set(f"Exit Order Modified: {modified_orders[i]}")
                    elif account_id == 2:
                        self.child_order_status.set(f"Exit Order Modified: {modified_orders[i]}")
                    logger.info(f"Exit order modified for account {account_id}: {modified_orders[i]}")
            
            if successful_modifications > 0:
                messagebox.showinfo("Success", f"Exit orders modified successfully for {successful_modifications} account(s)")
                logger.info(f"Exit orders modified successfully for {successful_modifications} account(s)")
            else:
                messagebox.showerror("Error", "No exit orders were successfully modified")
                logger.error("No exit orders were successfully modified")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            logger.error(f"Value error in modify_exit_orders: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error modifying exit orders: {e}")
            logger.error(f"Error in modify_exit_orders: {e}")

    def cancel_exit_orders(self):
        """Cancel exit orders across all active accounts"""
        try:
            # Get active accounts that can place orders and have exit orders
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_order(account_id) == 1 and
                    self.exit_order_numbers[account_id]):
                    active_accounts.append(account_id)
            
            if not active_accounts:
                messagebox.showerror("Error", "No exit orders found to cancel")
                return
            
            logger.info(f"Cancelling exit orders for accounts: {active_accounts}")
            
            # Cancel orders for each active account
            apis = []
            order_numbers = []
            active_flags = []
            
            for account_id in active_accounts:
                api = self.account_manager.get_api(account_id)
                if api:
                    apis.append(api)
                    order_numbers.append(self.exit_order_numbers[account_id])
                    active_flags.append(True)
                else:
                    logger.error(f"No API available for account {account_id}")
                    active_flags.append(False)
            
            # Cancel exit orders in parallel using threading
            cancelled_orders = self._cancel_exit_orders_parallel(active_accounts, apis, order_numbers, active_flags)
            
            # Clear exit order numbers and update UI
            successful_cancels = sum(1 for result in cancelled_orders if result is not None)
            
            for account_id in active_accounts:
                self.exit_order_numbers[account_id] = ''
                if account_id == 1:
                    self.master_order_status.set("Exit Order Cancelled")
                elif account_id == 2:
                    self.child_order_status.set("Exit Order Cancelled")
                logger.info(f"Exit order cancelled for account {account_id}")
            
            # Update UI state
            self.exit_button.config(state='normal', text="SELL Order")
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            
            if successful_cancels > 0:
                messagebox.showinfo("Success", f"Exit orders cancelled successfully for {successful_cancels} account(s)")
                logger.info(f"Exit orders cancelled successfully for {successful_cancels} account(s)")
            else:
                messagebox.showerror("Error", "No exit orders were successfully cancelled")
                logger.error("No exit orders were successfully cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cancelling exit orders: {e}")
            logger.error(f"Error in cancel_exit_orders: {e}")

    def exit_all_orders_market(self):
        """Exit all orders at market price for both master and child accounts"""
        try:
            # Check if exit all button is disabled (no orders to exit)
            if self.exit_all_button['state'] == 'disabled':
                messagebox.showwarning("Warning", "No orders to sell! Place buy orders first.")
                return
            
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit All Orders", 
                "Are you sure you want to exit all orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                logger.info("Exit all orders cancelled by user")
                return
            
            logger.info("Exiting all orders at market price")
            
            # Get logged-in accounts (check login_status == 1)
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if self.account_state_manager.get_login_status(account_id) == 1:
                    active_accounts.append(account_id)
            
            if not active_accounts:
                messagebox.showerror("Error", "No logged-in accounts available for market exit")
                return
            
            # Check for existing exit orders and modify or place new orders
            for account_id in active_accounts:
                existing_order = self.account_state_manager.get_exit_order_info(account_id)
                
                if existing_order:
                    # Modify existing order to market price
                    logger.info(f"Found existing exit order for account {account_id}: {existing_order['order_number']}")
                    self._modify_exit_order_to_market(account_id, existing_order)
                else:
                    # Place new market exit order
                    logger.info(f"No existing exit order for account {account_id}, placing new market order")
                    self._place_market_exit_order(account_id)
            
            # Stop all monitoring after placing exit orders
            self._stop_monitoring()
            
            messagebox.showinfo("Success", f"Market exit orders placed for {len(active_accounts)} account(s)")
            logger.info("Market exit orders placed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing market exit orders: {e}")
            logger.error(f"Error in exit_all_orders_market: {e}")

    def exit_master_orders_market(self):
        """Exit master account orders at market price"""
        try:
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit Master Orders", 
                "Are you sure you want to exit Master orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                logger.info("Exit master orders cancelled by user")
                return
            
            logger.info("Exiting master orders at market price")
            
            if self.account_state_manager.get_login_status(1) != 1:
                messagebox.showerror("Error", "Master account is not logged in")
                return
            
            # Check for existing exit order and modify or place new order
            existing_order = self.account_state_manager.get_exit_order_info(1)
            
            if existing_order:
                # Modify existing order to market price
                logger.info(f"Found existing exit order for Master: {existing_order['order_number']}")
                self._modify_exit_order_to_market(1, existing_order)
                messagebox.showinfo("Success", "Master exit order modified to market price successfully")
            else:
                # Place new market exit order
                logger.info("No existing exit order for Master, placing new market order")
                self._place_market_exit_order(1)
                messagebox.showinfo("Success", "Master market exit order placed successfully")
            
            # Update master account can_order flag to 0 (master can no longer place orders)
            self.account_state_manager.update_can_order(1, 0, "Master account exited at market price")
            logger.info("Master account can_order set to 0 after market exit")
            
            logger.info("Master market exit process completed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing master market exit order: {e}")
            logger.error(f"Error in exit_master_orders_market: {e}")

    def exit_child_orders_market(self):
        """Exit child account orders at market price"""
        try:
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit Child Orders", 
                "Are you sure you want to exit Child orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                logger.info("Exit child orders cancelled by user")
                return
            
            logger.info("Exiting child orders at market price")
            
            if self.account_state_manager.get_login_status(2) != 1:
                messagebox.showerror("Error", "Child account is not logged in")
                return
            
            # Check for existing exit order and modify or place new order
            existing_order = self.account_state_manager.get_exit_order_info(2)
            
            if existing_order:
                # Modify existing order to market price
                logger.info(f"Found existing exit order for Child: {existing_order['order_number']}")
                self._modify_exit_order_to_market(2, existing_order)
                messagebox.showinfo("Success", "Child exit order modified to market price successfully")
            else:
                # Place new market exit order
                logger.info("No existing exit order for Child, placing new market order")
                self._place_market_exit_order(2)
                messagebox.showinfo("Success", "Child market exit order placed successfully")
            
            # Update child account can_order flag to 0 (child can no longer place orders)
            self.account_state_manager.update_can_order(2, 0, "Child account exited at market price")
            logger.info("Child account can_order set to 0 after market exit")
            
            logger.info("Child market exit process completed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing child market exit order: {e}")
            logger.error(f"Error in exit_child_orders_market: {e}")

    def _place_market_exit_order(self, account_id):
        """Helper function to place market exit order for a specific account"""
        try:
            # Get position details from account state
            account_status = self.account_state_manager.get_account_status(account_id)
            if not account_status or not account_status.get('current_symbol') or not account_status.get('current_quantity'):
                logger.error(f"No position data found for account {account_id} in account state")
                return
            
            symbol = account_status['current_symbol']
            quantity = int(account_status['current_quantity'])
            
            api = self.account_manager.get_api(account_id)
            if not api:
                logger.error(f"No API available for account {account_id}")
                return
            
            # Use existing API object directly - no need to re-authenticate
            
            logger.info(f"Market exit for account {account_id}: {symbol} qty={quantity}")
            
            # Determine exchange and product type based on symbol
            if 'SENSEX' in symbol:  # Fixed: Check for SENSEX instead of BFO
                exchange = 'BFO'
                product_type = 'M'
            else:
                exchange = 'NFO'
                product_type = 'I'
            
            # Place market exit order directly
            result = api.place_order(
                buy_or_sell='S',
                product_type=product_type,
                exchange=exchange,
                tradingsymbol=symbol,
                quantity=str(quantity),
                discloseqty=0,
                price_type='MKT',
                price='0',
                trigger_price='0',
                retention='DAY',
                remarks='market_exit'
            )
            
            # Log the broker response
            logger.info(f"Broker response for account {account_id}: {result}")
            
            if result and result.get('stat') == 'Ok':
                order_number = result.get('norenordno')
                self.exit_order_numbers[account_id] = order_number
                logger.info(f"Market exit order placed for account {account_id}: {order_number}")
                
                # Store exit order info in account state manager
                self.account_state_manager.update_exit_order_info(
                    account_id, 
                    order_number, 
                    'MKT',  # Market order
                    0,      # Market orders have price 0
                    quantity
                )
                
                # Update order status display
                if account_id == 1:
                    self.master_order_status.set(f"Market Exit Order: {order_number}")
                elif account_id == 2:
                    self.child_order_status.set(f"Market Exit Order: {order_number}")
            else:
                # Log the rejection reason from broker
                if result:
                    error_msg = result.get('emsg', 'Unknown error')
                    logger.warning(f"Market exit order rejected for account {account_id}: {error_msg}")
                    logger.info(f"Full rejection details: {result}")
                else:
                    logger.error(f"Market exit order failed for account {account_id}: No response from broker")
                
                # Still update UI to show attempt was made
                if account_id == 1:
                    self.master_order_status.set("Market Exit Attempted (Rejected)")
                elif account_id == 2:
                    self.child_order_status.set("Market Exit Attempted (Rejected)")
                
        except Exception as e:
            logger.error(f"Error placing market exit order for account {account_id}: {e}")

    def _modify_exit_order_to_market(self, account_id, existing_order):
        """Helper function to modify existing exit order to market price"""
        try:
            api = self.account_manager.get_api(account_id)
            if not api:
                logger.error(f"No API available for account {account_id}")
                return
            
            order_number = existing_order['order_number']
            symbol = existing_order.get('symbol')
            quantity = existing_order['quantity']
            
            # If symbol is not in existing order, get it from account state
            if not symbol:
                account_status = self.account_state_manager.get_account_status(account_id)
                if account_status and account_status.get('current_symbol'):
                    symbol = account_status['current_symbol']
                else:
                    logger.error(f"No symbol found for account {account_id}")
                    return
            
            logger.info(f"Modifying existing exit order {order_number} to market price for account {account_id}")
            
            # Determine exchange and product type based on symbol
            if 'SENSEX' in symbol:
                exchange = 'BFO'
                product_type = 'M'
            else:
                exchange = 'NFO'
                product_type = 'I'
            
            # Modify order to market price
            result = api.modify_order(
                orderno=order_number,
                exchange=exchange,
                tradingsymbol=symbol,
                newquantity=str(quantity),
                newprice_type='MKT',
                newprice='0',
                newtrigger_price='0',
                amo='NO'
            )
            
            # Log the broker response
            logger.info(f"Modify order response for account {account_id}: {result}")
            
            if result and result.get('stat') == 'Ok':
                logger.info(f"Successfully modified exit order to market for account {account_id}: {order_number}")
                
                # Update exit order info in CSV with new price type
                self.account_state_manager.update_exit_order_info(
                    account_id, 
                    order_number, 
                    'MKT',  # Changed to market order
                    0,      # Market orders have price 0
                    quantity
                )
                
                # Update order status display
                if account_id == 1:
                    self.master_order_status.set(f"Exit Order Modified to Market: {order_number}")
                elif account_id == 2:
                    self.child_order_status.set(f"Exit Order Modified to Market: {order_number}")
            else:
                # Log the rejection reason from broker
                if result:
                    error_msg = result.get('emsg', 'Unknown error')
                    logger.warning(f"Modify exit order rejected for account {account_id}: {error_msg}")
                    logger.info(f"Full modify rejection details: {result}")
                else:
                    logger.error(f"Modify exit order failed for account {account_id}: No response from broker")
                
                # Still update UI to show attempt was made
                if account_id == 1:
                    self.master_order_status.set("Exit Order Modify Attempted (Rejected)")
                elif account_id == 2:
                    self.child_order_status.set("Exit Order Modify Attempted (Rejected)")
                
        except Exception as e:
            logger.error(f"Error modifying exit order for account {account_id}: {e}")

    def exit_all_orders_market_silent(self):
        """Exit all orders at market price without confirmation popup (for SL/Target breaches) - PARALLEL EXECUTION"""
        try:
            logger.info("Executing silent market exit for SL/Target - PARALLEL MODE")
            
            # Get logged-in accounts (check login_status == 1)
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if self.account_state_manager.get_login_status(account_id) == 1:
                    active_accounts.append(account_id)
            
            if not active_accounts:
                logger.warning("No logged-in accounts available for silent market exit")
                return
            
            # Place market exit orders in parallel using threading
            self._place_market_exit_orders_parallel(active_accounts)
            
            logger.info(f"Silent market exit orders placed in parallel for {len(active_accounts)} account(s)")
            
        except Exception as e:
            logger.error(f"Error in silent market exit: {e}")
    
    def _place_market_exit_orders_parallel(self, active_accounts):
        """Place market exit orders in parallel using threading"""
        import threading
        
        def place_single_market_exit(account_id):
            """Place market exit order for single account"""
            try:
                logger.info(f"Placing parallel market exit for account {account_id}")
                self._place_market_exit_order(account_id)
            except Exception as e:
                logger.error(f"Error in parallel market exit for account {account_id}: {e}")
        
        # Create and start threads for each active account
        threads = []
        for account_id in active_accounts:
            thread = threading.Thread(target=place_single_market_exit, args=(account_id,))
            threads.append(thread)
            thread.start()
            logger.info(f"Started parallel exit thread for account {account_id}")
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info("All parallel market exit threads completed")
    
    def _place_exit_orders_parallel(self, active_accounts, account_data, price, order_type):
        """Place exit orders in parallel using threading"""
        import threading
        
        order_numbers = [None] * len(active_accounts)  # Initialize with None values
        
        def place_single_exit_order(account_id, index):
            """Place exit order for single account"""
            try:
                logger.info(f"Placing parallel exit order for account {account_id}")
                
                api = self.account_manager.get_api(account_id)
                if not api:
                    logger.error(f"No API available for account {account_id}")
                    return
                
                # Get account-specific data
                symbol = account_data[account_id]['symbol']
                quantity = account_data[account_id]['quantity']
                
                # Determine exchange and product type based on symbol
                if 'BFO' in symbol:
                    exchange = 'BFO'
                    product_type = 'M'
                else:
                    exchange = 'NFO'
                    product_type = 'I'
                
                # Place individual exit order directly
                result = api.place_order(
                    buy_or_sell='S',
                    product_type=product_type,
                    exchange=exchange,
                    tradingsymbol=symbol,
                    quantity=str(quantity),
                    discloseqty=0,
                    price_type=order_type,
                    price=str(price) if order_type == 'LMT' else '0',
                    trigger_price='0',
                    retention='DAY',
                    remarks='exit_order'
                )
                
                if result and result.get('stat') == 'Ok':
                    order_number = result.get('norenordno')
                    order_numbers[index] = order_number
                    logger.info(f"Exit order placed for account {account_id}: {order_number}")
                else:
                    logger.error(f"Exit order failed for account {account_id}: {result}")
                    
            except Exception as e:
                logger.error(f"Error in parallel exit order for account {account_id}: {e}")
        
        # Create and start threads for each active account
        threads = []
        for i, account_id in enumerate(active_accounts):
            thread = threading.Thread(target=place_single_exit_order, args=(account_id, i))
            threads.append(thread)
            thread.start()
            logger.info(f"Started parallel exit thread for account {account_id}")
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info("All parallel exit order threads completed")
        return order_numbers

    def _cancel_exit_orders_parallel(self, active_accounts, apis, order_numbers, active_flags):
        """Cancel exit orders in parallel using threading"""
        import threading
        
        cancelled_orders = [None] * len(active_accounts)
        
        def cancel_single_exit_order(account_id, index):
            """Cancel exit order for single account"""
            try:
                if index < len(apis) and index < len(order_numbers) and active_flags[index]:
                    api = apis[index]
                    order_number = order_numbers[index]
                    
                    # Cancel order directly
                    result = api.cancel_order(orderno=order_number)
                    
                    if result and result.get('stat') == 'Ok':
                        cancelled_orders[index] = order_number
                        logger.info(f"Exit order cancelled for account {account_id}: {order_number}")
                    else:
                        logger.error(f"Failed to cancel exit order for account {account_id}: {result}")
                        cancelled_orders[index] = None
                else:
                    logger.warning(f"Skipping cancel for account {account_id} - no valid API or order number")
                    cancelled_orders[index] = None
                    
            except Exception as e:
                logger.error(f"Error cancelling exit order for account {account_id}: {e}")
                cancelled_orders[index] = None
        
        # Create and start threads for each active account
        threads = []
        for i, account_id in enumerate(active_accounts):
            thread = threading.Thread(target=cancel_single_exit_order, args=(account_id, i))
            threads.append(thread)
            thread.start()
            logger.info(f"Started parallel cancel thread for account {account_id}")
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info("All parallel cancel threads completed")
        return cancelled_orders

    def _modify_exit_orders_parallel(self, active_accounts, account_data, price):
        """Modify exit orders in parallel using threading"""
        import threading
        
        modified_orders = [None] * len(active_accounts)
        
        def modify_single_exit_order(account_id, index):
            """Modify exit order for single account"""
            try:
                api = self.account_manager.get_api(account_id)
                if not api:
                    logger.error(f"No API available for account {account_id}")
                    modified_orders[index] = None
                    return
                
                # Get account-specific data
                symbol = account_data[account_id]['symbol']
                quantity = account_data[account_id]['quantity']
                order_number = self.exit_order_numbers[account_id]
                
                # Determine exchange and product type based on symbol
                if 'BFO' in symbol:
                    exchange = 'BFO'
                    product_type = 'M'
                else:
                    exchange = 'NFO'
                    product_type = 'I'
                
                # Modify individual exit order directly
                result = api.modify_order(
                    orderno=order_number,
                    newprice=str(price),
                    newqty=str(quantity),
                    newproducttype=product_type,
                    newordertype='LMT',
                    newtriggerprice='0'
                )
                
                if result and result.get('stat') == 'Ok':
                    modified_order = result.get('norenordno')
                    modified_orders[index] = modified_order
                    logger.info(f"Exit order modified for account {account_id}: {modified_order}")
                else:
                    logger.error(f"Failed to modify exit order for account {account_id}: {result}")
                    modified_orders[index] = None
                    
            except Exception as e:
                logger.error(f"Error modifying exit order for account {account_id}: {e}")
                modified_orders[index] = None
        
        # Create and start threads for each active account
        threads = []
        for i, account_id in enumerate(active_accounts):
            thread = threading.Thread(target=modify_single_exit_order, args=(account_id, i))
            threads.append(thread)
            thread.start()
            logger.info(f"Started parallel modify thread for account {account_id}")
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        logger.info("All parallel modify threads completed")
        return modified_orders

    def cancel_master_buy_order(self):
        """Cancel master buy order"""
        try:
            logger.info("Cancel master buy order clicked")
            
            # Check if master account can order
            can_order = self.account_state_manager.get_can_order(1)
            if can_order == 0:
                messagebox.showinfo("Order Already Cancelled", "Master order is already cancelled")
                return
            
            # Get master API and order info
            master_api = self.account_manager.get_api(1)
            if not master_api:
                messagebox.showerror("Error", "Master API not available")
                return
            
            # Get order ID from account state
            master_status = self.account_state_manager.get_account_status(1)
            if not master_status or not master_status.get('current_order_id'):
                messagebox.showwarning("No Order Found", "No master order found to cancel")
                return
            
            order_id = master_status['current_order_id']
            
            # Cancel the order
            success = self._cancel_single_order(1, master_api, order_id, "Master")
            
            if success:
                # Update can_order flag to 0
                self.account_state_manager.update_can_order(1, 0, "Order cancelled by user")
                
                # Update UI
                self.master_order_status.set("Master buy order cancelled by user")
                self.cancel_master_buy_button.config(state="disabled", text="Master Buy Cancelled")
                
                # Disable buy button until release
                self.buy_button.config(state="disabled", text="Press RELEASE to Enable")
                self.set_buy_price_box_state("disabled")  # Disable price box when buy button is disabled
                
                logger.info("Master buy order cancelled successfully")
            else:
                messagebox.showerror("Error", "Failed to cancel master buy order")
                
        except Exception as e:
            logger.error(f"Error cancelling master buy order: {e}")
            messagebox.showerror("Error", f"Error cancelling master buy order: {str(e)}")
        
    def cancel_child_buy_order(self):
        """Cancel child buy order"""
        try:
            logger.info("Cancel child buy order clicked")
            
            # Check if child account can order
            can_order = self.account_state_manager.get_can_order(2)
            if can_order == 0:
                messagebox.showinfo("Order Already Cancelled", "Child order is already cancelled")
                return
            
            # Get child API and order info
            child_api = self.account_manager.get_api(2)
            if not child_api:
                messagebox.showerror("Error", "Child API not available")
                return
            
            # Get order ID from account state
            child_status = self.account_state_manager.get_account_status(2)
            if not child_status or not child_status.get('current_order_id'):
                messagebox.showwarning("No Order Found", "No child order found to cancel")
                return
            
            order_id = child_status['current_order_id']
            
            # Cancel the order
            success = self._cancel_single_order(2, child_api, order_id, "Child")
            
            if success:
                # Update can_order flag to 0
                self.account_state_manager.update_can_order(2, 0, "Order cancelled by user")
                
                # Update UI
                self.child_order_status.set("Child buy order cancelled by user")
                self.cancel_child_buy_button.config(state="disabled", text="Child Buy Cancelled")
                
                # Disable buy button until release
                self.buy_button.config(state="disabled", text="Press RELEASE to Enable")
                self.set_buy_price_box_state("disabled")  # Disable price box when buy button is disabled
                
                logger.info("Child buy order cancelled successfully")
            else:
                messagebox.showerror("Error", "Failed to cancel child buy order")
                
        except Exception as e:
            logger.error(f"Error cancelling child buy order: {e}")
            messagebox.showerror("Error", f"Error cancelling child buy order: {str(e)}")
        
        
    def on_trail_type_changed(self, event=None):
        """Handle trail type dropdown selection change"""
        try:
            trail_type = self.trail_type_selected.get()
            
            # Clear current trail value when type changes
            self.trail_value.set("")
            
            # Update status message based on selected type
            if trail_type == "Point":
                self.trail_status_text.set("Point Trail Selected - Enter value and click Enable")
            elif trail_type == "Percent":
                self.trail_status_text.set("Percent Trail Selected - Enter value and click Enable")
            else:
                self.trail_status_text.set("Trailing Disabled")
            
            logger.info(f"Trail type changed to: {trail_type}")
            
        except Exception as e:
            logger.error(f"Error handling trail type change: {e}")
        
    def enable_trail(self):
        """Enable trailing stop with current settings"""
        try:
            trail_type = self.trail_type_selected.get()
            trail_value_text = self.trail_value.get().strip()
            
            # Validate inputs
            if not trail_type:
                messagebox.showerror("Error", "Please select a trail type (Point or Percent)")
                return
                
            if not trail_value_text:
                messagebox.showerror("Error", "Please enter a trail value")
                return
            
            trail_value = float(trail_value_text)
            
            # Validate based on trail type
            if trail_type == "Point":
                if trail_value <= 0:
                    messagebox.showerror("Error", "Point trail must be greater than 0")
                    return
            elif trail_type == "Percent":
                if trail_value <= 0 or trail_value >= 100:
                    messagebox.showerror("Error", "Percent trail must be between 0 and 100")
                    return
            
            # Determine reference price for calculation
            reference_price = None
            
            if self.trailing_active:
                # If trailing is already active, use current trailing high price
                reference_price = self.trailing_high_price
                logger.info(f"Editing trailing value - using current trailing high: {reference_price}")
            elif self.target_price_level:
                # If target is set but trailing not active, use target price
                reference_price = self.target_price_level
                logger.info(f"Setting up trailing - using target price: {reference_price}")
            else:
                # No reference price available
                messagebox.showerror("Error", "Please set a target price first before enabling trailing")
                return
            
            # Calculate what the trailing stop would be at reference price
            if trail_type == "Point":
                calculated_trailing_stop = reference_price - trail_value
            else:  # Percent
                calculated_trailing_stop = reference_price * (1 - trail_value / 100)
            
            # Check if trailing stop would be below SL price (if SL is set)
            if self.sl_price_level and calculated_trailing_stop < self.sl_price_level:
                messagebox.showerror("Error", 
                    f"Trailing stop price ({calculated_trailing_stop:.2f}) cannot be below SL price ({self.sl_price_level})\n"
                    f"Please reduce trail value or increase SL price")
                return
            
            # Enable trailing
            self.enable_trailing_value.set(True)
            
            if self.trailing_active:
                # Update existing trailing with new value
                self.trailing_stop_price = calculated_trailing_stop
                
                # Update status for both accounts
                self.master_order_status.set(f"TRAILING @ {self.trailing_high_price} (Stop: {self.trailing_stop_price:.2f})")
                self.child_order_status.set(f"TRAILING @ {self.trailing_high_price} (Stop: {self.trailing_stop_price:.2f})")
                
                # Update trail status
                self.trail_status_text.set(f"Trailing Active - Stop: {self.trailing_stop_price:.2f}")
                
                # Update real-time trailing stop display
                self.update_trailing_stop_display(self.trailing_high_price)
                
                logger.info(f"Trailing value updated - {trail_type} trail: {trail_value}, new stop: {self.trailing_stop_price:.2f}")
            else:
                # Initial setup - update status based on trail type
                if trail_type == "Point":
                    self.trail_status_text.set(f"Trailing Ready - Point Trail: {trail_value}")
                else:
                    self.trail_status_text.set(f"Trailing Ready - Percent Trail: {trail_value}%")
                
                logger.info(f"Trailing configured - {trail_type} trail: {trail_value} (Ready for target activation)")
            
            # Update button states
            self.update_trail_button_states()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid trail value")
        except Exception as e:
            logger.error(f"Error enabling trail: {e}")
            messagebox.showerror("Error", f"Error enabling trail: {e}")
        
    def disable_trail(self):
        """Disable trailing stop"""
        try:
            self.enable_trailing_value.set(False)
            self.trail_status_text.set("Trailing Disabled")
            
            # Stop any active trailing mode
            if self.trailing_active:
                self.trailing_active = False
                self.trailing_start_price = None
                self.trailing_high_price = None
                self.trailing_stop_price = None
                # Clear trailing stop display
                self.trailing_stop_display_label.config(text="")
                logger.info("Active trailing mode stopped")
            
            # Update button states
            self.update_trail_button_states()
            
            logger.info("Trailing disabled")
            
        except Exception as e:
            logger.error(f"Error disabling trail: {e}")
            messagebox.showerror("Error", f"Error disabling trail: {e}")
    
    def update_trail_button_states(self):
        """Update trail button states based on current trailing status"""
        try:
            logger.info(f"DEBUG: update_trail_button_states called - trailing_active={self.trailing_active}, enable_trailing_value={self.enable_trailing_value.get()}")
            
            if self.trailing_active:
                # Trailing is active - enable editing
                self.enable_trail_button.config(state="normal", bg="lightgreen", text="Update")
                self.disable_trail_button.config(state="normal", bg="lightcoral")
                logger.info("Button states: Trailing active - Enable button set to 'Update'")
            elif self.enable_trailing_value.get():
                # Trailing is enabled but not active yet - allow editing values
                self.enable_trail_button.config(state="normal", bg="lightgreen", text="Update")
                self.disable_trail_button.config(state="normal", bg="lightcoral")
                logger.info("Button states: Trailing enabled but not active - Enable button set to 'Update' for editing")
            else:
                # Trailing not enabled - check if target is set
                if self.target_price_level:
                    # Target is set but trailing not enabled - ready to enable
                    self.enable_trail_button.config(state="normal", bg="lightgreen", text="Enable")
                    self.disable_trail_button.config(state="disabled", bg="gray")
                    logger.info("Button states: Target set, trailing not enabled - Enable button ready")
                else:
                    # No target set - can't enable trailing
                    self.enable_trail_button.config(state="disabled", bg="gray", text="Enable")
                    self.disable_trail_button.config(state="disabled", bg="gray")
                    logger.info("Button states: No target set - Enable button disabled")
        except Exception as e:
            logger.error(f"Error updating trail button states: {e}")
    
    def start_trailing_mode(self, current_price):
        """Start trailing mode when target is reached"""
        try:
            # Stop target monitoring (we're now in trailing mode)
            self.stop_target_monitoring()
            
            # Set up trailing variables
            self.trailing_active = True
            self.trailing_start_price = current_price
            self.trailing_high_price = current_price
            
            # Calculate initial trailing stop based on trail type
            trail_type = self.trail_type_selected.get()
            trail_value = float(self.trail_value.get())
            
            if trail_type == "Point":
                self.trailing_stop_price = current_price - trail_value
            else:  # Percent
                self.trailing_stop_price = current_price * (1 - trail_value / 100)
            
            # Update status for both accounts
            self.master_order_status.set(f"TRAILING ACTIVE @ {current_price} (Stop: {self.trailing_stop_price:.2f})")
            self.child_order_status.set(f"TRAILING ACTIVE @ {current_price} (Stop: {self.trailing_stop_price:.2f})")
            
            # Update trail status
            self.trail_status_text.set(f"Trailing Active - Stop: {self.trailing_stop_price:.2f}")
            
            # Update real-time trailing stop display
            self.update_trailing_stop_display(current_price)
            
            # Update button states for editing capability
            self.update_trail_button_states()
            
            logger.info(f"Trailing mode started at {current_price}, initial stop: {self.trailing_stop_price:.2f}")
            logger.info(f"Button states updated - Enable button should now show 'Update' and be enabled")
            
        except Exception as e:
            logger.error(f"Error starting trailing mode: {e}")
    
    def check_trailing_stop(self, current_price):
        """Check if trailing stop should be triggered or updated"""
        try:
            if not self.trailing_active:
                return
                
            current_price_float = float(current_price)
            
            # Update trailing high if price moved up
            if current_price_float > self.trailing_high_price:
                self.trailing_high_price = current_price_float
                
                # Update trailing stop
                trail_type = self.trail_type_selected.get()
                trail_value = float(self.trail_value.get())
                
                if trail_type == "Point":
                    new_trailing_stop = current_price_float - trail_value
                else:  # Percent
                    new_trailing_stop = current_price_float * (1 - trail_value / 100)
                
                # Only update if new stop is higher (never move stop down)
                if new_trailing_stop > self.trailing_stop_price:
                    self.trailing_stop_price = new_trailing_stop
                    
                    # Update status for both accounts
                    self.master_order_status.set(f"TRAILING @ {current_price_float} (Stop: {self.trailing_stop_price:.2f})")
                    self.child_order_status.set(f"TRAILING @ {current_price_float} (Stop: {self.trailing_stop_price:.2f})")
                    
                    # Update trail status
                    self.trail_status_text.set(f"Trailing Active - Stop: {self.trailing_stop_price:.2f}")
                    
                    # Update real-time trailing stop display
                    self.update_trailing_stop_display(current_price_float)
                    
                    logger.info(f"Trailing stop updated to {self.trailing_stop_price:.2f} (High: {self.trailing_high_price:.2f})")
            
            # Check if trailing stop is hit
            elif current_price_float <= self.trailing_stop_price:
                # Stop trailing immediately to prevent duplicate triggers
                self.trailing_active = False
                logger.warning(f"TRAILING STOP HIT! Current: {current_price_float}, Stop: {self.trailing_stop_price:.2f}")
                self.execute_trailing_stop_exit(current_price_float)
                
        except Exception as e:
            logger.error(f"Error checking trailing stop: {e}")
    
    def execute_trailing_stop_exit(self, current_price):
        """Execute market order exit when trailing stop is hit"""
        try:
            logger.info(f"Executing trailing stop exit at {current_price}")
            
            # Stop trailing
            self.trailing_active = False
            self.trailing_start_price = None
            self.trailing_high_price = None
            self.trailing_stop_price = None
            
            # Update status for both accounts
            self.master_order_status.set(f"TRAILING STOP HIT @ {current_price}")
            self.child_order_status.set(f"TRAILING STOP HIT @ {current_price}")
            
            # Update trail status
            self.trail_status_text.set(f"Trailing Stop Hit @ {current_price}")
            
            # Clear trailing stop display
            self.trailing_stop_display_label.config(text="")
            
            # Execute market orders for both accounts
            self._execute_trailing_market_orders(current_price)
            
        except Exception as e:
            logger.error(f"Error executing trailing stop exit: {e}")
    
    def _execute_trailing_market_orders(self, current_price):
        """Execute market orders for trailing stop exit"""
        try:
            logger.info("Executing trailing stop market exit orders")
            
            # Get active accounts that can place orders
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_order(account_id) == 1):
                    active_accounts.append(account_id)
            
            if not active_accounts:
                logger.warning("No active accounts available for trailing stop exit")
                return
            
            # Place market exit orders in parallel using threading
            self._place_market_exit_orders_parallel(active_accounts)
            
            logger.info(f"Trailing stop market exit orders placed in parallel for {len(active_accounts)} account(s)")
            
        except Exception as e:
            logger.error(f"Error executing trailing stop market orders: {e}")
    
    def update_trailing_stop_display(self, current_price):
        """Update real-time trailing stop display"""
        try:
            if self.trailing_active and self.trailing_stop_price:
                display_text = f"Trailing Stop: {self.trailing_stop_price:.2f} | High: {self.trailing_high_price:.2f}"
                self.trailing_stop_display_label.config(text=display_text)
            else:
                self.trailing_stop_display_label.config(text="")
        except Exception as e:
            logger.error(f"Error updating trailing stop display: {e}")
    
    def stop_trailing_monitoring(self):
        """Stop trailing monitoring"""
        try:
            self.trailing_active = False
            self.trailing_start_price = None
            self.trailing_high_price = None
            self.trailing_stop_price = None
            
            # Clear trail status display
            self.trail_status_text.set("Trailing Inactive")
            
            # Clear trailing stop display
            self.trailing_stop_display_label.config(text="")
            
            logger.info("Trailing monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trailing monitoring: {e}")
        
    def cancel_buy_orders(self):
        """Cancel buy orders for both Master and Child accounts in parallel"""
        try:
            logger.info("Cancel buy orders clicked")
            
            # Check can_order flags for both accounts
            master_can_order = self.account_state_manager.get_can_order(1)
            child_can_order = self.account_state_manager.get_can_order(2)
            
            # If both accounts have can_order=0, show message
            if master_can_order == 0 and child_can_order == 0:
                messagebox.showinfo("Orders Already Cancelled", "All orders are already cancelled")
                return
            
            # Prepare cancellation tasks
            cancellation_tasks = []
            
            # Prepare Master order cancellation if can_order=1
            if master_can_order == 1:
                master_api = self.account_manager.get_api(1)
                if master_api:
                    master_status = self.account_state_manager.get_account_status(1)
                    if master_status and master_status.get('current_order_id'):
                        order_id = master_status['current_order_id']
                        cancellation_tasks.append({
                            'account_id': 1,
                            'api': master_api,
                            'order_id': order_id,
                            'account_name': 'Master'
                        })
            
            # Prepare Child order cancellation if can_order=1
            if child_can_order == 1:
                child_api = self.account_manager.get_api(2)
                if child_api:
                    child_status = self.account_state_manager.get_account_status(2)
                    if child_status and child_status.get('current_order_id'):
                        order_id = child_status['current_order_id']
                        cancellation_tasks.append({
                            'account_id': 2,
                            'api': child_api,
                            'order_id': order_id,
                            'account_name': 'Child'
                        })
            
            if not cancellation_tasks:
                messagebox.showwarning("No Orders", "No valid orders found to cancel")
                return
            
            # Execute cancellations in parallel using threading
            results = self._cancel_orders_parallel(cancellation_tasks)
            
            # Process results
            cancelled_any = False
            cancelled_master = False
            cancelled_child = False
            
            for result in results:
                if result['success']:
                    cancelled_any = True
                    if result['account_id'] == 1:
                        cancelled_master = True
                        self.master_order_status.set("Master buy order cancelled by user")
                    elif result['account_id'] == 2:
                        cancelled_child = True
                        self.child_order_status.set("Child buy order cancelled by user")
            
            # Update UI based on what was cancelled
            if cancelled_any:
                # Disable all cancel buttons
                self.cancel_buy_button.config(state="disabled", text="Buy Orders Cancelled")
                self.cancel_master_buy_button.config(state="disabled")
                self.cancel_child_buy_button.config(state="disabled")
                
                # Disable buy button until release
                self.buy_button.config(state="disabled", text="Press RELEASE to Enable")
                self.set_buy_price_box_state("disabled")  # Disable price box when buy button is disabled
                
                # Success - orders cancelled (no popup needed)
            else:
                messagebox.showwarning("No Orders", "No orders were successfully cancelled")
                
        except Exception as e:
            logger.error(f"Error cancelling buy orders: {e}")
            messagebox.showerror("Error", f"Error cancelling buy orders: {str(e)}")
    
    def _cancel_single_order(self, account_id: int, api, order_id: str, account_name: str) -> bool:
        """Helper method to cancel a single order via API"""
        try:
            logger.info(f"Cancelling {account_name} order: {order_id}")
            
            # Call the API to cancel the order
            cancel_response = api.cancel_order(orderno=order_id)
            
            # Check if cancellation was successful
            if cancel_response and cancel_response.get('stat') == 'Ok':
                logger.info(f"Successfully cancelled {account_name} order: {order_id}")
                return True
            else:
                logger.error(f"Failed to cancel {account_name} order {order_id}: {cancel_response}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling {account_name} order {order_id}: {e}")
            return False
    
    def _cancel_orders_parallel(self, cancellation_tasks):
        """Cancel multiple orders in parallel using threading"""
        results = []
        threads = []
        
        def cancel_order_thread(task):
            """Thread function to cancel a single order"""
            try:
                account_id = task['account_id']
                api = task['api']
                order_id = task['order_id']
                account_name = task['account_name']
                
                # Cancel the order
                success = self._cancel_single_order(account_id, api, order_id, account_name)
                
                if success:
                    # Update can_order flag to 0
                    self.account_state_manager.update_can_order(account_id, 0, "Order cancelled by user")
                    logger.info(f"{account_name} buy order cancelled successfully")
                
                # Store result
                results.append({
                    'account_id': account_id,
                    'account_name': account_name,
                    'success': success,
                    'order_id': order_id
                })
                
            except Exception as e:
                logger.error(f"Error in cancellation thread for {task['account_name']}: {e}")
                results.append({
                    'account_id': task['account_id'],
                    'account_name': task['account_name'],
                    'success': False,
                    'order_id': task['order_id'],
                    'error': str(e)
                })
        
        # Start threads for each cancellation task
        for task in cancellation_tasks:
            thread = threading.Thread(target=cancel_order_thread, args=(task,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return results
    
    def _modify_single_order(self, account_id: int, api, order_id: str, symbol: str, quantity: int, new_price: float, account_name: str) -> bool:
        """Helper method to modify a single order via API"""
        try:
            logger.info(f"Modifying {account_name} order: {order_id} to price: {new_price}")
            
            # Determine exchange based on symbol
            if 'SENSEX' in symbol:
                exchange = 'BFO'
            else:
                exchange = 'NFO'
            
            # Call the API to modify the order
            modify_response = api.modify_order(
                exchange=exchange,
                tradingsymbol=symbol,
                orderno=order_id,
                newquantity=int(quantity),
                newprice_type='LMT',
                newprice=new_price
            )
            
            # Check if modification was successful
            if modify_response and modify_response.get('stat') == 'Ok':
                logger.info(f"Successfully modified {account_name} order: {order_id}")
                return True
            else:
                logger.error(f"Failed to modify {account_name} order {order_id}: {modify_response}")
                return False
                
        except Exception as e:
            logger.error(f"Error modifying {account_name} order {order_id}: {e}")
            return False
    
    def _modify_orders_parallel(self, modification_tasks, new_price):
        """Modify multiple orders in parallel using threading"""
        results = []
        threads = []
        
        def modify_order_thread(task):
            """Thread function to modify a single order"""
            try:
                account_id = task['account_id']
                api = task['api']
                order_id = task['order_id']
                symbol = task['symbol']
                quantity = task['quantity']
                account_name = task['account_name']
                
                # Modify the order
                success = self._modify_single_order(account_id, api, order_id, symbol, quantity, new_price, account_name)
                
                if success:
                    # Update account state with new price
                    self.account_state_manager.update_order_info(
                        account_id, order_id, symbol, int(quantity), new_price
                    )
                    logger.info(f"{account_name} buy order modified successfully")
                
                # Store result
                results.append({
                    'account_id': account_id,
                    'account_name': account_name,
                    'success': success,
                    'order_id': order_id,
                    'new_price': new_price
                })
                
            except Exception as e:
                logger.error(f"Error in modification thread for {task['account_name']}: {e}")
                results.append({
                    'account_id': task['account_id'],
                    'account_name': task['account_name'],
                    'success': False,
                    'order_id': task['order_id'],
                    'new_price': new_price,
                    'error': str(e)
                })
        
        # Start threads for each modification task
        for task in modification_tasks:
            thread = threading.Thread(target=modify_order_thread, args=(task,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return results
        
    def modify_buy_orders(self):
        """Modify buy orders for both Master and Child accounts in parallel with coordination"""
        try:
            logger.info("Modify buy orders clicked")
            
            # 1. Validate inputs
            if not self.modify_buy_value.get().strip():
                messagebox.showerror("Error", "Please enter a price in the modify buy box")
                return
            
            # Validate the price
            try:
                new_price = float(self.modify_buy_value.get())
                if new_price <= 0:
                    messagebox.showerror("Error", "Price must be greater than 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid price")
                return
            
            # Check if we have current trading symbol
            if not self.current_trading_symbol:
                messagebox.showerror("Error", "No trading symbol found. Please place buy orders first.")
                return
            
            # 2. Check can_order flags for both accounts
            master_can_order = self.account_state_manager.get_can_order(1)
            child_can_order = self.account_state_manager.get_can_order(2)
            
            # If both accounts have can_order=0, show message
            if master_can_order == 0 and child_can_order == 0:
                messagebox.showinfo("Orders Already Cancelled", "All orders are already cancelled")
                return
            
            # 3. Prepare modification tasks
            modification_tasks = []
            
            # Prepare Master order modification if can_order=1
            if master_can_order == 1:
                master_api = self.account_manager.get_api(1)
                if master_api:
                    master_status = self.account_state_manager.get_account_status(1)
                    if master_status and master_status.get('current_order_id'):
                        modification_tasks.append({
                            'account_id': 1,
                            'api': master_api,
                            'order_id': master_status['current_order_id'],
                            'symbol': master_status['current_symbol'],
                            'quantity': master_status['current_quantity'],
                            'account_name': 'Master'
                        })
            
            # Prepare Child order modification if can_order=1
            if child_can_order == 1:
                child_api = self.account_manager.get_api(2)
                if child_api:
                    child_status = self.account_state_manager.get_account_status(2)
                    if child_status and child_status.get('current_order_id'):
                        modification_tasks.append({
                            'account_id': 2,
                            'api': child_api,
                            'order_id': child_status['current_order_id'],
                            'symbol': child_status['current_symbol'],
                            'quantity': child_status['current_quantity'],
                            'account_name': 'Child'
                        })
            
            if not modification_tasks:
                messagebox.showwarning("No Orders", "No valid orders found to modify")
                return
            
            # 4. Reset order states for coordination
            self.order_states = {1: "PENDING", 2: "PENDING"}
            logger.info("Order states reset for modify operations")
            
            # 5. Execute modifications in parallel using threading
            results = self._modify_orders_parallel(modification_tasks, new_price)
            
            # 6. Process results
            modified_any = False
            modified_master = False
            modified_child = False
            
            for result in results:
                if result['success']:
                    modified_any = True
                    if result['account_id'] == 1:
                        modified_master = True
                        self.master_order_status.set("Master buy order modified by user")
                    elif result['account_id'] == 2:
                        modified_child = True
                        self.child_order_status.set("Child buy order modified by user")
            
            # 7. Update UI based on what was modified
            if modified_any:
                # Keep modify button enabled for further modifications
                self.modify_buy_button.config(text="Modify Buy")
                
                # Adjust SL/Target prices based on new buy price
                self._adjust_sl_target_for_modified_price(new_price)
                
                # Success - orders modified (no popup needed)
            else:
                messagebox.showwarning("No Orders", "No orders were successfully modified")
                
        except Exception as e:
            logger.error(f"Error modifying buy orders: {e}")
            messagebox.showerror("Error", f"Error modifying buy orders: {str(e)}")
    
    def _adjust_sl_target_for_modified_price(self, new_buy_price):
        """Adjust SL/Target prices when buy order price is modified"""
        try:
            # Initialize sl_target_states if it doesn't exist
            if not hasattr(self, 'sl_target_states'):
                self.sl_target_states = {}
            
            # Check if either SL or Target were previously calculated
            sl_calculated = self.sl_target_states.get('sl_calculated', False)
            target_calculated = self.sl_target_states.get('target_calculated', False)
            
            if not (sl_calculated or target_calculated):
                logger.info("Neither SL nor Target calculated yet, skipping adjustment")
                return
            
            # Get current points difference
            sl_points = self.sl_target_states.get('sl_points', 0)
            target_points = self.sl_target_states.get('target_points', 0)
            
            # Calculate new prices maintaining the same points difference
            new_sl_price = None
            new_target_price = None
            
            if sl_calculated:
                new_sl_price = max(0, new_buy_price - sl_points)  # Ensure SL never goes below 0
                # Check if SL was capped at 0
                if new_buy_price - sl_points < 0:
                    logger.warning(f"SL capped at 0 due to low modified buy price. Buy: {new_buy_price}, SL points: {sl_points}")
            
            if target_calculated:
                new_target_price = new_buy_price + target_points
            
            # Update state
            state_update = {'buy_price': new_buy_price}
            if new_sl_price is not None:
                state_update['sl_price'] = new_sl_price
            if new_target_price is not None:
                state_update['target_price'] = new_target_price
            
            self.sl_target_states.update(state_update)
            
            # Update UI display and button text
            if new_sl_price is not None:
                self.sl_price_value.set(f"{new_sl_price:.2f}")
                self.sl_price_button.config(text=f"SL Set @{new_sl_price:.2f}")
            
            if new_target_price is not None:
                self.target_price_value.set(f"{new_target_price:.2f}")
                self.target_price_button.config(text=f"Target Set @{new_target_price:.2f}")
            
            # Log the adjustment
            adjustment_parts = []
            if new_sl_price is not None:
                adjustment_parts.append(f"SL: {new_sl_price}")
            if new_target_price is not None:
                adjustment_parts.append(f"Target: {new_target_price}")
            
            logger.info(f"SL/Target adjusted for new buy price - {', '.join(adjustment_parts)} (Buy: {new_buy_price})")
            
        except Exception as e:
            logger.error(f"Error adjusting SL/Target for modified price: {e}")
        
    def cancel_exit_orders(self):
        """Cancel exit orders - TO BE IMPLEMENTED"""
        logger.info("Cancel exit orders clicked - Function not implemented yet")
        
    def modify_exit_orders(self):
        """Modify exit orders - TO BE IMPLEMENTED"""
        logger.info("Modify exit orders clicked - Function not implemented yet")
        
        
    def logout_child_account(self):
        """Logout child account - TO BE IMPLEMENTED"""
        logger.info("Logout child account clicked - Function not implemented yet")
        
    def open_configuration(self):
        """Open configuration window"""
        try:
            config_window = ConfigWindow(self.root, self.config_manager)
            config_window.open()
        except Exception as e:
            logger.error(f"Error opening configuration window: {e}")
            messagebox.showerror("Error", f"Failed to open configuration window: {e}")
        
    
    def run(self):
        """Start the application"""
        logger.info("Starting Master-Child Trading GUI - Original UI Layout")
        
        
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()

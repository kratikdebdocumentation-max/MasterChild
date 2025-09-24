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

class MainWindow:
    """Main application window - Recreated with original UI layout"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("***Kratik's Soft*** - Master Account Not Logged In")
        self.root.geometry("900x490")
        
        # Center the window on screen
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
        
        # Auto-login master account
        self.auto_login_master()
        
        # Initialize quantity dropdown with default values
        self.update_quantity_dropdown()
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
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
            sl_points = self.config_manager.get_setting('default_auto_sl', 20)
            target_points = self.config_manager.get_setting('default_auto_target', 30)
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
        
        # Quantity selection (moved to left)
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
        
        # Cancel Buy and Modify Buy (left side)
        self.cancel_buy_button = tk.Button(
            self.order_frame, text="Cancel Buy", 
            command=self.cancel_buy_orders, width=15, height=2,
            state="disabled"
        )
        self.cancel_buy_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Modify Buy box first, then button
        self.modify_buy_box = tk.Entry(
            self.order_frame, textvariable=self.modify_buy_value, width=10
        )
        self.modify_buy_box.grid(row=0, column=1, padx=5, pady=5)
        
        self.modify_buy_button = tk.Button(
            self.order_frame, text="Modify Buy", 
            command=self.modify_buy_orders, width=15, height=2,
            state="disabled"
        )
        self.modify_buy_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Cancel Exit and Modify Exit (right side)
        self.cancel_exit_button = tk.Button(
            self.order_frame, text="Cancel Exit", 
            command=self.cancel_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.cancel_exit_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Modify Exit box first, then button
        self.modify_exit_box = tk.Entry(
            self.order_frame, textvariable=self.modify_exit_value, width=10
        )
        self.modify_exit_box.grid(row=0, column=4, padx=5, pady=5)
        
        self.modify_exit_button = tk.Button(
            self.order_frame, text="Modify Exit", 
            command=self.modify_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.modify_exit_button.grid(row=0, column=5, padx=5, pady=5)

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
            command=self.logout_child_account, width=25, height=2
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
    
    def update_live_price(self, live_price: float):
        """Update live price display and buy price box (first time only)"""
        try:
            # Always update Premium Price box (live updates)
            self.premium_price_value.set(f"{live_price:.2f}")
            
            # Update Buy Price box ONLY if it's empty (first time only)
            if not self.price_value.get().strip():
                self.price_value.set(f"{live_price:.2f}")
                logger.info(f"Initial buy price set: {live_price:.2f}")
            
            # Check SL/Target breaches if monitoring is active
            self.check_sl_target_breach(live_price)
            
            # Check trailing stop updates
            self.check_trailing_stop(live_price)
            
            logger.info(f"Live price updated: {live_price:.2f}")
        except Exception as e:
            logger.error(f"Error updating live price: {e}")
    
    def check_sl_target_breach(self, live_price: float):
        """Check for SL/Target breaches - from old project"""
        try:
            
            # Check SL breach
            if self.sl_monitoring_active and self.sl_price_level is not None:
                if live_price <= self.sl_price_level:
                    logger.info(f"SL BREACH DETECTED! Current price: {live_price}, SL: {self.sl_price_level}")
                    self._trigger_sl_breach(live_price)
            
            # Check Target breach
            if self.target_monitoring_active and self.target_price_level is not None:
                if live_price >= self.target_price_level:
                    logger.info(f"TARGET HIT! Current price: {live_price}, Target: {self.target_price_level}")
                    self._trigger_target_breach(live_price)
                    
        except Exception as e:
            logger.error(f"Error checking SL/Target breaches: {e}")
    
    def _trigger_sl_breach(self, current_price: float):
        """Handle SL breach - place exit orders - from old project"""
        try:
            logger.info(f"SL BREACH DETECTED! Current price: {current_price}, SL: {self.sl_price_level}")
            
            # Stop SL monitoring
            self.stop_sl_monitoring()
            
            # Update UI to show breach
            self.sl_price_button.config(text=f"SL TRIGGERED @{current_price:.2f}", bg="red", fg="white")
            
            # Place exit orders (placeholder for now)
            self._place_exit_orders_for_breach("SL", current_price)
            
            logger.info("SL breach handled - exit orders placed")
            
        except Exception as e:
            logger.error(f"Error handling SL breach: {e}")
    
    def _trigger_target_breach(self, current_price: float):
        """Handle Target breach - start trailing if enabled, otherwise exit"""
        try:
            logger.info(f"TARGET HIT! Current price: {current_price}, Target: {self.target_price_level}")
            
            # Update UI to show target hit
            self.target_price_button.config(text=f"TARGET HIT @{current_price:.2f}", bg="green", fg="white")
            
            # Check if trailing is enabled
            if self.enable_trailing_value.get():
                # Start trailing instead of exiting
                logger.info("Trailing is enabled - starting trailing mode")
                self.start_trailing_mode(current_price)
                logger.info("Target breach handled - trailing mode started (no exit orders)")
            else:
                # Stop Target monitoring and exit
                self.stop_target_monitoring()
                self._place_exit_orders_for_breach("TARGET", current_price)
                logger.info("Target breach handled - exit orders placed")
            
        except Exception as e:
            logger.error(f"Error handling Target breach: {e}")
    
    def _place_exit_orders_for_breach(self, breach_type: str, current_price: float):
        """Place exit orders when SL or Target is breached - PARALLEL EXECUTION"""
        try:
            logger.info(f"Placing exit orders for {breach_type} breach at price {current_price} - PARALLEL MODE")
            
            # Get active accounts that have positions to exit
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_exit(account_id) == 1):
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
    
    def update_order_status(self, account_num: int, status_message: str):
        """Update order status display and handle order state changes"""
        try:
            # Update UI display
            if account_num == 1:
                self.master_order_status.set(status_message)
            elif account_num == 2:
                self.child_order_status.set(status_message)
            
            # Extract order status from message for state tracking
            status = self._extract_order_status(status_message)
            if status:
                self._on_order_status_update(account_num, status)
            
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
                    
                    # Check positions after successful login
                    self.root.after(1000, self.check_startup_positions)  # Delay to ensure UI is ready
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
                            
                            # Check positions after successful login (if master is also logged in)
                            if self.account_manager.is_account_active(1):  # Only check if master is also active
                                self.root.after(1000, self.check_startup_positions)  # Delay to ensure UI is ready
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
        
    def release_buttons(self):
        """Release button states - enable buy and sell order buttons"""
        try:
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
            # Clear order information for Master account
            self.account_state_manager.update_order_info(1, '', '', 0, 0.0)
            self.account_state_manager.clear_exit_order_info(1)
            logger.info("Order information and exit order info cleared for Master account")
            
            # Clear order information for Child account
            self.account_state_manager.update_order_info(2, '', '', 0, 0.0)
            self.account_state_manager.clear_exit_order_info(2)
            logger.info("Order information and exit order info cleared for Child account")
            
        except Exception as e:
            logger.error(f"Error clearing order information: {e}")
            raise
    
    def _reset_ui_state(self):
        """Reset UI state - enable buttons and clear form fields"""
        try:
            # Enable buy button
            self.buy_button.config(state='normal', text="BUY")
            
            # Re-enable price box for new orders
            self.price_box.config(state='normal', bg='white')
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            logger.info("BUY button and Price box re-enabled for new orders")
            
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
            
            logger.info("Management buttons disabled until new orders are placed")
            
        except Exception as e:
            logger.error(f"Error resetting UI state: {e}")
            raise
    
    def _reset_sl_target_controls(self):
        """Reset SL/Target controls to initial state"""
        try:
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
            
            # Disable controls
            self.sl_price_box.config(state="disabled")
            self.target_price_box.config(state="disabled")
            self.sl_price_button.config(state="disabled", text="SL Price")
            self.target_price_button.config(state="disabled", text="Target Price")
            
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
            self.enable_trail_button.config(state="normal", bg="lightgreen")
            self.disable_trail_button.config(state="disabled", bg="gray")
            
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
        """Verify PnL from broker - TO BE IMPLEMENTED"""
        logger.info("Verify PnL from broker clicked - Function not implemented yet")
        
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
        """Update strike dropdown based on selected index and price"""
        try:
            selected_index = self.selected_index.get()
            if selected_index:
                current_price = self.index_manager.get_index_price(selected_index)
                if current_price > 0:
                    strikes = self.index_manager.get_strike_list(selected_index, current_price)
                    self.strike_dropdown['values'] = strikes
                    # Don't auto-select any strike - let user choose from dropdown
                    logger.info(f"Strike dropdown populated with {len(strikes)} strikes for {selected_index}")
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
            
            # Clear order information for both accounts on startup
            self.account_state_manager.update_order_info(1, '', '', 0, 0.0)
            self.account_state_manager.update_order_info(2, '', '', 0, 0.0)
            logger.info("Order information cleared on startup for both accounts")
            
            logger.info("Account states reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting account states: {e}")
    
    def check_startup_positions(self):
        """Check for open positions on startup and warn user"""
        try:
            # Check positions for all logged-in accounts
            has_open_positions, all_positions, summary = self.account_manager.check_all_positions()
            
            if has_open_positions:
                # Build detailed warning message
                warning_msg = "⚠️ OPEN POSITIONS DETECTED ⚠️\n\n"
                warning_msg += f"{summary}\n\n"
                warning_msg += "POSITION DETAILS:\n"
                warning_msg += "─" * 50 + "\n"
                
                for account_num, account_data in all_positions.items():
                    if account_data['count'] > 0:
                        client_name = account_data['client_name']
                        warning_msg += f"\n🔸 {client_name}:\n"
                        
                        for i, position in enumerate(account_data['positions'], 1):
                            symbol = position.get('tsym', 'Unknown')
                            net_qty = position.get('netqty', '0')
                            exchange = position.get('exch', 'Unknown')
                            avg_price = position.get('netavgprc', '0')
                            
                            warning_msg += f"   {i}. {symbol} ({exchange})\n"
                            warning_msg += f"      Qty: {net_qty}, Avg Price: ₹{avg_price}\n"
                
                warning_msg += "\n" + "─" * 50 + "\n"
                warning_msg += "❗ IMPORTANT: Please close all existing positions\n"
                warning_msg += "before placing new orders to avoid conflicts.\n\n"
                warning_msg += "Would you like to continue anyway?"
                
                # Show warning dialog with Yes/No options
                result = messagebox.askyesno(
                    "Open Positions Warning", 
                    warning_msg,
                    icon='warning'
                )
                
                if result:
                    logger.warning("User chose to continue despite open positions")
                    messagebox.showinfo("Reminder", "Please remember to close existing positions before placing new orders.")
                else:
                    logger.info("User chose to exit due to open positions")
                    messagebox.showinfo("Exiting", "Please close existing positions and restart the application.")
                    self.root.quit()
                    return
            else:
                logger.info("Position check completed - No open positions found")
                
        except Exception as e:
            logger.error(f"Error checking startup positions: {e}")
            messagebox.showwarning("Position Check Error", 
                                 f"Could not check positions on startup: {str(e)}\n\n"
                                 "Please manually verify that you have no open positions before trading.")
        
    def on_expiry_selected(self, *args):
        """On expiry selected - TO BE IMPLEMENTED"""
        logger.info("On expiry selected called - Function not implemented yet")
        
    def on_option_selected(self, *args):
        """On option selected - TO BE IMPLEMENTED"""
        logger.info("On option selected called - Function not implemented yet")
        
    def on_strike_selected(self, *args):
        """Handle strike selection - automatically subscribe and fetch price"""
        try:
            strike = self.selected_strike.get()
            index = self.selected_index.get()
            option = self.selected_option.get()
            expiry = self.expiry_value.get()
            
            # Only proceed if all required fields are selected
            if all([index, expiry, strike, option]):
                # Clear Buy Price box for new symbol selection
                self.price_value.set("")
                logger.info("Buy price box cleared for new symbol selection")
                
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
            
            # 5. Place orders in parallel
            self._place_orders_parallel(active_accounts, trading_symbol, price, master_quantity, index)
            
            # 6. Auto-set SL and Target based on buy order price
            self.auto_set_sl_target_from_buy_price(price)
            
            # 7. Disable buy button with price display and enable management buttons
            self.buy_button.config(state="disabled", text=f"Buy @{price}")
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
            master_can_exit = self.account_state_manager.get_can_exit(1)
            child_can_exit = self.account_state_manager.get_can_exit(2)
            
            logger.info(f"Buy orders filled check - Master: filled_qty={master_filled_qty}, can_exit={master_can_exit}")
            logger.info(f"Buy orders filled check - Child: filled_qty={child_filled_qty}, can_exit={child_can_exit}")
            
            # Only return True if at least one account has actual filled positions
            has_filled_positions = (master_filled_qty > 0 and master_can_exit == 1) or (child_filled_qty > 0 and child_can_exit == 1)
            
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
            self.sl_price_button.config(text=f"SL Set @{new_sl_price}", bg="orange", fg="white")
            
            # Update sl_target_states with new SL points for proper distance maintenance during buy order modification
            if hasattr(self, 'current_buy_order_open_value') and self.current_buy_order_open_value:
                # Calculate new SL points based on manual SL price
                new_sl_points = self.current_buy_order_open_value - new_sl_price
                
                # Update sl_target_states to maintain this distance during future buy order modifications
                if not hasattr(self, 'sl_target_states'):
                    self.sl_target_states = {}
                
                self.sl_target_states.update({
                    'sl_calculated': True,
                    'sl_price': new_sl_price,
                    'sl_points': new_sl_points,
                    'buy_price': self.current_buy_order_open_value
                })
                
                logger.info(f"Manual SL set - Price: {new_sl_price}, Points from buy: {new_sl_points}, Buy price: {self.current_buy_order_open_value}")
            else:
                logger.warning("No current buy price available - SL points cannot be calculated for distance maintenance")
            
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
            self.target_price_button.config(text=f"Target Set @{new_target_price}", bg="orange", fg="white")
            
            # Update sl_target_states with new Target points for proper distance maintenance during buy order modification
            if hasattr(self, 'current_buy_order_open_value') and self.current_buy_order_open_value:
                # Calculate new Target points based on manual Target price
                new_target_points = new_target_price - self.current_buy_order_open_value
                
                # Update sl_target_states to maintain this distance during future buy order modifications
                if not hasattr(self, 'sl_target_states'):
                    self.sl_target_states = {}
                
                self.sl_target_states.update({
                    'target_calculated': True,
                    'target_price': new_target_price,
                    'target_points': new_target_points,
                    'buy_price': self.current_buy_order_open_value
                })
                
                logger.info(f"Manual Target set - Price: {new_target_price}, Points from buy: {new_target_points}, Buy price: {self.current_buy_order_open_value}")
            else:
                logger.warning("No current buy price available - Target points cannot be calculated for distance maintenance")
            
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
    
    def _on_order_status_update(self, account_id: int, status: str):
        """Handle order status updates from websocket"""
        try:
            # Update order state
            self.order_states[account_id] = status
            logger.info(f"Account {account_id} order status updated to: {status}")
            
            # CRITICAL DEBUG: Log detailed information about the status
            logger.info(f"DEBUG - Account {account_id} status: '{status}' (type: {type(status)})")
            logger.info(f"DEBUG - Current account can_order: {self.account_state_manager.get_can_order(account_id)}")
            
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
            
            # Activate SL/Target monitoring when buy orders are completed
            if status == "COMPLETE":
                # Get current symbol and price for the completed order
                account_status = self.account_state_manager.get_account_status(account_id)
                if account_status:
                    symbol = account_status.get('current_symbol', '')
                    price = account_status.get('current_price', 0.0)
                    
                    # Additional safety check: Only activate if account can still order (not rejected)
                    can_order = self.account_state_manager.get_can_order(account_id)
                    if can_order == 1:  # Account can still order = order was successful
                        self.on_buy_order_completed(account_id, symbol, price)
                        logger.info(f"SL/Target monitoring activated for account {account_id} - order was successful")
                    else:
                        logger.warning(f"Order marked as COMPLETE but account {account_id} cannot order - likely rejected. NOT activating SL/Target monitoring")
                
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
            self._update_exit_button_states()
                
            logger.info("Exit buttons updated after buy order completion")
            
        except Exception as e:
            logger.error(f"Error handling buy order completion: {e}")
    
    def _update_exit_button_states(self):
        """Update exit button states based on accounts with positions"""
        try:
            master_can_exit = self.account_state_manager.get_can_exit(1)
            child_can_exit = self.account_state_manager.get_can_exit(2)
            
            # Enable general exit buttons if any account has position
            if master_can_exit or child_can_exit:
                self.exit_button.config(state='normal')
                self.exit_all_button.config(state='normal')
            else:
                self.exit_button.config(state='disabled')
                self.exit_all_button.config(state='disabled')
            
            # Enable individual exit buttons based on account positions
            if master_can_exit and self.account_manager.accounts[1]['active']:
                self.exit_master_button.config(state='normal')
            else:
                self.exit_master_button.config(state='disabled')
                
            if child_can_exit and self.account_manager.accounts[2]['active']:
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
            alert_message = "⚠️ WEBSOCKET CONNECTION ISSUES DETECTED ⚠️\n\n"
            
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
            logger.info(f"SL monitoring activated at {sl_price}")
        except Exception as e:
            logger.error(f"Error starting SL monitoring: {e}")
    
    def start_target_monitoring(self, target_price):
        """Start monitoring Target price - from old project"""
        try:
            self.target_monitoring_active = True
            self.target_price_level = target_price
            self.target_price_button.config(text=f"Target placed @{target_price}", bg="green", fg="white")
            logger.info(f"Target monitoring activated at {target_price}")
        except Exception as e:
            logger.error(f"Error starting Target monitoring: {e}")
    
    def stop_sl_monitoring(self):
        """Stop SL monitoring - from old project"""
        try:
            self.sl_monitoring_active = False
            self.sl_price_level = None
            self.sl_button_state = "ready"
            self.sl_price_button.config(text="SL Price", bg="SystemButtonFace", fg="black")
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
                    self.account_state_manager.get_can_exit(account_id) == 1):
                    
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
            
            # Modify orders for each active account individually
            modified_orders = []
            
            for account_id in active_accounts:
                api = self.account_manager.get_api(account_id)
                if not api:
                    logger.error(f"No API available for account {account_id}")
                    modified_orders.append(None)
                    continue
                
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
                else:
                    modified_order = None
                
                modified_orders.append(modified_order)
            
            # Update order status displays
            for i, account_id in enumerate(active_accounts):
                if i < len(modified_orders) and modified_orders[i]:
                    if account_id == 1:
                        self.master_order_status.set(f"Exit Order Modified: {modified_orders[i]}")
                    elif account_id == 2:
                        self.child_order_status.set(f"Exit Order Modified: {modified_orders[i]}")
                    logger.info(f"Exit order modified for account {account_id}: {modified_orders[i]}")
            
            messagebox.showinfo("Success", f"Exit orders modified successfully for {len(active_accounts)} account(s)")
            logger.info("Exit orders modified successfully")
                
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
            
            # Cancel exit orders directly
            cancelled_orders = []
            for i, account_id in enumerate(active_accounts):
                if i < len(apis) and i < len(order_numbers) and active_flags[i]:
                    api = apis[i]
                    order_number = order_numbers[i]
                    
                    # Cancel order directly
                    result = api.cancel_order(orderno=order_number)
                    
                    if result and result.get('stat') == 'Ok':
                        cancelled_orders.append(order_number)
                        logger.info(f"Exit order cancelled for account {account_id}: {order_number}")
                    else:
                        logger.error(f"Failed to cancel exit order for account {account_id}: {result}")
                        cancelled_orders.append(None)
                else:
                    cancelled_orders.append(None)
            
            # Clear exit order numbers and update UI
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
                
                messagebox.showinfo("Success", f"Exit orders cancelled successfully for {len(active_accounts)} account(s)")
                logger.info("Exit orders cancelled successfully")
            else:
                messagebox.showerror("Error", "No valid APIs available for cancelling exit orders")
                
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
            
            # Get active accounts that can exit positions
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_exit(account_id) == 1):
                    active_accounts.append(account_id)
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts available for market exit")
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
            
            if not (self.account_manager.accounts[1]['active'] and 
                    self.account_state_manager.get_can_exit(1) == 1):
                messagebox.showerror("Error", "Master account is not active or cannot exit positions")
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
            
            if not (self.account_manager.accounts[2]['active'] and 
                    self.account_state_manager.get_can_exit(2) == 1):
                messagebox.showerror("Error", "Child account is not active or cannot exit positions")
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
            
            # Check if API is properly authenticated before placing order
            try:
                # Check API connection by getting order book
                orderbook_response = api.get_orderbook()
                if not orderbook_response:
                    logger.warning(f"API not authenticated for account {account_id}, attempting re-login...")
                    # Attempt to re-login
                    success, client_name = self.account_manager.login_account(account_id)
                    if not success:
                        logger.error(f"Failed to re-authenticate account {account_id}: {client_name}")
                        return
                    logger.info(f"Successfully re-authenticated account {account_id}: {client_name}")
            except Exception as e:
                logger.warning(f"API authentication check failed for account {account_id}: {e}")
                # Attempt to re-login
                success, client_name = self.account_manager.login_account(account_id)
                if not success:
                    logger.error(f"Failed to re-authenticate account {account_id}: {client_name}")
                    return
                logger.info(f"Successfully re-authenticated account {account_id}: {client_name}")
            
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
            
            # Get active accounts that have positions to exit
            active_accounts = []
            for account_id in [1, 2]:  # Master and Child
                if (self.account_manager.accounts[account_id]['active'] and 
                    self.account_state_manager.get_can_exit(account_id) == 1):
                    active_accounts.append(account_id)
            
            if not active_accounts:
                logger.warning("No active accounts with positions available for silent market exit")
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
            
            # Check if target price is set
            if not self.target_price_level:
                messagebox.showerror("Error", "Please set a target price first before enabling trailing")
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
            
            # Calculate what the trailing stop would be at current target price
            if trail_type == "Point":
                calculated_trailing_stop = self.target_price_level - trail_value
            else:  # Percent
                calculated_trailing_stop = self.target_price_level * (1 - trail_value / 100)
            
            # Check if trailing stop would be below SL price (if SL is set)
            if self.sl_price_level and calculated_trailing_stop < self.sl_price_level:
                messagebox.showerror("Error", 
                    f"Trailing stop price ({calculated_trailing_stop:.2f}) cannot be below SL price ({self.sl_price_level})\n"
                    f"Please reduce trail value or increase SL price")
                return
            
            # Enable trailing
            self.enable_trailing_value.set(True)
            
            # Update status based on trail type
            if trail_type == "Point":
                self.trail_status_text.set(f"Trailing Ready - Point Trail: {trail_value} (Will activate when target reached)")
            else:
                self.trail_status_text.set(f"Trailing Ready - Percent Trail: {trail_value}% (Will activate when target reached)")
            
            # Update button states
            self.enable_trail_button.config(state="disabled", bg="gray")
            self.disable_trail_button.config(state="normal", bg="lightcoral")
            
            logger.info(f"Trailing configured - {trail_type} trail: {trail_value} (Ready for target activation)")
            
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
            self.enable_trail_button.config(state="normal", bg="lightgreen")
            self.disable_trail_button.config(state="disabled", bg="gray")
            
            logger.info("Trailing disabled")
            
        except Exception as e:
            logger.error(f"Error disabling trail: {e}")
            messagebox.showerror("Error", f"Error disabling trail: {e}")
    
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
            
            logger.info(f"Trailing mode started at {current_price}, initial stop: {self.trailing_stop_price:.2f}")
            
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
            
            # Use the same fixed market exit function for consistency
            for account_id in active_accounts:
                self._place_market_exit_order(account_id)
            
            logger.info(f"Trailing stop market exit orders placed for {len(active_accounts)} account(s)")
            
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

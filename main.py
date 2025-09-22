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
        
        # SL and Target monitoring variables
        self.sl_monitoring_active = False
        self.target_monitoring_active = False
        self.sl_price_level = None
        self.target_price_level = None
        
        # Button state tracking for two-step confirmation
        self.sl_button_state = "ready"  # "ready", "showing_price", "confirmed"
        self.target_button_state = "ready"  # "ready", "showing_price", "confirmed"
        
        # Auto SL/Target system variables
        self.sl_difference_from_buy = -20  # Default SL points from buy price
        self.target_difference_from_buy = 30  # Default Target points from buy price
        self.current_buy_order_open_value = None  # Track current buy order open value
        
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
        
        # Reset rejection blocks button
        self.reset_rejection_button = ttk.Button(
            self.login_frame, text="RESET BLOCKS", 
            command=self.reset_rejection_blocks, width=12
        )
        self.reset_rejection_button.pack(side=tk.LEFT, padx=5)

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
            
            logger.info(f"Live price updated: {live_price:.2f}")
        except Exception as e:
            logger.error(f"Error updating live price: {e}")
    
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
    
    def on_buy_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle buy order completion"""
        try:
            logger.info(f"Buy order completed for account {account_num}: {symbol} @ {price}")
            # Additional logic can be added here for buy order completion
        except Exception as e:
            logger.error(f"Error handling buy order completion: {e}")
    
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
                else:
                    # Update UI to show login failed
                    self.root.after(0, self.update_child_login_ui, False, "Login Failed")
                    logger.error(f"Child account login failed")
                    
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
        """Release buttons - TO BE IMPLEMENTED"""
        logger.info("Release buttons clicked - Function not implemented yet")
        
    def reset_rejection_blocks(self):
        """Reset rejection blocks - TO BE IMPLEMENTED"""
        logger.info("Reset rejection blocks clicked - Function not implemented yet")
        
    def verify_pnl_from_broker(self):
        """Verify PnL from broker - TO BE IMPLEMENTED"""
        logger.info("Verify PnL from broker clicked - Function not implemented yet")
        
    def update_selections(self, *args):
        """Update selections when index changes"""
        try:
            selected_index = self.selected_index.get()
            if selected_index:
                logger.info(f"Index selected: {selected_index}")
                
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
                    if strikes:
                        # Set middle strike as default (current price)
                        middle_index = len(strikes) // 2
                        self.selected_strike.set(strikes[middle_index])
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
            
            logger.info("Account states reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting account states: {e}")
        
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
            
            # 6. Disable buy button and enable management buttons
            self.buy_button.config(state="disabled")
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
                
        except Exception as e:
            logger.error(f"Error handling order status update for account {account_id}: {e}")
        
    def place_exit_orders(self):
        """Place exit orders - TO BE IMPLEMENTED"""
        logger.info("Place exit orders clicked - Function not implemented yet")
        
    def cancel_master_buy_order(self):
        """Cancel master buy order - TO BE IMPLEMENTED"""
        logger.info("Cancel master buy order clicked - Function not implemented yet")
        
    def cancel_child_buy_order(self):
        """Cancel child buy order - TO BE IMPLEMENTED"""
        logger.info("Cancel child buy order clicked - Function not implemented yet")
        
    def set_sl_price(self):
        """Set SL price - TO BE IMPLEMENTED"""
        logger.info("Set SL price clicked - Function not implemented yet")
        
    def set_target_price(self):
        """Set target price - TO BE IMPLEMENTED"""
        logger.info("Set target price clicked - Function not implemented yet")
        
    def on_trail_type_changed(self, event):
        """On trail type changed - TO BE IMPLEMENTED"""
        logger.info("Trail type changed - Function not implemented yet")
        
    def enable_trail(self):
        """Enable trail - TO BE IMPLEMENTED"""
        logger.info("Enable trail clicked - Function not implemented yet")
        
    def disable_trail(self):
        """Disable trail - TO BE IMPLEMENTED"""
        logger.info("Disable trail clicked - Function not implemented yet")
        
    def cancel_buy_orders(self):
        """Cancel buy orders - TO BE IMPLEMENTED"""
        logger.info("Cancel buy orders clicked - Function not implemented yet")
        
    def modify_buy_orders(self):
        """Modify buy orders - TO BE IMPLEMENTED"""
        logger.info("Modify buy orders clicked - Function not implemented yet")
        
    def cancel_exit_orders(self):
        """Cancel exit orders - TO BE IMPLEMENTED"""
        logger.info("Cancel exit orders clicked - Function not implemented yet")
        
    def modify_exit_orders(self):
        """Modify exit orders - TO BE IMPLEMENTED"""
        logger.info("Modify exit orders clicked - Function not implemented yet")
        
    def exit_all_orders_market(self):
        """Exit all orders at market - TO BE IMPLEMENTED"""
        logger.info("Exit all orders at market clicked - Function not implemented yet")
        
    def exit_master_orders_market(self):
        """Exit master orders at market - TO BE IMPLEMENTED"""
        logger.info("Exit master orders at market clicked - Function not implemented yet")
        
    def exit_child_orders_market(self):
        """Exit child orders at market - TO BE IMPLEMENTED"""
        logger.info("Exit child orders at market clicked - Function not implemented yet")
        
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

"""
Main GUI window for Master-Child Trading System
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from datetime import datetime
import calendar
# from config import Config  # Not currently used
from trading.account_manager import AccountManager
from trading.order_manager import OrderManager
from trading.websocket_manager import WebSocketManager
from trading.position_manager import PositionManager
from trading.account_state_manager import AccountStateManager
from market_data.symbol_manager import SymbolManager
from market_data.expiry_manager import ExpiryManager
from utils.telegram_notifications import send_sos_message
from logger import applicationLogger

class MainWindow:
    """Main application window"""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.root = tk.Tk()
        
        # Load settings
        self.settings = settings or {
            'child_default_lots': 1,
            'default_sl_points': 20,
            'default_target_points': 30
        }

        self.root.title("***Kratik's Soft*** - Master Account Not Logged In")
        self.root.geometry("900x490")
        
        # Center the window on screen
        self.center_window()
        
        # Master account holder name
        self.master_account_name = tk.StringVar()
        self.master_account_name.set("Not Logged In")
        
        # Initialize managers
        self.account_manager = AccountManager()
        self.order_manager = OrderManager()
        self.websocket_manager = WebSocketManager(self.account_manager, self.order_manager)
        self.state_manager = AccountStateManager()
        
        # Ensure Master account is always active
        self.state_manager.ensure_master_always_active()
        self.state_manager.reset_blocked_accounts_on_startup()
        
        # Log current account states after initialization
        applicationLogger.info("Account states initialized - CSV reset on startup")
        
        # Set up price feed callback for dynamic order management
        self.order_manager.dynamic_order_manager.set_price_feed_callback(self.get_current_price)
        self.position_manager = PositionManager()
        self.symbol_manager = SymbolManager()
        self.expiry_manager = ExpiryManager()
        
        # Position tracking for local PnL calculation
        self.position_data = {
            1: {  # Master account
                'buy_price': None,
                'qty': None,
                'active': False,
                'verified_pnl': None,
                'needs_verification': False,
                'symbol': None
            },
            2: {  # Child account
                'buy_price': None,
                'qty': None,
                'active': False,
                'verified_pnl': None,
                'needs_verification': False,
                'symbol': None
            }
        }

        
        # Set up live price callback
        self.websocket_manager.set_live_price_callback(self.update_live_price)
        
        # Set up order status callback
        self.websocket_manager.set_order_status_callback(self.update_order_status)
        self.websocket_manager.set_buy_order_completed_callback(self.on_buy_order_completed)
        self.websocket_manager.set_sell_order_completed_callback(self.on_sell_order_completed)
        
        # Set PnL update callback
        self.websocket_manager.set_pnl_update_callback(self.update_pnl_on_trade)
        
        # Set order state callback for cross-account coordination
        self.websocket_manager.set_order_state_callback(self.update_order_state)
        
        # Set order rejection callback for buy order rejections
        self.websocket_manager.set_order_rejection_callback(self.handle_buy_order_rejection)
        
        # Clean up old master files first
        self.cleanup_old_master_files()
        
        # Calculate and store expiry dates for all indices
        self.calculate_and_store_expiry_dates()
        
        # GUI variables
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize with master account
        self.initialize_master_account()
        
        # Initialize UI states after GUI is created
        self.root.after(100, self.initialize_ui_states)
    
    def initialize_ui_states(self):
        """Initialize UI states after GUI is fully created"""
        try:
            # Initialize Show PnL button state
            self.update_verify_pnl_button_state()
            
            # Initialize price input state
            self.update_price_input_state()
            
            applicationLogger.info("UI states initialized successfully")
        except Exception as e:
            applicationLogger.error(f"Error initializing UI states: {e}")
    
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
        # Initialize SL/Target differences from settings
        self.sl_difference_from_buy = -self.settings.get('default_sl_points', 20)  # Default SL points from buy price
        self.target_difference_from_buy = self.settings.get('default_target_points', 30)  # Default Target points from buy price
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

        # self.create_account_display()  # Hidden - will be part of website dashboard
        self.create_order_status_display()
        self.create_bottom_control_panel()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
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
            self.trading_frame, textvariable=self.qty1_var, width=10
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
    
    def create_account_display(self):
        """Create account display frame"""
        self.account_frame = tk.Frame(self.root)
        self.account_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Account buttons and displays
        accounts = [
            (1, "MASTER1", self.master1_value),
            (2, "CHILD", self.child_value)
        ]
        
        for i, (account_num, name, value_var) in enumerate(accounts):
            # Account button
            button = tk.Button(
                self.account_frame, text=name, 
                command=lambda num=account_num: self.login_account(num), 
                width=15, height=2
            )
            button.grid(row=i, column=0, padx=5, pady=5)
            
            # Account value display
            value_box = tk.Entry(
                self.account_frame, textvariable=value_var, 
                state='readonly', width=23, font=('Helvetica', 12)
            )
            value_box.grid(row=i, column=1, padx=5, pady=5)
            
            # Order status button
            status_button = tk.Button(
                self.account_frame, text=f"Order Status {account_num}", 
                width=15, height=2
            )
            status_button.grid(row=i, column=2, padx=5, pady=5)
            
            # MTM button
            mtm_button = tk.Button(
                self.account_frame, text=f"MTM{account_num}", 
                command=lambda num=account_num: self.update_mtm(num), 
                width=5, height=2, 
                state=tk.NORMAL if account_num == 1 else tk.DISABLED
            )
            mtm_button.grid(row=i, column=4, padx=5, pady=5)
            
            # Order details button
            details_button = tk.Button(
                self.account_frame, text="OrdDet", 
                command=lambda num=account_num: self.show_order_details(num), 
                width=5, height=2,
                state=tk.NORMAL if account_num == 1 else tk.DISABLED
            )
            details_button.grid(row=i, column=5, padx=5, pady=5)
    
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
    
    
    def initialize_master_account(self):
        """Initialize master account on startup"""
        try:
            success, client_name = self.account_manager.login_account(1)
            if success:
                self.websocket_manager.connect_feed(1)

                # Update window title with master account name
                self.root.title(f"***Kratik's Soft*** - Master Account {client_name} Logged in")
                self.master_account_name.set(client_name)
                # Update button text to show logged in status
                self.update_login_button_text(1, client_name)
                # Update master order status to show it's ready
                self.master_order_status.set(self.get_ready_status_message(1))
                
                # Refresh PnL after master account initialization
                self.update_pnl_on_trade(1)
                
                applicationLogger.info(f"Master account initialized successfully: {client_name}")
            else:
                messagebox.showerror("Error", f"Failed to initialize master account: {client_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error initializing master account: {e}")
    
    def login_account(self, account_num: int):
        """Login to a specific account or unblock if blocked"""
        try:
            # Check if child account is blocked and needs to be unblocked
            if account_num == 2 and self.account_manager.accounts[2].get('blocked', False):
                success, message = self.account_manager.unblock_account(2)
                if success:
                    self.child_orders_blocked = False
                    client_name = self.account_manager.accounts[2].get('client_name', 'Child Account')
                    
                    # Update state manager with new separated status
                    self.state_manager.update_login_status(2, 'logged_in', 'Child account unblocked and logged in')
                    self.state_manager.update_order_status(2, 'ready', 'Child account ready for orders')
                    
                    self.login_button2.config(text=f"{client_name} Logged in")
                    self.login_button2.config(state='disabled', style="LoginSuccess.TButton")
                    self.child_order_status.set(f"{client_name} - Ready for Orders")
                    messagebox.showinfo("Success", f"Child account unblocked successfully.\n{message}")
                    applicationLogger.info(f"Child account unblocked: {client_name}")
                else:
                    messagebox.showerror("Error", f"Failed to unblock child account: {message}")
                return
            
            # Normal login process
            success, client_name = self.account_manager.login_account(account_num)
            if success:
                # Update state manager with new separated status
                self.state_manager.update_login_status(account_num, 'logged_in', 'Account logged in successfully')
                self.state_manager.update_order_status(account_num, 'ready', 'Account ready for orders')
                
                self.websocket_manager.connect_feed(account_num)
                self.update_account_display(account_num, client_name)
                self.enable_account_buttons(account_num)

                
                # Update window title if this is the master account
                if account_num == 1:
                    self.root.title(f"***Kratik's Soft*** - Master Account {client_name} Logged in")
                    self.master_account_name.set(client_name)
                    
                    # Automatically login child account after master account login
                    self.auto_login_child_account()
                
                # Update button text to show logged in status
                self.update_login_button_text(account_num, client_name)
                
                # Update order status to show account is ready
                if account_num == 1:
                    self.master_order_status.set(self.get_ready_status_message(1))
                elif account_num == 2:
                    self.child_order_status.set(self.get_ready_status_message(2))
                    # Reset child order blocking when child logs back in
                    self.child_orders_blocked = False
                    applicationLogger.info("Child account logged in - Order blocking reset")
                
                # Refresh PnL after successful login
                self.update_pnl_on_trade(account_num)
            else:
                self.show_login_error(account_num, f"Login failed: {client_name}")
                messagebox.showerror("Error", f"Login failed: {client_name}")
        except Exception as e:
            self.show_login_error(account_num, f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error logging in: {e}")
    
    def update_account_display(self, account_num: int, client_name: str):
        """Update account display"""
        if account_num == 1:
            self.master1_value.set(client_name)
        elif account_num == 2:
            self.child_value.set(client_name)
    

    def auto_login_child_account(self):
        """Automatically login child account after master account login"""
        try:
            # Check if child account exists and is not already active
            if 2 in self.account_manager.accounts and not self.account_manager.is_account_active(2):
                applicationLogger.info("Attempting automatic child account login...")
                success, client_name = self.account_manager.login_account(2)
                if success:
                    # Update state manager with new separated status
                    self.state_manager.update_login_status(2, 'logged_in', 'Child account auto-logged in')
                    self.state_manager.update_order_status(2, 'ready', 'Child account ready for orders')
                    
                    # Set up websocket feed for child account
                    self.websocket_manager.connect_feed(2)
                    self.update_account_display(2, client_name)
                    self.enable_account_buttons(2)
                    
                    # Update button text to show logged in status
                    self.update_login_button_text(2, client_name)
                    
                    # Update order status to show account is ready
                    self.child_order_status.set(self.get_ready_status_message(2))
                    
                    # Refresh PnL after successful login
                    self.update_pnl_on_trade(2)
                    
                    applicationLogger.info(f"Child account automatically logged in: {client_name}")
                else:
                    applicationLogger.warning(f"Automatic child account login failed: {client_name}")
            else:
                applicationLogger.info("Child account already active or not available")
        except Exception as e:
            applicationLogger.error(f"Error in automatic child account login: {e}")

    def update_login_button_text(self, account_num: int, client_name: str):
        """Update login button text to show logged in status"""
        if account_num == 2:  # Child account
            self.login_button2.config(text=f"{client_name} Logged in")
            self.login_button2.config(state='disabled', style="LoginSuccess.TButton")
    
    def show_login_error(self, account_num: int, error_message: str):
        """Show login error with red border"""
        if account_num == 2:  # Child account
            self.login_button2.config(text=f"Login Error: {error_message}")
            self.login_button2.config(state='normal', style="LoginError.TButton")
            # Reset to normal style after 3 seconds
            self.root.after(3000, self.reset_login_button)
    
    def reset_login_button(self):
        """Reset login button to normal state"""
        self.login_button2.config(text="Login Child Account")
        self.login_button2.config(state='normal', style="LoginButton.TButton")
    
    def open_configuration(self):
        """Open configuration window"""
        try:
            from gui.config_window import show_configuration_window
            
            # Show configuration window with current settings
            new_settings = show_configuration_window(self.settings)
            
            # Update current settings if they were changed
            if new_settings:
                self.settings.update(new_settings)
                applicationLogger.info(f"Configuration updated: {self.settings}")
                
                # Show a message that settings were updated
                from tkinter import messagebox
                messagebox.showinfo("Configuration Updated", 
                                  "Settings have been updated successfully!\n\n"
                                  "The changes will take effect immediately.")
                
        except Exception as e:
            applicationLogger.error(f"Error opening configuration window: {e}")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to open configuration window: {e}")
    
    def enable_account_buttons(self, account_num: int):
        """Enable buttons for an account"""
        # This would enable the appropriate buttons based on account number
        pass
    
    def has_active_orders(self):
        """Check if there are any active orders in the system"""
        try:
            # Check if buy button is disabled (indicates orders are placed)
            if self.buy_button['state'] == 'disabled':
                return True
            
            # Check if exit button is disabled (indicates exit orders are placed)
            if self.exit_button['state'] == 'disabled':
                return True
            
            # Check if any order numbers exist
            for order_num in self.order_numbers.values():
                if order_num:
                    return True
            
            for order_num in self.exit_order_numbers.values():
                if order_num:
                    return True
            
            return False
            
        except Exception as e:
            applicationLogger.error(f"Error checking active orders: {e}")
            return False
    
    def _are_buy_orders_filled(self):
        """Check if buy orders are filled/completed (not just placed)"""
        try:
            # Check if buy orders are completed by looking at order status
            master_status = self.master_order_status.get()
            child_status = self.child_order_status.get()
            
            # Check if any account shows "Buy Order Complete" status
            if "Buy Order Complete" in master_status or "Buy Order Complete" in child_status:
                return True
            
            # Also check if SL/Target monitoring is already active (indicates buy orders were filled)
            if hasattr(self, 'sl_monitoring_active') and self.sl_monitoring_active:
                return True
                
            if hasattr(self, 'target_monitoring_active') and self.target_monitoring_active:
                return True
            
            return False
            
        except Exception as e:
            applicationLogger.error(f"Error checking if buy orders are filled: {e}")
            return False
    
    def update_selections(self, *args):
        """Update selections based on index"""
        index = self.selected_index.get()
        if index in ["NIFTY", "BANKNIFTY", "SENSEX"]:
            # Update expiry dropdown with multiple options
            expiry_list = self.expiry_manager.get_expiry_list(index)
            self.expiry_dropdown['values'] = expiry_list
            if expiry_list:
                self.expiry_value.set(expiry_list[0])  # Set to first (current) expiry
            
            # Check if there are any active orders
            has_active_orders = self.has_active_orders()
            
            # Always reset quantity, price boxes, and trading symbols when index changes
            self.qty1_var.set("")
            self.price_value.set("")
            self.master1_value.set("")
            self.child_value.set("")
            
            # Clear option selection if no active orders
            if not has_active_orders:
                self.selected_option.set("")
                self.selected_strike.set("")
                self.index_ltp_value.set("--")
                applicationLogger.info("Cleared option, strike, quantity, and price selections - no active orders")
            else:
                applicationLogger.info("Reset quantity and price boxes due to index change")
            
            # Fetch Index LTP immediately when Index is selected
            self.fetch_index_ltp(index)
            
            # Fetch current index price and update strike list
            try:
                api = self.account_manager.get_api(1)  # Use master account API
                if api:
                    current_price = self.symbol_manager.get_index_price(api, index)
                    if current_price:
                        # Get current option type for strike generation
                        option_type = self.selected_option.get() if self.selected_option.get() in ["CE", "PE"] else None
                        strikes = self.expiry_manager.get_strike_list(index, current_price, option_type)
                        self.strike_dropdown['values'] = strikes
                        applicationLogger.info(f"Updated strikes for {index} based on price {current_price} and option {option_type}: {strikes}")
                    else:
                        # Fallback to default strikes if price fetch fails
                        applicationLogger.warning(f"Could not fetch price for {index}, using default strikes")
                        default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                        option_type = self.selected_option.get() if self.selected_option.get() in ["CE", "PE"] else None
                        strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option_type)
                        self.strike_dropdown['values'] = strikes
                else:
                    # Fallback if no API available
                    applicationLogger.warning("Master account API not available, using default strikes")
                    default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                    option_type = self.selected_option.get() if self.selected_option.get() in ["CE", "PE"] else None
                    strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option_type)
                    self.strike_dropdown['values'] = strikes
            except Exception as e:
                applicationLogger.error(f"Error updating strikes for {index}: {e}")
                # Fallback to default strikes on error
                default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                option_type = self.selected_option.get() if self.selected_option.get() in ["CE", "PE"] else None
                strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option_type)
                self.strike_dropdown['values'] = strikes
            
            # Update quantity dropdown based on index
            self.update_quantity_options_for_index(index)
    
    def on_expiry_selected(self, *args):
        """Handle expiry selection"""
        expiry = self.expiry_value.get()
        index = self.selected_index.get()
        option = self.selected_option.get()
        
        if expiry and index:
            # Update strikes when expiry changes
            if option in ["CE", "PE"]:
                self.update_strikes_for_option(index, option)
        
        # Also call the original concatenate_values method
        self.concatenate_values()
    
    def on_option_selected(self, *args):
        """Handle option selection and fetch Index LTP if CE or PE is selected"""
        option = self.selected_option.get()
        index = self.selected_index.get()
        
        if option in ["CE", "PE"] and index:
            # Fetch Index LTP and get the price for strike calculation
            current_price = self.fetch_index_ltp_and_get_price(index)
            
            # Update strikes based on new option type with the fetched price
            self.update_strikes_for_option_with_price(index, option, current_price)
        
        # Also call the original concatenate_values method
        self.concatenate_values()
    
    def update_strikes_for_option_with_price(self, index: str, option: str, current_price: float = None):
        """Update strikes when option type changes, using provided price"""
        try:
            if current_price:
                strikes = self.expiry_manager.get_strike_list(index, current_price, option)
                self.strike_dropdown['values'] = strikes
                applicationLogger.info(f"Updated strikes for {index} {option} based on price {current_price}: {strikes}")
            else:
                # Fallback to default strikes if no price provided
                applicationLogger.warning(f"No price provided for {index}, using default strikes")
                default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option)
                self.strike_dropdown['values'] = strikes
        except Exception as e:
            applicationLogger.error(f"Error updating strikes for {index} {option}: {e}")
            # Fallback to default strikes on error
            default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
            strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option)
            self.strike_dropdown['values'] = strikes

    def update_strikes_for_option(self, index: str, option: str):
        """Update strikes when option type changes (legacy method for backward compatibility)"""
        try:
            # Get current index price
            api = self.account_manager.get_api(1)
            if api:
                current_price = self.symbol_manager.get_index_price(api, index)
                if current_price:
                    strikes = self.expiry_manager.get_strike_list(index, current_price, option)
                    self.strike_dropdown['values'] = strikes
                    applicationLogger.info(f"Updated strikes for {index} {option} based on price {current_price}: {strikes}")
                else:
                    # Fallback to default strikes if price fetch fails
                    applicationLogger.warning(f"Could not fetch price for {index}, using default strikes")
                    default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                    strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option)
                    self.strike_dropdown['values'] = strikes
            else:
                # Fallback if no API available
                applicationLogger.warning("Master account API not available, using default strikes")
                default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option)
                self.strike_dropdown['values'] = strikes
        except Exception as e:
            applicationLogger.error(f"Error updating strikes for {index} {option}: {e}")
            # Fallback to default strikes on error
            default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
            strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000), option)
            self.strike_dropdown['values'] = strikes
    
    def on_strike_selected(self, *args):
        """Handle strike selection - automatically subscribe and fetch price"""
        strike = self.selected_strike.get()
        index = self.selected_index.get()
        option = self.selected_option.get()
        expiry = self.expiry_value.get()
        
        # Only proceed if all required fields are selected
        if all([index, expiry, strike, option]):
            # Generate trading symbol
            trading_symbol = self.concatenate_values()
            if trading_symbol:
                # Automatically fetch price and subscribe
                self.auto_fetch_and_subscribe(trading_symbol)
    
    def fetch_index_ltp(self, index):
        """Fetch and display Index LTP"""
        try:
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                self.index_ltp_value.set("No API")
                return
            
            # Get Index LTP
            ltp = self.symbol_manager.get_index_price(api, index)
            if ltp:
                self.index_ltp_value.set(f"{ltp:.2f}")
                applicationLogger.info(f"Index LTP for {index}: {ltp}")
            else:
                self.index_ltp_value.set("N/A")
                applicationLogger.warning(f"Could not fetch Index LTP for {index}")
                
        except Exception as e:
            self.index_ltp_value.set("Error")
            applicationLogger.error(f"Error fetching Index LTP for {index}: {e}")

    def fetch_index_ltp_and_get_price(self, index):
        """Fetch and display Index LTP, return the price for further use"""
        try:
            # Check if master account is logged in
            if not self.account_manager.is_account_active(1):
                self.index_ltp_value.set("Master Not Logged In")
                applicationLogger.warning(f"Cannot fetch Index LTP for {index}: Master account not logged in")
                return None
            
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                self.index_ltp_value.set("No API")
                applicationLogger.warning(f"Cannot fetch Index LTP for {index}: API not available")
                return None
            
            # Get Index LTP
            ltp = self.symbol_manager.get_index_price(api, index)
            if ltp:
                self.index_ltp_value.set(f"{ltp:.2f}")
                applicationLogger.info(f"Index LTP for {index}: {ltp}")
                return ltp
            else:
                self.index_ltp_value.set("N/A")
                applicationLogger.warning(f"Could not fetch Index LTP for {index}")
                return None
                
        except Exception as e:
            self.index_ltp_value.set("Error")
            applicationLogger.error(f"Error fetching Index LTP for {index}: {e}")
            return None
    
    def concatenate_values(self, *args):
        """Concatenate selected values to create trading symbol"""
        index = self.selected_index.get()
        expiry = self.expiry_value.get()
        strike = self.selected_strike.get()
        option = self.selected_option.get()
        
        if all([index, expiry, strike, option]):
            if index == "SENSEX":
                trading_symbol = self._generate_sensex_symbol(expiry, strike, option)
            else:

                # Convert CE/PE to C/P for NIFTY and BANKNIFTY
                if option == "CE":
                    option_type = "C"
                elif option == "PE":
                    option_type = "P"
                else:
                    option_type = option
                
                trading_symbol = f"{index}{expiry}{option_type}{strike}"
            
            # Update all account displays
            self.master1_value.set(trading_symbol)
            self.child_value.set(trading_symbol)

            
            # Update quantity options based on lot size
            self.update_quantity_options(trading_symbol)
            
            return trading_symbol
        return ""
    

    def update_quantity_options(self, trading_symbol: str):
        """Update quantity dropdown based on lot size from master scrip file"""
        try:
            # Get token and lot size from symbol manager
            token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
            
            if lot_size:
                # Generate quantity options based on lot size
                quantities = self.symbol_manager.get_quantity_options(lot_size)
                self.qty_dropdown['values'] = quantities
                applicationLogger.info(f"Updated quantity options for {trading_symbol} with lot size {lot_size}: {quantities}")
            else:
                # Fallback to default quantities if lot size not found
                index = self.selected_index.get()
                if index in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                    quantities = self.expiry_manager.get_quantity_list(index)
                    self.qty_dropdown['values'] = quantities
                    applicationLogger.warning(f"Lot size not found for {trading_symbol}, using default quantities")
                
        except Exception as e:
            applicationLogger.error(f"Error updating quantity options for {trading_symbol}: {e}")
            # Fallback to default quantities on error
            index = self.selected_index.get()
            if index in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                quantities = self.expiry_manager.get_quantity_list(index)
                self.qty_dropdown['values'] = quantities
    
    def update_quantity_options_for_index(self, index: str):
        """Update quantity dropdown based on index when no complete symbol is available"""
        try:
            if index == "SENSEX":
                # For SENSEX, use lot size 20 to generate proper quantities
                quantities = self.symbol_manager.get_quantity_options(20)
                self.qty_dropdown['values'] = quantities
                applicationLogger.info(f"Updated quantity options for {index} with lot size 20: {quantities}")
            else:
                # For other indices, use the default method
                quantities = self.expiry_manager.get_quantity_list(index)
                self.qty_dropdown['values'] = quantities
                applicationLogger.info(f"Updated quantity options for {index} using default method: {quantities}")
        except Exception as e:
            applicationLogger.error(f"Error updating quantity options for {index}: {e}")
            # Final fallback
            quantities = self.expiry_manager.get_quantity_list(index)
            self.qty_dropdown['values'] = quantities
    
    def _generate_sensex_symbol(self, expiry: str, strike: str, option: str) -> str:
        """
        Generate SENSEX symbol based on expiry type
        
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
            applicationLogger.error(f"Error generating SENSEX symbol: {e}")
            # Fallback to original format
            return f"SENSEX{expiry}{strike}{option}"
    
    def _get_last_friday(self, year: int, month: int) -> datetime:
        """Get the last Friday of the month"""
        from datetime import timedelta
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        # Find the last Friday
        days_back = (last_date.weekday() - 4) % 7
        if days_back == 0 and last_date.weekday() != 4:
            days_back = 7
        last_friday = last_date - timedelta(days=days_back)
        
        return last_friday
    
    def _get_last_thursday(self, year: int, month: int) -> datetime:
        """Get the last Thursday of the month"""
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
    
    def calculate_and_store_expiry_dates(self):
        """Calculate and store expiry dates for all indices in CSV with date"""
        try:
            import os
            import csv
            from datetime import datetime
            
            # Check if we already calculated today
            csv_file = os.path.join('data', 'expiry_dates.csv')
            today = datetime.now().strftime('%Y-%m-%d')
            
            if os.path.exists(csv_file):
                # Check if file was created today
                file_time = datetime.fromtimestamp(os.path.getmtime(csv_file))
                if file_time.strftime('%Y-%m-%d') == today:
                    applicationLogger.info("Expiry dates already calculated today, loading from CSV")
                    self.load_expiry_dates_from_csv()
                    return
            
            applicationLogger.info("Calculating expiry dates for all indices...")
            
            # Calculate expiry dates for each index
            expiry_data = {}
            indices = ["SENSEX", "NIFTY", "BANKNIFTY"]
            
            for index in indices:
                try:
                    current_expiry, next_expiry = self._calculate_expiry_for_index(index)
                    expiry_data[index] = {
                        'current': current_expiry,
                        'next': next_expiry
                    }
                    applicationLogger.info(f"{index} - Current: {current_expiry.strftime('%d-%b-%Y')}, Next: {next_expiry.strftime('%d-%b-%Y')}")
                except Exception as e:
                    applicationLogger.error(f"Error calculating expiry for {index}: {e}")
                    continue
            
            # Store in CSV
            self._save_expiry_dates_to_csv(expiry_data)
            
            # Load the data
            self.load_expiry_dates_from_csv()
            
        except Exception as e:
            applicationLogger.error(f"Error calculating and storing expiry dates: {e}")
    
    def _calculate_expiry_for_index(self, index: str):
        """Calculate current and next expiry for a specific index"""
        import os
        from datetime import datetime
        
        # For SENSEX, use the enhanced calculation from findexpiry.py
        if index == "SENSEX":
            from findexpiry import get_sensex_expiry_dates
            sensex_dates = get_sensex_expiry_dates()
            
            if not sensex_dates or len(sensex_dates) < 2:
                raise ValueError(f"Not enough SENSEX expiry dates found. Found: {len(sensex_dates) if sensex_dates else 0}, Required: 2")
            
            # Convert string dates to datetime objects
            current_date = datetime.strptime(sensex_dates[0][0], '%d-%b-%Y')
            next_date = datetime.strptime(sensex_dates[1][0], '%d-%b-%Y')
            
            return current_date, next_date
        
        # For other indices, use the original method
        master_file_path = self._get_master_file_path(index)
        
        if not master_file_path or not os.path.exists(master_file_path):
            raise FileNotFoundError(f"Master file not found for {index}: {master_file_path}")
        
        # Parse the master file for expiry dates
        expiry_dates = self._parse_master_file_for_expiry_dates(master_file_path, index)
        
        if not expiry_dates:
            raise ValueError(f"No expiry dates found for {index}")
        
        # Sort in increasing order
        expiry_dates.sort()
        
        # Take the first two expiry dates
        if len(expiry_dates) < 2:
            raise ValueError(f"Not enough expiry dates for {index}. Found: {len(expiry_dates)}, Required: 2")
        
        return expiry_dates[0], expiry_dates[1]
    
    def _get_master_file_path(self, index: str) -> str:
        """Get the appropriate master file path based on index"""
        import os
        
        data_dir = "data"
        
        if index == "SENSEX":
            # Use the latest BFO file
            bfo_files = [f for f in os.listdir(data_dir) if f.startswith("BFO_symbols.txt_") and f.endswith(".txt")]
            if bfo_files:
                latest_bfo = sorted(bfo_files)[-1]
                return os.path.join(data_dir, latest_bfo)
        elif index in ["NIFTY", "BANKNIFTY"]:
            # Use the latest NFO file
            nfo_files = [f for f in os.listdir(data_dir) if f.startswith("NFO_symbols.txt_") and f.endswith(".txt")]
            if nfo_files:
                latest_nfo = sorted(nfo_files)[-1]
                return os.path.join(data_dir, latest_nfo)
        
        return None
    
    def _parse_master_file_for_expiry_dates(self, file_path: str, index: str) -> list:
        """Parse master file and extract unique expiry dates for the selected index"""
        from datetime import datetime
        expiry_dates = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file):
                    line = line.strip()
                    if line and not line.startswith('Exchange'):  # Skip header
                        fields = line.split(',')
                        if len(fields) >= 6:
                            symbol = fields[4]  # Trading symbol
                            expiry_str = fields[5]  # Expiry date
                            
                            # Filter by index type
                            if index == "SENSEX" and 'SENSEX' in symbol and not symbol.startswith('SENSEX50'):
                                try:
                                    expiry_date = datetime.strptime(expiry_str, '%d-%b-%Y')
                                    expiry_dates.add(expiry_date)
                                except ValueError:
                                    continue
                            elif index in ["NIFTY", "BANKNIFTY"] and index in symbol:
                                try:
                                    expiry_date = datetime.strptime(expiry_str, '%d-%b-%Y')
                                    expiry_dates.add(expiry_date)
                                except ValueError:
                                    continue
            
            return list(expiry_dates)
            
        except Exception as e:
            applicationLogger.error(f"Error parsing master file {file_path}: {e}")
            return []
    
    def _save_expiry_dates_to_csv(self, expiry_data: dict):
        """Save expiry dates to CSV file"""
        import os
        import csv
        from datetime import datetime
        
        csv_file = os.path.join('data', 'expiry_dates.csv')
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Index', 'Current_Expiry', 'Next_Expiry', 'Calculated_Date'])
                
                for index, data in expiry_data.items():
                    writer.writerow([
                        index,
                        data['current'].strftime('%d-%b-%Y'),
                        data['next'].strftime('%d-%b-%Y'),
                        datetime.now().strftime('%Y-%m-%d')
                    ])
            
            applicationLogger.info(f"Expiry dates saved to {csv_file}")
            
        except Exception as e:
            applicationLogger.error(f"Error saving expiry dates to CSV: {e}")
    
    def load_expiry_dates_from_csv(self):
        """Load expiry dates from CSV file"""
        import os
        import csv
        from datetime import datetime
        
        csv_file = os.path.join('data', 'expiry_dates.csv')
        
        if not os.path.exists(csv_file):
            applicationLogger.warning("Expiry CSV file not found")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    index = row['Index']
                    current_str = row['Current_Expiry']
                    next_str = row['Next_Expiry']
                    
                    # Parse dates
                    current_date = datetime.strptime(current_str, '%d-%b-%Y')
                    next_date = datetime.strptime(next_str, '%d-%b-%Y')
                    
                    # Store in instance variables for the default index (SENSEX)
                    if index == 'SENSEX':
                        self.current_expiry = current_date
                        self.next_expiry = next_date
                        applicationLogger.info(f"SENSEX - Current expiry: {current_date.strftime('%d-%b-%Y')}")
                        applicationLogger.info(f"SENSEX - Next expiry: {next_date.strftime('%d-%b-%Y')}")
            
        except Exception as e:
            applicationLogger.error(f"Error loading expiry dates from CSV: {e}")
    
    def cleanup_old_master_files(self):
        """Clean up old master files, keep only the latest 3 days"""
        try:
            import os
            import glob
            from datetime import datetime, timedelta
            
            data_dir = "data"
            cutoff_date = datetime.now() - timedelta(days=3)
            
            # File patterns to clean up
            patterns = [
                "BFO_symbols.txt_*.txt",
                "NFO_symbols.txt_*.txt", 
                "NSE_symbols.txt_*.txt",
                "MCX_symbols.txt_*.txt"
            ]
            
            cleaned_files = 0
            
            for pattern in patterns:
                files = glob.glob(os.path.join(data_dir, pattern))
                
                for file_path in files:
                    try:
                        # Extract date from filename
                        filename = os.path.basename(file_path)
                        date_str = filename.split('_')[-1].replace('.txt', '')
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Delete if older than 3 days
                        if file_date < cutoff_date:
                            os.remove(file_path)
                            cleaned_files += 1
                            applicationLogger.info(f"Deleted old master file: {filename}")
                            
                    except (ValueError, IndexError) as e:
                        # Skip files that don't match expected format
                        continue
            
            applicationLogger.info(f"Cleanup completed: {cleaned_files} old master files deleted")
            
        except Exception as e:
            applicationLogger.error(f"Error cleaning up old master files: {e}")
    
    def auto_fetch_and_subscribe(self, trading_symbol):
        """Automatically fetch current price for selected symbol and subscribe to websocket"""
        try:
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                self.price_value.set("No API")
                applicationLogger.warning("Master account not available for auto-fetch")
                return
            
            # Get latest price
            price = self.symbol_manager.get_latest_price(api, trading_symbol)
            if price:
                self.price_value.set(price)
                # Leave exit and modify boxes empty - they will be populated when buttons are pressed
                self.premium_price_value.set(price)  # Set initial premium price
                
                # Clear modify price fields when fetching new price
                self.modify_buy_value.set("")
                self.modify_exit_value.set("")
                applicationLogger.info("Modify price fields cleared after auto-fetch")
                
                # Subscribe to websocket for live updates
                self.subscribe_to_live_price(api, trading_symbol)
                applicationLogger.info(f"Auto-subscribed to {trading_symbol} at price {price}")
            else:
                self.price_value.set("N/A")
                applicationLogger.warning(f"Could not fetch price for {trading_symbol}")
                
        except Exception as e:
            self.price_value.set("Error")
            applicationLogger.error(f"Error in auto-fetch for {trading_symbol}: {e}")

    def fetch_price(self):

        """Fetch current price for selected symbol and subscribe to websocket"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                messagebox.showerror("Error", "Master account not available")
                return
            
            # Get latest price
            price = self.symbol_manager.get_latest_price(api, trading_symbol)
            if price:
                self.price_value.set(price)

                # Leave exit and modify boxes empty - they will be populated when buttons are pressed
                self.premium_price_value.set(price)  # Set initial premium price
                
                # Clear modify price fields when fetching new price
                self.modify_buy_value.set("")
                self.modify_exit_value.set("")
                applicationLogger.info("Modify price fields cleared after fetching new price")
                
                # Subscribe to websocket for live updates
                self.subscribe_to_live_price(api, trading_symbol)
            else:
                messagebox.showerror("Error", "Could not fetch price")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching price: {e}")
    

    def subscribe_to_live_price(self, api, trading_symbol: str):
        """Subscribe to websocket for live price updates using master account (account 1) only"""
        try:
            # Determine exchange
            if 'SENSEX' in trading_symbol:
                exchange = 'BFO'
            else:
                exchange = 'NFO'
            
            # Get token for the symbol
            token = self.symbol_manager.get_token(trading_symbol)
            if not token:
                applicationLogger.error(f"Could not get token for {trading_symbol}")
                return
            
            # Unsubscribe from previous subscription if exists
            if self.current_subscription:
                try:
                    api.unsubscribe(self.current_subscription)
                    applicationLogger.info(f"Unsubscribed from previous: {self.current_subscription}")
                except Exception as e:
                    applicationLogger.warning(f"Error unsubscribing from previous: {e}")
            
            # Subscribe to new symbol using master account's WebSocket (account 1)
            websocket_token = f'{exchange}|{token}'
            api.subscribe(websocket_token)
            self.current_subscription = websocket_token
            applicationLogger.info(f"Subscribed to live price feed via master account: {websocket_token}")
            
        except Exception as e:
            applicationLogger.error(f"Error subscribing to live price: {e}")
    
    def update_live_price(self, live_price: float):
        """Update the premium price box with live price and check SL/Target breaches"""
        try:
            # Update the premium price box with live price
            self.premium_price_value.set(f"{live_price:.2f}")
            applicationLogger.debug(f"Updated live price: {live_price}")
            
            # Calculate local PnL for active positions
            self.calculate_local_pnl(live_price)
            
            # Check for SL/Target breaches
            self.check_sl_target_breach(live_price)
            
            # Check for trailing stop updates
            self.check_trailing_stop(live_price)
            
        except Exception as e:
            applicationLogger.error(f"Error updating live price: {e}")
    
    def calculate_local_pnl(self, live_price: float):
        """Calculate local PnL for active positions based on live price"""
        try:
            for account_num in [1, 2]:  # Master and child accounts
                position = self.position_data[account_num]
                
                # Only calculate if position is active
                if position['active'] and position['buy_price'] is not None and position['qty'] is not None:
                    buy_price = position['buy_price']
                    qty = position['qty']
                    
                    # Calculate unrealized PnL
                    unrealized_pnl = (live_price - buy_price) * qty
                    
                    # PnL display removed - only shown when Show PnL is pressed
                    
                    # Mark as needing verification
                    position['needs_verification'] = True
                    
                    applicationLogger.debug(f"Local PnL calculated for account {account_num}: {unrealized_pnl:.2f} (Price: {live_price:.2f}, Buy: {buy_price:.2f}, Qty: {qty})")
                    
        except Exception as e:
            applicationLogger.error(f"Error calculating local PnL: {e}")
    
    def verify_pnl_from_broker(self):
        """Verify PnL by fetching actual data from broker and show for 1 second"""
        try:
            applicationLogger.info("Verifying PnL from broker...")
            
            # Show PnL display
            self.show_pnl_display()
            
            pnl_found = False
            for account_num in [1, 2]:  # Master and child accounts
                position = self.position_data[account_num]
                
                # Only verify if account is active and has positions
                if (self.account_manager.accounts[account_num]['active'] or 
                    self.account_manager.accounts[account_num].get('blocked', False)):
                    
                    api = self.account_manager.accounts[account_num]['api']
                    if api:
                        # Get actual PnL from broker
                        broker_pnl = self.calculate_pnl(api)
                        
                        # Update position data
                        position['verified_pnl'] = broker_pnl
                        position['needs_verification'] = False
                        
                        # Update PnL display
                        self.update_pnl_display(account_num, broker_pnl)
                        pnl_found = True
                        
                        status = "blocked" if self.account_manager.accounts[account_num].get('blocked', False) else "active"
                        applicationLogger.info(f"Verified PnL for account {account_num} ({status}): {broker_pnl}")
            
            if not pnl_found:
                applicationLogger.warning("No active accounts found for PnL verification")
                # Set empty values to show that button was pressed
                self.master_pnl_value.set("No Data")
                self.child_pnl_value.set("No Data")
            
            # Log verification complete
            applicationLogger.info("PnL verification completed successfully")
            
            # Schedule hiding PnL display after 1 second
            self.root.after(1000, self.hide_pnl_display)
            
        except Exception as e:
            applicationLogger.error(f"Error verifying PnL from broker: {e}")
            # Hide PnL display even if there's an error
            self.root.after(1000, self.hide_pnl_display)
    
    def update_verify_pnl_button_state(self):
        """Update Show PnL button state based on active positions"""
        try:
            # Check if any account has an active position
            has_active_position = any(
                self.position_data[account_num]['active'] 
                for account_num in [1, 2]
            )
            
            # Disable button if any position is active, enable otherwise
            if has_active_position:
                self.verify_pnl_button.config(state='disabled')
                applicationLogger.debug("Show PnL button disabled - active position detected")
            else:
                self.verify_pnl_button.config(state='normal')
                applicationLogger.debug("Show PnL button enabled - no active positions")
                
        except Exception as e:
            applicationLogger.error(f"Error updating Show PnL button state: {e}")
    
    def hide_pnl_display(self):
        """Clear PnL display values"""
        try:
            self.master_pnl_value.set("")
            self.child_pnl_value.set("")
            applicationLogger.debug("PnL display values cleared")
        except Exception as e:
            applicationLogger.error(f"Error clearing PnL display: {e}")
    
    def show_pnl_display(self):
        """Show PnL display (widgets are always visible, just ensure values are set)"""
        try:
            # Widgets are always visible, this method just ensures they're ready
            applicationLogger.debug("PnL display ready to show values")
        except Exception as e:
            applicationLogger.error(f"Error preparing PnL display: {e}")
    
    def update_price_input_state(self):
        """Update price input box state based on active positions"""
        try:
            # Check if price_box exists
            if not hasattr(self, 'price_box'):
                applicationLogger.error("Price box not found - GUI may not be fully initialized")
                return
            
            # Check if any account has an active position
            has_active_position = any(
                self.position_data[account_num]['active'] 
                for account_num in [1, 2]
            )
            
            # Disable price input if any position is active, enable otherwise
            if has_active_position:
                self.price_box.config(state='disabled', bg='lightgray')
                applicationLogger.info("Price input box disabled - active position detected")
            else:
                self.price_box.config(state='normal', bg='white')
                applicationLogger.info("Price input box enabled - no active positions")
                
        except Exception as e:
            applicationLogger.error(f"Error updating price input state: {e}")
    
    def get_account_name(self, account_num: int) -> str:
        """Get the account holder name for a specific account"""
        try:
            if account_num in self.account_manager.accounts:
                client_name = self.account_manager.accounts[account_num].get('client_name')
                if client_name:
                    return client_name
            return "Not Logged In"
        except Exception as e:
            applicationLogger.error(f"Error getting account name for account {account_num}: {e}")
            return "Not Logged In"
    
    def get_ready_status_message(self, account_num: int) -> str:
        """Get the ready status message with account holder name"""
        try:
            account_name = self.get_account_name(account_num)
            return f"{account_name} Ready - No Orders"
        except Exception as e:
            applicationLogger.error(f"Error getting ready status message for account {account_num}: {e}")
            return "Ready - No Orders"
    
    def update_order_status(self, account_num: int, status_message: str):
        """Update order status display for an account"""
        try:
            if account_num == 1:  # Master account
                self.master_order_status.set(status_message)
                applicationLogger.info(f"Master order status updated: {status_message}")
            elif account_num == 2:  # Child account
                self.child_order_status.set(status_message)
                applicationLogger.info(f"Child order status updated: {status_message}")
        except Exception as e:
            applicationLogger.error(f"Error updating order status for account {account_num}: {e}")
    
    def _update_account_status_displays(self):
        """Update account status displays based on current state manager status"""
        try:
            # Update Master account status
            master_status = self.state_manager.get_account_status(1)
            if master_status:
                if master_status['status'] == 'active':
                    self.master_order_status.set("Master Account Ready")
                else:
                    self.master_order_status.set("Master Not Logged In")
            else:
                self.master_order_status.set("Master Not Logged In")
            
            # Update Child account status
            child_status = self.state_manager.get_account_status(2)
            if child_status:
                if child_status['status'] == 'active':
                    self.child_order_status.set("Child Account Ready")
                else:
                    self.child_order_status.set("Child Not Logged In")
            else:
                self.child_order_status.set("Child Not Logged In")
                
            applicationLogger.info("Account status displays updated after release")
            
        except Exception as e:
            applicationLogger.error(f"Error updating account status displays: {e}")
    
    def on_buy_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle buy order completion - start SL/Target monitoring if configured"""
        try:
            applicationLogger.info(f"Buy order completed for account {account_num}: {symbol} @ {price}")
            
            # Check if SL and Target prices are set
            sl_price_text = self.sl_price_value.get().strip()
            target_price_text = self.target_price_value.get().strip()
            
            if sl_price_text:
                try:
                    sl_price = float(sl_price_text)
                    self.start_sl_monitoring(sl_price)
                    applicationLogger.info(f"SL monitoring started at: {sl_price}")
                except ValueError:
                    applicationLogger.warning("Invalid SL price format")
            
            if target_price_text:
                try:
                    target_price = float(target_price_text)
                    self.start_target_monitoring(target_price)
                    applicationLogger.info(f"Target monitoring started at: {target_price}")
                except ValueError:
                    applicationLogger.warning("Invalid Target price format")
            
            # Enable exit button when buy orders are completed
            self.exit_button.config(state='normal')
            self.exit_all_button.config(state='normal')
            
            # Enable individual exit buttons based on active accounts
            if 1 in self.account_manager.get_all_active_accounts():
                self.exit_master_button.config(state='normal')
            if 2 in self.account_manager.get_all_active_accounts():
                self.exit_child_button.config(state='normal')
                
            applicationLogger.info("Sell Order buttons enabled after buy order completion")
            
            # Track position data for local PnL calculation
            if account_num in self.position_data:
                # Get quantity from the order that was placed
                qty = self.quantities.get(account_num, 0)
                self.position_data[account_num]['buy_price'] = price
                self.position_data[account_num]['qty'] = qty
                self.position_data[account_num]['active'] = True
                self.position_data[account_num]['symbol'] = symbol
                self.position_data[account_num]['needs_verification'] = False
                
                applicationLogger.info(f"Position tracked for account {account_num}: {symbol} @ {price}, Qty: {qty}")
            
            # Update Show PnL button state
            self.update_verify_pnl_button_state()
            
            # Update price input state
            self.update_price_input_state()
            
            # Update PnL after buy order completion
            self.update_pnl_on_trade(account_num)
                    
        except Exception as e:
            applicationLogger.error(f"Error handling buy order completion: {e}")
    
    def on_sell_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle sell order completion - reset SL/Target monitoring and check if both accounts are complete"""
        try:
            applicationLogger.info(f"Sell order completed for account {account_num}: {symbol} @ {price}")
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            applicationLogger.info("SL and Target monitoring reset after sell order completion")
            
            # Clear position data for local PnL calculation
            if account_num in self.position_data:
                self.position_data[account_num]['active'] = False
                self.position_data[account_num]['buy_price'] = None
                self.position_data[account_num]['qty'] = None
                self.position_data[account_num]['symbol'] = None
                self.position_data[account_num]['needs_verification'] = False
                
                applicationLogger.info(f"Position cleared for account {account_num} after sell completion")
            
            # Update Show PnL button state
            self.update_verify_pnl_button_state()
            
            # Update price input state
            self.update_price_input_state()
            
            # Update PnL after sell order completion
            self.update_pnl_on_trade(account_num)
            
            # Block accounts when lifecycle completes
            if account_num == 1:  # Master account
                self.block_master_account("Master lifecycle completed")
                # If Child was already blocked, keep it blocked until Release button
                if self.is_child_account_blocked():
                    applicationLogger.info("Child account remains blocked until Release button is pressed")
            elif account_num == 2:  # Child account
                self.block_child_account("Child lifecycle completed")
                # If Master was already blocked, keep it blocked until Release button
                if self.is_master_account_blocked():
                    applicationLogger.info("Master account remains blocked until Release button is pressed")
            
            # Check if both master and child sell orders are complete
            self.check_and_reset_after_sell_complete()
            
        except Exception as e:
            applicationLogger.error(f"Error handling sell order completion: {e}")
    
    def check_and_reset_after_sell_complete(self):
        """Check if both accounts have completed sell orders and reset to buy order status"""
        try:
            # Check if both master and child accounts are active and have completed sell orders
            master_active = self.account_manager.accounts[1]['active']
            child_active = self.account_manager.accounts[2]['active']
            
            if not master_active and not child_active:
                return  # No active accounts
            
            # Check if both active accounts show sell order complete status
            master_sell_complete = False
            child_sell_complete = False
            
            if master_active:
                master_status = self.master_order_status.get()
                master_sell_complete = "Sell Order Complete" in master_status
                applicationLogger.info(f"Master sell complete check: {master_sell_complete} (status: {master_status})")
            
            if child_active:
                child_status = self.child_order_status.get()
                child_sell_complete = "Sell Order Complete" in child_status
                applicationLogger.info(f"Child sell complete check: {child_sell_complete} (status: {child_status})")
            
            # If both active accounts have completed sell orders, reset to buy order status
            if (not master_active or master_sell_complete) and (not child_active or child_sell_complete):
                applicationLogger.info("Both accounts have completed sell orders - resetting to buy order status")
                self.reset_to_buy_order_status()
            
        except Exception as e:
            applicationLogger.error(f"Error checking sell order completion: {e}")
    
    def reset_to_buy_order_status(self):
        """Reset UI after sell orders are complete - keep BUY button disabled until Release is pressed"""
        try:
            # Reset order status displays
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(self.get_ready_status_message(1))
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(self.get_ready_status_message(2))
            
            # Keep buy button disabled - user must press Release button to enable
            self.buy_button.config(state='disabled', text="Press RELEASE to Enable")
            
            # Keep price box disabled - user must press Release button to enable
            self.price_box.config(state='disabled', bg='lightgray')
            
            # Disable exit-related buttons
            self.exit_button.config(state='disabled')
            self.exit_all_button.config(state='disabled')
            self.exit_master_button.config(state='disabled')
            self.exit_child_button.config(state='disabled')
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            
            # Disable buy-related buttons until new orders are placed
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            self.cancel_master_buy_button.config(state='disabled')
            self.cancel_child_buy_button.config(state='disabled')
            
            # Clear order numbers
            self.order_numbers = {1: None, 2: None}
            self.exit_order_numbers = {1: None, 2: None}
            
            applicationLogger.info("UI reset after sell completion - BUY button and Price Box disabled until Release is pressed")
            
        except Exception as e:
            applicationLogger.error(f"Error resetting to buy order status: {e}")
    
    def _handle_margin_shortfall(self):
        """Handle margin shortfall scenario - show error and reset UI"""
        try:
            details = self.order_manager.margin_shortfall_details
            if not details:
                return
            
            failed_accounts = details['failed_accounts']
            cancelled_orders = details['cancelled_orders']
            
            # Create error message
            error_msg = "MARGIN SHORTFALL DETECTED!\n\n"
            error_msg += "Order placement failed due to insufficient margin on one or more accounts.\n\n"
            
            if failed_accounts:
                error_msg += "Failed Accounts:\n"
                for account_index, error_reason in failed_accounts:
                    account_name = self.get_account_name(account_index + 1)
                    error_msg += f"• {account_name}: {error_reason}\n"
            
            if cancelled_orders:
                error_msg += "\nCancelled Orders (due to margin shortfall):\n"
                for account_index, order_num in cancelled_orders:
                    account_name = self.get_account_name(account_index)
                    error_msg += f"• {account_name}: Order {order_num}\n"
            
            error_msg += "\nAll orders have been cancelled. Please check your margin and try again."
            
            # Show error popup
            messagebox.showerror("Margin Shortfall Error", error_msg)
            
            # Reset UI to initial state
            self._reset_ui_after_margin_shortfall()
            
            # Reset margin shortfall flags
            self.order_manager.margin_shortfall_occurred = False
            self.order_manager.margin_shortfall_details = None
            
        except Exception as e:
            applicationLogger.error(f"Error handling margin shortfall: {e}")
            messagebox.showerror("Error", f"Error handling margin shortfall: {e}")
    
    def _handle_buy_order_failure(self, failed_accounts, successful_orders, all_active_accounts):
        """Handle buy order failure - cancel entire lifecycle"""
        try:
            applicationLogger.error(f"Handling buy order failure for accounts: {failed_accounts}")
            
            # Cancel all successful orders to maintain consistency
            if successful_orders:
                applicationLogger.info(f"Cancelling successful orders: {successful_orders}")
                self._cancel_successful_orders(successful_orders)
            
            # Block all accounts that were supposed to be active
            for account_num in all_active_accounts:
                if account_num == 1:
                    self.block_master_account("Buy order placement failed")
                elif account_num == 2:
                    self.block_child_account("Buy order placement failed")
            
            # Create error message
            error_msg = "BUY ORDER PLACEMENT FAILED!\n\n"
            error_msg += "One or more accounts failed to place buy orders.\n\n"
            
            if failed_accounts:
                error_msg += "Failed Accounts:\n"
                for account_num in failed_accounts:
                    account_name = self.get_account_name(account_num)
                    error_msg += f"• {account_name}\n"
            
            if successful_orders:
                error_msg += "\nSuccessfully Placed Orders (now cancelled):\n"
                for account_num, order_num in successful_orders:
                    account_name = self.get_account_name(account_num)
                    error_msg += f"• {account_name}: Order {order_num}\n"
            
            error_msg += "\nAll orders have been cancelled to maintain consistency.\n"
            error_msg += "Please check your accounts and try again."
            
            # Show error popup
            messagebox.showerror("Buy Order Failure", error_msg)
            
            # Reset UI to initial state
            self._reset_ui_after_order_failure()
            
        except Exception as e:
            applicationLogger.error(f"Error handling buy order failure: {e}")
            messagebox.showerror("Error", f"Error handling buy order failure: {e}")
    
    def _cancel_successful_orders(self, successful_orders):
        """Cancel all successful orders to maintain consistency"""
        try:
            for account_num, order_num in successful_orders:
                if order_num:
                    api = self.account_manager.get_api(account_num)
                    if api:
                        # Cancel the order
                        cancel_result = api.cancel_order(order_num)
                        if cancel_result and cancel_result.get('stat') == 'Ok':
                            applicationLogger.info(f"Successfully cancelled order {order_num} for account {account_num}")
                        else:
                            applicationLogger.error(f"Failed to cancel order {order_num} for account {account_num}")
                            
                        # Clear the order number
                        self.order_numbers[account_num] = None
                        
        except Exception as e:
            applicationLogger.error(f"Error cancelling successful orders: {e}")
    
    def _reset_ui_after_order_failure(self):
        """Reset UI to initial state after order failure"""
        try:
            # Re-enable buy button
            self.buy_button.config(state='normal', text="BUY")
            
            # Disable all other buttons
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            self.cancel_master_buy_button.config(state='disabled')
            self.cancel_child_buy_button.config(state='disabled')
            self.exit_button.config(state='disabled')
            self.exit_all_button.config(state='disabled')
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            
            # Clear order numbers
            self.order_numbers = {1: None, 2: None}
            self.exit_order_numbers = {1: None, 2: None}
            
            # Reset order status displays
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(self.get_ready_status_message(1))
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(self.get_ready_status_message(2))
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            
            # Re-enable price box
            self.price_box.config(state='normal', bg='white')
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            
            applicationLogger.info("UI reset after buy order failure")
            
        except Exception as e:
            applicationLogger.error(f"Error resetting UI after order failure: {e}")
    
    def logout_child_account(self):
        """Block child account from sending orders while keeping PnL active"""
        try:
            if self.account_manager.accounts[2]['active'] or self.account_manager.accounts[2].get('blocked', False):
                # Block the child account from sending orders
                success, message = self.account_manager.logout_account(2)
                if success:
                    # Update state manager to reflect blocked status
                    self.state_manager.update_order_status(2, 'blocked', 'Child account logged out - orders blocked')
                    
                    # Block child account from sending any orders
                    self.child_orders_blocked = True
                    
                    # Update UI to show blocked status
                    client_name = self.account_manager.accounts[2].get('client_name', 'Child Account')
                    self.child_order_status.set(f"{client_name} - Orders Blocked (PnL Active)")
                    self.login_button2.config(text=f"{client_name} - Orders Blocked")
                    self.login_button2.config(state='disabled', style="LoginError.TButton")
                    
                    # Disable any active trailing for child account
                    if self.trailing_active:
                        self.trailing_active = False
                        self.trailing_stop_display_label.config(text="")
                        self.trail_status_text.set("Trailing Disabled - Child Orders Blocked")
                    
                    applicationLogger.info("Child account blocked from sending orders - PnL monitoring continues")
                    messagebox.showinfo("Success", f"Child account blocked from sending orders.\nPnL monitoring continues for {client_name}.")
                else:
                    applicationLogger.error(f"Failed to block child account: {message}")
                    messagebox.showerror("Error", f"Failed to block child account: {message}")
            else:
                messagebox.showwarning("Warning", "Child account is not logged in")
        except Exception as e:
            applicationLogger.error(f"Error blocking child account: {e}")
            messagebox.showerror("Error", f"Error blocking child account: {e}")
    
    def place_buy_orders(self):
        """Place buy orders across all active accounts"""
        try:
            # Check if Master account is blocked
            if self.is_master_account_blocked():
                applicationLogger.warning(f"Master account is blocked: {self.master_block_reason}")
                return
            
            # Check if Child account is blocked
            if self.is_child_account_blocked():
                applicationLogger.warning(f"Child account is blocked: {self.child_block_reason}")
                return
            
            # No global rejection blocking check - we'll handle individual account blocking in the order logic

            # Check if buy button is disabled (orders already placed)
            if self.buy_button['state'] == 'disabled':
                messagebox.showwarning("Warning", "Orders already placed! Use RELEASE button to enable new orders.")
                return
                
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.price_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Store original buy price for modify functionality
            self.original_buy_price = price
            applicationLogger.info(f"Original buy price stored: {price}")
            

            # Set quantities for all accounts - master uses selected quantity, child uses configured lots
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    
                    if lot_size:
                        # Master account: Use selected quantity (ensure it's multiple of lot size)
                        if qty1 % lot_size == 0:
                            master_qty = qty1
                        else:
                            master_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                        
                        # Child account: Use configured lots * lot size
                        child_lots = self.settings.get('child_default_lots', 1)
                        child_qty = lot_size * child_lots
                        
                        self.quantities[1] = master_qty
                        self.quantities[2] = child_qty
                        
                        applicationLogger.info(f"Master quantity: {master_qty} (selected: {qty1}, lot size: {lot_size})")
                        applicationLogger.info(f"Child quantity: {child_qty} (lots: {child_lots}, lot size: {lot_size})")
                    else:
                        # Fallback to original quantity if lot size not found
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.warning(f"Lot size not found, using original quantity for both accounts: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get active accounts from state manager
            active_accounts = self.state_manager.get_active_accounts()
            
            # Remove child account if orders are blocked (legacy check)
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from buy orders")
            
            applicationLogger.info(f"Active accounts: {active_accounts}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts found. Please login to accounts first.")
                return
            
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            applicationLogger.info(f"Placing buy orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place regular buy orders (limit orders)
            order_numbers = self.order_manager.place_buy_orders(
                apis, quantities, trading_symbol, price, active_flags
            )
            
            # Check for margin shortfall and handle accordingly
            if self.order_manager.margin_shortfall_occurred:
                self._handle_margin_shortfall()
                return
            
            # Check for any order placement failures and handle accordingly
            failed_orders = []
            successful_orders = []
            
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    successful_orders.append((active_accounts[i], order_num))
                else:
                    failed_orders.append(active_accounts[i])
            
            # If any orders failed, cancel entire lifecycle
            if failed_orders:
                applicationLogger.error(f"Order placement failed for accounts: {failed_orders}")
                self._handle_buy_order_failure(failed_orders, successful_orders, active_accounts)
                return
            
            # Update order numbers for successful orders
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    self.order_numbers[active_accounts[i]] = order_num
            
            # Auto-set SL and Target based on buy order price
            self.auto_set_sl_target_from_buy_price(price)
            
            # Start cross-account coordination if both master and child are active
            if 1 in active_accounts and 2 in active_accounts:
                self.start_order_coordination()
                applicationLogger.info("Cross-account coordination started for buy orders")
            

            # Update order status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Orders Placed - Waiting for Status")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Orders Placed - Waiting for Status")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            # Disable buy button and update text with price
            self.buy_button.config(state='disabled', text=f"OrderPlaced@{price}")
            applicationLogger.info("Buy button disabled to prevent duplicate orders")
            
            # Gray out the price box to prevent price changes after order placement
            self.price_box.config(state='disabled', bg='lightgray')
            applicationLogger.info("Price box grayed out after order placement")
            
            # Enable buy-related buttons for order management
            self.cancel_buy_button.config(state='normal')
            # Don't enable modify button yet - wait for order state confirmation
            self.modify_buy_button.config(state='disabled')
            
            # Enable individual cancel buttons based on active accounts
            if 1 in active_accounts:
                self.cancel_master_buy_button.config(state='normal', text="Cancel Master Buy Order")
            if 2 in active_accounts:
                self.cancel_child_buy_button.config(state='normal', text="Cancel Child Buy Order")
            
            applicationLogger.info("Cancel Buy and Modify Buy buttons enabled after buy orders placed")
            
            # Keep exit button disabled until buy orders are completed
            self.exit_button.config(state='disabled')
            applicationLogger.info("Sell Order button kept disabled until buy orders are completed")
            
        except Exception as e:

            applicationLogger.error(f"Error placing buy orders: {e}")
            # Update order status displays to show error
            active_accounts = self.account_manager.get_all_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Error: {str(e)[:50]}...")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Error: {str(e)[:50]}...")
            else:
                self.child_order_status.set("Child Not Logged In")
    
    def place_exit_orders(self, order_type='LMT'):
        """Place exit orders across all active accounts
        
        Args:
            order_type: 'LMT' for limit orders, 'MKT' for market orders
        """
        try:
            # No global rejection blocking check - we'll handle individual account blocking in the order logic

            # Check if exit button is disabled (orders already placed)
            if self.exit_button['state'] == 'disabled':
                messagebox.showwarning("Warning", "Exit orders already placed! Use RELEASE button to enable new orders.")
                return
                
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")

                return
            
            # If exit price box is empty, populate with current LTP and return (don't place order yet)
            if not self.price1_value.get().strip():
                current_ltp = self.premium_price_value.get()
                if current_ltp:
                    self.price1_value.set(current_ltp)
                    applicationLogger.info(f"Exit price box populated with current LTP: {current_ltp}")
                    return  # Stop here - user needs to press button again to place order
                else:
                    messagebox.showerror("Error", "Please fetch current price first")
                return
            
            price = float(self.price1_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Stop target and trailing monitoring when SELL Order button is pressed
            if self.target_monitoring_active:
                self.stop_target_monitoring()
                applicationLogger.info("Target monitoring stopped due to SELL Order button press")
            
            if self.trailing_active:
                self.stop_trailing_monitoring()
                applicationLogger.info("Trailing monitoring stopped due to SELL Order button press")
            
            # Log current position status for debugging
            accounts_with_positions = self.get_accounts_with_open_positions()
            applicationLogger.info(f"Position status before exit: {accounts_with_positions}")

            # Set quantities for all accounts - master uses selected quantity, child uses configured lots
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    
                    if lot_size:
                        # Master account: Use selected quantity (ensure it's multiple of lot size)
                        if qty1 % lot_size == 0:
                            master_qty = qty1
                        else:
                            master_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                        
                        # Child account: Use configured lots * lot size
                        child_lots = self.settings.get('child_default_lots', 1)
                        child_qty = lot_size * child_lots
                        
                        self.quantities[1] = master_qty
                        self.quantities[2] = child_qty
                        
                        applicationLogger.info(f"Master quantity: {master_qty} (selected: {qty1}, lot size: {lot_size})")
                        applicationLogger.info(f"Child quantity: {child_qty} (lots: {child_lots}, lot size: {lot_size})")
                    else:
                        # Fallback to original quantity if lot size not found
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.warning(f"Lot size not found, using original quantity for both accounts: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get accounts with open positions (position-based monitoring)
            accounts_with_positions = self.get_accounts_with_open_positions()
            
            # Filter by state manager - only accounts that can place exit orders
            active_accounts = []
            for account_id in accounts_with_positions:
                if self.state_manager.can_exit_orders(account_id):
                    active_accounts.append(account_id)
            
            # Remove child account if orders are blocked (legacy check)
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from exit orders")
            
            applicationLogger.info(f"Accounts with open positions for exit: {active_accounts}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No accounts with open positions found. All positions may already be closed.")
                return
            
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            applicationLogger.info(f"Placing exit orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place orders
            order_numbers = self.order_manager.place_exit_orders(
                apis, quantities, trading_symbol, price, active_flags, order_type
            )
            
            # Update exit order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    self.exit_order_numbers[active_accounts[i]] = order_num
            

            # Update order status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Exit Orders Placed - Waiting for Status")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Exit Orders Placed - Waiting for Status")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            # Disable exit button and update text with price
            self.exit_button.config(state='disabled', text=f"SellOrderPlaced@{price}")
            self.exit_all_button.config(state='disabled')
            applicationLogger.info("Sell Order button disabled to prevent duplicate orders")
            
            # Enable exit-related buttons for order management
            self.cancel_exit_button.config(state='normal')
            self.modify_exit_button.config(state='normal')
            applicationLogger.info("Cancel Exit and Modify Exit buttons enabled after exit orders placed")
            
        except Exception as e:

            applicationLogger.error(f"Error placing exit orders: {e}")
            # Update order status displays to show error
            active_accounts = self.account_manager.get_all_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Error: {str(e)[:50]}...")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Error: {str(e)[:50]}...")
            else:
                self.child_order_status.set("Child Not Logged In")
    
    def place_dynamic_stop_loss_orders(self, price):
        """Place dynamic stop loss orders (sell) with price adjustment"""
        try:
            # Get active accounts
            active_accounts = []
            apis = []
            quantities = []
            active_flags = []
            
            for i in range(1, 3):  # Master and Child accounts
                if self.account_manager.accounts[i]['active']:
                    # Check if account is blocked
                    if (i == 1 and self.is_master_account_blocked()) or (i == 2 and self.is_child_account_blocked()):
                        applicationLogger.warning(f"Account {i} is blocked, skipping dynamic stop loss order")
                        active_flags.append(False)
                        continue
                    
                    active_accounts.append(i)
                    apis.append(self.account_manager.accounts[i]['api'])
                    quantities.append(self.account_manager.accounts[i]['quantity'])
                    active_flags.append(True)
                else:
                    active_flags.append(False)
            
            if not active_accounts:
                applicationLogger.warning("No active accounts for dynamic stop loss orders")
                return
            
            # Get trading symbol
            trading_symbol = self.trading_symbol_var.get()
            
            applicationLogger.info(f"Placing dynamic stop loss orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place dynamic stop loss orders
            order_numbers = self.order_manager.place_dynamic_stop_loss_orders(
                apis, quantities, trading_symbol, price, active_flags
            )
            
            # Update order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num and i < len(active_accounts):
                    account_index = active_accounts[i] - 1  # Convert to 0-based index
                    self.order_numbers[account_index] = order_num
            
            applicationLogger.info("Dynamic stop loss orders placed successfully")
            
        except Exception as e:
            applicationLogger.error(f"Error placing dynamic stop loss orders: {e}")
            # Update order status displays to show error
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set("Error placing stop loss orders")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set("Error placing stop loss orders")
    
    def place_dynamic_target_orders(self, price):
        """Place dynamic target orders (sell) with price adjustment"""
        try:
            # Get active accounts
            active_accounts = []
            apis = []
            quantities = []
            active_flags = []
            
            for i in range(1, 3):  # Master and Child accounts
                if self.account_manager.accounts[i]['active']:
                    # Check if account is blocked
                    if (i == 1 and self.is_master_account_blocked()) or (i == 2 and self.is_child_account_blocked()):
                        applicationLogger.warning(f"Account {i} is blocked, skipping dynamic target order")
                        active_flags.append(False)
                        continue
                    
                    active_accounts.append(i)
                    apis.append(self.account_manager.accounts[i]['api'])
                    quantities.append(self.account_manager.accounts[i]['quantity'])
                    active_flags.append(True)
                else:
                    active_flags.append(False)
            
            if not active_accounts:
                applicationLogger.warning("No active accounts for dynamic target orders")
                return
            
            # Get trading symbol
            trading_symbol = self.trading_symbol_var.get()
            
            applicationLogger.info(f"Placing dynamic target orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place dynamic target orders
            order_numbers = self.order_manager.place_dynamic_target_orders(
                apis, quantities, trading_symbol, price, active_flags
            )
            
            # Update order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num and i < len(active_accounts):
                    account_index = active_accounts[i] - 1  # Convert to 0-based index
                    self.order_numbers[account_index] = order_num
            
            applicationLogger.info("Dynamic target orders placed successfully")
            
        except Exception as e:
            applicationLogger.error(f"Error placing dynamic target orders: {e}")
            # Update order status displays to show error
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set("Error placing target orders")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set("Error placing target orders")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol (used by dynamic order management)
        Uses last known price if current price is not available
        
        Args:
            symbol: Trading symbol
            
        Returns:
            float: Current price, None if not available
        """
        try:
            # First try to get current price from the premium price display
            current_price_str = self.premium_price_value.get()
            if current_price_str:
                price = float(current_price_str)
                # Update last known price
                self.last_known_prices[symbol] = price
                return price
            
            # If current price is not available, use last known price
            if symbol in self.last_known_prices:
                applicationLogger.debug(f"Using last known price for {symbol}: {self.last_known_prices[symbol]}")
                return self.last_known_prices[symbol]
            
            applicationLogger.warning(f"No price available for {symbol} (current or last known)")
            return None
            
        except Exception as e:
            applicationLogger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def block_master_account(self, reason: str):
        """
        Block Master account from all operations
        
        Args:
            reason: Reason for blocking (e.g., "Order cancelled", "Lifecycle completed")
        """
        self.master_account_blocked = True
        self.master_block_reason = reason
        applicationLogger.warning(f"Master account blocked: {reason}")
        
        # Update Master order status to show blocked state
        self.master_order_status.set(f"Master Blocked: {reason}")
    
    def unblock_master_account(self):
        """Unblock Master account (called by Release button)"""
        self.master_account_blocked = False
        self.master_block_reason = ""
        applicationLogger.info("Master account unblocked via Release button")
        
        # Reset Master order status
        if self.account_manager.accounts[1]['active']:
            self.master_order_status.set("Master Account Ready")
        else:
            self.master_order_status.set("Master Not Logged In")
    
    def is_master_account_blocked(self) -> bool:
        """Check if Master account is blocked"""
        return self.master_account_blocked or self.master_account_rejected_blocked
    
    def is_child_account_blocked(self) -> bool:
        """Check if Child account is blocked"""
        return self.child_account_blocked or self.child_account_rejected_blocked
    
    def is_any_account_rejected_blocked(self) -> bool:
        """Check if any account is blocked due to order rejection"""
        return self.master_account_rejected_blocked or self.child_account_rejected_blocked
    
    def get_blocked_accounts_info(self) -> str:
        """Get information about blocked accounts"""
        blocked_info = []
        if self.master_account_rejected_blocked:
            blocked_info.append(f"Master: {self.master_block_reason}")
        if self.child_account_rejected_blocked:
            blocked_info.append(f"Child: {self.child_block_reason}")
        return "; ".join(blocked_info) if blocked_info else "No accounts blocked"
    
    def update_window_title(self):
        """Update window title based on account status"""
        try:
            if self.is_any_account_rejected_blocked():
                blocked_info = self.get_blocked_accounts_info()
                self.root.title(f"***Kratik's Soft*** - ACCOUNTS BLOCKED: {blocked_info}")
            else:
                # Get master account name
                master_name = self.account_manager.accounts[1].get('client_name', 'Not Logged In')
                if master_name != 'Not Logged In':
                    self.root.title(f"***Kratik's Soft*** - Master Account {master_name} Logged in")
                else:
                    self.root.title("***Kratik's Soft*** - Master Account Not Logged In")
        except Exception as e:
            applicationLogger.error(f"Error updating window title: {e}")
    
    def handle_buy_order_rejection(self, account_num: int, symbol: str, rejection_reason: str):
        """Handle buy order rejection - block account silently"""
        try:
            applicationLogger.warning(f"Buy order rejected for account {account_num} - Symbol: {symbol}, Reason: {rejection_reason}")
            
            # Update state manager with new separated status
            self.state_manager.update_order_status(account_num, 'blocked', f"Buy order rejected: {rejection_reason}")
            # Note: No quantity change needed for rejection (order was never filled)
            
            # Update order status display to show blocked status
            if account_num == 1:
                self.master_order_status.set("Blocked till Reset")
            elif account_num == 2:
                self.child_order_status.set("Blocked till Reset")
            
            # Disable all trading buttons for this account
            self.disable_trading_buttons_for_account(account_num)
            
            # No popup - just log the blocking
            account_name = "Master" if account_num == 1 else "Child"
            applicationLogger.info(f"{account_name} account blocked due to buy order rejection - no further orders allowed")
            
        except Exception as e:
            applicationLogger.error(f"Error handling buy order rejection for account {account_num}: {e}")

    def block_account_on_rejection(self, account_num: int, reason: str):
        """Block account when order is rejected"""
        try:
            if account_num == 1:  # Master account
                self.master_account_rejected_blocked = True
                self.master_block_reason = f"Order Rejected: {reason}"
                applicationLogger.warning(f"Master account blocked due to order rejection: {reason}")
                self.master_order_status.set(f"BLOCKED - {reason}")
            elif account_num == 2:  # Child account
                self.child_account_rejected_blocked = True
                self.child_block_reason = f"Order Rejected: {reason}"
                applicationLogger.warning(f"Child account blocked due to order rejection: {reason}")
                self.child_order_status.set(f"BLOCKED - {reason}")
            
            # Update window title to show blocked status
            self.update_window_title()
        except Exception as e:
            applicationLogger.error(f"Error blocking account {account_num} on rejection: {e}")
    
    def disable_trading_buttons_for_account(self, account_num: int):
        """Disable all trading buttons for a specific account"""
        try:
            if account_num == 1:  # Master account
                # Disable master account specific buttons
                self.login_button1.config(state='disabled', text="Master - BLOCKED")
                applicationLogger.info("Master account trading buttons disabled due to order rejection")
            elif account_num == 2:  # Child account
                # Disable child account specific buttons
                self.login_button2.config(state='disabled', text="Child - BLOCKED")
                applicationLogger.info("Child account trading buttons disabled due to order rejection")
            
            # Disable main trading buttons if any account is blocked
            if self.is_any_account_rejected_blocked():
                self.buy_button.config(state='disabled', text="BLOCKED - Order Rejected")
                self.exit_button.config(state='disabled', text="BLOCKED - Order Rejected")
                self.cancel_buy_button.config(state='disabled')
                self.cancel_exit_button.config(state='disabled')
                self.modify_buy_button.config(state='disabled')
                self.modify_exit_button.config(state='disabled')
                applicationLogger.info("Main trading buttons disabled due to account rejection")
                
        except Exception as e:
            applicationLogger.error(f"Error disabling trading buttons for account {account_num}: {e}")

    def unblock_account_on_release(self, account_num: int):
        """Unblock account when release button is pressed"""
        try:
            if account_num == 1:  # Master account
                self.master_account_rejected_blocked = False
                self.master_block_reason = ""
                applicationLogger.info("Master account unblocked via Release button")
                # Update status based on account state
                if self.account_manager.accounts[1]['active']:
                    self.master_order_status.set("Master Account Ready")
                    # Re-enable master account buttons
                    self.login_button1.config(state='normal', text="Master - Ready")
                else:
                    self.master_order_status.set("Master Not Logged In")
            elif account_num == 2:  # Child account
                self.child_account_rejected_blocked = False
                self.child_block_reason = ""
                applicationLogger.info("Child account unblocked via Release button")
                # Update status based on account state
                if self.account_manager.accounts[2]['active']:
                    self.child_order_status.set("Child Account Ready")
                    # Re-enable child account buttons
                    self.login_button2.config(state='normal', text="Child - Ready")
                else:
                    self.child_order_status.set("Child Not Logged In")
            
            # Re-enable main trading buttons if no accounts are blocked
            if not self.is_any_account_rejected_blocked():
                self.buy_button.config(state='normal', text="BUY")
                self.exit_button.config(state='normal', text="EXIT")
                applicationLogger.info("Main trading buttons re-enabled after account unblock")
            
            # Update window title after unblocking
            self.update_window_title()
        except Exception as e:
            applicationLogger.error(f"Error unblocking account {account_num} on release: {e}")
    
    def block_child_account(self, reason: str):
        """
        Block Child account from all operations
        
        Args:
            reason: Reason for blocking (e.g., "Order cancelled", "Lifecycle completed")
        """
        self.child_account_blocked = True
        self.child_block_reason = reason
        applicationLogger.warning(f"Child account blocked: {reason}")
        
        # Update Child order status to show blocked state
        self.child_order_status.set(f"Child Blocked: {reason}")
    
    def unblock_child_account(self):
        """Unblock Child account (called by Release button)"""
        self.child_account_blocked = False
        self.child_block_reason = ""
        applicationLogger.info("Child account unblocked via Release button")
        
        # Reset Child order status
        if self.account_manager.accounts[2]['active']:
            self.child_order_status.set("Child Account Ready")
        else:
            self.child_order_status.set("Child Not Logged In")
    
    def is_child_account_blocked(self) -> bool:
        """Check if Child account is blocked"""
        return self.child_account_blocked
    
    def cancel_buy_orders(self):
        """Cancel buy orders across all active accounts"""
        try:
            # Get accounts that can place orders (not blocked/inactive)
            active_accounts = self.state_manager.get_active_accounts()
            
            # Remove child account if orders are blocked (legacy check)
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from cancel buy orders")
            
            # Only include accounts that have valid order numbers
            valid_accounts = []
            apis = []
            order_numbers = []
            
            for i in active_accounts:
                # Check if account is inactive (blocked due to rejection)
                if self.state_manager.is_account_inactive(i):
                    account_name = "Master" if i == 1 else "Child"
                    applicationLogger.warning(f"{account_name} account is inactive - skipping cancel")
                    continue
                    
                if i in self.order_numbers and self.order_numbers[i]:
                    valid_accounts.append(i)
                    apis.append(self.account_manager.get_api(i))
                    order_numbers.append(self.order_numbers[i])
                else:
                    applicationLogger.warning(f"Account {i} has no valid order number, skipping cancel")
            
            if not valid_accounts:
                messagebox.showerror("Error", "No valid orders found to cancel")
                return
            
            active_flags = [True] * len(valid_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)

            # Update status displays based on valid accounts that were cancelled
            if 1 in valid_accounts:
                self.master_order_status.set("Buy Orders Cancelled")
            else:
                # Check actual account state instead of just valid accounts
                master_status = self.state_manager.get_account_status(1)
                if master_status and master_status['status'] == 'inactive':
                    self.master_order_status.set("Blocked till Reset")
                else:
                    self.master_order_status.set("Master Not Logged In")
                
            if 2 in valid_accounts:
                self.child_order_status.set("Buy Orders Cancelled")
            else:
                # Check actual account state instead of just valid accounts
                child_status = self.state_manager.get_account_status(2)
                if child_status and child_status['status'] == 'inactive':
                    self.child_order_status.set("Blocked till Reset")
                else:
                    self.child_order_status.set("Child Not Logged In")
            
            # Re-enable buy button and disable buy-related management buttons
            self.buy_button.config(state='normal', text="BUY")
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            self.cancel_master_buy_button.config(state='disabled')
            self.cancel_child_buy_button.config(state='disabled')
            
            # Re-enable price box for new orders
            self.price_box.config(state='normal', bg='white')
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            applicationLogger.info("Buy button and price box re-enabled after cancelling buy orders")
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            
        except Exception as e:

            applicationLogger.error(f"Error cancelling buy orders: {e}")
            # Update order status displays to show error
            active_accounts = self.state_manager.get_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            else:
                # Check actual account state instead of just active status
                master_status = self.state_manager.get_account_status(1)
                if master_status and master_status['status'] == 'inactive':
                    self.master_order_status.set("Blocked till Reset")
                else:
                    self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            else:
                # Check actual account state instead of just active status
                child_status = self.state_manager.get_account_status(2)
                if child_status and child_status['status'] == 'inactive':
                    self.child_order_status.set("Blocked till Reset")
                else:
                    self.child_order_status.set("Child Not Logged In")
    
    def cancel_exit_orders(self):
        """Cancel exit orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            
            # Remove child account if orders are blocked
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from cancel exit orders")
            
            # Only include accounts that have valid exit order numbers
            valid_accounts = []
            apis = []
            order_numbers = []
            
            for i in active_accounts:
                if i in self.exit_order_numbers and self.exit_order_numbers[i]:
                    valid_accounts.append(i)
                    apis.append(self.account_manager.get_api(i))
                    order_numbers.append(self.exit_order_numbers[i])
                else:
                    applicationLogger.warning(f"Account {i} has no valid exit order number, skipping cancel")
            
            if not valid_accounts:
                messagebox.showerror("Error", "No valid exit orders found to cancel")
                return
            
            active_flags = [True] * len(valid_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)

            # Update status displays based on valid accounts that were cancelled
            if 1 in valid_accounts:
                self.master_order_status.set("Exit Orders Cancelled")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in valid_accounts:
                self.child_order_status.set("Exit Orders Cancelled")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            # Re-enable exit button and disable exit-related management buttons
            self.exit_button.config(state='normal', text="SELL Order")
            self.exit_all_button.config(state='normal')
            
            # Enable individual exit buttons based on active accounts
            if 1 in self.account_manager.get_all_active_accounts():
                self.exit_master_button.config(state='normal')
            if 2 in self.account_manager.get_all_active_accounts():
                self.exit_child_button.config(state='normal')
                
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            applicationLogger.info("Sell Order button re-enabled after cancelling exit orders")
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            
        except Exception as e:

            applicationLogger.error(f"Error cancelling exit orders: {e}")
            # Update order status displays to show error
            active_accounts = self.account_manager.get_all_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            else:
                self.child_order_status.set("Child Not Logged In")
    
    def cancel_master_buy_order(self):
        """Cancel buy order for master account only"""
        try:
            if not self.account_manager.is_account_active(1):
                self.cancel_master_buy_button.config(text="Master Not Logged In")
                return
            
            if 1 not in self.order_numbers or not self.order_numbers[1]:
                self.cancel_master_buy_button.config(text="No Master Order Found")
                return
            
            master_api = self.account_manager.get_api(1)
            master_order_number = self.order_numbers[1]
            
            # Cancel the master order
            self.order_manager.cancel_orders([master_api], [master_order_number], [True])
            
            # Update state manager with new separated status
            self.state_manager.update_order_status(1, 'blocked', 'Master buy order cancelled by user')
            # Note: No quantity change needed for cancellation (order was never filled)
            
            # Update master order status
            # Block Master account from further operations
            self.block_master_account("Master buy order cancelled")
            
            # Update button text to show cancellation
            self.cancel_master_buy_button.config(text="Master Buy Cancelled")
            
            # Keep buy button disabled until Release button is pressed
            self.buy_button.config(state='disabled', text="Press RELEASE to Enable")
            self.cancel_master_buy_button.config(state='disabled')
            
            # Keep price box disabled until Release button is pressed
            self.price_box.config(state='disabled', bg='lightgray')
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            applicationLogger.info("Master buy order cancelled successfully, price box re-enabled")
            
        except Exception as e:
            applicationLogger.error(f"Error cancelling master buy order: {e}")
            self.master_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            self.cancel_master_buy_button.config(text=f"Error: {str(e)[:20]}...")
    
    def cancel_child_buy_order(self):
        """Cancel buy order for child account only"""
        try:
            if not self.account_manager.is_account_active(2) and not self.account_manager.accounts[2].get('blocked', False):
                self.cancel_child_buy_button.config(text="Child Not Logged In")
                return
            
            if self.child_orders_blocked:
                self.cancel_child_buy_button.config(text="Child Orders Blocked")
                return
            
            if 2 not in self.order_numbers or not self.order_numbers[2]:
                self.cancel_child_buy_button.config(text="No Child Order Found")
                return
            
            child_api = self.account_manager.get_api(2)
            child_order_number = self.order_numbers[2]
            
            # Cancel the child order
            self.order_manager.cancel_orders([child_api], [child_order_number], [True])
            
            # Update state manager with new separated status
            self.state_manager.update_order_status(2, 'blocked', 'Child buy order cancelled by user')
            # Note: No quantity change needed for cancellation (order was never filled)
            
            # Block Child account from further operations
            self.block_child_account("Child buy order cancelled")
            
            # Update button text to show cancellation
            self.cancel_child_buy_button.config(text="Child Buy Cancelled")
            
            # Keep buy button disabled until Release button is pressed
            self.buy_button.config(state='disabled', text="Press RELEASE to Enable")
            self.cancel_child_buy_button.config(state='disabled')
            
            # Re-enable price box for new orders
            self.price_box.config(state='normal', bg='white')
            
            # Clear original buy price and modify box
            self.original_buy_price = None
            self.modify_buy_value.set("")
            applicationLogger.info("Child buy order cancelled successfully, price box re-enabled")
            
        except Exception as e:
            applicationLogger.error(f"Error cancelling child buy order: {e}")
            self.child_order_status.set(f"Cancel Error: {str(e)[:40]}...")
            self.cancel_child_buy_button.config(text=f"Error: {str(e)[:20]}...")
    
    
    def modify_buy_orders(self):
        """Modify buy orders across all active accounts"""
        try:
            # No global blocking check - we'll handle individual account blocking in the order logic
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            # Check if we have an original buy price
            if self.original_buy_price is None:
                messagebox.showerror("Error", "No original buy price found. Please place buy orders first.")
                return
            
            # Check if modify buy box has a value
            if not self.modify_buy_value.get().strip():
                messagebox.showerror("Error", "Please enter a price in the modify buy box")
                return
            
            # Validate the price
            try:
                price = float(self.modify_buy_value.get())
                if price <= 0:
                    messagebox.showerror("Error", "Price must be greater than 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid price")
                return
            
            qty1 = int(self.qty1_var.get())
            

            # Set quantities for all accounts - master uses selected quantity, child uses configured lots
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    
                    if lot_size:
                        # Master account: Use selected quantity (ensure it's multiple of lot size)
                        if qty1 % lot_size == 0:
                            master_qty = qty1
                        else:
                            master_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                        
                        # Child account: Use configured lots * lot size
                        child_lots = self.settings.get('child_default_lots', 1)
                        child_qty = lot_size * child_lots
                        
                        self.quantities[1] = master_qty
                        self.quantities[2] = child_qty
                        
                        applicationLogger.info(f"Master quantity: {master_qty} (selected: {qty1}, lot size: {lot_size})")
                        applicationLogger.info(f"Child quantity: {child_qty} (lots: {child_lots}, lot size: {lot_size})")
                    else:
                        # Fallback to original quantity if lot size not found
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.warning(f"Lot size not found, using original quantity for both accounts: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get accounts that can modify orders from state manager
            active_accounts = self.state_manager.get_accounts_for_modify()
            applicationLogger.info(f"Active accounts for modify buy orders: {active_accounts}")
            
            # Remove child account if orders are blocked (legacy check)
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from modify buy orders")
            
            # Only include accounts that have valid order numbers AND are in modifiable state
            valid_accounts = []
            apis = []
            order_numbers = []
            quantities = []
            
            for i in active_accounts:
                # State manager already filtered for accounts that can modify orders
                # No need for additional blocking checks
                
                if i in self.order_numbers and self.order_numbers[i]:
                    # Check order state for each account
                    if i == 1:  # Master account
                        order_state = self.master_order_state
                    elif i == 2:  # Child account
                        order_state = self.child_order_state
                    else:
                        order_state = None
                    
                    # Only allow modification if order is in PENDING or OPEN state
                    if order_state in ['PENDING', 'OPEN']:
                        valid_accounts.append(i)
                        apis.append(self.account_manager.get_api(i))
                        order_numbers.append(self.order_numbers[i])
                        quantities.append(self.quantities[i])
                        applicationLogger.info(f"Account {i} order is in {order_state} state - allowing modification")
                    else:
                        applicationLogger.warning(f"Account {i} order is in {order_state} state - cannot modify (must be PENDING or OPEN)")
                else:
                    applicationLogger.warning(f"Account {i} has no valid order number, skipping modify")
            
            if not valid_accounts:
                # Check if any orders exist but are in wrong state
                rejected_orders = []
                for i in active_accounts:
                    if i in self.order_numbers and self.order_numbers[i]:
                        if i == 1:
                            order_state = self.master_order_state
                        elif i == 2:
                            order_state = self.child_order_state
                        else:
                            order_state = None
                        
                        if order_state in ['REJECTED', 'CANCELLED', 'FILLED']:
                            rejected_orders.append(f"Account {i} ({order_state})")
                
                if rejected_orders:
                    error_msg = f"Cannot modify orders - some orders are not in modifiable state:\n{', '.join(rejected_orders)}\n\nOnly PENDING or OPEN orders can be modified."
                    messagebox.showerror("Modify Order Error", error_msg)
                    applicationLogger.error(f"Modify order blocked: {error_msg}")
                else:
                    messagebox.showerror("Error", "No valid orders found to modify")
                return
            
            active_flags = [True] * len(valid_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )

            # Auto-adjust SL and Target based on new buy order price
            self.auto_set_sl_target_from_buy_price(price)
            
            # Update the stored original buy price to the new price
            self.original_buy_price = price
            applicationLogger.info(f"Original buy price updated to: {price}")
            
            # Clear modify box after successful modification
            self.modify_buy_value.set("")
            applicationLogger.info("Modify Buy box cleared after successful modification")

            # Update status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Buy Orders Modified - Waiting for Status")
            else:
                # Check actual account state instead of just active status
                master_status = self.state_manager.get_account_status(1)
                if master_status and master_status['status'] == 'inactive':
                    self.master_order_status.set("Blocked till Reset")
                else:
                    self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Buy Orders Modified - Waiting for Status")
            else:
                # Check actual account state instead of just active status
                child_status = self.state_manager.get_account_status(2)
                if child_status and child_status['status'] == 'inactive':
                    self.child_order_status.set("Blocked till Reset")
                else:
                    self.child_order_status.set("Child Not Logged In")
            
        except Exception as e:

            applicationLogger.error(f"Error modifying buy orders: {e}")
            # Update order status displays to show error
            active_accounts = self.state_manager.get_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Modify Error: {str(e)[:40]}...")
            else:
                # Check actual account state instead of just active status
                master_status = self.state_manager.get_account_status(1)
                if master_status and master_status['status'] == 'inactive':
                    self.master_order_status.set("Blocked till Reset")
                else:
                    self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Modify Error: {str(e)[:40]}...")
            else:
                # Check actual account state instead of just active status
                child_status = self.state_manager.get_account_status(2)
                if child_status and child_status['status'] == 'inactive':
                    self.child_order_status.set("Blocked till Reset")
                else:
                    self.child_order_status.set("Child Not Logged In")
    
    def modify_exit_orders(self):
        """Modify exit orders across all active accounts"""
        try:
            # No global blocking check - we'll handle individual account blocking in the order logic
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")

                return
            
            # If modify exit box is empty, populate with current LTP and return (don't place order yet)
            if not self.modify_exit_value.get().strip():
                current_ltp = self.premium_price_value.get()
                if current_ltp:
                    self.modify_exit_value.set(current_ltp)
                    applicationLogger.info(f"Modify Exit box populated with current LTP: {current_ltp}")
                    return  # Stop here - user needs to press button again to place order
                else:
                    messagebox.showerror("Error", "Please fetch current price first")
                return
            
            price = float(self.modify_exit_value.get())
            qty1 = int(self.qty1_var.get())
            

            # Set quantities for all accounts - master uses selected quantity, child uses configured lots
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    
                    if lot_size:
                        # Master account: Use selected quantity (ensure it's multiple of lot size)
                        if qty1 % lot_size == 0:
                            master_qty = qty1
                        else:
                            master_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                        
                        # Child account: Use configured lots * lot size
                        child_lots = self.settings.get('child_default_lots', 1)
                        child_qty = lot_size * child_lots
                        
                        self.quantities[1] = master_qty
                        self.quantities[2] = child_qty
                        
                        applicationLogger.info(f"Master quantity: {master_qty} (selected: {qty1}, lot size: {lot_size})")
                        applicationLogger.info(f"Child quantity: {child_qty} (lots: {child_lots}, lot size: {lot_size})")
                    else:
                        # Fallback to original quantity if lot size not found
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.warning(f"Lot size not found, using original quantity for both accounts: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get accounts that can modify orders from state manager
            active_accounts = self.state_manager.get_accounts_for_modify()
            
            # Remove child account if orders are blocked (legacy check)
            if self.child_orders_blocked and 2 in active_accounts:
                active_accounts.remove(2)
                applicationLogger.warning("Child account orders are blocked - excluding from modify exit orders")
            
            # Only include accounts that have valid exit order numbers AND are in modifiable state
            valid_accounts = []
            apis = []
            order_numbers = []
            quantities = []
            
            for i in active_accounts:
                if i in self.exit_order_numbers and self.exit_order_numbers[i]:
                    # Check order state for each account
                    if i == 1:  # Master account
                        order_state = self.master_order_state
                    elif i == 2:  # Child account
                        order_state = self.child_order_state
                    else:
                        order_state = None
                    
                    # Only allow modification if order is in PENDING or OPEN state
                    if order_state in ['PENDING', 'OPEN']:
                        valid_accounts.append(i)
                        apis.append(self.account_manager.get_api(i))
                        order_numbers.append(self.exit_order_numbers[i])
                        quantities.append(self.quantities[i])
                        applicationLogger.info(f"Account {i} exit order is in {order_state} state - allowing modification")
                    else:
                        applicationLogger.warning(f"Account {i} exit order is in {order_state} state - cannot modify (must be PENDING or OPEN)")
                else:
                    applicationLogger.warning(f"Account {i} has no valid exit order number, skipping modify")
            
            if not valid_accounts:
                # Check if any orders exist but are in wrong state
                rejected_orders = []
                for i in active_accounts:
                    if i in self.exit_order_numbers and self.exit_order_numbers[i]:
                        if i == 1:
                            order_state = self.master_order_state
                        elif i == 2:
                            order_state = self.child_order_state
                        else:
                            order_state = None
                        
                        if order_state in ['REJECTED', 'CANCELLED', 'FILLED']:
                            rejected_orders.append(f"Account {i} ({order_state})")
                
                if rejected_orders:
                    error_msg = f"Cannot modify exit orders - some orders are not in modifiable state:\n{', '.join(rejected_orders)}\n\nOnly PENDING or OPEN orders can be modified."
                    messagebox.showerror("Modify Exit Order Error", error_msg)
                    applicationLogger.error(f"Modify exit order blocked: {error_msg}")
                else:
                    messagebox.showerror("Error", "No valid exit orders found to modify")
                return
            
            active_flags = [True] * len(valid_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )

            # Update status displays based on valid accounts that were modified
            if 1 in valid_accounts:
                self.master_order_status.set("Exit Orders Modified - Waiting for Status")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in valid_accounts:
                self.child_order_status.set("Exit Orders Modified - Waiting for Status")
            else:
                self.child_order_status.set("Child Not Logged In")
            
        except Exception as e:

            applicationLogger.error(f"Error modifying exit orders: {e}")
            # Update order status displays to show error
            active_accounts = self.account_manager.get_all_active_accounts()
            if 1 in active_accounts:
                self.master_order_status.set(f"Modify Error: {str(e)[:40]}...")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set(f"Modify Error: {str(e)[:40]}...")
            else:
                self.child_order_status.set("Child Not Logged In")
    
    def update_mtm(self, account_num: int):
        """Update MTM for an account"""
        try:
            api = self.account_manager.get_api(account_num)
            if not api:
                messagebox.showerror("Error", f"Account {account_num} not available")
                return
            
            mtm = self.position_manager.calculate_mtm(api)
            messagebox.showinfo("MTM", f"Account {account_num} MTM: {mtm}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error calculating MTM: {e}")
    
    def show_order_details(self, account_num: int):
        """Show order details for an account"""
        try:
            api = self.account_manager.get_api(account_num)
            if not api:
                messagebox.showerror("Error", f"Account {account_num} not available")
                return
            
            orders = self.order_manager.get_order_book(api)
            if not orders:
                messagebox.showinfo("Order Details", "No orders found")
                return
            
            # Create order details window
            self.create_order_details_window(orders)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching order details: {e}")
    
    def create_order_details_window(self, orders):
        """Create order details window"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Order Details")
        details_window.geometry("800x300")
        
        # Create scrollable frame
        canvas = tk.Canvas(details_window)
        scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        headers = ["tsym", "norenordno", "prc", "qty", "status", "trantype", "prctyp",
                  "fillshares", "avgprc", "uid", "rejreason"]
        
        for col, header in enumerate(headers):
            header_label = tk.Label(scrollable_frame, text=header, font=('bold', 12))
            header_label.grid(row=0, column=col, padx=10, pady=5, sticky='w')
        
        # Order data
        for row_idx, order in enumerate(orders, start=1):
            for col_idx, key in enumerate(headers):
                value = order.get(key, "")
                label = tk.Label(scrollable_frame, text=value)
                label.grid(row=row_idx, column=col_idx, padx=10, pady=5, sticky='w')
    
    def release_buttons(self):
        """Release button states - enable buy and sell order buttons"""
        # Reset only trading blocks while preserving actual login status
        self.state_manager.reset_trading_blocks(self.account_manager)
        applicationLogger.info("Trading blocks reset while preserving login status")
        
        # Also reset legacy blocking flags for backward compatibility
        self.master_account_blocked = False
        self.master_account_rejected_blocked = False
        self.child_account_blocked = False
        self.child_account_rejected_blocked = False
        
        # Update UI status displays based on actual account states
        self._update_account_status_displays()
        
        # Enable buy button
        self.buy_button.config(state='normal', text="BUY")
        
        # Re-enable price box for new orders
        self.price_box.config(state='normal', bg='white')
        
        # Clear original buy price and modify box
        self.original_buy_price = None
        self.modify_buy_value.set("")
        applicationLogger.info("BUY button and Price box re-enabled for new orders")
        
        # Disable buy-related buttons until new buy orders are placed
        self.cancel_buy_button.config(state='disabled')
        self.modify_buy_button.config(state='disabled')
        self.cancel_master_buy_button.config(state='disabled')
        self.cancel_child_buy_button.config(state='disabled')
        
        # Disable exit-related buttons until new orders are placed
        self.exit_button.config(state='disabled', text="SELL Order")
        self.exit_all_button.config(state='disabled')
        self.exit_master_button.config(state='disabled')
        self.exit_child_button.config(state='disabled')
        self.cancel_exit_button.config(state='disabled')
        self.modify_exit_button.config(state='disabled')
        
        # Stop SL/Target monitoring
        if self.sl_monitoring_active:
            self.stop_sl_monitoring()
        if self.target_monitoring_active:
            self.stop_target_monitoring()
        
        # Reset order status displays
        active_accounts = self.account_manager.get_all_active_accounts()
        if 1 in active_accounts:
            self.master_order_status.set(self.get_ready_status_message(1))
        else:
            self.master_order_status.set("Master Not Logged In")
            
        if 2 in active_accounts:
            self.child_order_status.set(self.get_ready_status_message(2))
        else:
            self.child_order_status.set("Child Not Logged In")
        
        applicationLogger.info("Buttons released - ready for new orders")
    
    def safe_get_order_book(self, api):
        """Safely get order book handling both API response formats
        
        Args:
            api: API instance
            
        Returns:
            List of orders or empty list if error
        """
        try:
            orders = api.get_order_book()
            
            # Handle dictionary response format (preferred)
            if isinstance(orders, dict) and orders.get('stat') == 'Ok':
                order_data = orders.get('data', [])
                if isinstance(order_data, list):
                    applicationLogger.info(f"Retrieved {len(order_data)} orders from order book (dict format)")
                    return order_data
                else:
                    applicationLogger.warning(f"Order book data is not a list: {type(order_data)}")
                    return []
            
            # Handle list response format (fallback)
            elif isinstance(orders, list):
                applicationLogger.info(f"Retrieved {len(orders)} orders from order book (list format)")
                return orders
                
            # Handle error response
            elif isinstance(orders, dict) and orders.get('stat') != 'Ok':
                error_msg = orders.get('emsg', 'Unknown error')
                applicationLogger.error(f"Order book API error: {error_msg}")
                return []
                
            # Handle unexpected response
            else:
                applicationLogger.error(f"Unexpected order book response format: {type(orders)} - {orders}")
                return []
                
        except Exception as e:
            applicationLogger.error(f"Error getting order book: {e}")
            return []
    
    def exit_all_orders_market(self):
        """Exit all orders at market price for both master and child accounts"""
        try:
            # Check if exit button is disabled (no orders to exit)
            if self.exit_button['state'] == 'disabled':
                messagebox.showwarning("Warning", "No orders to sell! Place buy orders first.")
                return
            
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit All Orders", 
                "Are you sure you want to exit all orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                applicationLogger.info("Exit all orders cancelled by user")
                return
            

            applicationLogger.info("Exiting all orders at market price")
            
            # Get active accounts
            active_accounts = [i for i in range(1, 3) if self.account_manager.accounts[i]['active']]
            
            if not active_accounts:
                self.master_order_status.set("No Active Accounts")
                self.child_order_status.set("No Active Accounts")
                return
            

            # Place market exit orders for all active accounts
            orders_processed = 0
            for account_num in active_accounts:
                api = self.account_manager.accounts[account_num]['api']
                if api:
                    # Get current orders using safe method
                    orders = self.safe_get_order_book(api)
                    if orders:
                        for order in orders:
                            if isinstance(order, dict) and order.get('status') in ['PENDING', 'OPEN']:
                                # Place market exit order
                                exit_result = api.place_order(
                                    buy_or_sell='S' if order.get('trantype') == 'B' else 'B',
                                    product_type=order.get('pcode', 'I'),
                                    exchange=order.get('exch', ''),
                                    tradingsymbol=order.get('tsym', ''),
                                    quantity=int(order.get('qty', 0)),
                                    discloseqty=0,
                                    price_type='MKT',
                                    price=0.0,
                                    trigger_price=None,
                                    retention='DAY',
                                    amo='NO',
                                    remarks='Market Exit'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Market exit order placed for account {account_num}: {exit_result.get('norenordno')}")
                                    orders_processed += 1
                                else:
                                    applicationLogger.error(f"Failed to place market exit order for account {account_num}: {exit_result}")
                    else:
                        applicationLogger.warning(f"No orders found for account {account_num}")
            
            if orders_processed == 0:
                applicationLogger.warning("No orders were processed for exit")
            
            # Update status
            self.master_order_status.set("All Orders - Market Exit Placed")
            self.child_order_status.set("All Orders - Market Exit Placed")
            
            # Block both accounts after exiting all orders at market price
            if orders_processed > 0:
                self.block_master_account("All orders exited at market price")
                self.block_child_account("All orders exited at market price")
                applicationLogger.info("Both accounts blocked after market exit - lifecycle completed")
            
            # Stop monitoring since all positions will be closed
            if self.sl_monitoring_active:
                self.stop_sl_monitoring()
                applicationLogger.info("SL monitoring stopped - all positions being closed")
            if self.target_monitoring_active:
                self.stop_target_monitoring()
                applicationLogger.info("Target monitoring stopped - all positions being closed")
            if self.trailing_active:
                self.stop_trailing_monitoring()
                applicationLogger.info("Trailing monitoring stopped - all positions being closed")
            
        except Exception as e:
            applicationLogger.error(f"Error in exit_all_orders_market: {e}")
            self.master_order_status.set(f"Error: {str(e)[:30]}...")
            self.child_order_status.set(f"Error: {str(e)[:30]}...")
    
    def exit_master_orders_market(self):
        """Exit master account orders at market price - modify existing sell orders or place new ones"""
        try:
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit Master Orders", 
                "Are you sure you want to exit Master orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                applicationLogger.info("Exit master orders cancelled by user")
                return
            

            applicationLogger.info("Exiting master orders at market price")
            
            if not self.account_manager.accounts[1]['active']:
                self.master_order_status.set("Master Not Logged In")
                return
            
            api = self.account_manager.accounts[1]['api']
            if api:
                # Get current orders using safe method
                orders = self.safe_get_order_book(api)
                if orders:
                    sell_orders_found = False
                    buy_orders_found = False
                    
                    for order in orders:
                        if isinstance(order, dict) and order.get('status') in ['PENDING', 'OPEN']:
                            if order.get('trantype') == 'S':  # Existing SELL order
                                sell_orders_found = True
                                # Modify existing sell order to market price
                                try:
                                    modify_result = api.modify_order(
                                        order_id=order.get('norenordno'),
                                        price_type='MKT',
                                        price=0.0,
                                        quantity=int(order.get('qty', 0)),
                                        product_type=order.get('pcode', 'I'),
                                        exchange=order.get('exch', ''),
                                        tradingsymbol=order.get('tsym', ''),
                                        retention='DAY',
                                        remarks='Master Market Exit - Modified'
                                    )
                                    
                                    if modify_result and modify_result.get('stat') == 'Ok':
                                        applicationLogger.info(f"Master sell order modified to market price: {order.get('norenordno')}")
                                    else:
                                        applicationLogger.error(f"Failed to modify master sell order: {modify_result}")
                                        self.master_order_status.set("Error: Failed to modify sell order - please exit manually")
                                        return
                                except Exception as e:
                                    applicationLogger.error(f"Error modifying master sell order: {e}")
                                    self.master_order_status.set(f"Error modifying sell order: {e}")
                                    return
                                    
                            elif order.get('trantype') == 'B':  # BUY order - place new sell order
                                buy_orders_found = True
                                # Place new market sell order
                                exit_result = api.place_order(
                                    buy_or_sell='S',
                                    product_type=order.get('pcode', 'I'),
                                    exchange=order.get('exch', ''),
                                    tradingsymbol=order.get('tsym', ''),
                                    quantity=int(order.get('qty', 0)),
                                    discloseqty=0,
                                    price_type='MKT',
                                    price=0.0,
                                    trigger_price=None,
                                    retention='DAY',
                                    amo='NO',
                                    remarks='Master Market Exit - New Sell'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Master new market sell order placed: {exit_result.get('norenordno')}")
                                else:
                                    applicationLogger.error("Failed to place master market sell order")
                                    self.master_order_status.set("Error: Failed to place sell order - please exit manually")
                                    return
                        
                        # Update status based on what was found
                        if sell_orders_found and buy_orders_found:
                            self.master_order_status.set("Master Orders - Modified Sell & Placed New Sell")
                        elif sell_orders_found:
                            self.master_order_status.set("Master Orders - Modified Existing Sell to Market")
                        elif buy_orders_found:
                            self.master_order_status.set("Master Orders - Placed New Market Sell")
                        
                        # Block Master account after exiting at market price
                        if sell_orders_found or buy_orders_found:
                            self.block_master_account("Master exited at market price")
                            applicationLogger.info("Master account blocked after market exit - lifecycle completed")
                    else:
                        self.master_order_status.set("Master Orders - No Open Orders to Exit")
                else:
                    self.master_order_status.set("Master Orders - No Orders Found")
            else:
                self.master_order_status.set("Master API Not Available")
                
        except Exception as e:
            applicationLogger.error(f"Error in exit_master_orders_market: {e}")
            self.master_order_status.set(f"Error: {str(e)[:30]}...")
    
    def exit_child_orders_market(self):
        """Exit child account orders at market price - modify existing sell orders or place new ones"""
        try:
            # Show confirmation popup
            result = messagebox.askyesno(
                "Confirm Exit Child Orders", 
                "Are you sure you want to exit Child orders at market price?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if not result:
                applicationLogger.info("Exit child orders cancelled by user")
                return
            
            applicationLogger.info("Exiting child orders at market price")
            
            if not self.account_manager.accounts[2]['active']:
                self.child_order_status.set("Child Not Logged In")
                return
            
            api = self.account_manager.accounts[2]['api']
            if api:
                # Get current orders using safe method
                orders = self.safe_get_order_book(api)
                if orders:
                    sell_orders_found = False
                    buy_orders_found = False
                    
                    for order in orders:
                        if isinstance(order, dict) and order.get('status') in ['PENDING', 'OPEN']:
                            if order.get('trantype') == 'S':  # Existing SELL order
                                sell_orders_found = True
                                # Modify existing sell order to market price
                                try:
                                    modify_result = api.modify_order(
                                        order_id=order.get('norenordno'),
                                        price_type='MKT',
                                        price=0.0,
                                        quantity=int(order.get('qty', 0)),
                                        product_type=order.get('pcode', 'I'),
                                        exchange=order.get('exch', ''),
                                        tradingsymbol=order.get('tsym', ''),
                                        retention='DAY',
                                        remarks='Child Market Exit - Modified'
                                    )
                                    
                                    if modify_result and modify_result.get('stat') == 'Ok':
                                        applicationLogger.info(f"Child sell order modified to market price: {order.get('norenordno')}")
                                    else:
                                        applicationLogger.error(f"Failed to modify child sell order: {modify_result}")
                                        self.child_order_status.set("Error: Failed to modify sell order - please exit manually")
                                        return
                                except Exception as e:
                                    applicationLogger.error(f"Error modifying child sell order: {e}")
                                    self.child_order_status.set(f"Error modifying sell order: {e}")
                                    return
                                    
                            elif order.get('trantype') == 'B':  # BUY order - place new sell order
                                buy_orders_found = True
                                # Place new market sell order
                                exit_result = api.place_order(
                                    buy_or_sell='S',
                                    product_type=order.get('pcode', 'I'),
                                    exchange=order.get('exch', ''),
                                    tradingsymbol=order.get('tsym', ''),
                                    quantity=int(order.get('qty', 0)),
                                    discloseqty=0,
                                    price_type='MKT',
                                    price=0.0,
                                    trigger_price=None,
                                    retention='DAY',
                                    amo='NO',
                                    remarks='Child Market Exit - New Sell'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Child new market sell order placed: {exit_result.get('norenordno')}")
                                else:
                                    applicationLogger.error("Failed to place child market sell order")
                                    self.child_order_status.set("Error: Failed to place sell order - please exit manually")
                                    return
                        
                        # Update status based on what was found
                        if sell_orders_found and buy_orders_found:
                            self.child_order_status.set("Child Orders - Modified Sell & Placed New Sell")
                        elif sell_orders_found:
                            self.child_order_status.set("Child Orders - Modified Existing Sell to Market")
                        elif buy_orders_found:
                            self.child_order_status.set("Child Orders - Placed New Market Sell")
                        
                        # Block Child account after exiting at market price
                        if sell_orders_found or buy_orders_found:
                            self.block_child_account("Child exited at market price")
                            applicationLogger.info("Child account blocked after market exit - waiting for Master lifecycle to complete")
                    else:
                        self.child_order_status.set("Child Orders - No Open Orders to Exit")
                else:
                    self.child_order_status.set("Child Orders - No Orders Found")
            else:
                self.child_order_status.set("Child API Not Available")
                
        except Exception as e:
            applicationLogger.error(f"Error in exit_child_orders_market: {e}")
            self.child_order_status.set(f"Error: {str(e)[:30]}...")
    
    def set_sl_price(self):
        """Set Stop Loss price with two-step confirmation"""
        try:
            if self.sl_button_state == "ready":
                # First press: Show current price in the box
                current_price = self.premium_price_value.get()
                if current_price:
                    current_price_float = float(current_price)
                    # Suggest SL price (1% below current price for long positions)
                    suggested_sl = round(current_price_float * 0.99, 2)
                    self.sl_price_value.set(str(suggested_sl))
                    
                    # Update button state and appearance
                    self.sl_button_state = "showing_price"
                    self.sl_price_button.config(text="Confirm SL", bg="yellow", fg="black")
                    applicationLogger.info(f"SL price suggested: {suggested_sl} (1% below LTP: {current_price_float}) - Press again to confirm")
                else:
                    applicationLogger.warning("Please fetch current price first to set SL")
                    
            elif self.sl_button_state == "showing_price":
                # Second press: Confirm and set the SL price
                sl_price_text = self.sl_price_value.get().strip()
                
                if sl_price_text:
                    # Validate SL price
                    sl_price = float(sl_price_text)
                    
                    # Check if SL price conflicts with configured trailing stop
                    if (self.enable_trailing_value.get() and 
                        self.target_price_level and 
                        self.trail_value.get().strip()):
                        
                        trail_type = self.trail_type_selected.get()
                        trail_value = float(self.trail_value.get())
                        
                        # Calculate what the trailing stop would be at target price
                        if trail_type == "Point":
                            calculated_trailing_stop = self.target_price_level - trail_value
                        else:  # Percent
                            calculated_trailing_stop = self.target_price_level * (1 - trail_value / 100)
                        
                        # Check if SL price is above trailing stop
                        if sl_price > calculated_trailing_stop:
                            messagebox.showerror("Error", 
                                f"SL price ({sl_price}) cannot be above trailing stop price ({calculated_trailing_stop:.2f})\n"
                                f"Please reduce SL price or increase trail value")
                            return
                    
                    # Set the SL price level
                    self.sl_price_level = sl_price
                    self.sl_button_state = "confirmed"
                    
                    # Update SL difference from current buy order open value
                    if self.current_buy_order_open_value is not None:
                        self.sl_difference_from_buy = round(sl_price - self.current_buy_order_open_value, 2)
                        applicationLogger.info(f"SL difference updated: {self.sl_difference_from_buy} points from buy price")
                    
                    # Check if buy orders are filled/completed
                    if self._are_buy_orders_filled():
                        # If buy orders are filled, immediately start SL monitoring
                        self.start_sl_monitoring(sl_price)
                        applicationLogger.info(f"SL price confirmed and monitoring started: {sl_price} (buy orders are filled)")
                    else:
                        # If buy orders not filled yet, just set the price (monitoring will start after buy order is filled)
                        self.sl_price_button.config(text=f"SL Set @{sl_price}", bg="orange", fg="white")
                        applicationLogger.info(f"SL price confirmed: {sl_price} (monitoring will start after buy order is filled)")
                else:
                    applicationLogger.warning("Please enter a valid SL price")
                    
            elif self.sl_button_state == "confirmed":
                # Third press: Allow modification of confirmed SL price
                current_sl = self.sl_price_value.get()
                if current_sl:
                    self.sl_price_value.set(current_sl)  # Keep current value for editing
                    self.sl_button_state = "showing_price"
                    self.sl_price_button.config(text="Confirm SL", bg="yellow", fg="black")
                    applicationLogger.info(f"SL price ready for modification: {current_sl}")
                else:
                    # If no current value, go back to ready state
                    self.sl_button_state = "ready"
                    self.sl_price_button.config(text="SL Price", bg="SystemButtonFace", fg="black")
                    applicationLogger.info("SL price reset to ready state")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid SL price")
        except Exception as e:
            applicationLogger.error(f"Error setting SL price: {e}")
            messagebox.showerror("Error", f"Error setting SL price: {e}")
    
    def set_target_price(self):
        """Set Target price with two-step confirmation"""
        try:
            if self.target_button_state == "ready":
                # First press: Show current price in the box
                current_price = self.premium_price_value.get()
                if current_price:
                    current_price_float = float(current_price)
                    # Suggest target price (1% above current price for long positions)
                    suggested_target = round(current_price_float * 1.01, 2)
                    self.target_price_value.set(str(suggested_target))
                    
                    # Update button state and appearance
                    self.target_button_state = "showing_price"
                    self.target_price_button.config(text="Confirm Target", bg="yellow", fg="black")
                    applicationLogger.info(f"Target price suggested: {suggested_target} (1% above LTP: {current_price_float}) - Press again to confirm")
                else:
                    applicationLogger.warning("Please fetch current price first to set Target")
                    
            elif self.target_button_state == "showing_price":
                # Second press: Confirm and set the Target price
                target_price_text = self.target_price_value.get().strip()
                
                if target_price_text:
                    # Validate Target price
                    target_price = float(target_price_text)
                    
                    # Set the target price level
                    self.target_price_level = target_price
                    self.target_button_state = "confirmed"
                    
                    # Update Target difference from current buy order open value
                    if self.current_buy_order_open_value is not None:
                        self.target_difference_from_buy = round(target_price - self.current_buy_order_open_value, 2)
                        applicationLogger.info(f"Target difference updated: {self.target_difference_from_buy} points from buy price")
                    
                    # Check if buy orders are filled/completed
                    if self._are_buy_orders_filled():
                        # If buy orders are filled, immediately start Target monitoring
                        self.start_target_monitoring(target_price)
                        applicationLogger.info(f"Target price confirmed and monitoring started: {target_price} (buy orders are filled)")
                    else:
                        # If buy orders not filled yet, just set the price (monitoring will start after buy order is filled)
                        self.target_price_button.config(text=f"Target Set @{target_price}", bg="orange", fg="white")
                        applicationLogger.info(f"Target price confirmed: {target_price} (monitoring will start after buy order is filled)")
                else:
                    applicationLogger.warning("Please enter a valid Target price")
                    
            elif self.target_button_state == "confirmed":
                # Third press: Allow modification of confirmed Target price
                current_target = self.target_price_value.get()
                if current_target:
                    self.target_price_value.set(current_target)  # Keep current value for editing
                    self.target_button_state = "showing_price"
                    self.target_price_button.config(text="Confirm Target", bg="yellow", fg="black")
                    applicationLogger.info(f"Target price ready for modification: {current_target}")
                else:
                    # If no current value, go back to ready state
                    self.target_button_state = "ready"
                    self.target_price_button.config(text="Target Price", bg="SystemButtonFace", fg="black")
                    applicationLogger.info("Target price reset to ready state")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid Target price")
        except Exception as e:
            applicationLogger.error(f"Error setting target price: {e}")
            messagebox.showerror("Error", f"Error setting target price: {e}")
    
    def enable_trail(self):
        """Enable trailing stop with current settings"""
        try:
            trail_type = self.trail_type_selected.get()
            trail_value_text = self.trail_value.get().strip()
            
            if not trail_type:
                messagebox.showerror("Error", "Please select a trail type (Point or Percent)")
                return
                
            if not trail_value_text:
                messagebox.showerror("Error", "Please enter a trail value")
                return
            
            # Check if target is set (doesn't need to be active yet)
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
            
            # Update status
            if trail_type == "Point":
                self.trail_status_text.set(f"Trailing Ready - Point Trail: {trail_value} (Will activate when target reached)")
            else:
                self.trail_status_text.set(f"Trailing Ready - Percent Trail: {trail_value}% (Will activate when target reached)")
            
            # Update button states
            self.enable_trail_button.config(state="disabled", bg="gray")
            self.disable_trail_button.config(state="normal", bg="lightcoral")
            
            applicationLogger.info(f"Trailing configured - {trail_type} trail: {trail_value} (Ready for target activation)")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid trail value")
        except Exception as e:
            applicationLogger.error(f"Error enabling trail: {e}")
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
                applicationLogger.info("Active trailing mode stopped")
            
            # Update button states
            self.enable_trail_button.config(state="normal", bg="lightgreen")
            self.disable_trail_button.config(state="disabled", bg="gray")
            
            applicationLogger.info("Trailing disabled")
            
        except Exception as e:
            applicationLogger.error(f"Error disabling trail: {e}")
            messagebox.showerror("Error", f"Error disabling trail: {e}")
    
    def on_trail_type_changed(self, event=None):
        """Handle trail type dropdown selection change"""
        try:
            trail_type = self.trail_type_selected.get()
            
            # Clear the value field when type changes
            self.trail_value.set("")
            
            # Update status with requirements
            if trail_type == "Point":
                self.trail_status_text.set("Point Trail Selected - Enter value and click Enable")
            elif trail_type == "Percent":
                self.trail_status_text.set("Percent Trail Selected - Enter value and click Enable")
            else:
                self.trail_status_text.set("Trailing Disabled")
                
        except Exception as e:
            applicationLogger.error(f"Error handling trail type change: {e}")
    
    def start_sl_monitoring(self, sl_price):
        """Start monitoring Stop Loss price"""
        self.sl_monitoring_active = True
        self.sl_price_level = sl_price
        self.sl_price_button.config(text=f"SL placed @{sl_price}", bg="red", fg="white")
        applicationLogger.info(f"SL monitoring activated at {sl_price}")
    
    def start_target_monitoring(self, target_price):
        """Start monitoring Target price"""
        self.target_monitoring_active = True
        self.target_price_level = target_price
        self.target_price_button.config(text=f"Target placed @{target_price}", bg="green", fg="white")
        applicationLogger.info(f"Target monitoring activated at {target_price}")
    
    def stop_sl_monitoring(self):
        """Stop SL monitoring"""
        self.sl_monitoring_active = False
        self.sl_price_level = None
        self.sl_button_state = "ready"
        self.sl_price_button.config(text="SL Price", bg="SystemButtonFace", fg="black")
        applicationLogger.info("SL monitoring stopped")
    
    def stop_target_monitoring(self):
        """Stop Target monitoring"""
        self.target_monitoring_active = False
        self.target_price_level = None
        self.target_button_state = "ready"
        self.target_price_button.config(text="Target Price", bg="SystemButtonFace", fg="black")
        applicationLogger.info("Target monitoring stopped")
    
    def stop_trailing_monitoring(self):
        """Stop Trailing monitoring"""
        self.trailing_active = False
        self.trailing_start_price = None
        self.trailing_high_price = None
        self.trailing_stop_price = None
        # Clear trail status display
        if hasattr(self, 'trail_status_text'):
            self.trail_status_text.set("Trailing Inactive")
        applicationLogger.info("Trailing monitoring stopped")
    
    def get_accounts_with_open_positions(self):
        """Get list of accounts that have open positions (filled buy orders without filled sell orders)"""
        try:
            accounts_with_positions = []
            
            for account_num in [1, 2]:  # Master and Child accounts
                if not self.account_manager.accounts[account_num]['active']:
                    continue  # Skip inactive accounts
                
                api = self.account_manager.accounts[account_num]['api']
                if not api:
                    continue
                
                # Get order book for this account
                orders = api.get_order_book()
                if not orders or orders.get('stat') != 'Ok':
                    continue
                
                order_data = orders.get('data', [])
                if not isinstance(order_data, list):
                    continue
                
                # Check for filled buy and sell orders
                has_filled_buy = False
                has_filled_sell = False
                
                for order in order_data:
                    if not isinstance(order, dict):
                        continue
                    
                    status = order.get('status', '')
                    trantype = order.get('trantype', '')
                    
                    if status.upper() == 'COMPLETE':
                        if trantype.upper() == 'B':
                            has_filled_buy = True
                        elif trantype.upper() == 'S':
                            has_filled_sell = True
                
                # Account has open position if it has filled buy but no filled sell
                if has_filled_buy and not has_filled_sell:
                    accounts_with_positions.append(account_num)
                    applicationLogger.debug(f"Account {account_num} has open position")
                else:
                    applicationLogger.debug(f"Account {account_num} position status - Buy: {has_filled_buy}, Sell: {has_filled_sell}")
            
            applicationLogger.info(f"Accounts with open positions: {accounts_with_positions}")
            return accounts_with_positions
            
        except Exception as e:
            applicationLogger.error(f"Error checking accounts with open positions: {e}")
            # Fallback to active accounts if there's an error
            return self.account_manager.get_all_active_accounts()
    
    def reset_sl_target_monitoring(self):
        """Reset SL and Target monitoring - clear fields and deactivate"""
        # Stop monitoring
        if self.sl_monitoring_active:
            self.stop_sl_monitoring()
        if self.target_monitoring_active:
            self.stop_target_monitoring()
        
        # Clear the price fields
        self.sl_price_value.set("")
        self.target_price_value.set("")
        
        # Reset differences to default values
        # Reset to configured default values
        self.sl_difference_from_buy = -self.settings.get('default_sl_points', 20)
        self.target_difference_from_buy = self.settings.get('default_target_points', 30)
        self.current_buy_order_open_value = None
        
        applicationLogger.info("SL and Target monitoring reset and fields cleared")
    
    def auto_set_sl_target_from_buy_price(self, buy_open_value):
        """Automatically set SL and Target based on buy order open value"""
        try:
            if buy_open_value is None:
                return
                
            # Update current buy order open value
            self.current_buy_order_open_value = buy_open_value
            
            # Calculate SL and Target based on stored differences
            sl_price = round(buy_open_value + self.sl_difference_from_buy, 2)
            target_price = round(buy_open_value + self.target_difference_from_buy, 2)
            
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
            
            # Start monitoring if buy orders are filled
            if self._are_buy_orders_filled():
                self.start_sl_monitoring(sl_price)
                self.start_target_monitoring(target_price)
                applicationLogger.info(f"Auto SL/Target set and monitoring started - SL: {sl_price}, Target: {target_price} (Buy Open: {buy_open_value})")
            else:
                applicationLogger.info(f"Auto SL/Target set - SL: {sl_price}, Target: {target_price} (Buy Open: {buy_open_value})")
                
        except Exception as e:
            applicationLogger.error(f"Error in auto_set_sl_target_from_buy_price: {e}")
    
    def update_sl_target_differences(self, buy_open_value):
        """Update SL and Target differences when user manually sets them"""
        try:
            if buy_open_value is None:
                return
                
            # Update SL difference if SL is set
            if self.sl_price_level is not None:
                self.sl_difference_from_buy = round(self.sl_price_level - buy_open_value, 2)
                applicationLogger.info(f"SL difference updated: {self.sl_difference_from_buy} points from buy price")
            
            # Update Target difference if Target is set
            if self.target_price_level is not None:
                self.target_difference_from_buy = round(self.target_price_level - buy_open_value, 2)
                applicationLogger.info(f"Target difference updated: {self.target_difference_from_buy} points from buy price")
                
        except Exception as e:
            applicationLogger.error(f"Error updating SL/Target differences: {e}")
    
    def check_sl_target_breach(self, current_price):
        """Check if current price breaches SL or Target levels"""
        try:
            current_price_float = float(current_price)
            
            # Check SL breach (price falls below SL for long positions)
            if (self.sl_monitoring_active and 
                self.sl_price_level and 
                current_price_float <= self.sl_price_level):
                
                applicationLogger.warning(f"SL BREACHED! Current: {current_price_float}, SL: {self.sl_price_level}")
                self.execute_sl_exit(current_price_float)
            
            # Check Target breach (price rises above target for long positions)
            if (self.target_monitoring_active and 
                self.target_price_level and 
                current_price_float >= self.target_price_level):
                
                applicationLogger.warning(f"TARGET REACHED! Current: {current_price_float}, Target: {self.target_price_level}")
                
                # Check if trailing is enabled
                if self.enable_trailing_value.get():
                    # Start trailing instead of exiting
                    self.start_trailing_mode(current_price_float)
                else:
                    # Exit at target (normal behavior)
                    self.execute_target_exit(current_price_float)
                
        except Exception as e:
            applicationLogger.error(f"Error checking SL/Target breach: {e}")
    
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
            
            # Update status
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(f"TRAILING ACTIVE @ {current_price} (Stop: {self.trailing_stop_price:.2f})")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(f"TRAILING ACTIVE @ {current_price} (Stop: {self.trailing_stop_price:.2f})")
            
            # Update trail status
            self.trail_status_text.set(f"Trailing Active - Stop: {self.trailing_stop_price:.2f}")
            
            # Update real-time trailing stop display
            self.update_trailing_stop_display(current_price)
            
            applicationLogger.info(f"Trailing mode started at {current_price}, initial stop: {self.trailing_stop_price:.2f}")
            
        except Exception as e:
            applicationLogger.error(f"Error starting trailing mode: {e}")
    
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
                    
                    # Update status
                    if self.account_manager.accounts[1]['active']:
                        self.master_order_status.set(f"TRAILING @ {current_price_float} (Stop: {self.trailing_stop_price:.2f})")
                    if self.account_manager.accounts[2]['active']:
                        self.child_order_status.set(f"TRAILING @ {current_price_float} (Stop: {self.trailing_stop_price:.2f})")
                    
                    # Update trail status
                    self.trail_status_text.set(f"Trailing Active - Stop: {self.trailing_stop_price:.2f}")
                    
                    # Update real-time trailing stop display
                    self.update_trailing_stop_display(current_price_float)
                    
                    applicationLogger.info(f"Trailing stop updated to {self.trailing_stop_price:.2f} (High: {self.trailing_high_price:.2f})")
            
            # Check if trailing stop is hit
            elif current_price_float <= self.trailing_stop_price:
                applicationLogger.warning(f"TRAILING STOP HIT! Current: {current_price_float}, Stop: {self.trailing_stop_price:.2f}")
                self.execute_trailing_stop_exit(current_price_float)
                
        except Exception as e:
            applicationLogger.error(f"Error checking trailing stop: {e}")
    
    def execute_trailing_stop_exit(self, current_price):
        """Execute exit when trailing stop is hit"""
        try:
            applicationLogger.info(f"Executing trailing stop exit at {current_price}")
            
            # Stop trailing
            self.trailing_active = False
            self.trailing_start_price = None
            self.trailing_high_price = None
            self.trailing_stop_price = None
            
            # Update status
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(f"TRAILING STOP HIT @ {current_price}")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(f"TRAILING STOP HIT @ {current_price}")
            
            # Update trail status
            self.trail_status_text.set("Trailing Disabled")
            
            # Clear trailing stop display
            self.trailing_stop_display_label.config(text="")
            
            # Stop monitoring since position is being closed
            if self.target_monitoring_active:
                self.stop_target_monitoring()
            if self.trailing_active:
                self.stop_trailing_monitoring()
            
            # Set the exit price to current price and call regular exit function
            self.price1_value.set(str(current_price))
            self.place_exit_orders()
            
        except Exception as e:
            applicationLogger.error(f"Error executing trailing stop exit: {e}")
    
    def update_trailing_stop_display(self, current_price):
        """Update the real-time trailing stop display"""
        try:
            if not self.trailing_active or not self.trailing_stop_price:
                return
            
            trail_type = self.trail_type_selected.get()
            trail_value = float(self.trail_value.get())
            
            # Calculate the equivalent point value
            if trail_type == "Point":
                point_value = trail_value
                display_text = f"Trailing Stop: {self.trailing_stop_price:.2f} (Trail: {point_value} pts)"
            else:  # Percent
                # Calculate equivalent point value based on current high price
                point_value = self.trailing_high_price * (trail_value / 100)
                display_text = f"Trailing Stop: {self.trailing_stop_price:.2f} (Trail: {point_value:.2f} pts = {trail_value}%)"
            
            # Update the display
            self.trailing_stop_display_label.config(text=display_text)
            
        except Exception as e:
            applicationLogger.error(f"Error updating trailing stop display: {e}")
    
    def execute_sl_exit(self, current_price):
        """Execute limit exit when SL is breached"""
        try:
            applicationLogger.info(f"Executing SL exit at limit price. Current: {current_price}")
            
            # Stop SL monitoring
            self.stop_sl_monitoring()
            
            # Update status
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(f"SL TRIGGERED @ {current_price}")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(f"SL TRIGGERED @ {current_price}")
            
            # Stop monitoring since position is being closed
            if self.target_monitoring_active:
                self.stop_target_monitoring()
            if self.trailing_active:
                self.stop_trailing_monitoring()
            
            # Set the exit price to current price and call dynamic exit function
            self.price1_value.set(str(current_price))
            self.place_dynamic_stop_loss_orders(current_price)
            
        except Exception as e:
            applicationLogger.error(f"Error executing SL exit: {e}")
    
    def execute_target_exit(self, current_price):
        """Execute limit exit when Target is reached"""
        try:
            applicationLogger.info(f"Executing Target exit at limit price. Current: {current_price}")
            
            # Stop target monitoring
            self.stop_target_monitoring()
            
            # Update status
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(f"TARGET HIT @ {current_price}")
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(f"TARGET HIT @ {current_price}")
            
            # Stop monitoring since position is being closed
            if self.target_monitoring_active:
                self.stop_target_monitoring()
            if self.trailing_active:
                self.stop_trailing_monitoring()
            
            # Set the exit price to current price and call dynamic exit function
            self.price1_value.set(str(current_price))
            self.place_dynamic_target_orders(current_price)
            
        except Exception as e:
            applicationLogger.error(f"Error executing Target exit: {e}")
    
    def exit_all_orders_market_silent(self):
        """Exit all orders at market price without confirmation popup"""
        try:
            applicationLogger.info("Executing silent market exit for SL/Target")
            
            # Get active accounts
            active_accounts = [i for i in range(1, 3) if self.account_manager.accounts[i]['active']]
            
            if not active_accounts:
                return
            
            # Place market exit orders for all active accounts
            for account_num in active_accounts:
                api = self.account_manager.accounts[account_num]['api']
                if api:
                    # Get current orders and exit them at market price
                    orders = self.safe_get_order_book(api)
                    if orders:
                        for order in orders:
                            if isinstance(order, dict) and order.get('status') in ['PENDING', 'OPEN']:
                                # Place market exit order
                                exit_result = api.place_order(
                                    buy_or_sell='S' if order.get('trantype') == 'B' else 'B',
                                    product_type=order.get('pcode', 'I'),
                                    exchange=order.get('exch', ''),
                                    tradingsymbol=order.get('tsym', ''),
                                    quantity=int(order.get('qty', 0)),
                                    discloseqty=0,
                                    price_type='MKT',
                                    price=0.0,
                                    trigger_price=None,
                                    retention='DAY',
                                    amo='NO',
                                    remarks='SL/Target Exit'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Market exit order placed for account {account_num}: {exit_result.get('norenordno')}")
                                else:
                                    applicationLogger.error(f"Failed to place market exit order for account {account_num}")
                
        except Exception as e:
            applicationLogger.error(f"Error in silent market exit: {e}")
    
    def calculate_pnl(self, api):
        """Calculate PnL for a given API account"""
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
            applicationLogger.error(f"Error calculating PnL: {e}")
            return 0.0
    
    def update_pnl_display(self, account_num, pnl_value):
        """Update PnL display for specific account"""
        try:
            if account_num == 1:  # Master account
                self.master_pnl_value.set(f"{pnl_value}")
            elif account_num == 2:  # Child account
                self.child_pnl_value.set(f"{pnl_value}")
        except Exception as e:
            applicationLogger.error(f"Error updating PnL display: {e}")
    
    def refresh_pnl(self):
        """Refresh PnL for all active and blocked accounts - DISABLED (only shown on Show PnL)"""
        try:
            applicationLogger.info("PnL refresh disabled - use Show PnL button to see PnL")
            # PnL display is now only shown when Show PnL button is pressed
        except Exception as e:
            applicationLogger.error(f"Error in refresh_pnl: {e}")
    
    def update_pnl_on_trade(self, account_num):
        """Update PnL when a trade is executed"""
        try:
            # Update PnL for both active and blocked accounts
            if (self.account_manager.accounts[account_num]['active'] or 
                self.account_manager.accounts[account_num].get('blocked', False)):
                api = self.account_manager.accounts[account_num]['api']
                if api:
                    pnl_value = self.calculate_pnl(api)
                    # PnL display removed - only shown when Show PnL is pressed
                    status = "blocked" if self.account_manager.accounts[account_num].get('blocked', False) else "active"
                    applicationLogger.info(f"PnL calculated for account {account_num} ({status}): {pnl_value}")
        except Exception as e:
            applicationLogger.error(f"Error updating PnL on trade: {e}")
    
    def update_order_state(self, account_num: int, status: str, reporttype: str, trantype: str):
        """Update order state for cross-account coordination"""
        try:
            if account_num == 1:  # Master account
                self.master_order_state = status.upper()
            elif account_num == 2:  # Child account
                self.child_order_state = status.upper()
            
            applicationLogger.info(f"Order state updated - Master: {self.master_order_state}, Child: {self.child_order_state}")
            
            # Check for REJECTED status and block account
            if status.upper() == 'REJECTED':
                # Extract rejection reason from reporttype or use default
                rejection_reason = reporttype if reporttype else "Order Rejected"
                self.block_account_on_rejection(account_num, rejection_reason)
                
                # Show popup to inform user about the blocking
                if account_num == 1:
                    messagebox.showerror(
                        "Master Order Rejected", 
                        f"Master order was REJECTED: {rejection_reason}\n\n"
                        "Master account is now BLOCKED from all operations.\n"
                        "Use the RELEASE button to unblock the account."
                    )
                elif account_num == 2:
                    messagebox.showerror(
                        "Child Order Rejected", 
                        f"Child order was REJECTED: {rejection_reason}\n\n"
                        "Child account is now BLOCKED from all operations.\n"
                        "Use the RELEASE button to unblock the account."
                    )
            
            # Update modify button state based on order states
            self.update_modify_button_state()
            
            # Trigger cross-account coordination if both orders are placed
            if self.order_coordination_active:
                self.check_cross_account_coordination()
                
        except Exception as e:
            applicationLogger.error(f"Error updating order state: {e}")
    
    def update_modify_button_state(self):
        """Update modify button state based on current order states"""
        try:
            # Check if any orders are in modifiable state
            master_modifiable = self.master_order_state in ['PENDING', 'OPEN']
            child_modifiable = self.child_order_state in ['PENDING', 'OPEN']
            
            # Enable modify buy button only if at least one order is modifiable
            if master_modifiable or child_modifiable:
                self.modify_buy_button.config(state='normal')
                applicationLogger.info("Modify Buy button enabled - orders are in modifiable state")
            else:
                self.modify_buy_button.config(state='disabled')
                applicationLogger.info("Modify Buy button disabled - no orders in modifiable state")
            
            # For exit orders, we need to check if there are any exit orders to modify
            # This is a simplified check - in a more complex system, we'd track exit order states separately
            has_exit_orders = any(self.exit_order_numbers.values())
            if has_exit_orders and (master_modifiable or child_modifiable):
                self.modify_exit_button.config(state='normal')
                applicationLogger.info("Modify Exit button enabled - exit orders are in modifiable state")
            else:
                self.modify_exit_button.config(state='disabled')
                applicationLogger.info("Modify Exit button disabled - no exit orders in modifiable state")
                
        except Exception as e:
            applicationLogger.error(f"Error updating modify button state: {e}")
    
    def start_order_coordination(self):
        """Start cross-account coordination monitoring"""
        try:
            self.order_coordination_active = True
            self.master_order_state = None
            self.child_order_state = None
            applicationLogger.info("Cross-account coordination started")
        except Exception as e:
            applicationLogger.error(f"Error starting order coordination: {e}")
    
    def stop_order_coordination(self):
        """Stop cross-account coordination monitoring"""
        try:
            self.order_coordination_active = False
            if self.coordination_timer:
                self.root.after_cancel(self.coordination_timer)
                self.coordination_timer = None
            applicationLogger.info("Cross-account coordination stopped")
        except Exception as e:
            applicationLogger.error(f"Error stopping order coordination: {e}")
    
    def check_cross_account_coordination(self):
        """Check and handle cross-account coordination scenarios"""
        try:
            if not self.order_coordination_active:
                return
            
            master_state = self.master_order_state
            child_state = self.child_order_state
            
            applicationLogger.info(f"Checking coordination - Master: {master_state}, Child: {child_state}")
            
            # Scenario 1: Master FILLED, Child PENDING/OPEN
            if master_state == 'FILLED' and child_state in ['PENDING', 'OPEN']:
                self.handle_master_filled_child_pending()
            
            # Scenario 2: Master FILLED, Child REJECTED
            elif master_state == 'FILLED' and child_state == 'REJECTED':
                self.handle_master_filled_child_rejected()
            
            # Scenario 3: Master REJECTED, Child FILLED
            elif master_state == 'REJECTED' and child_state == 'FILLED':
                self.handle_master_rejected_child_filled()
            
            # Scenario 4: Master REJECTED, Child PENDING
            elif master_state == 'REJECTED' and child_state == 'PENDING':
                self.handle_master_rejected_child_pending()
            
            # Scenario 5: Master PENDING, Child FILLED
            elif master_state == 'PENDING' and child_state == 'FILLED':
                self.handle_master_pending_child_filled()
            
            # Scenario 6: Master PENDING, Child REJECTED
            elif master_state == 'PENDING' and child_state == 'REJECTED':
                self.handle_master_pending_child_rejected()
                
        except Exception as e:
            applicationLogger.error(f"Error in cross-account coordination: {e}")
    
    def handle_master_filled_child_pending(self):
        """Master FILLED, Child PENDING/OPEN - Wait 2s then cancel child"""
        try:
            applicationLogger.info("Master FILLED, Child PENDING/OPEN - Starting 2s timeout")
            
            # Cancel child order after 2 seconds
            self.coordination_timer = self.root.after(2000, self.cancel_child_order_and_block_exit)
            
        except Exception as e:
            applicationLogger.error(f"Error handling master filled child pending: {e}")
    
    def handle_master_filled_child_rejected(self):
        """Master FILLED, Child REJECTED - Skip child operations"""
        try:
            applicationLogger.info("Master FILLED, Child REJECTED - Blocking child operations")
            # Child operations are already blocked since order was rejected
            self.stop_order_coordination()
            
        except Exception as e:
            applicationLogger.error(f"Error handling master filled child rejected: {e}")
    
    def handle_master_rejected_child_filled(self):
        """Master REJECTED, Child FILLED - Exit child at market price immediately"""
        try:
            applicationLogger.info("Master REJECTED, Child FILLED - Exiting child at market price")
            
            # Show popup with master rejection reason
            messagebox.showerror(
                "Critical Error", 
                "Master order was REJECTED but Child order was FILLED!\n\n"
                "This creates an inconsistent position. Child will be exited at market price immediately."
            )
            
            # Exit child at market price
            self.exit_child_at_market_price()
            self.stop_order_coordination()
            
        except Exception as e:
            applicationLogger.error(f"Error handling master rejected child filled: {e}")
    
    def handle_master_rejected_child_pending(self):
        """Master REJECTED, Child PENDING - Cancel child order immediately"""
        try:
            applicationLogger.info("Master REJECTED, Child PENDING - Cancelling child order")
            
            # Cancel child order immediately
            self.cancel_child_order_immediately()
            self.stop_order_coordination()
            
        except Exception as e:
            applicationLogger.error(f"Error handling master rejected child pending: {e}")
    
    def handle_master_pending_child_filled(self):
        """Master PENDING, Child FILLED - Cancel master and exit child"""
        try:
            applicationLogger.info("Master PENDING, Child FILLED - Cancelling master and exiting child")
            
            # Cancel master order
            self.cancel_master_order_immediately()
            
            # Exit child at market price
            self.exit_child_at_market_price()
            self.stop_order_coordination()
            
        except Exception as e:
            applicationLogger.error(f"Error handling master pending child filled: {e}")
    
    def handle_master_pending_child_rejected(self):
        """Master PENDING, Child REJECTED - Show popup and continue with master only"""
        try:
            applicationLogger.info("Master PENDING, Child REJECTED - Showing popup and continuing with master")
            
            # Show popup error for child
            messagebox.showerror(
                "Child Order Rejected", 
                "Child order was REJECTED but Master order is still PENDING.\n\n"
                "Continuing with Master order only."
            )
            
            # Continue with master only - no action needed as master is still pending
            
        except Exception as e:
            applicationLogger.error(f"Error handling master pending child rejected: {e}")
    
    def cancel_child_order_and_block_exit(self):
        """Cancel child order after timeout and block exit calls"""
        try:
            applicationLogger.info("Timeout reached - Cancelling child order and blocking exit calls")
            
            # Cancel child order
            self.cancel_child_order_immediately()
            
            # Block exit calls for child account
            self.block_child_exit_calls()
            
            self.stop_order_coordination()
            
        except Exception as e:
            applicationLogger.error(f"Error cancelling child order after timeout: {e}")
    
    def cancel_child_order_immediately(self):
        """Cancel child order immediately"""
        try:
            if self.account_manager.accounts[2]['active']:
                api = self.account_manager.accounts[2]['api']
                if api:
                    # Get child's buy orders and cancel them
                    orders = api.get_order_book()
                    if orders and isinstance(orders, list):
                        for order in orders:
                            if (isinstance(order, dict) and 
                                order.get('status') in ['PENDING', 'OPEN'] and 
                                order.get('trantype') == 'B'):
                                
                                api.cancel_order(orderno=order.get('norenordno'))
                                applicationLogger.info(f"Cancelled child buy order: {order.get('norenordno')}")
            
        except Exception as e:
            applicationLogger.error(f"Error cancelling child order: {e}")
    
    def cancel_master_order_immediately(self):
        """Cancel master order immediately"""
        try:
            if self.account_manager.accounts[1]['active']:
                api = self.account_manager.accounts[1]['api']
                if api:
                    # Get master's buy orders and cancel them
                    orders = api.get_order_book()
                    if orders and isinstance(orders, list):
                        for order in orders:
                            if (isinstance(order, dict) and 
                                order.get('status') in ['PENDING', 'OPEN'] and 
                                order.get('trantype') == 'B'):
                                
                                api.cancel_order(orderno=order.get('norenordno'))
                                applicationLogger.info(f"Cancelled master buy order: {order.get('norenordno')}")
            
        except Exception as e:
            applicationLogger.error(f"Error cancelling master order: {e}")
    
    def exit_child_at_market_price(self):
        """Exit child position at market price"""
        try:
            if self.account_manager.accounts[2]['active']:
                api = self.account_manager.accounts[2]['api']
                if api:
                    # Get child's filled buy orders and exit them
                    orders = api.get_order_book()
                    if orders and isinstance(orders, list):
                        for order in orders:
                            if (isinstance(order, dict) and 
                                order.get('status') == 'COMPLETE' and 
                                order.get('trantype') == 'B'):
                                
                                # Place market sell order
                                api.place_order(
                                    buy_or_sell='S',
                                    product_type=order.get('pcode', 'I'),
                                    exchange=order.get('exch', ''),
                                    tradingsymbol=order.get('tsym', ''),
                                    quantity=int(order.get('qty', 0)),
                                    discloseqty=0,
                                    price_type='MKT',
                                    price=0.0,
                                    trigger_price=None,
                                    retention='DAY',
                                    amo='NO',
                                    remarks='Emergency Exit - Master Rejected'
                                )
                                applicationLogger.info(f"Exited child position at market price")
            
        except Exception as e:
            applicationLogger.error(f"Error exiting child at market price: {e}")
    
    def block_child_exit_calls(self):
        """Block exit calls for child account"""
        try:
            # Disable child exit button
            if hasattr(self, 'exit_button'):
                self.exit_button.config(state='disabled')
            
            applicationLogger.info("Child exit calls blocked")
            
        except Exception as e:
            applicationLogger.error(f"Error blocking child exit calls: {e}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


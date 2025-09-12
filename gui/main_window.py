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
from market_data.symbol_manager import SymbolManager
from market_data.expiry_manager import ExpiryManager
from utils.telegram_notifications import send_sos_message
from logger import applicationLogger

class MainWindow:
    """Main application window"""
    
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("Duplicator - Master Not Logged In")
        self.root.geometry("850x450")
        
        # Master account holder name
        self.master_account_name = tk.StringVar()
        self.master_account_name.set("Not Logged In")
        
        # Initialize managers
        self.account_manager = AccountManager()
        self.order_manager = OrderManager()
        self.websocket_manager = WebSocketManager(self.account_manager, self.order_manager)
        self.position_manager = PositionManager()
        self.symbol_manager = SymbolManager()
        self.expiry_manager = ExpiryManager()

        
        # Set up live price callback
        self.websocket_manager.set_live_price_callback(self.update_live_price)
        
        # Set up order status callback
        self.websocket_manager.set_order_status_callback(self.update_order_status)
        self.websocket_manager.set_buy_order_completed_callback(self.on_buy_order_completed)
        self.websocket_manager.set_sell_order_completed_callback(self.on_sell_order_completed)
        
        # GUI variables
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize with master account
        self.initialize_master_account()
    
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

        self.sl_price_value = tk.StringVar()
        self.target_price_value = tk.StringVar()
        
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
        
        # SL and Target monitoring variables
        self.sl_monitoring_active = False
        self.target_monitoring_active = False
        self.sl_price_level = None
        self.target_price_level = None
        
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
    
    def create_style(self):
        """Create custom styles"""
        self.style = ttk.Style()
        self.style.configure("TButton", padding=(10, 10))
        self.style.configure("GreenButton.TButton", background="green")
        self.style.configure("RedButton.TButton", background="red")
    
    def create_login_buttons(self):
        """Create login buttons frame"""
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Child account login buttons
        self.login_button2 = tk.Button(
            self.login_frame, text="Login Child Account", 
            command=lambda: self.login_account(2), 
            width=20, height=3
        )
        self.login_button2.pack(side=tk.LEFT, padx=10)
        
        
        # Utility buttons
        self.release_button = ttk.Button(
            self.login_frame, text="RELEASE", 
            command=self.release_buttons, width=20
        )
        self.release_button.pack(side=tk.LEFT, padx=10)
        

        # Premium Price display
        tk.Label(self.login_frame, text="Premium Price:").pack(side=tk.LEFT, padx=5)
        self.premium_price_box = tk.Entry(
            self.login_frame, textvariable=self.premium_price_value, 
            width=15, state='readonly', font=('Helvetica', 12, 'bold')
        )
        self.premium_price_box.pack(side=tk.LEFT, padx=5)
    
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
        
        # Expiry display
        tk.Label(self.selection_frame, text="Expiry:").grid(row=0, column=2, padx=10)
        self.expiry_label = tk.Label(self.selection_frame, textvariable=self.expiry_value)
        self.expiry_label.grid(row=0, column=3, padx=10)
        
        # Option type (moved to left)
        tk.Label(self.selection_frame, text="Option:").grid(row=0, column=4, padx=10)
        option_types = ["CE", "PE"]
        self.option_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_option, 
            values=option_types, width=5
        )
        self.option_dropdown.grid(row=0, column=5, padx=10)
        self.selected_option.trace_add('write', self.on_option_selected)
        
        # Index LTP display (next to Option)
        tk.Label(self.selection_frame, text="Index LTP:").grid(row=0, column=6, padx=10)
        self.index_ltp_label = tk.Label(
            self.selection_frame, textvariable=self.index_ltp_value,
            font=('Helvetica', 10, 'bold'), fg="blue", width=10
        )
        self.index_ltp_label.grid(row=0, column=7, padx=5)
        
        # Strike selection (moved to right)
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
        
        # Exit button
        self.exit_button = ttk.Button(
            self.trading_frame, text="EXIT", 

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
        
        # SL Price and Target Price controls (next to order status)
        self.sl_price_button = tk.Button(
            self.status_frame, text="SL Price", 
            command=self.set_sl_price, width=20, height=1
        )
        self.sl_price_button.grid(row=0, column=2, padx=10, pady=5)
        
        self.sl_price_box = tk.Entry(
            self.status_frame, textvariable=self.sl_price_value, width=10
        )
        self.sl_price_box.grid(row=0, column=3, padx=5, pady=5)
        
        self.target_price_button = tk.Button(
            self.status_frame, text="Target Price", 
            command=self.set_target_price, width=20, height=1
        )
        self.target_price_button.grid(row=1, column=2, padx=10, pady=5)
        
        self.target_price_box = tk.Entry(
            self.status_frame, textvariable=self.target_price_value, width=10
        )
        self.target_price_box.grid(row=1, column=3, padx=5, pady=5)
    
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
        
        self.modify_buy_button = tk.Button(
            self.order_frame, text="Modify Buy", 
            command=self.modify_buy_orders, width=15, height=2,
            state="disabled"
        )

        self.modify_buy_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.modify_buy_box = tk.Entry(
            self.order_frame, textvariable=self.modify_buy_value, width=10
        )

        self.modify_buy_box.grid(row=0, column=2, padx=5, pady=5)
        
        # Cancel Exit and Modify Exit (right side)
        self.cancel_exit_button = tk.Button(
            self.order_frame, text="Cancel Exit", 
            command=self.cancel_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.cancel_exit_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.modify_exit_button = tk.Button(
            self.order_frame, text="Modify Exit", 

            command=self.modify_exit_orders, width=15, height=2,
            state="disabled"
        )
        self.modify_exit_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.modify_exit_box = tk.Entry(
            self.order_frame, textvariable=self.modify_exit_value, width=10
        )
        self.modify_exit_box.grid(row=0, column=5, padx=5, pady=5)
    

    def create_bottom_control_panel(self):
        """Create bottom control panel with exit and logout buttons"""
        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Exit All Orders at Market Price
        self.exit_all_button = tk.Button(
            self.bottom_frame, text="Exit All Orders at Market Price", 
            command=self.exit_all_orders_market, width=25, height=2
        )
        self.exit_all_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Exit Order Master at Market Price
        self.exit_master_button = tk.Button(
            self.bottom_frame, text="Exit Order Master at Market Price", 
            command=self.exit_master_orders_market, width=25, height=2
        )
        self.exit_master_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Exit Order Child at Market Price
        self.exit_child_button = tk.Button(
            self.bottom_frame, text="Exit Order Child at Market Price", 
            command=self.exit_child_orders_market, width=25, height=2
        )
        self.exit_child_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Child Account Logout
        self.child_logout_button = tk.Button(
            self.bottom_frame, text="Child Account Logout", 
            command=self.logout_child_account, width=25, height=2
        )
        self.child_logout_button.grid(row=0, column=3, padx=5, pady=5)
    
    
    def initialize_master_account(self):
        """Initialize master account on startup"""
        try:
            success, client_name = self.account_manager.login_account(1)
            if success:
                self.websocket_manager.connect_feed(1)

                # Update window title with master account name
                self.root.title(f"Duplicator - Master {client_name}")
                self.master_account_name.set(client_name)
                # Update button text to show logged in status
                self.update_login_button_text(1, client_name)
                # Update master order status to show it's ready
                self.master_order_status.set(self.get_ready_status_message(1))
                applicationLogger.info(f"Master account initialized successfully: {client_name}")
            else:
                messagebox.showerror("Error", f"Failed to initialize master account: {client_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error initializing master account: {e}")
    
    def login_account(self, account_num: int):
        """Login to a specific account"""
        try:
            success, client_name = self.account_manager.login_account(account_num)
            if success:
                self.websocket_manager.connect_feed(account_num)
                self.update_account_display(account_num, client_name)
                self.enable_account_buttons(account_num)

                
                # Update window title if this is the master account
                if account_num == 1:
                    self.root.title(f"Duplicator - Master {client_name}")
                    self.master_account_name.set(client_name)
                
                # Update button text to show logged in status
                self.update_login_button_text(account_num, client_name)
                
                # Update order status to show account is ready
                if account_num == 1:
                    self.master_order_status.set(self.get_ready_status_message(1))
                elif account_num == 2:
                    self.child_order_status.set(self.get_ready_status_message(2))
            else:
                messagebox.showerror("Error", f"Login failed: {client_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error logging in: {e}")
    
    def update_account_display(self, account_num: int, client_name: str):
        """Update account display"""
        if account_num == 1:
            self.master1_value.set(client_name)
        elif account_num == 2:
            self.child_value.set(client_name)
    

    def update_login_button_text(self, account_num: int, client_name: str):
        """Update login button text to show logged in status"""
        if account_num == 2:  # Child account
            self.login_button2.config(text=f"Logged in {client_name}")
            self.login_button2.config(state='disabled', bg='lightgreen')
    
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
            # Update expiry
            expiry = self.expiry_manager.get_expiry_date(index)
            self.expiry_value.set(expiry)
            
            # Check if there are any active orders
            has_active_orders = self.has_active_orders()
            
            # Clear option selection if no active orders
            if not has_active_orders:
                self.selected_option.set("")
                self.selected_strike.set("")
                self.index_ltp_value.set("--")
                applicationLogger.info("Cleared option and strike selections - no active orders")
            
            # Fetch current index price and update strike list
            try:
                api = self.account_manager.get_api(1)  # Use master account API
                if api:
                    current_price = self.symbol_manager.get_index_price(api, index)
                    if current_price:
                        strikes = self.expiry_manager.get_strike_list(index, current_price)
                        self.strike_dropdown['values'] = strikes
                        applicationLogger.info(f"Updated strikes for {index} based on price {current_price}: {strikes}")
                    else:
                        # Fallback to default strikes if price fetch fails
                        applicationLogger.warning(f"Could not fetch price for {index}, using default strikes")
                        default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                        strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000))
                        self.strike_dropdown['values'] = strikes
                else:
                    # Fallback if no API available
                    applicationLogger.warning("Master account API not available, using default strikes")
                    default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                    strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000))
                    self.strike_dropdown['values'] = strikes
            except Exception as e:
                applicationLogger.error(f"Error updating strikes for {index}: {e}")
                # Fallback to default strikes on error
                default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000))
                self.strike_dropdown['values'] = strikes
            
            # Update quantity list
            quantities = self.expiry_manager.get_quantity_list(index)
            self.qty_dropdown['values'] = quantities
    
    def on_option_selected(self, *args):
        """Handle option selection and fetch Index LTP if CE or PE is selected"""
        option = self.selected_option.get()
        index = self.selected_index.get()
        
        if option in ["CE", "PE"] and index:
            # Fetch Index LTP when CE or PE is selected
            self.fetch_index_ltp(index)
        
        # Also call the original concatenate_values method
        self.concatenate_values()
    
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
    
    def _generate_sensex_symbol(self, expiry: str, strike: str, option: str) -> str:
        """
        Generate SENSEX symbol based on expiry type
        
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
                
                # Check if it's the last Friday of the month (monthly expiry)
                last_day = calendar.monthrange(year_full, month_num)[1]
                last_friday = self._get_last_friday(year_full, month_num)
                
                if day_num == last_friday.day:
                    # Monthly expiry format: SENSEX25SEP87200CE
                    return f"SENSEX{year}{month}{strike}{option}"
                else:
                    # Daily expiry format: SENSEX2591187200CE
                    return f"SENSEX{year}{month_num:d}{day_num:02d}{strike}{option}"
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
            
            # Check for SL/Target breaches
            self.check_sl_target_breach(live_price)
            
        except Exception as e:
            applicationLogger.error(f"Error updating live price: {e}")
    
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
            applicationLogger.info("Exit button enabled after buy order completion")
                    
        except Exception as e:
            applicationLogger.error(f"Error handling buy order completion: {e}")
    
    def on_sell_order_completed(self, account_num: int, symbol: str, price: float):
        """Handle sell order completion - reset SL/Target monitoring and check if both accounts are complete"""
        try:
            applicationLogger.info(f"Sell order completed for account {account_num}: {symbol} @ {price}")
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            applicationLogger.info("SL and Target monitoring reset after sell order completion")
            
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
        """Reset UI to buy order status after sell orders are complete"""
        try:
            # Reset order status displays
            if self.account_manager.accounts[1]['active']:
                self.master_order_status.set(self.get_ready_status_message(1))
            if self.account_manager.accounts[2]['active']:
                self.child_order_status.set(self.get_ready_status_message(2))
            
            # Re-enable buy button
            self.buy_button.config(state='normal', text="BUY")
            
            # Disable exit-related buttons
            self.exit_button.config(state='disabled')
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            
            # Disable buy-related buttons until new orders are placed
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            
            # Clear order numbers
            self.order_numbers = {1: None, 2: None}
            self.exit_order_numbers = {1: None, 2: None}
            
            applicationLogger.info("UI reset to buy order status after sell completion")
            
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
    
    def _reset_ui_after_margin_shortfall(self):
        """Reset UI to initial state after margin shortfall"""
        try:
            # Re-enable buy button
            self.buy_button.config(state='normal', text="BUY")
            
            # Disable all other buttons
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            self.exit_button.config(state='disabled')
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
            
            applicationLogger.info("UI reset after margin shortfall")
            
        except Exception as e:
            applicationLogger.error(f"Error resetting UI after margin shortfall: {e}")
    
    def logout_child_account(self):
        """Logout child account (account 2)"""
        try:
            if self.account_manager.accounts[2]['active']:
                # Logout the child account
                success, message = self.account_manager.logout_account(2)
                if success:
                    # Update UI to show logged out status
                    self.child_order_status.set("Child Not Logged In")
                    self.update_login_button_text(2, "Not Logged In")
                    applicationLogger.info("Child account logged out successfully")
                    messagebox.showinfo("Success", "Child account logged out successfully")
                else:
                    applicationLogger.error(f"Failed to logout child account: {message}")
                    messagebox.showerror("Error", f"Failed to logout child account: {message}")
            else:
                messagebox.showwarning("Warning", "Child account is not logged in")
        except Exception as e:
            applicationLogger.error(f"Error logging out child account: {e}")
            messagebox.showerror("Error", f"Error logging out child account: {e}")
    
    def place_buy_orders(self):
        """Place buy orders across all active accounts"""
        try:

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
            

            # Set quantities for all accounts - use same quantity for both master and child
            # Ensure quantity is a multiple of lot size
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    if lot_size and qty1 % lot_size == 0:
                        # Quantity is already a multiple of lot size, use as is
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.info(f"Using same quantity for both accounts: {qty1} (lot size: {lot_size})")
                    else:
                        # Adjust quantity to be a multiple of lot size
                        if lot_size:
                            adjusted_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                            self.quantities[1] = adjusted_qty
                            self.quantities[2] = adjusted_qty
                            applicationLogger.info(f"Adjusted quantity to lot size multiple: {adjusted_qty} (original: {qty1}, lot size: {lot_size})")
                        else:
                            # Fallback to original quantity if lot size not found
                            self.quantities[1] = qty1
                            self.quantities[2] = qty1
                            applicationLogger.warning(f"Lot size not found, using original quantity: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
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
            
            # Place orders
            order_numbers = self.order_manager.place_buy_orders(
                apis, quantities, trading_symbol, price, active_flags
            )
            
            # Check for margin shortfall and handle accordingly
            if self.order_manager.margin_shortfall_occurred:
                self._handle_margin_shortfall()
                return
            
            # Update order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    self.order_numbers[active_accounts[i]] = order_num
            

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
            
            # Enable buy-related buttons for order management
            self.cancel_buy_button.config(state='normal')
            self.modify_buy_button.config(state='normal')
            applicationLogger.info("Cancel Buy and Modify Buy buttons enabled after buy orders placed")
            
            # Keep exit button disabled until buy orders are completed
            self.exit_button.config(state='disabled')
            applicationLogger.info("Exit button kept disabled until buy orders are completed")
            
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
    
    def place_exit_orders(self):
        """Place exit orders across all active accounts"""
        try:

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
            

            # Set quantities for all accounts - use same quantity for both master and child
            # Ensure quantity is a multiple of lot size
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    if lot_size and qty1 % lot_size == 0:
                        # Quantity is already a multiple of lot size, use as is
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.info(f"Using same quantity for both accounts: {qty1} (lot size: {lot_size})")
                    else:
                        # Adjust quantity to be a multiple of lot size
                        if lot_size:
                            adjusted_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                            self.quantities[1] = adjusted_qty
                            self.quantities[2] = adjusted_qty
                            applicationLogger.info(f"Adjusted quantity to lot size multiple: {adjusted_qty} (original: {qty1}, lot size: {lot_size})")
                        else:
                            # Fallback to original quantity if lot size not found
                            self.quantities[1] = qty1
                            self.quantities[2] = qty1
                            applicationLogger.warning(f"Lot size not found, using original quantity: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            applicationLogger.info(f"Active accounts for exit: {active_accounts}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts found. Please login to accounts first.")
                return
            
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            applicationLogger.info(f"Placing exit orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place orders
            order_numbers = self.order_manager.place_exit_orders(
                apis, quantities, trading_symbol, price, active_flags
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
            self.exit_button.config(state='disabled', text=f"ExitOrderPlaced@{price}")
            applicationLogger.info("Exit button disabled to prevent duplicate orders")
            
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
    
    def cancel_buy_orders(self):
        """Cancel buy orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)

            # Update status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Buy Orders Cancelled")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Buy Orders Cancelled")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            # Re-enable buy button and disable buy-related management buttons
            self.buy_button.config(state='normal', text="BUY")
            self.cancel_buy_button.config(state='disabled')
            self.modify_buy_button.config(state='disabled')
            applicationLogger.info("Buy button re-enabled after cancelling buy orders")
            
            # Reset SL and Target monitoring
            self.reset_sl_target_monitoring()
            
        except Exception as e:

            applicationLogger.error(f"Error cancelling buy orders: {e}")
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
    
    def cancel_exit_orders(self):
        """Cancel exit orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.exit_order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)

            # Update status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Exit Orders Cancelled")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Exit Orders Cancelled")
            else:
                self.child_order_status.set("Child Not Logged In")
            
            # Re-enable exit button and disable exit-related management buttons
            self.exit_button.config(state='normal', text="EXIT")
            self.cancel_exit_button.config(state='disabled')
            self.modify_exit_button.config(state='disabled')
            applicationLogger.info("Exit button re-enabled after cancelling exit orders")
            
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
    
    def modify_buy_orders(self):
        """Modify buy orders across all active accounts"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")

                return
            
            # If modify buy box is empty, populate with current LTP and return (don't place order yet)
            if not self.modify_buy_value.get().strip():
                current_ltp = self.premium_price_value.get()
                if current_ltp:
                    self.modify_buy_value.set(current_ltp)
                    applicationLogger.info(f"Modify Buy box populated with current LTP: {current_ltp}")
                    return  # Stop here - user needs to press button again to place order
                else:
                    messagebox.showerror("Error", "Please fetch current price first")
                return
            
            price = float(self.modify_buy_value.get())
            qty1 = int(self.qty1_var.get())
            

            # Set quantities for all accounts - use same quantity for both master and child
            # Ensure quantity is a multiple of lot size
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    if lot_size and qty1 % lot_size == 0:
                        # Quantity is already a multiple of lot size, use as is
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.info(f"Using same quantity for both accounts: {qty1} (lot size: {lot_size})")
                    else:
                        # Adjust quantity to be a multiple of lot size
                        if lot_size:
                            adjusted_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                            self.quantities[1] = adjusted_qty
                            self.quantities[2] = adjusted_qty
                            applicationLogger.info(f"Adjusted quantity to lot size multiple: {adjusted_qty} (original: {qty1}, lot size: {lot_size})")
                        else:
                            # Fallback to original quantity if lot size not found
                            self.quantities[1] = qty1
                            self.quantities[2] = qty1
                            applicationLogger.warning(f"Lot size not found, using original quantity: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )

            # Update status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Buy Orders Modified - Waiting for Status")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
                self.child_order_status.set("Buy Orders Modified - Waiting for Status")
            else:
                self.child_order_status.set("Child Not Logged In")
            
        except Exception as e:

            applicationLogger.error(f"Error modifying buy orders: {e}")
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
    
    def modify_exit_orders(self):
        """Modify exit orders across all active accounts"""
        try:
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
            

            # Set quantities for all accounts - use same quantity for both master and child
            # Ensure quantity is a multiple of lot size
            if trading_symbol:
                try:
                    # Get lot size for the trading symbol
                    token, lot_size = self.symbol_manager.get_token_and_lot_size(trading_symbol)
                    if lot_size and qty1 % lot_size == 0:
                        # Quantity is already a multiple of lot size, use as is
                        self.quantities[1] = qty1
                        self.quantities[2] = qty1
                        applicationLogger.info(f"Using same quantity for both accounts: {qty1} (lot size: {lot_size})")
                    else:
                        # Adjust quantity to be a multiple of lot size
                        if lot_size:
                            adjusted_qty = ((qty1 + lot_size - 1) // lot_size) * lot_size
                            self.quantities[1] = adjusted_qty
                            self.quantities[2] = adjusted_qty
                            applicationLogger.info(f"Adjusted quantity to lot size multiple: {adjusted_qty} (original: {qty1}, lot size: {lot_size})")
                        else:
                            # Fallback to original quantity if lot size not found
                            self.quantities[1] = qty1
                            self.quantities[2] = qty1
                            applicationLogger.warning(f"Lot size not found, using original quantity: {qty1}")
                except Exception as e:
                    applicationLogger.error(f"Error getting lot size: {e}")
                    # Fallback to original quantity
                    self.quantities[1] = qty1
                    self.quantities[2] = qty1
            else:
                # Fallback if trading symbol not available
                self.quantities[1] = qty1
                self.quantities[2] = qty1
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.exit_order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )

            # Update status displays based on active accounts
            if 1 in active_accounts:
                self.master_order_status.set("Exit Orders Modified - Waiting for Status")
            else:
                self.master_order_status.set("Master Not Logged In")
                
            if 2 in active_accounts:
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

        """Release button states - enable buy and exit buttons"""
        # Enable buy button
        self.buy_button.config(state='normal', text="BUY")
        
        # Disable buy-related buttons until new buy orders are placed
        self.cancel_buy_button.config(state='disabled')
        self.modify_buy_button.config(state='disabled')
        
        # Disable exit-related buttons until new orders are placed
        self.exit_button.config(state='disabled', text="EXIT")
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
    
    
    
    def exit_all_orders_market(self):
        """Exit all orders at market price for both master and child accounts"""
        try:
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
            for account_num in active_accounts:
                api = self.account_manager.accounts[account_num]['api']
                if api:
                    # Get current orders and exit them at market price
                    orders = api.get_order_book()
                    if orders and orders.get('stat') == 'Ok':
                        order_data = orders.get('data', [])
                        if isinstance(order_data, list):
                            for order in order_data:
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
                                    else:
                                        applicationLogger.error(f"Failed to place market exit order for account {account_num}")
            
            # Update status
            self.master_order_status.set("All Orders - Market Exit Placed")
            self.child_order_status.set("All Orders - Market Exit Placed")
            
        except Exception as e:
            applicationLogger.error(f"Error in exit_all_orders_market: {e}")
            self.master_order_status.set(f"Error: {str(e)[:30]}...")
            self.child_order_status.set(f"Error: {str(e)[:30]}...")
    
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
                applicationLogger.info("Exit master orders cancelled by user")
                return
            

            applicationLogger.info("Exiting master orders at market price")
            
            if not self.account_manager.accounts[1]['active']:
                self.master_order_status.set("Master Not Logged In")
                return
            
            api = self.account_manager.accounts[1]['api']
            if api:
                # Get current orders and exit them at market price
                orders = api.get_order_book()
                if orders and orders.get('stat') == 'Ok':
                    order_data = orders.get('data', [])
                    if isinstance(order_data, list):
                        for order in order_data:
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
                                    remarks='Master Market Exit'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Master market exit order placed: {exit_result.get('norenordno')}")
                                else:
                                    applicationLogger.error("Failed to place master market exit order")
                
                self.master_order_status.set("Master Orders - Market Exit Placed")
            else:
                self.master_order_status.set("Master API Not Available")
                
        except Exception as e:
            applicationLogger.error(f"Error in exit_master_orders_market: {e}")
            self.master_order_status.set(f"Error: {str(e)[:30]}...")
    
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
                applicationLogger.info("Exit child orders cancelled by user")
                return
            
            applicationLogger.info("Exiting child orders at market price")
            
            if not self.account_manager.accounts[2]['active']:
                self.child_order_status.set("Child Not Logged In")
                return
            
            api = self.account_manager.accounts[2]['api']
            if api:
                # Get current orders and exit them at market price
                orders = api.get_order_book()
                if orders and orders.get('stat') == 'Ok':
                    order_data = orders.get('data', [])
                    if isinstance(order_data, list):
                        for order in order_data:
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
                                    remarks='Child Market Exit'
                                )
                                
                                if exit_result and exit_result.get('stat') == 'Ok':
                                    applicationLogger.info(f"Child market exit order placed: {exit_result.get('norenordno')}")
                                else:
                                    applicationLogger.error("Failed to place child market exit order")
                
                self.child_order_status.set("Child Orders - Market Exit Placed")
            else:
                self.child_order_status.set("Child API Not Available")
                
        except Exception as e:
            applicationLogger.error(f"Error in exit_child_orders_market: {e}")
            self.child_order_status.set(f"Error: {str(e)[:30]}...")
    
    def set_sl_price(self):
        """Set Stop Loss price and activate monitoring if buy order is active"""
        try:
            # Check if SL price is manually entered
            sl_price_text = self.sl_price_value.get().strip()
            
            if sl_price_text:
                # Validate SL price
                sl_price = float(sl_price_text)
                
                # Check if buy orders are filled/completed
                if self._are_buy_orders_filled():
                    # If buy orders are filled, immediately start SL monitoring
                    self.start_sl_monitoring(sl_price)
                    applicationLogger.info(f"SL price set and monitoring started: {sl_price} (buy orders are filled)")
                else:
                    # If buy orders not filled yet, just set the price (monitoring will start after buy order is filled)
                    self.sl_price_button.config(text=f"SL set @{sl_price}", bg="orange", fg="white")
                    applicationLogger.info(f"SL price set to: {sl_price} (monitoring will start after buy order is filled)")
            else:
                # Auto-suggest SL price based on current price
                current_price = self.premium_price_value.get()
                if current_price:
                    current_price_float = float(current_price)
                    # Suggest SL price (1% below current price for long positions)
                    suggested_sl = round(current_price_float * 0.99, 2)
                    self.sl_price_value.set(str(suggested_sl))
                    
                    # Check if buy orders are filled/completed
                    if self._are_buy_orders_filled():
                        # If buy orders are filled, immediately start SL monitoring
                        self.start_sl_monitoring(suggested_sl)
                        applicationLogger.info(f"SL price suggested and monitoring started: {suggested_sl} (buy orders are filled)")
                    else:
                        # If buy orders not filled yet, just set the price
                        self.sl_price_button.config(text=f"SL set @{suggested_sl}", bg="orange", fg="white")
                        applicationLogger.info(f"SL price suggested: {suggested_sl} (1% below LTP: {current_price_float})")
                else:
                    applicationLogger.warning("Please fetch current price first to set SL")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid SL price")
        except Exception as e:
            applicationLogger.error(f"Error setting SL price: {e}")
            messagebox.showerror("Error", f"Error setting SL price: {e}")
    
    def set_target_price(self):
        """Set Target price and activate monitoring if buy order is active"""
        try:
            # Check if Target price is manually entered
            target_price_text = self.target_price_value.get().strip()
            
            if target_price_text:
                # Validate Target price
                target_price = float(target_price_text)
                
                # Check if buy orders are filled/completed
                if self._are_buy_orders_filled():
                    # If buy orders are filled, immediately start Target monitoring
                    self.start_target_monitoring(target_price)
                    applicationLogger.info(f"Target price set and monitoring started: {target_price} (buy orders are filled)")
                else:
                    # If buy orders not filled yet, just set the price (monitoring will start after buy order is filled)
                    self.target_price_button.config(text=f"Target set @{target_price}", bg="orange", fg="white")
                    applicationLogger.info(f"Target price set to: {target_price} (monitoring will start after buy order is filled)")
            else:
                # Auto-suggest Target price based on current price
                current_price = self.premium_price_value.get()
                if current_price:
                    current_price_float = float(current_price)
                    # Suggest target price (1% above current price for long positions)
                    suggested_target = round(current_price_float * 1.01, 2)
                    self.target_price_value.set(str(suggested_target))
                    
                    # Check if buy orders are filled/completed
                    if self._are_buy_orders_filled():
                        # If buy orders are filled, immediately start Target monitoring
                        self.start_target_monitoring(suggested_target)
                        applicationLogger.info(f"Target price suggested and monitoring started: {suggested_target} (buy orders are filled)")
                    else:
                        # If buy orders not filled yet, just set the price
                        self.target_price_button.config(text=f"Target set @{suggested_target}", bg="orange", fg="white")
                        applicationLogger.info(f"Target price suggested: {suggested_target} (1% above LTP: {current_price_float})")
                else:
                    applicationLogger.warning("Please fetch current price first to set Target")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid Target price")
        except Exception as e:
            applicationLogger.error(f"Error setting target price: {e}")
            messagebox.showerror("Error", f"Error setting target price: {e}")
    
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
        self.sl_price_button.config(text="SL Price", bg="SystemButtonFace", fg="black")
        applicationLogger.info("SL monitoring stopped")
    
    def stop_target_monitoring(self):
        """Stop Target monitoring"""
        self.target_monitoring_active = False
        self.target_price_level = None
        self.target_price_button.config(text="Target Price", bg="SystemButtonFace", fg="black")
        applicationLogger.info("Target monitoring stopped")
    
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
        
        applicationLogger.info("SL and Target monitoring reset and fields cleared")
    
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
                self.execute_target_exit(current_price_float)
                
        except Exception as e:
            applicationLogger.error(f"Error checking SL/Target breach: {e}")
    
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
            
            # Set the exit price to current price and call regular exit function
            self.price1_value.set(str(current_price))
            self.place_exit_orders()
            
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
            
            # Set the exit price to current price and call regular exit function
            self.price1_value.set(str(current_price))
            self.place_exit_orders()
            
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
                    orders = api.get_order_book()
                    if orders and orders.get('stat') == 'Ok':
                        order_data = orders.get('data', [])
                        if isinstance(order_data, list):
                            for order in order_data:
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
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


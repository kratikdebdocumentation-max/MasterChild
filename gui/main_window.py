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
        self.root.geometry("800x350")
        
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
        
        # Premium price variable for live updates
        self.premium_price_value = tk.StringVar()
        
        # Order status variables
        self.master_order_status = tk.StringVar()
        self.child_order_status = tk.StringVar()
        self.master_order_status.set("No Orders")
        self.child_order_status.set("No Orders")
        
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
        self.create_order_status_display()
        # self.create_account_display()  # Hidden - will be part of website dashboard
        self.create_order_buttons()
    
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
        
        # Strike selection
        tk.Label(self.selection_frame, text="Select Strike:").grid(row=0, column=4, padx=10)
        self.strike_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_strike, 
            width=15
        )
        self.strike_dropdown.grid(row=0, column=5, padx=10)
        
        # Option type
        tk.Label(self.selection_frame, text="Option:").grid(row=0, column=6, padx=10)
        option_types = ["CE", "PE"]
        self.option_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.selected_option, 
            values=option_types, width=5
        )
        self.option_dropdown.grid(row=0, column=7, padx=10)
        self.selected_option.trace_add('write', self.concatenate_values)
        
        # Refresh strikes button
        self.refresh_strikes_button = ttk.Button(
            self.selection_frame, text="Refresh Strikes", 
            command=self.refresh_strikes, width=15
        )
        self.refresh_strikes_button.grid(row=0, column=8, padx=10)
    
    def create_trading_frame(self):
        """Create trading controls frame"""
        self.trading_frame = tk.Frame(self.root)
        self.trading_frame.pack(side=tk.TOP, pady=10)
        
        # Fetch price button
        self.fetch_button = tk.Button(
            self.trading_frame, text="Fetch Price", 
            command=self.fetch_price, width=20, height=3
        )
        self.fetch_button.pack(side=tk.LEFT, padx=10)
        
        # Price display
        tk.Label(self.trading_frame, text="Price").pack(side=tk.LEFT, padx=5)
        self.price_box = tk.Entry(
            self.trading_frame, textvariable=self.price_value, width=10
        )
        self.price_box.pack(side=tk.LEFT, padx=5)
        
        # Quantity selection
        tk.Label(self.trading_frame, text="Qty").pack(side=tk.LEFT, padx=5)
        self.qty_dropdown = ttk.Combobox(
            self.trading_frame, textvariable=self.qty1_var, width=10
        )
        self.qty_dropdown.pack(side=tk.LEFT, padx=5)
        
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
            command=self.place_exit_orders, width=20, style="RedButton.TButton"
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
            fg="darkblue"
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
        
        # Cancel buttons
        self.cancel_buy_button = tk.Button(
            self.order_frame, text="Cancel Buy", 
            command=self.cancel_buy_orders, width=15, height=2
        )
        self.cancel_buy_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.cancel_exit_button = tk.Button(
            self.order_frame, text="Cancel Exit", 
            command=self.cancel_exit_orders, width=15, height=2
        )
        self.cancel_exit_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Modify buy
        self.modify_buy_button = tk.Button(
            self.order_frame, text="Modify Buy", 
            command=self.modify_buy_orders, width=15, height=2
        )
        self.modify_buy_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.modify_buy_box = tk.Entry(
            self.order_frame, textvariable=self.modify_buy_value, width=10
        )
        self.modify_buy_box.grid(row=0, column=3, padx=5, pady=5)
        
        # Modify exit
        self.modify_exit_button = tk.Button(
            self.order_frame, text="Modify Exit", 
            command=self.modify_exit_orders, width=15, height=2
        )
        self.modify_exit_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.modify_exit_box = tk.Entry(
            self.order_frame, textvariable=self.modify_exit_value, width=10
        )
        self.modify_exit_box.grid(row=0, column=5, padx=5, pady=5)
    
    
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
    
    def update_selections(self, *args):
        """Update selections based on index"""
        index = self.selected_index.get()
        if index in ["NIFTY", "BANKNIFTY", "SENSEX"]:
            # Update expiry
            expiry = self.expiry_manager.get_expiry_date(index)
            self.expiry_value.set(expiry)
            
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
                self.price1_value.set(price)
                self.modify_buy_value.set(price)
                self.modify_exit_value.set(price)
                self.premium_price_value.set(price)  # Set initial premium price
                
                # Subscribe to websocket for live updates
                self.subscribe_to_live_price(api, trading_symbol)
            else:
                messagebox.showerror("Error", "Could not fetch price")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching price: {e}")
    
    def subscribe_to_live_price(self, api, trading_symbol: str):
        """Subscribe to websocket for live price updates"""
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
            
            # Subscribe to new symbol
            websocket_token = f'{exchange}|{token}'
            api.subscribe(websocket_token)
            self.current_subscription = websocket_token
            applicationLogger.info(f"Subscribed to live price feed: {websocket_token}")
            
        except Exception as e:
            applicationLogger.error(f"Error subscribing to live price: {e}")
    
    def update_live_price(self, live_price: float):
        """Update the premium price box with live price"""
        try:
            # Update the premium price box with live price
            self.premium_price_value.set(f"{live_price:.2f}")
            applicationLogger.debug(f"Updated live price: {live_price}")
        except Exception as e:
            applicationLogger.error(f"Error updating live price: {e}")
    
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
    
    def place_buy_orders(self):
        """Place buy orders across all active accounts"""
        try:
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.price_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for all accounts
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            
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
            
            # Update order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    self.order_numbers[active_accounts[i]] = order_num
            
            # Reset order status displays
            self.master_order_status.set("Orders Placed - Waiting for Status")
            self.child_order_status.set("Orders Placed - Waiting for Status")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing buy orders: {e}")
    
    def place_exit_orders(self):
        """Place exit orders across all active accounts"""
        try:
            if not self.qty1_var.get():
                messagebox.showerror("Error", "Please select quantity")
                return
            
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.price1_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for all accounts
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            
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
            
            # Reset order status displays
            self.master_order_status.set("Exit Orders Placed - Waiting for Status")
            self.child_order_status.set("Exit Orders Placed - Waiting for Status")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing exit orders: {e}")
    
    def cancel_buy_orders(self):
        """Cancel buy orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)
            # Update status displays
            self.master_order_status.set("Buy Orders Cancelled")
            self.child_order_status.set("Buy Orders Cancelled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cancelling buy orders: {e}")
    
    def cancel_exit_orders(self):
        """Cancel exit orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.exit_order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)
            # Update status displays
            self.master_order_status.set("Exit Orders Cancelled")
            self.child_order_status.set("Exit Orders Cancelled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cancelling exit orders: {e}")
    
    def modify_buy_orders(self):
        """Modify buy orders across all active accounts"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.modify_buy_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for all accounts
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )
            # Update status displays
            self.master_order_status.set("Buy Orders Modified - Waiting for Status")
            self.child_order_status.set("Buy Orders Modified - Waiting for Status")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error modifying buy orders: {e}")
    
    def modify_exit_orders(self):
        """Modify exit orders across all active accounts"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.modify_exit_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for all accounts
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.exit_order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )
            # Update status displays
            self.master_order_status.set("Exit Orders Modified - Waiting for Status")
            self.child_order_status.set("Exit Orders Modified - Waiting for Status")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error modifying exit orders: {e}")
    
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
        """Release button states"""
        self.buy_button.state(['!pressed', '!disabled'])
        self.exit_button.state(['!pressed', '!disabled'])
    
    
    def refresh_strikes(self):
        """Manually refresh strike prices based on current index selection"""
        try:
            index = self.selected_index.get()
            if not index:
                messagebox.showwarning("Warning", "Please select an index first")
                return
            
            if index not in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                messagebox.showwarning("Warning", "Invalid index selected")
                return
            
            # Get master account API
            api = self.account_manager.get_api(1)
            if not api:
                messagebox.showerror("Error", "Master account not available")
                return
            
            # Fetch current index price
            current_price = self.symbol_manager.get_index_price(api, index)
            if current_price:
                strikes = self.expiry_manager.get_strike_list(index, current_price)
                self.strike_dropdown['values'] = strikes
                
                # Show current price to user
                messagebox.showinfo(
                    "Strikes Updated", 
                    f"{index} Current Price: ₹{current_price:,.2f}\nStrikes updated around this price"
                )
                applicationLogger.info(f"Manually refreshed strikes for {index} at price {current_price}")
            else:
                messagebox.showerror("Error", f"Could not fetch current price for {index}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing strikes: {e}")
            applicationLogger.error(f"Error in refresh_strikes: {e}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

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
        self.root.title("Shoonya Master-Child Trading System")
        self.root.geometry("1200x600")
        
        # Initialize managers
        self.account_manager = AccountManager()
        self.order_manager = OrderManager()
        self.websocket_manager = WebSocketManager(self.account_manager, self.order_manager, self)
        self.position_manager = PositionManager()
        self.symbol_manager = SymbolManager()
        self.expiry_manager = ExpiryManager()
        
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
        self.modify_sell_value = tk.StringVar()
        
        # Quantity variables
        self.qty1_var = tk.StringVar()
        
        # Account display variables
        self.master1_value = tk.StringVar()
        self.child2_value = tk.StringVar()
        
        # Order numbers
        self.order_numbers = {
            1: '', 2: ''
        }
        self.sell_order_numbers = {
            1: '', 2: ''
        }
        
        # Quantities
        self.quantities = {
            1: '', 2: ''
        }
    
    def create_widgets(self):
        """Create GUI widgets"""
        self.create_style()
        self.create_login_buttons()
        self.create_selection_frame()
        self.create_trading_frame()
        self.create_account_display()
        self.create_order_buttons()
        self.create_modify_buttons()
    
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
        
        # Child account login button
        self.login_button2 = tk.Button(
            self.login_frame, text="CHILD", 
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
        
        self.premium_price_button = ttk.Button(
            self.login_frame, text="Premium Price", 
            command=self.update_premium_price, width=20
        )
        self.premium_price_button.pack(side=tk.LEFT, padx=10)
    
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
        
        # Sell price
        self.price1_box = tk.Entry(
            self.trading_frame, textvariable=self.price1_value, width=10
        )
        self.price1_box.pack(side=tk.LEFT, padx=5)
        
        # Sell button
        self.sell_button = ttk.Button(
            self.trading_frame, text="SELL", 
            command=self.place_sell_orders, width=20, style="RedButton.TButton"
        )
        self.sell_button.pack(side=tk.LEFT, padx=10)
    
    def create_account_display(self):
        """Create account display frame"""
        self.account_frame = tk.Frame(self.root)
        self.account_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Account buttons and displays
        accounts = [
            (1, "MASTER", self.master1_value),
            (2, "CHILD", self.child2_value)
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
                width=15, height=2, bg="lightgray"
            )
            status_button.grid(row=i, column=2, padx=5, pady=5)
            
            # Store button reference for WebSocket updates
            if account_num == 1:
                self.master1_status_button = status_button
            elif account_num == 2:
                self.child2_status_button = status_button
            
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
        
        self.cancel_sell_button = tk.Button(
            self.order_frame, text="Cancel Sell", 
            command=self.cancel_sell_orders, width=15, height=2
        )
        self.cancel_sell_button.grid(row=0, column=1, padx=5, pady=5)
    
    def create_modify_buttons(self):
        """Create modify order buttons"""
        self.modify_frame = tk.Frame(self.root)
        self.modify_frame.pack(side=tk.TOP, pady=10)
        
        # Modify buy
        self.modify_buy_button = tk.Button(
            self.modify_frame, text="Modify Buy", 
            command=self.modify_buy_orders, width=15, height=2
        )
        self.modify_buy_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.modify_buy_box = tk.Entry(
            self.modify_frame, textvariable=self.modify_buy_value, width=10
        )
        self.modify_buy_box.grid(row=0, column=1, padx=5, pady=5)
        
        # Modify sell
        self.modify_sell_button = tk.Button(
            self.modify_frame, text="Modify Sell", 
            command=self.modify_sell_orders, width=15, height=2
        )
        self.modify_sell_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.modify_sell_box = tk.Entry(
            self.modify_frame, textvariable=self.modify_sell_value, width=10
        )
        self.modify_sell_box.grid(row=1, column=1, padx=5, pady=5)
    
    def initialize_master_account(self):
        """Initialize master account on startup"""
        try:
            success, client_name = self.account_manager.login_account(1)
            if success:
                self.websocket_manager.connect_feed(1)
                applicationLogger.info("Master account initialized successfully")
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
                messagebox.showinfo("Success", f"Logged in to account {account_num}: {client_name}")
            else:
                messagebox.showerror("Error", f"Login failed: {client_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error logging in: {e}")
    
    def update_account_display(self, account_num: int, client_name: str):
        """Update account display"""
        if account_num == 1:
            self.master1_value.set(client_name)
        elif account_num == 2:
            self.child2_value.set(client_name)
    
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
                trading_symbol = f"{index}{expiry}{option}{strike}"
            
            # Update account displays
            self.master1_value.set(trading_symbol)
            self.child2_value.set(trading_symbol)
            
            return trading_symbol
        return ""
    
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
        """Fetch current price for selected symbol"""
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
                self.modify_sell_value.set(price)
            else:
                messagebox.showerror("Error", "Could not fetch price")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching price: {e}")
    
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
            
            # Set quantities for Master and Child
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            elif self.selected_index.get() == "SENSEX":
                self.quantities[2] = 20
            
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
            
            messagebox.showinfo("Success", "Buy orders placed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing buy orders: {e}")
    
    def place_sell_orders(self):
        """Place sell orders across all active accounts"""
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
            
            # Set quantities for Master and Child
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            elif self.selected_index.get() == "SENSEX":
                self.quantities[2] = 20
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            applicationLogger.info(f"Active accounts for sell: {active_accounts}")
            
            if not active_accounts:
                messagebox.showerror("Error", "No active accounts found. Please login to accounts first.")
                return
            
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            applicationLogger.info(f"Placing sell orders for accounts: {active_accounts}")
            applicationLogger.info(f"Trading symbol: {trading_symbol}, Price: {price}")
            applicationLogger.info(f"Quantities: {quantities}")
            
            # Place orders
            order_numbers = self.order_manager.place_sell_orders(
                apis, quantities, trading_symbol, price, active_flags
            )
            
            # Update sell order numbers
            for i, order_num in enumerate(order_numbers):
                if order_num:
                    self.sell_order_numbers[active_accounts[i]] = order_num
            
            messagebox.showinfo("Success", "Sell orders placed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error placing sell orders: {e}")
    
    def cancel_buy_orders(self):
        """Cancel buy orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)
            messagebox.showinfo("Success", "Buy orders cancelled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cancelling buy orders: {e}")
    
    def cancel_sell_orders(self):
        """Cancel sell orders across all active accounts"""
        try:
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.sell_order_numbers[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.cancel_orders(apis, order_numbers, active_flags)
            messagebox.showinfo("Success", "Sell orders cancelled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cancelling sell orders: {e}")
    
    def modify_buy_orders(self):
        """Modify buy orders across all active accounts"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.modify_buy_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for Master and Child
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            elif self.selected_index.get() == "SENSEX":
                self.quantities[2] = 20
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )
            messagebox.showinfo("Success", "Buy orders modified")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error modifying buy orders: {e}")
    
    def modify_sell_orders(self):
        """Modify sell orders across all active accounts"""
        try:
            trading_symbol = self.concatenate_values()
            if not trading_symbol:
                messagebox.showerror("Error", "Please select all required fields")
                return
            
            price = float(self.modify_sell_value.get())
            qty1 = int(self.qty1_var.get())
            
            # Set quantities for Master and Child
            self.quantities[1] = qty1
            if self.selected_index.get() == "NIFTY":
                self.quantities[2] = 25
            elif self.selected_index.get() == "BANKNIFTY":
                self.quantities[2] = 15
            elif self.selected_index.get() == "SENSEX":
                self.quantities[2] = 20
            
            # Get active accounts
            active_accounts = self.account_manager.get_all_active_accounts()
            apis = [self.account_manager.get_api(i) for i in active_accounts]
            order_numbers = [self.sell_order_numbers[i] for i in active_accounts]
            quantities = [self.quantities[i] for i in active_accounts]
            active_flags = [True] * len(active_accounts)
            
            self.order_manager.modify_orders(
                apis, order_numbers, quantities, trading_symbol, price, active_flags
            )
            messagebox.showinfo("Success", "Sell orders modified")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error modifying sell orders: {e}")
    
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
        details_window.geometry("1200x400")
        
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
        self.sell_button.state(['!pressed', '!disabled'])
    
    def update_premium_price(self):
        """Update premium price (placeholder)"""
        pass
    
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

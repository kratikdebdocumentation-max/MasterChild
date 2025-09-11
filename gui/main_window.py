"""
Modern GUI window for Master-Child Trading System
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
from .theme import ModernTheme, ModernColors, ModernFonts, ModernIcons
from .components import (
    ModernCard, ModernButton, ModernEntry, ModernLabel, 
    ModernCombobox, StatusIndicator, ProgressBar, AccountCard
)
from .settings_window import SettingsWindow

class MainWindow:
    """Modern main application window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Shoonya Master-Child Trading System")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        
        # Initialize theme
        self.theme = ModernTheme()
        self.theme.set_theme("light")  # Set light theme as default
        self.theme.configure_styles(self.root)
        
        # Force apply theme to root window
        self.root.configure(bg=self.theme.get_theme()["primary"])
        
        # Initialize managers
        self.account_manager = AccountManager()
        self.order_manager = OrderManager()
        self.websocket_manager = WebSocketManager(self.account_manager, self.order_manager, self)
        self.position_manager = PositionManager()
        self.symbol_manager = SymbolManager()
        self.expiry_manager = ExpiryManager()
        
        # GUI variables
        self.setup_variables()
        
        # Create modern GUI
        self.create_modern_layout()
        
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
    
    def create_modern_layout(self):
        """Create modern GUI layout"""
        # Create main container with padding
        main_container = tk.Frame(self.root, bg=self.theme.get_theme()["primary"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Force apply light theme background
        main_container.configure(bg="#f5f5f5")
        
        # Create header
        self.create_header(main_container)
        
        # Create main content area
        content_frame = tk.Frame(main_container, bg="#f5f5f5")
        content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Left panel - Account management
        self.create_account_panel(content_frame)
        
        # Center panel - Trading controls
        self.create_trading_panel(content_frame)
        
        # Right panel - Order management
        self.create_order_panel(content_frame)
        
        # Bottom panel - Status and logs
        self.create_status_panel(main_container)
    
    def create_header(self, parent):
        """Create modern header with title and controls"""
        header_frame = tk.Frame(parent, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = ModernLabel(
            header_frame,
            text=f"{ModernIcons.CHART} Shoonya Master-Child Trading System",
            style="title"
        )
        title_label.pack(side="left")
        
        # Theme toggle and controls
        controls_frame = tk.Frame(header_frame, bg="#f5f5f5")
        controls_frame.pack(side="right")
        
        # Settings button
        settings_btn = ModernButton(
            controls_frame,
            text="Settings",
            icon=ModernIcons.SETTINGS,
            command=self.open_settings,
            style="primary"
        )
        settings_btn.pack(side="left", padx=(0, 10))
        
        # Theme toggle
        self.theme_btn = ModernButton(
            controls_frame,
            text="☀️",  # Force light theme icon
            command=self.toggle_theme,
            style="primary"
        )
        self.theme_btn.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_btn = ModernButton(
            controls_frame,
            text="Refresh",
            icon=ModernIcons.REFRESH,
            command=self.refresh_all_data,
            style="primary"
        )
        self.refresh_btn.pack(side="left")
    
    def create_account_panel(self, parent):
        """Create modern account management panel"""
        # Left panel container
        left_panel = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # Account cards
        self.master_card = AccountCard(
            left_panel,
            account_name="Master Account",
            account_type="MASTER"
        )
        self.master_card.pack(fill="x", pady=(0, 10))
        self.master_card.on_login = lambda: self.login_account(1)
        self.master_card.on_status = lambda: self.show_order_details(1)
        self.master_card.on_mtm = lambda: self.update_mtm(1)
        
        self.child_card = AccountCard(
            left_panel,
            account_name="Child Account",
            account_type="CHILD"
        )
        self.child_card.pack(fill="x")
        self.child_card.on_login = lambda: self.login_account(2)
        self.child_card.on_status = lambda: self.show_order_details(2)
        self.child_card.on_mtm = lambda: self.update_mtm(2)
    
    def create_trading_panel(self, parent):
        """Create modern trading controls panel"""
        # Center panel container
        center_panel = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        center_panel.pack(side="left", fill="both", expand=True, padx=10)
        
        # Instrument selection card
        self.create_instrument_selection_card(center_panel)
        
        # Trading controls card
        self.create_trading_controls_card(center_panel)
    
    def create_instrument_selection_card(self, parent):
        """Create instrument selection card"""
        selection_card = ModernCard(parent, title="Instrument Selection")
        selection_card.pack(fill="x", pady=(0, 15))
        
        # Selection grid
        grid_frame = tk.Frame(selection_card.content_frame, bg=self.theme.get_theme()["card"])
        grid_frame.pack(fill="x")
        
        # Index selection
        ModernLabel(grid_frame, text="Index:", style="secondary").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.index_dropdown = ModernCombobox(
            grid_frame,
            textvariable=self.selected_index,
            values=["BANKNIFTY", "NIFTY", "SENSEX"],
            width=15
        )
        self.index_dropdown.grid(row=0, column=1, padx=(0, 20), pady=5)
        self.selected_index.trace_add('write', self.update_selections)
        
        # Expiry display
        ModernLabel(grid_frame, text="Expiry:", style="secondary").grid(row=0, column=2, sticky="w", padx=(0, 10), pady=5)
        self.expiry_label = tk.Label(grid_frame, textvariable=self.expiry_value, font=ModernFonts.BODY, fg=self.theme.get_theme()["text"], bg=self.theme.get_theme()["card"])
        self.expiry_label.grid(row=0, column=3, padx=(0, 20), pady=5)
        
        # Strike selection
        ModernLabel(grid_frame, text="Strike:", style="secondary").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        self.strike_dropdown = ModernCombobox(
            grid_frame,
            textvariable=self.selected_strike,
            width=15
        )
        self.strike_dropdown.grid(row=1, column=1, padx=(0, 20), pady=5)
        
        # Option type
        ModernLabel(grid_frame, text="Option:", style="secondary").grid(row=1, column=2, sticky="w", padx=(0, 10), pady=5)
        self.option_dropdown = ModernCombobox(
            grid_frame,
            textvariable=self.selected_option,
            values=["CE", "PE"],
            width=8
        )
        self.option_dropdown.grid(row=1, column=3, padx=(0, 20), pady=5)
        self.selected_option.trace_add('write', self.concatenate_values)
        
        # Refresh strikes button
        self.refresh_strikes_btn = ModernButton(
            grid_frame,
            text="Refresh Strikes",
            icon=ModernIcons.REFRESH,
            command=self.refresh_strikes,
            style="primary"
        )
        self.refresh_strikes_btn.grid(row=1, column=4, padx=(10, 0), pady=5)
    
    def create_trading_controls_card(self, parent):
        """Create trading controls card"""
        trading_card = ModernCard(parent, title="Trading Controls")
        trading_card.pack(fill="x", pady=(0, 15))
        
        # Trading controls grid
        controls_frame = tk.Frame(trading_card.content_frame, bg=self.theme.get_theme()["card"])
        controls_frame.pack(fill="x")
        
        # Price section
        price_frame = tk.Frame(controls_frame, bg=self.theme.get_theme()["card"])
        price_frame.pack(fill="x", pady=(0, 15))
        
        # Fetch price button
        self.fetch_btn = ModernButton(
            price_frame,
            text="Fetch Price",
            icon=ModernIcons.PRICE,
            command=self.fetch_price,
            style="primary"
        )
        self.fetch_btn.pack(side="left", padx=(0, 15))
        
        # Price input
        ModernLabel(price_frame, text="Price:", style="secondary").pack(side="left", padx=(0, 5))
        self.price_entry = ModernEntry(
            price_frame,
            textvariable=self.price_value,
            width=12
        )
        self.price_entry.pack(side="left", padx=(0, 15))
        
        # Quantity selection
        ModernLabel(price_frame, text="Quantity:", style="secondary").pack(side="left", padx=(0, 5))
        self.qty_dropdown = ModernCombobox(
            price_frame,
            textvariable=self.qty1_var,
            width=10
        )
        self.qty_dropdown.pack(side="left")
        
        # Buy/Sell buttons
        action_frame = tk.Frame(controls_frame, bg=self.theme.get_theme()["card"])
        action_frame.pack(fill="x")
        
        # Buy section
        buy_frame = tk.Frame(action_frame, bg=self.theme.get_theme()["card"])
        buy_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ModernLabel(buy_frame, text="BUY", style="normal").pack()
        self.buy_btn = ModernButton(
            buy_frame,
            text="BUY",
            icon=ModernIcons.BUY,
            command=self.place_buy_orders,
            style="primary"
        )
        self.buy_btn.pack(fill="x", pady=(5, 0))
        
        # Sell section
        sell_frame = tk.Frame(action_frame, bg=self.theme.get_theme()["card"])
        sell_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        ModernLabel(sell_frame, text="SELL", style="normal").pack()
        self.sell_btn = ModernButton(
            sell_frame,
            text="SELL",
            icon=ModernIcons.SELL,
            command=self.place_sell_orders,
            style="primary"
        )
        self.sell_btn.pack(fill="x", pady=(5, 0))
    
    def create_order_panel(self, parent):
        """Create order management panel"""
        # Right panel container
        right_panel = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        
        # Order management card
        order_card = ModernCard(right_panel, title="Order Management")
        order_card.pack(fill="x", pady=(0, 15))
        
        # Cancel orders section
        cancel_frame = tk.Frame(order_card.content_frame, bg=self.theme.get_theme()["card"])
        cancel_frame.pack(fill="x", pady=(0, 15))
        
        ModernLabel(cancel_frame, text="Cancel Orders", style="subtitle").pack(anchor="w")
        
        cancel_buttons_frame = tk.Frame(cancel_frame, bg=self.theme.get_theme()["card"])
        cancel_buttons_frame.pack(fill="x", pady=(10, 0))
        
        self.cancel_buy_btn = ModernButton(
            cancel_buttons_frame,
            text="Cancel Buy",
            icon=ModernIcons.CANCEL,
            command=self.cancel_buy_orders,
            style="primary"
        )
        self.cancel_buy_btn.pack(fill="x", pady=(0, 5))
        
        self.cancel_sell_btn = ModernButton(
            cancel_buttons_frame,
            text="Cancel Sell",
            icon=ModernIcons.CANCEL,
            command=self.cancel_sell_orders,
            style="primary"
        )
        self.cancel_sell_btn.pack(fill="x")
        
        # Modify orders section
        modify_frame = tk.Frame(order_card.content_frame, bg=self.theme.get_theme()["card"])
        modify_frame.pack(fill="x")
        
        ModernLabel(modify_frame, text="Modify Orders", style="subtitle").pack(anchor="w")
        
        # Modify buy
        modify_buy_frame = tk.Frame(modify_frame, bg=self.theme.get_theme()["card"])
        modify_buy_frame.pack(fill="x", pady=(10, 5))
        
        self.modify_buy_btn = ModernButton(
            modify_buy_frame,
            text="Modify Buy",
            icon=ModernIcons.MODIFY,
            command=self.modify_buy_orders,
            style="primary"
        )
        self.modify_buy_btn.pack(side="left", padx=(0, 10))
        
        self.modify_buy_entry = ModernEntry(
            modify_buy_frame,
            textvariable=self.modify_buy_value,
            placeholder="New Price",
            width=10
        )
        self.modify_buy_entry.pack(side="left")
        
        # Modify sell
        modify_sell_frame = tk.Frame(modify_frame, bg=self.theme.get_theme()["card"])
        modify_sell_frame.pack(fill="x", pady=(5, 0))
        
        self.modify_sell_btn = ModernButton(
            modify_sell_frame,
            text="Modify Sell",
            icon=ModernIcons.MODIFY,
            command=self.modify_sell_orders,
            style="primary"
        )
        self.modify_sell_btn.pack(side="left", padx=(0, 10))
        
        self.modify_sell_entry = ModernEntry(
            modify_sell_frame,
            textvariable=self.modify_sell_value,
            placeholder="New Price",
            width=10
        )
        self.modify_sell_entry.pack(side="left")
    
    def create_status_panel(self, parent):
        """Create status and logs panel"""
        status_card = ModernCard(parent, title="System Status")
        status_card.pack(fill="x", pady=(20, 0))
        
        # Status indicators
        status_frame = tk.Frame(status_card.content_frame, bg=self.theme.get_theme()["card"])
        status_frame.pack(fill="x")
        
        # Connection status
        self.connection_status = StatusIndicator(status_frame, status="inactive")
        self.connection_status.pack(side="left", padx=(0, 20))
        
        # Market status
        self.market_status = StatusIndicator(status_frame, status="inactive")
        self.market_status.pack(side="left", padx=(0, 20))
        
        # Order status
        self.order_status = StatusIndicator(status_frame, status="inactive")
        self.order_status.pack(side="left")
        
        # Progress bar for operations
        self.progress_bar = ProgressBar(status_card.content_frame)
        self.progress_bar.pack(fill="x", pady=(10, 0))
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        if self.theme.current_theme == "dark":
            self.theme.set_theme("light")
            self.theme_btn.configure(text="☀️")
        else:
            self.theme.set_theme("dark")
            self.theme_btn.configure(text="🌙")
        
        # Reconfigure styles
        self.theme.configure_styles(self.root)
        # Note: In a full implementation, you'd need to update all widgets
    
    def refresh_all_data(self):
        """Refresh all data and connections"""
        try:
            self.progress_bar.set_progress(25)
            self.connection_status.update_status("loading")
            
            # Refresh strikes
            self.refresh_strikes()
            
            self.progress_bar.set_progress(50)
            
            # Refresh account status
            self.update_account_status()
            
            self.progress_bar.set_progress(75)
            
            # Refresh market data
            self.fetch_price()
            
            self.progress_bar.set_progress(100)
            self.connection_status.update_status("active")
            
        except Exception as e:
            self.connection_status.update_status("error")
            messagebox.showerror("Error", f"Error refreshing data: {e}")
    
    def update_account_status(self):
        """Update account status indicators"""
        # Update master account status
        if self.account_manager.get_api(1):
            self.master_card.update_status("active")
        else:
            self.master_card.update_status("inactive")
        
        # Update child account status
        if self.account_manager.get_api(2):
            self.child_card.update_status("active")
        else:
            self.child_card.update_status("inactive")
    
    def open_settings(self):
        """Open settings window"""
        settings_window = SettingsWindow(
            self.root,
            on_theme_change=self.on_theme_change
        )
    
    def on_theme_change(self, new_theme: str):
        """Handle theme change from settings"""
        self.theme.set_theme(new_theme)
        self.theme.configure_styles(self.root)
        self.theme_btn.configure(text="🌙" if new_theme == "dark" else "☀️")
    
    
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
                self.update_account_status()
                messagebox.showinfo("Success", f"Logged in to account {account_num}: {client_name}")
            else:
                messagebox.showerror("Error", f"Login failed: {client_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error logging in: {e}")
    
    def update_account_display(self, account_num: int, client_name: str):
        """Update account display"""
        if account_num == 1:
            self.master_card.update_name(client_name)
            self.master1_value.set(client_name)
        elif account_num == 2:
            self.child_card.update_name(client_name)
            self.child2_value.set(client_name)
    
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
        """Create modern order details window"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Order Details")
        details_window.geometry("1400x500")
        details_window.configure(bg=self.theme.get_theme()["primary"])
        
        # Header
        header_frame = tk.Frame(details_window, bg=self.theme.get_theme()["primary"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ModernLabel(
            header_frame,
            text=f"{ModernIcons.ORDER} Order Details",
            style="title"
        )
        title_label.pack(side="left")
        
        close_btn = ModernButton(
            header_frame,
            text="Close",
            command=details_window.destroy,
            style="primary"
        )
        close_btn.pack(side="right")
        
        # Create scrollable frame
        canvas = tk.Canvas(details_window, bg=self.theme.get_theme()["primary"])
        scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.get_theme()["card"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", pady=(0, 20))
        
        # Headers
        headers = ["Symbol", "Order No", "Price", "Qty", "Status", "Type", "Order Type",
                  "Filled", "Avg Price", "User ID", "Reject Reason"]
        
        header_frame = tk.Frame(scrollable_frame, bg=self.theme.get_theme()["accent"])
        header_frame.pack(fill="x", pady=(0, 10))
        
        for col, header in enumerate(headers):
            header_label = ModernLabel(
                header_frame, 
                text=header, 
                style="normal"
            )
            header_label.configure(
                bg=self.theme.get_theme()["accent"],
                fg="white",
                font=ModernFonts.BODY_BOLD
            )
            header_label.grid(row=0, column=col, padx=10, pady=10, sticky='w')
        
        # Order data
        for row_idx, order in enumerate(orders, start=1):
            row_frame = tk.Frame(scrollable_frame, bg=self.theme.get_theme()["card"])
            row_frame.pack(fill="x", pady=2)
            
            # Alternate row colors
            if row_idx % 2 == 0:
                row_frame.configure(bg=self.theme.get_theme()["secondary"])
            
            for col_idx, key in enumerate(headers):
                # Map display headers to order keys
                key_mapping = {
                    "Symbol": "tsym",
                    "Order No": "norenordno", 
                    "Price": "prc",
                    "Qty": "qty",
                    "Status": "status",
                    "Type": "trantype",
                    "Order Type": "prctyp",
                    "Filled": "fillshares",
                    "Avg Price": "avgprc",
                    "User ID": "uid",
                    "Reject Reason": "rejreason"
                }
                
                value = order.get(key_mapping[key], "")
                
                # All status use the same grey theme
                style = "normal"
                
                label = ModernLabel(
                    row_frame, 
                    text=str(value), 
                    style=style
                )
                label.configure(bg=row_frame.cget("bg"))
                label.grid(row=0, column=col_idx, padx=10, pady=5, sticky='w')
    
    def release_buttons(self):
        """Release button states"""
        # Modern buttons don't need this functionality
        pass
    
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

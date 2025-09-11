"""
Modern PyQt6 Trading Application with Live Price Updates
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget, QSplitter, QFrame, QGridLayout, QGroupBox, QScrollArea, QTextEdit
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve, QRect, QObject
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QLinearGradient
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
import qdarkstyle
from datetime import datetime
import json
import threading

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.account_manager import AccountManager
from trading.order_manager import OrderManager
from trading.websocket_manager import WebSocketManager
from trading.position_manager import PositionManager
from market_data.symbol_manager import SymbolManager
from market_data.expiry_manager import ExpiryManager
from logger import applicationLogger

class WebSocketPriceHandler(QObject):
    """Handles WebSocket price updates for PyQt6"""
    
    price_updated = pyqtSignal(str, float)  # symbol, price
    quote_updated = pyqtSignal(dict)  # full quote data
    
    def __init__(self):
        super().__init__()
        self.subscribed_symbols = {}
        self.current_prices = {}
    
    def handle_quote_update(self, tick_data):
        """Handle quote updates from WebSocket"""
        try:
            # Debug: Log all tick data received
            applicationLogger.info(f"🔍 WebSocket Tick Data Received: {tick_data}")
            applicationLogger.info(f"🔍 Tick Data Type: {type(tick_data)}")
            applicationLogger.info(f"🔍 Tick Data Keys: {list(tick_data.keys()) if isinstance(tick_data, dict) else 'Not a dict'}")
            
            if isinstance(tick_data, dict):
                # Log specific fields
                applicationLogger.info(f"🔍 Message Type (t): {tick_data.get('t', 'Not found')}")
                applicationLogger.info(f"🔍 Symbol (tsym): {tick_data.get('tsym', 'Not found')}")
                applicationLogger.info(f"🔍 Last Price (lp): {tick_data.get('lp', 'Not found')}")
                applicationLogger.info(f"🔍 Exchange (e): {tick_data.get('e', 'Not found')}")
                applicationLogger.info(f"🔍 Token (tk): {tick_data.get('tk', 'Not found')}")
                
                if 'lp' in tick_data:  # Last price
                    symbol = tick_data.get('tsym', 'Unknown')
                    price = float(tick_data.get('lp', 0))
                    
                    applicationLogger.info(f"✅ Processing price update: {symbol} = {price}")
                    
                    self.current_prices[symbol] = price
                    self.price_updated.emit(symbol, price)
                    self.quote_updated.emit(tick_data)
                    
                    applicationLogger.info(f"✅ Price update emitted: {symbol} = {price}")
                else:
                    applicationLogger.warning(f"⚠️ No 'lp' field in tick data: {tick_data}")
            else:
                applicationLogger.warning(f"⚠️ Tick data is not a dictionary: {tick_data}")
                
        except Exception as e:
            applicationLogger.error(f"❌ Error handling quote update: {e}")
            import traceback
            applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")

class ModernTradingApp(QMainWindow):
    """Modern PyQt6 Trading Application with Live Price Updates"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shoonya Master-Child Trading System - Live Prices")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 800)
        
        # Initialize managers
        self.account_manager = AccountManager()
        self.order_manager = OrderManager()
        self.websocket_manager = WebSocketManager(self.account_manager, self.order_manager, self)
        self.position_manager = PositionManager()
        self.symbol_manager = SymbolManager()
        self.expiry_manager = ExpiryManager()
        
        # Initialize WebSocket price handler
        self.price_handler = WebSocketPriceHandler()
        self.price_handler.price_updated.connect(self.update_live_price)
        self.price_handler.quote_updated.connect(self.update_quote_display)
        
        # Current trading symbol and subscription
        self.current_symbol = None
        self.current_token = None
        self.current_exchange = None
        self.is_subscribed = False
        
        # Initialize UI
        self.init_ui()
        self.apply_modern_theme()
        
        # Initialize with master account
        self.initialize_master_account()
        
        # Setup price update timer
        self.price_timer = QTimer()
        self.price_timer.timeout.connect(self.refresh_price_display)
        self.price_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Account Management
        self.create_account_panel(splitter)
        
        # Center panel - Trading Controls
        self.create_trading_panel(splitter)
        
        # Right panel - Order Management
        self.create_order_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([300, 600, 300])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
    
    def create_account_panel(self, parent):
        """Create account management panel"""
        account_widget = QWidget()
        account_layout = QVBoxLayout(account_widget)
        account_layout.setSpacing(10)
        
        # Master Account Card
        master_card = self.create_account_card("MASTER", "Master Account", "👑")
        account_layout.addWidget(master_card)
        
        # Child Account Card
        child_card = self.create_account_card("CHILD", "Child Account", "👶")
        account_layout.addWidget(child_card)
        
        parent.addWidget(account_widget)
    
    def create_account_card(self, account_type, account_name, icon):
        """Create account card widget"""
        card = QGroupBox(f"{icon} {account_type} Account")
        card.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Account name
        name_label = QLabel(account_name)
        name_label.setFont(QFont("Segoe UI", 10))
        name_label.setStyleSheet("color: #666666; margin-left: 10px;")
        layout.addWidget(name_label)
        
        # Status indicator
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 0, 10, 0)
        
        status_indicator = QLabel("●")
        status_indicator.setStyleSheet("color: #ff6b6b; font-size: 16px;")
        status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_label = QLabel("INACTIVE")
        status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status_label.setStyleSheet("color: #ff6b6b;")
        
        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_frame)
        
        # Account input
        account_input = QLineEdit()
        account_input.setPlaceholderText("Account details...")
        account_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(account_input)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet(self.get_button_style())
        login_btn.clicked.connect(lambda: self.login_account(1 if account_type == "MASTER" else 2))
        
        status_btn = QPushButton("Status")
        status_btn.setStyleSheet(self.get_button_style())
        status_btn.clicked.connect(lambda: self.show_order_details(1 if account_type == "MASTER" else 2))
        
        mtm_btn = QPushButton("MTM")
        mtm_btn.setStyleSheet(self.get_button_style())
        mtm_btn.clicked.connect(lambda: self.update_mtm(1 if account_type == "MASTER" else 2))
        
        button_layout.addWidget(login_btn)
        button_layout.addWidget(status_btn)
        button_layout.addWidget(mtm_btn)
        
        layout.addLayout(button_layout)
        
        return card
    
    def create_trading_panel(self, parent):
        """Create trading controls panel"""
        trading_widget = QWidget()
        trading_layout = QVBoxLayout(trading_widget)
        trading_layout.setSpacing(15)
        
        # Instrument Selection Card
        instrument_card = self.create_instrument_selection_card()
        trading_layout.addWidget(instrument_card)
        
        # Trading Controls Card
        trading_card = self.create_trading_controls_card()
        trading_layout.addWidget(trading_card)
        
        # Price Chart Card
        chart_card = self.create_price_chart_card()
        trading_layout.addWidget(chart_card)
        
        parent.addWidget(trading_widget)
    
    def create_instrument_selection_card(self):
        """Create instrument selection card"""
        card = QGroupBox("Instrument Selection")
        card.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        card.setStyleSheet(self.get_card_style())
        
        layout = QGridLayout(card)
        layout.setSpacing(10)
        
        # Index selection
        layout.addWidget(QLabel("Index:"), 0, 0)
        self.index_combo = QComboBox()
        self.index_combo.addItems(["BANKNIFTY", "NIFTY", "SENSEX"])
        self.index_combo.setStyleSheet(self.get_combo_style())
        self.index_combo.currentTextChanged.connect(self.update_selections)
        layout.addWidget(self.index_combo, 0, 1)
        
        # Expiry display
        layout.addWidget(QLabel("Expiry:"), 0, 2)
        self.expiry_label = QLabel("--")
        self.expiry_label.setStyleSheet("color: #666666; font-weight: bold;")
        layout.addWidget(self.expiry_label, 0, 3)
        
        # Strike selection
        layout.addWidget(QLabel("Strike:"), 1, 0)
        self.strike_combo = QComboBox()
        self.strike_combo.setStyleSheet(self.get_combo_style())
        layout.addWidget(self.strike_combo, 1, 1)
        
        # Option type
        layout.addWidget(QLabel("Option:"), 1, 2)
        self.option_combo = QComboBox()
        self.option_combo.addItems(["CE", "PE"])
        self.option_combo.setStyleSheet(self.get_combo_style())
        self.option_combo.currentTextChanged.connect(self.concatenate_values)
        layout.addWidget(self.option_combo, 1, 3)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Strikes")
        refresh_btn.setStyleSheet(self.get_button_style())
        refresh_btn.clicked.connect(self.refresh_strikes)
        layout.addWidget(refresh_btn, 1, 4)
        
        return card
    
    def create_trading_controls_card(self):
        """Create trading controls card with live price updates"""
        card = QGroupBox("Trading Controls")
        card.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        card.setStyleSheet(self.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Live Price Display Section
        live_price_group = QGroupBox("Live Price")
        live_price_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        live_price_layout = QVBoxLayout(live_price_group)
        
        # Current symbol display
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbol:"))
        self.current_symbol_label = QLabel("No symbol selected")
        self.current_symbol_label.setStyleSheet("font-weight: bold; color: #007bff;")
        symbol_layout.addWidget(self.current_symbol_label)
        symbol_layout.addStretch()
        
        # Live price display
        price_display_layout = QHBoxLayout()
        price_display_layout.addWidget(QLabel("Live Price:"))
        self.live_price_label = QLabel("0.00")
        self.live_price_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #28a745; 
            background-color: #f8f9fa; 
            padding: 8px; 
            border: 2px solid #e0e0e0; 
            border-radius: 5px;
        """)
        price_display_layout.addWidget(self.live_price_label)
        
        # Subscription status
        self.subscription_status = QLabel("● Not Subscribed")
        self.subscription_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        price_display_layout.addWidget(self.subscription_status)
        
        live_price_layout.addLayout(symbol_layout)
        live_price_layout.addLayout(price_display_layout)
        layout.addWidget(live_price_group)
        
        # Price section
        price_layout = QHBoxLayout()
        price_layout.setSpacing(10)
        
        fetch_btn = QPushButton("Fetch Price")
        fetch_btn.setStyleSheet(self.get_button_style())
        fetch_btn.clicked.connect(self.fetch_price)
        price_layout.addWidget(fetch_btn)
        
        subscribe_btn = QPushButton("Subscribe Live")
        subscribe_btn.setStyleSheet(self.get_info_button_style())
        subscribe_btn.clicked.connect(self.toggle_subscription)
        price_layout.addWidget(subscribe_btn)
        
        price_layout.addWidget(QLabel("Price:"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("0.00")
        self.price_input.setStyleSheet(self.get_input_style())
        price_layout.addWidget(self.price_input)
        
        price_layout.addWidget(QLabel("Quantity:"))
        self.qty_combo = QComboBox()
        self.qty_combo.setStyleSheet(self.get_combo_style())
        price_layout.addWidget(self.qty_combo)
        
        price_layout.addStretch()
        layout.addLayout(price_layout)
        
        # Buy/Sell buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        
        buy_btn = QPushButton("BUY")
        buy_btn.setStyleSheet(self.get_buy_button_style())
        buy_btn.clicked.connect(self.place_buy_orders)
        action_layout.addWidget(buy_btn)
        
        sell_btn = QPushButton("SELL")
        sell_btn.setStyleSheet(self.get_sell_button_style())
        sell_btn.clicked.connect(self.place_sell_orders)
        action_layout.addWidget(sell_btn)
        
        layout.addLayout(action_layout)
        
        return card
    
    def create_price_chart_card(self):
        """Create price chart card with real-time updates"""
        card = QGroupBox("Live Market Data")
        card.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        card.setStyleSheet(self.get_card_style())
        
        layout = QVBoxLayout(card)
        
        # Real-time price display
        price_display_group = QGroupBox("Real-time Price Updates")
        price_display_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        price_display_layout = QVBoxLayout(price_display_group)
        
        # Price history display
        self.price_history_text = QTextEdit()
        self.price_history_text.setMaximumHeight(200)
        self.price_history_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.price_history_text.setPlaceholderText("Price updates will appear here...")
        price_display_layout.addWidget(self.price_history_text)
        
        # Market data summary
        market_summary_layout = QHBoxLayout()
        
        self.market_summary_label = QLabel("Market Status: Ready")
        self.market_summary_label.setStyleSheet("color: #6c757d; font-weight: bold;")
        market_summary_layout.addWidget(self.market_summary_label)
        
        market_summary_layout.addStretch()
        
        self.last_update_label = QLabel("Last Update: --")
        self.last_update_label.setStyleSheet("color: #6c757d; font-size: 10px;")
        market_summary_layout.addWidget(self.last_update_label)
        
        price_display_layout.addLayout(market_summary_layout)
        layout.addWidget(price_display_group)
        
        # Chart placeholder
        chart_label = QLabel("Price Chart\n(Advanced charting will be added here)")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 30px;
                color: #666666;
                font-size: 14px;
            }
        """)
        layout.addWidget(chart_label)
        
        return card
    
    def create_order_panel(self, parent):
        """Create order management panel"""
        order_widget = QWidget()
        order_layout = QVBoxLayout(order_widget)
        order_layout.setSpacing(15)
        
        # Order Management Card
        order_card = QGroupBox("Order Management")
        order_card.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        order_card.setStyleSheet(self.get_card_style())
        
        order_layout_main = QVBoxLayout(order_card)
        order_layout_main.setSpacing(15)
        
        # Cancel Orders Section
        cancel_group = QGroupBox("Cancel Orders")
        cancel_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        cancel_layout = QVBoxLayout(cancel_group)
        
        cancel_buy_btn = QPushButton("Cancel Buy")
        cancel_buy_btn.setStyleSheet(self.get_warning_button_style())
        cancel_buy_btn.clicked.connect(self.cancel_buy_orders)
        cancel_layout.addWidget(cancel_buy_btn)
        
        cancel_sell_btn = QPushButton("Cancel Sell")
        cancel_sell_btn.setStyleSheet(self.get_warning_button_style())
        cancel_sell_btn.clicked.connect(self.cancel_sell_orders)
        cancel_layout.addWidget(cancel_sell_btn)
        
        order_layout_main.addWidget(cancel_group)
        
        # Modify Orders Section
        modify_group = QGroupBox("Modify Orders")
        modify_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        modify_layout = QVBoxLayout(modify_group)
        
        # Modify Buy
        modify_buy_layout = QHBoxLayout()
        modify_buy_btn = QPushButton("Modify Buy")
        modify_buy_btn.setStyleSheet(self.get_button_style())
        modify_buy_btn.clicked.connect(self.modify_buy_orders)
        modify_buy_layout.addWidget(modify_buy_btn)
        
        self.modify_buy_input = QLineEdit()
        self.modify_buy_input.setPlaceholderText("New Price")
        self.modify_buy_input.setStyleSheet(self.get_input_style())
        modify_buy_layout.addWidget(self.modify_buy_input)
        
        modify_layout.addLayout(modify_buy_layout)
        
        # Modify Sell
        modify_sell_layout = QHBoxLayout()
        modify_sell_btn = QPushButton("Modify Sell")
        modify_sell_btn.setStyleSheet(self.get_button_style())
        modify_sell_btn.clicked.connect(self.modify_sell_orders)
        modify_sell_layout.addWidget(modify_sell_btn)
        
        self.modify_sell_input = QLineEdit()
        self.modify_sell_input.setPlaceholderText("New Price")
        self.modify_sell_input.setStyleSheet(self.get_input_style())
        modify_sell_layout.addWidget(self.modify_sell_input)
        
        modify_layout.addLayout(modify_sell_layout)
        
        order_layout_main.addWidget(modify_group)
        
        # Orders Table
        orders_group = QGroupBox("Active Orders")
        orders_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        orders_layout = QVBoxLayout(orders_group)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels(["Symbol", "Type", "Price", "Qty", "Status", "Time"])
        self.orders_table.setStyleSheet(self.get_table_style())
        orders_layout.addWidget(self.orders_table)
        
        order_layout_main.addWidget(orders_group)
        
        order_layout.addWidget(order_card)
        parent.addWidget(order_widget)
    
    def apply_modern_theme(self):
        """Apply modern theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                background-color: #f5f5f5;
                color: #333333;
            }
        """)
    
    def get_card_style(self):
        """Get card styling"""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
    
    def get_button_style(self):
        """Get button styling"""
        return """
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """
    
    def get_buy_button_style(self):
        """Get buy button styling"""
        return """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """
    
    def get_sell_button_style(self):
        """Get sell button styling"""
        return """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """
    
    def get_warning_button_style(self):
        """Get warning button styling"""
        return """
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
        """
    
    def get_info_button_style(self):
        """Get info button styling"""
        return """
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """
    
    def get_input_style(self):
        """Get input field styling"""
        return """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
        """
    
    def get_combo_style(self):
        """Get combo box styling"""
        return """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
            }
        """
    
    def get_table_style(self):
        """Get table styling"""
        return """
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """
    
    def initialize_master_account(self):
        """Initialize master account on startup"""
        try:
            success, client_name = self.account_manager.login_account(1)
            if success:
                # Setup WebSocket with custom quote callback
                self.setup_websocket_with_price_updates(1)
                applicationLogger.info("Master account initialized successfully")
            else:
                applicationLogger.error(f"Failed to initialize master account: {client_name}")
        except Exception as e:
            applicationLogger.error(f"Error initializing master account: {e}")
    
    def setup_websocket_with_price_updates(self, account_num):
        """Setup WebSocket with price update callbacks"""
        try:
            applicationLogger.info(f"🔧 Setting up WebSocket for account {account_num}")
            
            api = self.account_manager.get_api(account_num)
            if not api:
                applicationLogger.error(f"❌ No API available for account {account_num}")
                return False
            
            applicationLogger.info(f"✅ API found for account {account_num}")
            
            # Custom callbacks that include price updates
            def order_update_callback(tick_data):
                """Handle order updates"""
                applicationLogger.info(f"📋 Order update received: {tick_data}")
            
            def quote_update_callback(tick_data):
                """Handle quote updates with price display"""
                applicationLogger.info(f"📊 Quote update received: {tick_data}")
                applicationLogger.info(f"📊 Quote update type: {type(tick_data)}")
                # Handle price updates for PyQt6
                self.price_handler.handle_quote_update(tick_data)
            
            def socket_open_callback():
                """Handle socket open"""
                applicationLogger.info(f"🔌 WebSocket is now open for Account {account_num}")
                if hasattr(self, 'market_summary_label'):
                    self.market_summary_label.setText("Market Status: Connected")
                    self.market_summary_label.setStyleSheet("color: #28a745; font-weight: bold;")
            
            applicationLogger.info(f"🔧 Starting WebSocket with callbacks for account {account_num}")
            
            # Start WebSocket with custom callbacks
            api.start_websocket(
                order_update_callback=order_update_callback,
                subscribe_callback=quote_update_callback,
                socket_open_callback=socket_open_callback
            )
            
            applicationLogger.info(f"✅ WebSocket started successfully for account {account_num}")
            return True
            
        except Exception as e:
            applicationLogger.error(f"❌ Error setting up WebSocket with price updates: {e}")
            import traceback
            applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def login_account(self, account_num):
        """Login to a specific account"""
        try:
            success, client_name = self.account_manager.login_account(account_num)
            if success:
                # Setup WebSocket with price updates
                self.setup_websocket_with_price_updates(account_num)
                applicationLogger.info(f"Logged in to account {account_num}: {client_name}")
            else:
                applicationLogger.error(f"Login failed: {client_name}")
        except Exception as e:
            applicationLogger.error(f"Error logging in: {e}")
    
    def update_selections(self):
        """Update selections based on index"""
        index = self.index_combo.currentText()
        if index in ["NIFTY", "BANKNIFTY", "SENSEX"]:
            # Update expiry
            expiry = self.expiry_manager.get_expiry_date(index)
            self.expiry_label.setText(expiry)
            
            # Update strikes
            try:
                api = self.account_manager.get_api(1)
                if api:
                    current_price = self.symbol_manager.get_index_price(api, index)
                    if current_price:
                        strikes = self.expiry_manager.get_strike_list(index, current_price)
                        self.strike_combo.clear()
                        self.strike_combo.addItems([str(s) for s in strikes])
                    else:
                        # Fallback to default strikes
                        default_prices = {"NIFTY": 24000, "BANKNIFTY": 52000, "SENSEX": 81000}
                        strikes = self.expiry_manager.get_strike_list(index, default_prices.get(index, 20000))
                        self.strike_combo.clear()
                        self.strike_combo.addItems([str(s) for s in strikes])
            except Exception as e:
                applicationLogger.error(f"Error updating strikes for {index}: {e}")
            
            # Update quantity list
            quantities = self.expiry_manager.get_quantity_list(index)
            self.qty_combo.clear()
            self.qty_combo.addItems([str(q) for q in quantities])
    
    def concatenate_values(self):
        """Concatenate selected values to create trading symbol"""
        index = self.index_combo.currentText()
        expiry = self.expiry_label.text()
        strike = self.strike_combo.currentText()
        option = self.option_combo.currentText()
        
        applicationLogger.info(f"🔗 Concatenate values - Index: {index}, Expiry: {expiry}, Strike: {strike}, Option: {option}")
        
        if all([index, expiry, strike, option]):
            if index == "SENSEX":
                trading_symbol = self._generate_sensex_symbol(expiry, strike, option)
                applicationLogger.info(f"🔗 Generated SENSEX symbol: {trading_symbol}")
            else:
                trading_symbol = f"{index}{expiry}{option}{strike}"
                applicationLogger.info(f"🔗 Generated symbol: {trading_symbol}")
            return trading_symbol
        else:
            applicationLogger.warning(f"⚠️ Missing values for symbol generation - Index: {index}, Expiry: {expiry}, Strike: {strike}, Option: {option}")
        return ""
    
    def _generate_sensex_symbol(self, expiry, strike, option):
        """Generate SENSEX symbol"""
        try:
            if len(expiry) == 7:  # Daily expiry like "11SEP25"
                day = expiry[:2]
                month = expiry[2:5]
                year = expiry[5:]
                
                month_num = datetime.strptime(month, '%b').month
                year_full = 2000 + int(year)
                day_num = int(day)
                
                # Check if it's the last Friday of the month
                import calendar
                last_day = calendar.monthrange(year_full, month_num)[1]
                last_friday = self._get_last_friday(year_full, month_num)
                
                if day_num == last_friday.day:
                    return f"SENSEX{year}{month}{strike}{option}"
                else:
                    return f"SENSEX{year}{month_num:d}{day_num:02d}{strike}{option}"
            else:
                return f"SENSEX{expiry}{strike}{option}"
        except Exception as e:
            applicationLogger.error(f"Error generating SENSEX symbol: {e}")
            return f"SENSEX{expiry}{strike}{option}"
    
    def _get_last_friday(self, year, month):
        """Get the last Friday of the month"""
        import calendar
        from datetime import timedelta
        
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        days_back = (last_date.weekday() - 4) % 7
        if days_back == 0 and last_date.weekday() != 4:
            days_back = 7
        last_friday = last_date - timedelta(days=days_back)
        
        return last_friday
    
    def fetch_price(self):
        """Fetch current price for selected symbol"""
        try:
            applicationLogger.info(f"💰 Fetch price called")
            
            trading_symbol = self.concatenate_values()
            applicationLogger.info(f"💰 Trading symbol: {trading_symbol}")
            
            if not trading_symbol:
                applicationLogger.warning("⚠️ No trading symbol generated")
                return
            
            api = self.account_manager.get_api(1)
            if not api:
                applicationLogger.error("❌ No API available for price fetch")
                return
            
            applicationLogger.info(f"💰 API found, fetching price for {trading_symbol}")
            price = self.symbol_manager.get_latest_price(api, trading_symbol)
            applicationLogger.info(f"💰 Price fetched: {price}")
            
            if price:
                self.price_input.setText(str(price))
                self.live_price_label.setText(f"{price:.2f}")
                self.current_symbol_label.setText(trading_symbol)
                
                # Update current symbol info for subscription
                self.current_symbol = trading_symbol
                self.current_token = self.symbol_manager.get_token(trading_symbol)
                self.current_exchange = 'BFO' if 'SENSEX' in trading_symbol else 'NFO'
                
                applicationLogger.info(f"✅ Fetched price for {trading_symbol}: {price}")
                applicationLogger.info(f"✅ Current symbol: {self.current_symbol}")
                applicationLogger.info(f"✅ Current token: {self.current_token}")
                applicationLogger.info(f"✅ Current exchange: {self.current_exchange}")
            else:
                applicationLogger.warning(f"⚠️ No price returned for {trading_symbol}")
        except Exception as e:
            applicationLogger.error(f"❌ Error fetching price: {e}")
            import traceback
            applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    def refresh_strikes(self):
        """Manually refresh strike prices"""
        self.update_selections()
    
    def toggle_subscription(self):
        """Toggle WebSocket subscription for live price updates"""
        try:
            applicationLogger.info(f"🔄 Toggle subscription called")
            applicationLogger.info(f"🔄 Current symbol: {self.current_symbol}")
            applicationLogger.info(f"🔄 Current token: {self.current_token}")
            applicationLogger.info(f"🔄 Current exchange: {self.current_exchange}")
            applicationLogger.info(f"🔄 Is subscribed: {self.is_subscribed}")
            
            if not self.current_symbol or not self.current_token:
                applicationLogger.warning("⚠️ No symbol selected for subscription")
                return
            
            api = self.account_manager.get_api(1)
            if not api:
                applicationLogger.error("❌ No API available for subscription")
                return
            
            if self.is_subscribed:
                # Unsubscribe
                applicationLogger.info(f"🔌 Unsubscribing from {self.current_symbol}")
                success = self.websocket_manager.unsubscribe_from_symbol(
                    api, self.current_exchange, self.current_token
                )
                if success:
                    self.is_subscribed = False
                    self.subscription_status.setText("● Not Subscribed")
                    self.subscription_status.setStyleSheet("color: #dc3545; font-weight: bold;")
                    applicationLogger.info(f"✅ Unsubscribed from {self.current_symbol}")
                else:
                    applicationLogger.error(f"❌ Failed to unsubscribe from {self.current_symbol}")
            else:
                # Subscribe
                applicationLogger.info(f"🔌 Subscribing to {self.current_symbol}")
                applicationLogger.info(f"🔌 Exchange: {self.current_exchange}, Token: {self.current_token}")
                
                success = self.websocket_manager.subscribe_to_symbol(
                    api, self.current_exchange, self.current_token
                )
                if success:
                    self.is_subscribed = True
                    self.subscription_status.setText("● Subscribed")
                    self.subscription_status.setStyleSheet("color: #28a745; font-weight: bold;")
                    applicationLogger.info(f"✅ Subscribed to {self.current_symbol}")
                    
                    # Setup WebSocket callback for this symbol
                    self.setup_websocket_price_callback()
                else:
                    applicationLogger.error(f"❌ Failed to subscribe to {self.current_symbol}")
        except Exception as e:
            applicationLogger.error(f"❌ Error toggling subscription: {e}")
            import traceback
            applicationLogger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    def setup_websocket_price_callback(self):
        """Setup WebSocket callback for price updates"""
        try:
            # Get the API and setup custom quote callback
            api = self.account_manager.get_api(1)
            if api:
                # Store the original quote callback
                original_quote_callback = getattr(api, '_original_quote_callback', None)
                
                def custom_quote_callback(tick_data):
                    """Custom quote callback for price updates"""
                    # Call original callback if it exists
                    if original_quote_callback:
                        original_quote_callback(tick_data)
                    
                    # Handle price updates
                    self.price_handler.handle_quote_update(tick_data)
                
                # Set the custom callback
                api.subscribe_callback = custom_quote_callback
                applicationLogger.info("WebSocket price callback setup completed")
        except Exception as e:
            applicationLogger.error(f"Error setting up WebSocket callback: {e}")
    
    def update_live_price(self, symbol, price):
        """Update live price display"""
        try:
            if symbol == self.current_symbol:
                self.live_price_label.setText(f"{price:.2f}")
                self.price_input.setText(f"{price:.2f}")
                
                # Update price color based on change
                current_price = float(price)
                if hasattr(self, 'last_price') and self.last_price:
                    if current_price > self.last_price:
                        self.live_price_label.setStyleSheet("""
                            font-size: 18px; 
                            font-weight: bold; 
                            color: #28a745; 
                            background-color: #d4edda; 
                            padding: 8px; 
                            border: 2px solid #28a745; 
                            border-radius: 5px;
                        """)
                    elif current_price < self.last_price:
                        self.live_price_label.setStyleSheet("""
                            font-size: 18px; 
                            font-weight: bold; 
                            color: #dc3545; 
                            background-color: #f8d7da; 
                            padding: 8px; 
                            border: 2px solid #dc3545; 
                            border-radius: 5px;
                        """)
                else:
                    self.live_price_label.setStyleSheet("""
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #28a745; 
                        background-color: #f8f9fa; 
                        padding: 8px; 
                        border: 2px solid #e0e0e0; 
                        border-radius: 5px;
                    """)
                
                # Update price history
                self.update_price_history(symbol, price)
                
                self.last_price = current_price
        except Exception as e:
            applicationLogger.error(f"Error updating live price: {e}")
    
    def update_price_history(self, symbol, price):
        """Update price history display"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            price_change = ""
            
            if hasattr(self, 'last_price') and self.last_price:
                change = price - self.last_price
                if change > 0:
                    price_change = f" (+{change:.2f})"
                elif change < 0:
                    price_change = f" ({change:.2f})"
            
            price_entry = f"[{current_time}] {symbol}: {price:.2f}{price_change}\n"
            
            # Add to price history
            self.price_history_text.append(price_entry)
            
            # Keep only last 50 entries
            text = self.price_history_text.toPlainText()
            lines = text.split('\n')
            if len(lines) > 50:
                self.price_history_text.setPlainText('\n'.join(lines[-50:]))
            
            # Scroll to bottom
            cursor = self.price_history_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.price_history_text.setTextCursor(cursor)
            
            # Update last update time
            self.last_update_label.setText(f"Last Update: {current_time}")
            
        except Exception as e:
            applicationLogger.error(f"Error updating price history: {e}")
    
    def update_quote_display(self, quote_data):
        """Update detailed quote display"""
        try:
            # This can be used to show more detailed quote information
            # For now, just log the full quote data
            applicationLogger.info(f"Full quote data: {quote_data}")
        except Exception as e:
            applicationLogger.error(f"Error updating quote display: {e}")
    
    def refresh_price_display(self):
        """Refresh price display periodically"""
        try:
            if self.is_subscribed and self.current_symbol:
                # The WebSocket will handle real-time updates
                # This method can be used for additional periodic updates
                pass
        except Exception as e:
            applicationLogger.error(f"Error refreshing price display: {e}")
    
    def place_buy_orders(self):
        """Place buy orders"""
        # Implementation here
        pass
    
    def place_sell_orders(self):
        """Place sell orders"""
        # Implementation here
        pass
    
    def cancel_buy_orders(self):
        """Cancel buy orders"""
        # Implementation here
        pass
    
    def cancel_sell_orders(self):
        """Cancel sell orders"""
        # Implementation here
        pass
    
    def modify_buy_orders(self):
        """Modify buy orders"""
        # Implementation here
        pass
    
    def modify_sell_orders(self):
        """Modify sell orders"""
        # Implementation here
        pass
    
    def show_order_details(self, account_num):
        """Show order details"""
        # Implementation here
        pass
    
    def update_mtm(self, account_num):
        """Update MTM"""
        # Implementation here
        pass

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Shoonya Trading System")
    app.setApplicationVersion("2.0.0")
    
    # Create and show main window
    window = ModernTradingApp()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

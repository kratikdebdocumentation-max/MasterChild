"""
Modern PyQt6 Components for Trading Application
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QFrame, QProgressBar, QSlider, QCheckBox,
                             QSpinBox, QDoubleSpinBox, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QLinearGradient, QPixmap
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from .themes import ThemeManager
import json

class ModernCard(QGroupBox):
    """Modern card component"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.theme_manager = ThemeManager()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup card UI"""
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.setStyleSheet("""
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

class ModernButton(QPushButton):
    """Modern button component with animations"""
    
    def __init__(self, text="", style="primary", parent=None):
        super().__init__(text, parent)
        self.style = style
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup button UI"""
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.setStyleSheet(self.theme_manager.get_button_style(self.style))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setup_animations(self):
        """Setup button animations"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event):
        """Handle mouse enter"""
        if not self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(QRect(self.x(), self.y() - 2, self.width(), self.height()))
            self.animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        if not self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(QRect(self.x(), self.y() + 2, self.width(), self.height()))
            self.animation.start()
        super().leaveEvent(event)

class ModernInput(QLineEdit):
    """Modern input component"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.placeholder_text = placeholder
        self.setup_ui()
    
    def setup_ui(self):
        """Setup input UI"""
        self.setPlaceholderText(self.placeholder_text)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background-color: #f8f9ff;
            }
            QLineEdit:hover {
                border: 2px solid #007bff;
            }
        """)

class ModernComboBox(QComboBox):
    """Modern combobox component"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup combobox UI"""
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            QComboBox:hover {
                border: 2px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)

class StatusIndicator(QWidget):
    """Modern status indicator component"""
    
    def __init__(self, status="inactive", parent=None):
        super().__init__(parent)
        self.status = status
        self.setup_ui()
    
    def setup_ui(self):
        """Setup status indicator UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Status circle
        self.circle = QLabel("●")
        self.circle.setFont(QFont("Segoe UI", 16))
        self.circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status text
        self.text = QLabel(self.status.upper())
        self.text.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        
        layout.addWidget(self.circle)
        layout.addWidget(self.text)
        layout.addStretch()
        
        self.update_status(self.status)
    
    def update_status(self, status):
        """Update status indicator"""
        self.status = status
        self.text.setText(status.upper())
        
        if status == "active":
            color = "#28a745"
        elif status == "error":
            color = "#dc3545"
        elif status == "warning":
            color = "#ffc107"
        elif status == "loading":
            color = "#17a2b8"
        else:  # inactive
            color = "#6c757d"
        
        self.circle.setStyleSheet(f"color: {color};")
        self.text.setStyleSheet(f"color: {color};")

class ModernTable(QTableWidget):
    """Modern table component"""
    
    def __init__(self, headers=None, parent=None):
        super().__init__(parent)
        self.headers = headers or []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup table UI"""
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        
        # Set alternating row colors
        self.setAlternatingRowColors(True)
        
        # Set selection behavior
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    
    def add_row(self, data):
        """Add a row to the table"""
        row_position = self.rowCount()
        self.insertRow(row_position)
        
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row_position, col, item)
    
    def clear_data(self):
        """Clear all data from table"""
        self.setRowCount(0)

class ProgressIndicator(QWidget):
    """Modern progress indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup progress indicator UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 6px;
            }
        """)
        
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #6c757d;")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
    
    def update_progress(self, value, status="Processing..."):
        """Update progress indicator"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

class AccountCard(ModernCard):
    """Account management card"""
    
    status_changed = pyqtSignal(str, str)  # account_type, status
    
    def __init__(self, account_type, account_name, icon, parent=None):
        super().__init__(f"{icon} {account_type} Account", parent)
        self.account_type = account_type
        self.account_name = account_name
        self.setup_ui()
    
    def setup_ui(self):
        """Setup account card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Account name
        name_label = QLabel(self.account_name)
        name_label.setFont(QFont("Segoe UI", 10))
        name_label.setStyleSheet("color: #666666; margin-left: 10px;")
        layout.addWidget(name_label)
        
        # Status indicator
        self.status_indicator = StatusIndicator("inactive")
        layout.addWidget(self.status_indicator)
        
        # Account input
        self.account_input = ModernInput("Account details...")
        layout.addWidget(self.account_input)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.login_btn = ModernButton("Login", "primary")
        self.status_btn = ModernButton("Status", "primary")
        self.mtm_btn = ModernButton("MTM", "primary")
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.status_btn)
        button_layout.addWidget(self.mtm_btn)
        
        layout.addLayout(button_layout)
    
    def update_status(self, status):
        """Update account status"""
        self.status_indicator.update_status(status)
        self.status_changed.emit(self.account_type, status)
    
    def update_name(self, name):
        """Update account name"""
        self.account_name = name
        # Update the name label
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() != self.account_name:
                widget.setText(name)
                break

class TradingCard(ModernCard):
    """Trading controls card"""
    
    order_placed = pyqtSignal(str, str, float, int)  # symbol, type, price, quantity
    
    def __init__(self, parent=None):
        super().__init__("Trading Controls", parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup trading card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Price section
        price_layout = QHBoxLayout()
        price_layout.setSpacing(10)
        
        self.fetch_btn = ModernButton("Fetch Price", "info")
        price_layout.addWidget(self.fetch_btn)
        
        price_layout.addWidget(QLabel("Price:"))
        self.price_input = ModernInput("0.00")
        price_layout.addWidget(self.price_input)
        
        price_layout.addWidget(QLabel("Quantity:"))
        self.qty_combo = ModernComboBox()
        price_layout.addWidget(self.qty_combo)
        
        price_layout.addStretch()
        layout.addLayout(price_layout)
        
        # Buy/Sell buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        
        self.buy_btn = ModernButton("BUY", "success")
        self.sell_btn = ModernButton("SELL", "danger")
        
        action_layout.addWidget(self.buy_btn)
        action_layout.addWidget(self.sell_btn)
        
        layout.addLayout(action_layout)
        
        # Connect signals
        self.buy_btn.clicked.connect(self.place_buy_order)
        self.sell_btn.clicked.connect(self.place_sell_order)
    
    def place_buy_order(self):
        """Place buy order"""
        symbol = self.get_trading_symbol()
        price = float(self.price_input.text() or 0)
        quantity = int(self.qty_combo.currentText() or 0)
        self.order_placed.emit(symbol, "BUY", price, quantity)
    
    def place_sell_order(self):
        """Place sell order"""
        symbol = self.get_trading_symbol()
        price = float(self.price_input.text() or 0)
        quantity = int(self.qty_combo.currentText() or 0)
        self.order_placed.emit(symbol, "SELL", price, quantity)
    
    def get_trading_symbol(self):
        """Get current trading symbol"""
        # This would be connected to the instrument selection
        return "SENSEX2591181200CE"  # Placeholder

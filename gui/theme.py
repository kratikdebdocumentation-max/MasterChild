"""
Modern theme system for Master-Child Trading GUI
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
import json
import os

class ModernTheme:
    """Modern theme management system"""
    
    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "primary": "#1a1a1a",
                "secondary": "#2d2d2d", 
                "accent": "#00d4aa",
                "accent_hover": "#00b894",
                "text": "#ffffff",
                "text_secondary": "#b0b0b0",
                "success": "#00d4aa",
                "danger": "#ff6b6b",
                "warning": "#feca57",
                "info": "#48dbfb",
                "border": "#404040",
                "hover": "#3d3d3d",
                "card": "#2d2d2d",
                "input_bg": "#1a1a1a",
                "input_border": "#404040",
                "button_bg": "#00d4aa",
                "button_hover": "#00b894",
                "button_text": "#ffffff"
            },
            "light": {
                "primary": "#f5f5f5",
                "secondary": "#e8e8e8",
                "accent": "#6c757d",
                "accent_hover": "#5a6268",
                "text": "#2c2c2c",
                "text_secondary": "#6c757d",
                "success": "#6c757d",
                "danger": "#6c757d",
                "warning": "#6c757d",
                "info": "#6c757d",
                "border": "#d0d0d0",
                "hover": "#e0e0e0",
                "card": "#ffffff",
                "input_bg": "#ffffff",
                "input_border": "#d0d0d0",
                "button_bg": "#6c757d",
                "button_hover": "#5a6268",
                "button_text": "#ffffff"
            }
        }
        
    def get_theme(self, theme_name: str = None) -> Dict[str, str]:
        """Get theme colors"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["dark"])
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
    
    def configure_styles(self, root: tk.Tk):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        theme = self.get_theme()
        
        # Configure root window
        root.configure(bg=theme["primary"])
        
        # Configure ttk styles
        style.theme_use('clam')
        
        # Button styles
        style.configure("Modern.TButton",
                       background=theme["button_bg"],
                       foreground=theme["button_text"],
                       borderwidth=1,
                       relief="solid",
                       focuscolor='none',
                       padding=(12, 8),
                       font=('Segoe UI', 9, 'normal'))
        
        style.map("Modern.TButton",
                 background=[('active', theme["button_hover"]),
                           ('pressed', theme["accent_hover"])])
        
        # All buttons use the same grey theme
        style.configure("Success.TButton",
                       background=theme["button_bg"],
                       foreground="white",
                       borderwidth=1,
                       relief="solid",
                       focuscolor='none',
                       padding=(12, 8),
                       font=('Segoe UI', 9, 'normal'))
        
        style.configure("Danger.TButton",
                       background=theme["button_bg"],
                       foreground="white",
                       borderwidth=1,
                       relief="solid",
                       focuscolor='none',
                       padding=(12, 8),
                       font=('Segoe UI', 9, 'normal'))
        
        style.configure("Info.TButton",
                       background=theme["button_bg"],
                       foreground="white",
                       borderwidth=1,
                       relief="solid",
                       focuscolor='none',
                       padding=(12, 8),
                       font=('Segoe UI', 9, 'normal'))
        
        style.configure("Warning.TButton",
                       background=theme["button_bg"],
                       foreground="white",
                       borderwidth=1,
                       relief="solid",
                       focuscolor='none',
                       padding=(12, 8),
                       font=('Segoe UI', 9, 'normal'))
        
        # Entry styles
        style.configure("Modern.TEntry",
                       fieldbackground=theme["input_bg"],
                       foreground=theme["text"],
                       borderwidth=1,
                       relief="solid",
                       padding=(10, 8),
                       font=('Segoe UI', 10))
        
        # Combobox styles
        style.configure("Modern.TCombobox",
                       fieldbackground=theme["input_bg"],
                       foreground=theme["text"],
                       borderwidth=1,
                       relief="solid",
                       padding=(10, 8),
                       font=('Segoe UI', 10))
        
        # Label styles
        style.configure("Title.TLabel",
                       background=theme["primary"],
                       foreground=theme["text"],
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure("Subtitle.TLabel",
                       background=theme["primary"],
                       foreground=theme["text_secondary"],
                       font=('Segoe UI', 12))
        
        style.configure("Modern.TLabel",
                       background=theme["primary"],
                       foreground=theme["text"],
                       font=('Segoe UI', 10))
        
        # Frame styles
        style.configure("Card.TFrame",
                       background=theme["card"],
                       relief="solid",
                       borderwidth=1)
        
        # Progressbar styles
        style.configure("Modern.Horizontal.TProgressbar",
                       background=theme["accent"],
                       troughcolor=theme["secondary"],
                       borderwidth=0,
                       lightcolor=theme["accent"],
                       darkcolor=theme["accent"])
        
        return style

class ModernColors:
    """Color constants for easy access"""
    
    # Dark theme colors
    DARK_PRIMARY = "#1a1a1a"
    DARK_SECONDARY = "#2d2d2d"
    DARK_ACCENT = "#00d4aa"
    DARK_TEXT = "#ffffff"
    DARK_TEXT_SECONDARY = "#b0b0b0"
    DARK_SUCCESS = "#00d4aa"
    DARK_DANGER = "#ff6b6b"
    DARK_WARNING = "#feca57"
    DARK_INFO = "#48dbfb"
    DARK_BORDER = "#404040"
    DARK_CARD = "#2d2d2d"
    
    # Light theme colors
    LIGHT_PRIMARY = "#ffffff"
    LIGHT_SECONDARY = "#f8f9fa"
    LIGHT_ACCENT = "#007bff"
    LIGHT_TEXT = "#212529"
    LIGHT_TEXT_SECONDARY = "#6c757d"
    LIGHT_SUCCESS = "#28a745"
    LIGHT_DANGER = "#dc3545"
    LIGHT_WARNING = "#ffc107"
    LIGHT_INFO = "#17a2b8"
    LIGHT_BORDER = "#dee2e6"
    LIGHT_CARD = "#ffffff"

class ModernFonts:
    """Font constants for consistent typography"""
    
    TITLE = ('Segoe UI', 18, 'bold')
    SUBTITLE = ('Segoe UI', 14, 'bold')
    BODY = ('Segoe UI', 10)
    BODY_BOLD = ('Segoe UI', 10, 'bold')
    SMALL = ('Segoe UI', 9)
    LARGE = ('Segoe UI', 12)
    MONOSPACE = ('Consolas', 10)

class ModernIcons:
    """Icon constants using Unicode symbols"""
    
    # Trading icons
    BUY = "📈"
    SELL = "📉"
    REFRESH = "🔄"
    LOGIN = "🔐"
    LOGOUT = "🚪"
    SETTINGS = "⚙️"
    CHART = "📊"
    WALLET = "💼"
    ALERT = "⚠️"
    SUCCESS = "✅"
    ERROR = "❌"
    INFO = "ℹ️"
    
    # Account icons
    MASTER = "👑"
    CHILD = "👶"
    ACCOUNT = "👤"
    
    # Order icons
    ORDER = "📋"
    MODIFY = "✏️"
    CANCEL = "❌"
    STATUS = "📊"
    
    # Market icons
    MARKET = "🏪"
    PRICE = "💰"
    VOLUME = "📊"
    TREND = "📈"

"""
Modern settings window for Master-Child Trading GUI
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from .theme import ModernTheme, ModernFonts, ModernIcons
from .components import ModernCard, ModernButton, ModernLabel, ModernEntry, ModernCombobox

class SettingsWindow:
    """Modern settings window"""
    
    def __init__(self, parent, on_theme_change: Optional[Callable] = None):
        self.parent = parent
        self.on_theme_change = on_theme_change
        self.theme = ModernTheme()
        self.theme.set_theme("light")  # Set light theme as default
        self.create_window()
    
    def create_window(self):
        """Create settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.configure(bg=self.theme.get_theme()["primary"])
        
        # Center the window
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create main container
        main_container = tk.Frame(self.window, bg=self.theme.get_theme()["primary"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Settings sections
        self.create_appearance_section(main_container)
        self.create_trading_section(main_container)
        self.create_notifications_section(main_container)
        
        # Action buttons
        self.create_action_buttons(main_container)
    
    def create_header(self, parent):
        """Create window header"""
        header_frame = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ModernLabel(
            header_frame,
            text=f"{ModernIcons.SETTINGS} Settings",
            style="title"
        )
        title_label.pack(side="left")
        
        close_btn = ModernButton(
            header_frame,
            text="✕",
            command=self.window.destroy,
            style="primary"
        )
        close_btn.pack(side="right")
    
    def create_appearance_section(self, parent):
        """Create appearance settings section"""
        appearance_card = ModernCard(parent, title="Appearance")
        appearance_card.pack(fill="x", pady=(0, 15))
        
        # Theme selection
        theme_frame = tk.Frame(appearance_card.content_frame, bg=self.theme.get_theme()["card"])
        theme_frame.pack(fill="x", pady=(0, 10))
        
        ModernLabel(theme_frame, text="Theme:", style="secondary").pack(side="left", padx=(0, 10))
        
        self.theme_var = tk.StringVar(value="light")
        self.theme_combobox = ModernCombobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["dark", "light"],
            width=15
        )
        self.theme_combobox.pack(side="left", padx=(0, 10))
        self.theme_combobox.bind("<<ComboboxSelected>>", self.on_theme_change_selected)
        
        # Window size
        size_frame = tk.Frame(appearance_card.content_frame, bg=self.theme.get_theme()["card"])
        size_frame.pack(fill="x", pady=(0, 10))
        
        ModernLabel(size_frame, text="Window Size:", style="secondary").pack(side="left", padx=(0, 10))
        
        self.size_var = tk.StringVar(value="1400x800")
        self.size_combobox = ModernCombobox(
            size_frame,
            textvariable=self.size_var,
            values=["1200x700", "1400x800", "1600x900", "1920x1080"],
            width=15
        )
        self.size_combobox.pack(side="left")
        
        # Animations
        animation_frame = tk.Frame(appearance_card.content_frame, bg=self.theme.get_theme()["card"])
        animation_frame.pack(fill="x")
        
        self.animation_var = tk.BooleanVar(value=True)
        self.animation_checkbox = tk.Checkbutton(
            animation_frame,
            text="Enable animations",
            variable=self.animation_var,
            bg=self.theme.get_theme()["card"],
            fg=self.theme.get_theme()["text"],
            selectcolor=self.theme.get_theme()["accent"],
            font=ModernFonts.BODY
        )
        self.animation_checkbox.pack(side="left")
    
    def create_trading_section(self, parent):
        """Create trading settings section"""
        trading_card = ModernCard(parent, title="Trading")
        trading_card.pack(fill="x", pady=(0, 15))
        
        # Default order type
        order_type_frame = tk.Frame(trading_card.content_frame, bg=self.theme.get_theme()["card"])
        order_type_frame.pack(fill="x", pady=(0, 10))
        
        ModernLabel(order_type_frame, text="Default Order Type:", style="secondary").pack(side="left", padx=(0, 10))
        
        self.order_type_var = tk.StringVar(value="MIS")
        self.order_type_combobox = ModernCombobox(
            order_type_frame,
            textvariable=self.order_type_var,
            values=["MIS", "CNC"],
            width=15
        )
        self.order_type_combobox.pack(side="left")
        
        # Auto-refresh interval
        refresh_frame = tk.Frame(trading_card.content_frame, bg=self.theme.get_theme()["card"])
        refresh_frame.pack(fill="x")
        
        ModernLabel(refresh_frame, text="Auto-refresh (seconds):", style="secondary").pack(side="left", padx=(0, 10))
        
        self.refresh_var = tk.StringVar(value="5")
        self.refresh_entry = ModernEntry(
            refresh_frame,
            textvariable=self.refresh_var,
            width=10
        )
        self.refresh_entry.pack(side="left")
    
    def create_notifications_section(self, parent):
        """Create notifications settings section"""
        notifications_card = ModernCard(parent, title="Notifications")
        notifications_card.pack(fill="x", pady=(0, 15))
        
        # Sound notifications
        sound_frame = tk.Frame(notifications_card.content_frame, bg=self.theme.get_theme()["card"])
        sound_frame.pack(fill="x", pady=(0, 10))
        
        self.sound_var = tk.BooleanVar(value=False)
        self.sound_checkbox = tk.Checkbutton(
            sound_frame,
            text="Enable sound notifications",
            variable=self.sound_var,
            bg=self.theme.get_theme()["card"],
            fg=self.theme.get_theme()["text"],
            selectcolor=self.theme.get_theme()["accent"],
            font=ModernFonts.BODY
        )
        self.sound_checkbox.pack(side="left")
        
        # Telegram notifications
        telegram_frame = tk.Frame(notifications_card.content_frame, bg=self.theme.get_theme()["card"])
        telegram_frame.pack(fill="x")
        
        self.telegram_var = tk.BooleanVar(value=False)
        self.telegram_checkbox = tk.Checkbutton(
            telegram_frame,
            text="Enable Telegram notifications",
            variable=self.telegram_var,
            bg=self.theme.get_theme()["card"],
            fg=self.theme.get_theme()["text"],
            selectcolor=self.theme.get_theme()["accent"],
            font=ModernFonts.BODY
        )
        self.telegram_checkbox.pack(side="left")
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Save button
        save_btn = ModernButton(
            button_frame,
            text="Save Settings",
            icon=ModernIcons.SUCCESS,
            command=self.save_settings,
            style="primary"
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        # Reset button
        reset_btn = ModernButton(
            button_frame,
            text="Reset to Defaults",
            icon=ModernIcons.REFRESH,
            command=self.reset_settings,
            style="primary"
        )
        reset_btn.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            style="primary"
        )
        cancel_btn.pack(side="right")
    
    def on_theme_change_selected(self, event):
        """Handle theme change"""
        new_theme = self.theme_var.get()
        self.theme.set_theme(new_theme)
        
        if self.on_theme_change:
            self.on_theme_change(new_theme)
    
    def save_settings(self):
        """Save settings"""
        try:
            # Save theme
            self.theme.set_theme(self.theme_var.get())
            
            # Save other settings (in a real implementation, you'd save to a config file)
            settings = {
                "theme": self.theme_var.get(),
                "window_size": self.size_var.get(),
                "animations": self.animation_var.get(),
                "order_type": self.order_type_var.get(),
                "refresh_interval": int(self.refresh_var.get()),
                "sound_notifications": self.sound_var.get(),
                "telegram_notifications": self.telegram_var.get()
            }
            
            # Here you would save to config file
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.theme_var.set("light")
        self.size_var.set("1400x800")
        self.animation_var.set(True)
        self.order_type_var.set("MIS")
        self.refresh_var.set("5")
        self.sound_var.set(False)
        self.telegram_var.set(False)
        
        messagebox.showinfo("Reset", "Settings reset to defaults")

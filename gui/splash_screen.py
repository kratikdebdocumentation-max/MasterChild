"""
Modern splash screen for Master-Child Trading GUI
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
from .theme import ModernTheme, ModernFonts, ModernIcons
from .components import ModernLabel, ProgressBar

class SplashScreen:
    """Modern splash screen with loading animation"""
    
    def __init__(self, on_complete: callable = None):
        self.on_complete = on_complete
        self.theme = ModernTheme()
        self.theme.set_theme("light")  # Set light theme as default
        self.create_splash()
        self.start_loading()
    
    def create_splash(self):
        """Create splash screen window"""
        self.window = tk.Tk()
        self.window.title("Shoonya Trading System")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        self.window.configure(bg=self.theme.get_theme()["primary"])
        
        # Center the window
        self.center_window()
        
        # Remove window decorations
        self.window.overrideredirect(True)
        
        # Create main container
        main_frame = tk.Frame(self.window, bg=self.theme.get_theme()["primary"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # App icon and title
        self.create_header(main_frame)
        
        # Loading section
        self.create_loading_section(main_frame)
        
        # Status text
        self.create_status_section(main_frame)
    
    def center_window(self):
        """Center the splash screen on the desktop"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_header(self, parent):
        """Create header with app icon and title"""
        header_frame = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        header_frame.pack(expand=True)
        
        # App icon
        icon_label = ModernLabel(
            header_frame,
            text=ModernIcons.CHART,
            style="title"
        )
        icon_label.configure(font=('Segoe UI', 48))
        icon_label.pack(pady=(0, 10))
        
        # App title
        title_label = ModernLabel(
            header_frame,
            text="Shoonya Master-Child Trading System",
            style="title"
        )
        title_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = ModernLabel(
            header_frame,
            text="Professional Trading Platform",
            style="secondary"
        )
        subtitle_label.pack()
    
    def create_loading_section(self, parent):
        """Create loading section with progress bar"""
        loading_frame = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        loading_frame.pack(fill="x", pady=(20, 0))
        
        # Progress bar
        self.progress_bar = ProgressBar(loading_frame)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Loading text
        self.loading_label = ModernLabel(
            loading_frame,
            text="Initializing system...",
            style="secondary"
        )
        self.loading_label.pack()
    
    def create_status_section(self, parent):
        """Create status section"""
        status_frame = tk.Frame(parent, bg=self.theme.get_theme()["primary"])
        status_frame.pack(fill="x", pady=(20, 0))
        
        # Version info
        version_label = ModernLabel(
            status_frame,
            text="Version 2.0.0 | Modern GUI",
            style="secondary"
        )
        version_label.pack()
    
    def start_loading(self):
        """Start loading animation in a separate thread"""
        def loading_thread():
            loading_steps = [
                ("Loading configuration...", 20),
                ("Connecting to trading APIs...", 40),
                ("Initializing account managers...", 60),
                ("Setting up market data feeds...", 80),
                ("Preparing user interface...", 100)
            ]
            
            for step_text, progress in loading_steps:
                self.window.after(0, self.update_loading, step_text, progress)
                time.sleep(0.8)  # Simulate loading time
            
            # Close splash screen and open main window
            self.window.after(0, self.close_splash)
        
        # Start loading in background thread
        thread = threading.Thread(target=loading_thread, daemon=True)
        thread.start()
    
    def update_loading(self, text: str, progress: int):
        """Update loading progress"""
        self.loading_label.configure(text=text)
        self.progress_bar.set_progress(progress)
        self.window.update()
    
    def close_splash(self):
        """Close splash screen and open main window"""
        self.window.destroy()
        if self.on_complete:
            self.on_complete()
    
    def run(self):
        """Run splash screen"""
        self.window.mainloop()

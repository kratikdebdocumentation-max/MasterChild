"""
Configuration window for Master-Child Trading System
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, Any, Optional
from logger import applicationLogger

class ConfigurationWindow:
    """Configuration window for setting trading parameters"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.settings = {}
        self.settings_file = "config/settings.json"
        
        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        
        # Load existing settings or use defaults
        self.load_settings()
        
        # Setup window
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Setup the configuration window"""
        self.root.title("Trading Configuration")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Make window modal
        self.root.transient()
        self.root.grab_set()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """Create the configuration widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Trading Configuration", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Default Settings", padding="15")
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Child default lots
        ttk.Label(config_frame, text="Child Default Lots:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.child_lots_var = tk.StringVar(value=str(self.settings.get('child_default_lots', 1)))
        self.child_lots_entry = ttk.Entry(config_frame, textvariable=self.child_lots_var, width=15)
        self.child_lots_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Default SL points
        ttk.Label(config_frame, text="Default SL Points:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sl_points_var = tk.StringVar(value=str(self.settings.get('default_sl_points', 20)))
        self.sl_points_entry = ttk.Entry(config_frame, textvariable=self.sl_points_var, width=15)
        self.sl_points_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Default Target points
        ttk.Label(config_frame, text="Default Target Points:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.target_points_var = tk.StringVar(value=str(self.settings.get('default_target_points', 30)))
        self.target_points_entry = ttk.Entry(config_frame, textvariable=self.target_points_var, width=15)
        self.target_points_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = """• Child lots will be multiplied by minimum lot size from master scripts
• SL/Target points will be used for auto-populating SL/Target values
• You can still modify these values manually in the main application"""
        
        ttk.Label(info_frame, text=info_text, wraplength=400, justify=tk.LEFT).pack()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Skip button
        skip_button = ttk.Button(button_frame, text="Skip", 
                                command=self.skip_configuration, width=12)
        skip_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button
        save_button = ttk.Button(button_frame, text="Save", 
                                command=self.save_configuration, width=12)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Next button
        next_button = ttk.Button(button_frame, text="Next", 
                                command=self.next_configuration, width=12)
        next_button.pack(side=tk.RIGHT)
        
        # Focus on first entry
        self.child_lots_entry.focus()
        
    def load_settings(self):
        """Load settings from file or use defaults"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                applicationLogger.info(f"Loaded settings from {self.settings_file}: {self.settings}")
            else:
                # Use default values
                self.settings = {
                    'child_default_lots': 1,
                    'default_sl_points': 20,
                    'default_target_points': 30
                }
                applicationLogger.info(f"Using default settings: {self.settings}")
        except Exception as e:
            applicationLogger.error(f"Error loading settings: {e}")
            self.settings = {
                'child_default_lots': 1,
                'default_sl_points': 20,
                'default_target_points': 30
            }
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            applicationLogger.info(f"Settings saved to {self.settings_file}: {self.settings}")
        except Exception as e:
            applicationLogger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def validate_inputs(self) -> bool:
        """Validate all input values"""
        try:
            # Validate child lots
            child_lots = int(self.child_lots_var.get())
            if child_lots <= 0:
                messagebox.showerror("Invalid Input", "Child default lots must be greater than 0")
                self.child_lots_entry.focus()
                return False
            
            # Validate SL points
            sl_points = float(self.sl_points_var.get())
            if sl_points <= 0:
                messagebox.showerror("Invalid Input", "Default SL points must be greater than 0")
                self.sl_points_entry.focus()
                return False
            
            # Validate Target points
            target_points = float(self.target_points_var.get())
            if target_points <= 0:
                messagebox.showerror("Invalid Input", "Default Target points must be greater than 0")
                self.target_points_entry.focus()
                return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for all fields")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error validating inputs: {e}")
            return False
    
    def skip_configuration(self):
        """Skip configuration and use last saved values"""
        applicationLogger.info("Configuration skipped - using last saved values")
        self.root.quit()
    
    def save_configuration(self):
        """Save current configuration without closing the window"""
        if not self.validate_inputs():
            return
        
        # Update settings with new values
        self.settings['child_default_lots'] = int(self.child_lots_var.get())
        self.settings['default_sl_points'] = float(self.sl_points_var.get())
        self.settings['default_target_points'] = float(self.target_points_var.get())
        
        # Save settings
        self.save_settings()
        
        applicationLogger.info(f"Configuration saved: {self.settings}")
        messagebox.showinfo("Success", "Configuration saved successfully!")
    
    def next_configuration(self):
        """Save configuration and proceed to main application"""
        if not self.validate_inputs():
            return
        
        # Update settings with new values
        self.settings['child_default_lots'] = int(self.child_lots_var.get())
        self.settings['default_sl_points'] = float(self.sl_points_var.get())
        self.settings['default_target_points'] = float(self.target_points_var.get())
        
        # Save settings
        self.save_settings()
        
        applicationLogger.info(f"Configuration completed and proceeding: {self.settings}")
        self.root.quit()
    
    def show_window(self) -> Dict[str, Any]:
        """Show the configuration window and return settings"""
        self.root.mainloop()
        self.root.destroy()
        return self.settings

def show_configuration_window() -> Dict[str, Any]:
    """Show configuration window and return settings"""
    config_window = ConfigurationWindow()
    return config_window.show_window()
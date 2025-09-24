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
    
    def __init__(self, current_settings: Dict[str, Any] = None):
        self.root = tk.Tk()
        self.settings = {}
        self.original_settings = {}  # Store original values for change detection
        self.settings_file = "config/settings.json"
        self.changes_made = False  # Track if any changes were made
        
        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        
        # Load existing settings or use defaults
        self.load_settings(current_settings)
        
        # Store original settings for comparison
        self.original_settings = self.settings.copy()
        
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
        child_lots_value = int(self.settings.get('child_default_lots', 1))
        self.child_lots_var = tk.StringVar()
        self.child_lots_entry = ttk.Entry(config_frame, textvariable=self.child_lots_var, width=15)
        self.child_lots_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.child_lots_var.trace('w', self.on_value_changed)
        
        # Default SL points
        ttk.Label(config_frame, text="Default SL Points:").grid(row=1, column=0, sticky=tk.W, pady=5)
        sl_points_value = float(self.settings.get('default_sl_points', 20))
        self.sl_points_var = tk.StringVar()
        self.sl_points_entry = ttk.Entry(config_frame, textvariable=self.sl_points_var, width=15)
        self.sl_points_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.sl_points_var.trace('w', self.on_value_changed)
        
        # Default Target points
        ttk.Label(config_frame, text="Default Target Points:").grid(row=2, column=0, sticky=tk.W, pady=5)
        target_points_value = float(self.settings.get('default_target_points', 30))
        self.target_points_var = tk.StringVar()
        self.target_points_entry = ttk.Entry(config_frame, textvariable=self.target_points_var, width=15)
        self.target_points_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.target_points_var.trace('w', self.on_value_changed)
        
        # Set values after all widgets are created and trace callbacks are set
        self.child_lots_var.set(str(child_lots_value))
        self.sl_points_var.set(str(sl_points_value))
        self.target_points_var.set(str(target_points_value))
        
        # Also set the entry widgets directly as a backup
        self.child_lots_entry.delete(0, tk.END)
        self.child_lots_entry.insert(0, str(child_lots_value))
        self.sl_points_entry.delete(0, tk.END)
        self.sl_points_entry.insert(0, str(sl_points_value))
        self.target_points_entry.delete(0, tk.END)
        self.target_points_entry.insert(0, str(target_points_value))
        
        # Force UI update to ensure values are displayed
        self.root.update_idletasks()
        self.root.update()
        applicationLogger.info(f"Configuration window values set - Child: {self.child_lots_var.get()}, SL: {self.sl_points_var.get()}, Target: {self.target_points_var.get()}")
        
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
        skip_button = ttk.Button(button_frame, text="SKIP", 
                                command=self.skip_configuration, width=15)
        skip_button.pack(side=tk.LEFT)
        
        # Save and Restart button
        save_restart_button = ttk.Button(button_frame, text="SAVE and Restart", 
                                       command=self.save_and_restart, width=20)
        save_restart_button.pack(side=tk.RIGHT)
        
        # Focus on first entry
        self.child_lots_entry.focus()
    
    def on_value_changed(self, *args):
        """Called when any input value changes"""
        self.changes_made = True
    
    def check_for_changes(self) -> bool:
        """Check if any values have been changed from original"""
        try:
            current_values = {
                'child_default_lots': int(self.child_lots_var.get()) if self.child_lots_var.get().isdigit() else 0,
                'default_sl_points': float(self.sl_points_var.get()) if self.sl_points_var.get().replace('.', '').isdigit() else 0,
                'default_target_points': float(self.target_points_var.get()) if self.target_points_var.get().replace('.', '').isdigit() else 0
            }
            
            # Compare with original settings
            for key, value in current_values.items():
                if key in self.original_settings and value != self.original_settings[key]:
                    return True
            return False
        except (ValueError, TypeError):
            return False
        
    def load_settings(self, current_settings: Dict[str, Any] = None):
        """Load settings from file or use defaults"""
        try:
            # If current settings are provided, use them as the base
            if current_settings:
                self.settings = current_settings.copy()
                applicationLogger.info(f"Using current settings: {self.settings}")
            elif os.path.exists(self.settings_file):
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
    
    
    def save_and_restart(self):
        """Save configuration and restart the program"""
        if not self.validate_inputs():
            return
        
        # Update settings with new values
        self.settings['child_default_lots'] = int(self.child_lots_var.get())
        self.settings['default_sl_points'] = float(self.sl_points_var.get())
        self.settings['default_target_points'] = float(self.target_points_var.get())
        
        # Save settings
        self.save_settings()
        
        applicationLogger.info(f"Configuration saved and restarting: {self.settings}")
        
        # Show confirmation message
        result = messagebox.askyesno("Restart Required", 
                                   "Configuration saved successfully!\n\n"
                                   "The program needs to restart to apply the changes.\n\n"
                                   "Do you want to restart now?")
        
        if result:
            self.restart_program()
        else:
            # User chose not to restart, just close the window
            self.root.quit()
    
    def restart_program(self):
        """Restart the program"""
        # Close the configuration window
        self.root.quit()
        self.root.destroy()
        
        # Restart the program
        import sys
        import os
        import subprocess
        
        try:
            # Get the current script path
            script_path = os.path.abspath(sys.argv[0])
            
            # Start a new instance of the program
            subprocess.Popen([sys.executable, script_path])
            
            # Exit the current instance
            sys.exit(0)
            
        except Exception as e:
            applicationLogger.error(f"Error restarting program: {e}")
            messagebox.showerror("Error", f"Failed to restart program: {e}")
    
    def show_window(self) -> Dict[str, Any]:
        """Show the configuration window and return settings"""
        # Ensure values are displayed before showing the window
        self.root.update_idletasks()
        self.root.update()
        
        # Force set values again right before showing the window
        self.refresh_values()
        
        # Also set values after a short delay to ensure window is fully displayed
        self.root.after(100, self.refresh_values)
        
        # Log the current values for debugging
        applicationLogger.info(f"Showing configuration window with values - Child: {self.child_lots_var.get()}, SL: {self.sl_points_var.get()}, Target: {self.target_points_var.get()}")
        
        self.root.mainloop()
        self.root.destroy()
        return self.settings
    
    def refresh_values(self):
        """Refresh the display values"""
        child_lots_value = int(self.settings.get('child_default_lots', 1))
        sl_points_value = float(self.settings.get('default_sl_points', 20))
        target_points_value = float(self.settings.get('default_target_points', 30))
        
        # Set StringVar values
        self.child_lots_var.set(str(child_lots_value))
        self.sl_points_var.set(str(sl_points_value))
        self.target_points_var.set(str(target_points_value))
        
        # Also set entry widgets directly
        self.child_lots_entry.delete(0, tk.END)
        self.child_lots_entry.insert(0, str(child_lots_value))
        self.sl_points_entry.delete(0, tk.END)
        self.sl_points_entry.insert(0, str(sl_points_value))
        self.target_points_entry.delete(0, tk.END)
        self.target_points_entry.insert(0, str(target_points_value))
        
        # Force update
        self.root.update_idletasks()
        self.root.update()

def show_configuration_window(current_settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """Show configuration window and return settings"""
    config_window = ConfigurationWindow(current_settings)
    return config_window.show_window()
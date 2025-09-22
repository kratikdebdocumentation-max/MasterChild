"""
Configuration Window for Master-Child GUI
Modal window for editing configuration settings
"""
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

class ConfigWindow:
    """Configuration window for editing settings"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
        self.entries = {}
        self.var_child_lots = None
        self.original_config = {}
        
    def open(self):
        """Open the configuration window"""
        try:
            # Create modal window
            self.window = tk.Toplevel(self.parent)
            self.window.title("Configuration Settings")
            self.window.geometry("500x600")
            self.window.resizable(False, False)
            
            # Make it modal
            self.window.transient(self.parent)
            self.window.grab_set()
            
            # Center the window
            self.center_window()
            
            # Load current configuration
            self.load_configuration()
            
            # Create the form
            self.create_form()
            
            # Focus on the window
            self.window.focus()
            
        except Exception as e:
            logger.error(f"Error opening configuration window: {e}")
            messagebox.showerror("Error", f"Failed to open configuration window: {e}")
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def load_configuration(self):
        """Load current configuration values"""
        try:
            self.original_config = {
                'default_auto_sl': self.config_manager.get_setting('default_auto_sl', '20'),
                'default_auto_target': self.config_manager.get_setting('default_auto_target', '30'),
                'child_lots': self.config_manager.get_setting('child_lots', 'min'),
                'sensex_lot_size': self.config_manager.get_setting('sensex_lot_size', '20'),
                'nifty_lot_size': self.config_manager.get_setting('nifty_lot_size', '75'),
                'banknifty_lot_size': self.config_manager.get_setting('banknifty_lot_size', '35')
            }
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def create_form(self):
        """Create the configuration form"""
        try:
            # Main frame
            main_frame = ttk.Frame(self.window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Configuration Settings", 
                                  font=('Arial', 16, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Form fields
            self.create_field(main_frame, "Default Auto SL:", "default_auto_sl", 
                            "Default auto stop loss points")
            
            self.create_field(main_frame, "Default Auto Target:", "default_auto_target", 
                            "Default auto target points")
            
            self.create_child_lots_field(main_frame)
            
            self.create_field(main_frame, "SENSEX Lot Size:", "sensex_lot_size", 
                            "min qty for sensex options")
            
            self.create_field(main_frame, "NIFTY Lot Size:", "nifty_lot_size", 
                            "min qty for nifty options")
            
            self.create_field(main_frame, "BANKNIFTY Lot Size:", "banknifty_lot_size", 
                            "min qty for banknifty options")
            
            # Buttons frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(pady=(30, 0))
            
            # Skip button
            skip_button = ttk.Button(buttons_frame, text="SKIP", 
                                   command=self.skip_changes, width=15)
            skip_button.pack(side=tk.LEFT, padx=(0, 10))
            
            # Save and Restart button
            save_button = ttk.Button(buttons_frame, text="SAVE and Restart", 
                                   command=self.save_and_restart, width=15)
            save_button.pack(side=tk.LEFT)
            
        except Exception as e:
            logger.error(f"Error creating form: {e}")
            messagebox.showerror("Error", f"Failed to create form: {e}")
    
    def create_field(self, parent, label_text, field_name, description):
        """Create a form field with label, entry, and description"""
        # Field frame
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Label
        label = ttk.Label(field_frame, text=label_text, width=20, anchor='w')
        label.pack(side=tk.LEFT)
        
        # Entry
        entry = ttk.Entry(field_frame, width=10)
        entry.pack(side=tk.LEFT, padx=(10, 0))
        entry.insert(0, self.original_config.get(field_name, ''))
        
        # Store reference
        self.entries[field_name] = entry
        
        # Description
        desc_label = ttk.Label(field_frame, text=f"({description})", 
                              font=('Arial', 9), foreground='gray')
        desc_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_child_lots_field(self, parent):
        """Create the child lots dropdown field"""
        # Field frame
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Label
        label = ttk.Label(field_frame, text="Child Lots:", width=20, anchor='w')
        label.pack(side=tk.LEFT)
        
        # Dropdown
        self.var_child_lots = tk.StringVar()
        child_lots_combo = ttk.Combobox(field_frame, textvariable=self.var_child_lots, 
                                       width=8, state="readonly")
        child_lots_combo['values'] = ['min', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        child_lots_combo.pack(side=tk.LEFT, padx=(10, 0))
        child_lots_combo.set(self.original_config.get('child_lots', 'min'))
        
        # Store reference
        self.entries['child_lots'] = child_lots_combo
        
        # Description
        desc_label = ttk.Label(field_frame, text="(Default child account lots)", 
                              font=('Arial', 9), foreground='gray')
        desc_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def validate_fields(self):
        """Validate all form fields"""
        try:
            errors = []
            
            # Validate numeric fields
            numeric_fields = ['default_auto_sl', 'default_auto_target', 
                            'sensex_lot_size', 'nifty_lot_size', 'banknifty_lot_size']
            
            for field_name in numeric_fields:
                value = self.entries[field_name].get().strip()
                if not value:
                    errors.append(f"{field_name} cannot be empty")
                else:
                    try:
                        int(value)
                    except ValueError:
                        errors.append(f"{field_name} must be a valid number")
            
            # Validate child_lots (already validated by dropdown)
            child_lots_value = self.var_child_lots.get()
            if not child_lots_value:
                errors.append("Child lots must be selected")
            
            if errors:
                messagebox.showerror("Validation Error", "\\n".join(errors))
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating fields: {e}")
            messagebox.showerror("Error", f"Validation error: {e}")
            return False
    
    def skip_changes(self):
        """Skip changes and close window"""
        try:
            self.window.destroy()
        except Exception as e:
            logger.error(f"Error closing window: {e}")
    
    def save_and_restart(self):
        """Save changes and restart application"""
        try:
            # Validate fields
            if not self.validate_fields():
                return
            
            # Get new values
            new_config = {}
            for field_name, widget in self.entries.items():
                if field_name == 'child_lots':
                    new_config[field_name] = self.var_child_lots.get()
                else:
                    new_config[field_name] = widget.get().strip()
            
            # Save to CSV
            self.save_configuration(new_config)
            
            # Show success message
            messagebox.showinfo("Success", "Configuration saved successfully. Application will restart.")
            
            # Close window
            self.window.destroy()
            
            # Restart application
            self.restart_application()
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def save_configuration(self, new_config):
        """Save configuration to CSV file"""
        try:
            # Create DataFrame
            data = []
            for setting_name, value in new_config.items():
                # Get description from original config
                description = self.get_setting_description(setting_name)
                data.append({
                    'setting_name': setting_name,
                    'value': value,
                    'description': description
                })
            
            # Save to CSV
            df = pd.DataFrame(data)
            df.to_csv('configuration.csv', index=False)
            
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration to CSV: {e}")
            raise
    
    def get_setting_description(self, setting_name):
        """Get description for a setting"""
        descriptions = {
            'default_auto_sl': 'Default auto stop loss points',
            'default_auto_target': 'Default auto target points',
            'child_lots': 'Default child account lots',
            'sensex_lot_size': 'min qty for sensex options',
            'nifty_lot_size': 'min qty for nifty options',
            'banknifty_lot_size': 'min qty for banknifty options'
        }
        return descriptions.get(setting_name, '')
    
    def restart_application(self):
        """Restart the application"""
        try:
            # Close current application
            self.parent.quit()
            
            # Start new instance
            python = sys.executable
            subprocess.Popen([python, __file__])
            
        except Exception as e:
            logger.error(f"Error restarting application: {e}")
            messagebox.showerror("Error", f"Failed to restart application: {e}")

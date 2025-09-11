"""
Modern UI components for Master-Child Trading GUI
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any
from .theme import ModernTheme, ModernColors, ModernFonts, ModernIcons

class ModernCard(tk.Frame):
    """Modern card component with shadow effect"""
    
    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = ModernTheme()
        self.title = title
        self.create_card()
    
    def create_card(self):
        """Create card with title and content area"""
        theme = self.theme.get_theme()
        
        # Configure card frame
        self.configure(
            bg=theme["card"],
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=12
        )
        
        # Title label
        if self.title:
            title_label = tk.Label(
                self,
                text=self.title,
                font=('Segoe UI', 11, 'normal'),
                bg=theme["card"],
                fg=theme["text_secondary"],
                anchor="w"
            )
            title_label.pack(fill="x", pady=(0, 10))
        
        # Content frame
        self.content_frame = tk.Frame(self, bg=theme["card"])
        self.content_frame.pack(fill="both", expand=True)

class ModernButton(tk.Button):
    """Modern button with hover effects"""
    
    def __init__(self, parent, text: str, command: Callable = None, 
                 style: str = "primary", icon: str = "", **kwargs):
        self.theme = ModernTheme()
        self.style = style
        self.icon = icon
        self.command = command
        
        # Prepare button text
        button_text = f"{icon} {text}" if icon else text
        
        super().__init__(
            parent,
            text=button_text,
            command=self._on_click,
            font=ModernFonts.BODY_BOLD,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            **kwargs
        )
        
        self.configure_style()
        self.bind_events()
    
    def configure_style(self):
        """Configure button appearance"""
        theme = self.theme.get_theme()
        
        # All buttons use the same grey color scheme
        bg_color = theme["button_bg"]
        hover_color = theme["button_hover"]
        
        self.configure(
            bg=bg_color,
            fg="white",
            padx=15,
            pady=8,
            relief="solid",
            borderwidth=1
        )
        
        self.hover_color = hover_color
        self.original_color = bg_color
    
    def bind_events(self):
        """Bind hover events"""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter"""
        self.configure(bg=self.hover_color)
    
    def _on_leave(self, event):
        """Handle mouse leave"""
        self.configure(bg=self.original_color)
    
    def _on_click(self):
        """Handle button click"""
        if self.command:
            self.command()

class ModernEntry(tk.Entry):
    """Modern entry with better styling"""
    
    def __init__(self, parent, placeholder: str = "", **kwargs):
        self.theme = ModernTheme()
        self.placeholder = placeholder
        self.placeholder_color = self.theme.get_theme()["text_secondary"]
        self.text_color = self.theme.get_theme()["text"]
        
        super().__init__(
            parent,
            font=ModernFonts.BODY,
            relief="solid",
            borderwidth=1,
            **kwargs
        )
        
        self.configure_style()
        self.bind_events()
        
        if placeholder:
            self.insert_placeholder()
    
    def configure_style(self):
        """Configure entry appearance"""
        theme = self.theme.get_theme()
        
        self.configure(
            bg=theme["input_bg"],
            fg=self.text_color,
            insertbackground=theme["text"],
            selectbackground=theme["accent"],
            selectforeground="white",
            bd=1,
            relief="solid"
        )
    
    def bind_events(self):
        """Bind focus events"""
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
    
    def insert_placeholder(self):
        """Insert placeholder text"""
        self.insert(0, self.placeholder)
        self.configure(fg=self.placeholder_color)
        self.placeholder_active = True
    
    def _on_focus_in(self, event):
        """Handle focus in"""
        if hasattr(self, 'placeholder_active') and self.placeholder_active:
            self.delete(0, tk.END)
            self.configure(fg=self.text_color)
            self.placeholder_active = False
    
    def _on_focus_out(self, event):
        """Handle focus out"""
        if not self.get() and self.placeholder:
            self.insert_placeholder()

class ModernLabel(tk.Label):
    """Modern label with consistent styling"""
    
    def __init__(self, parent, text: str = "", style: str = "normal", **kwargs):
        self.theme = ModernTheme()
        self.style = style
        
        super().__init__(parent, text=text, **kwargs)
        self.configure_style()
    
    def configure_style(self):
        """Configure label appearance"""
        theme = self.theme.get_theme()
        
        if self.style == "title":
            font = ModernFonts.TITLE
            fg = theme["text"]
        elif self.style == "subtitle":
            font = ModernFonts.SUBTITLE
            fg = theme["text"]
        elif self.style == "secondary":
            font = ModernFonts.BODY
            fg = theme["text_secondary"]
        elif self.style == "success":
            font = ModernFonts.BODY
            fg = theme["success"]
        elif self.style == "danger":
            font = ModernFonts.BODY
            fg = theme["danger"]
        elif self.style == "warning":
            font = ModernFonts.BODY
            fg = theme["warning"]
        else:  # normal
            font = ModernFonts.BODY
            fg = theme["text"]
        
        self.configure(
            font=font,
            fg=fg,
            bg=theme["primary"]
        )

class ModernCombobox(ttk.Combobox):
    """Modern combobox with better styling"""
    
    def __init__(self, parent, **kwargs):
        self.theme = ModernTheme()
        
        super().__init__(parent, **kwargs)
        self.configure_style()
    
    def configure_style(self):
        """Configure combobox appearance"""
        theme = self.theme.get_theme()
        
        self.configure(
            font=ModernFonts.BODY,
            style="Modern.TCombobox"
        )

class StatusIndicator(tk.Frame):
    """Modern status indicator with color coding"""
    
    def __init__(self, parent, status: str = "inactive", **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = ModernTheme()
        self.status = status
        self.create_indicator()
    
    def create_indicator(self):
        """Create status indicator"""
        theme = self.theme.get_theme()
        
        # Status circle
        self.circle = tk.Canvas(
            self,
            width=12,
            height=12,
            bg=theme["primary"],
            highlightthickness=0
        )
        self.circle.pack(side="left", padx=(0, 5))
        
        # Status label
        self.label = tk.Label(
            self,
            text=self.status.upper(),
            font=ModernFonts.SMALL,
            bg=theme["primary"],
            fg=theme["text_secondary"]
        )
        self.label.pack(side="left")
        
        self.update_status(self.status)
    
    def update_status(self, status: str):
        """Update status indicator"""
        theme = self.theme.get_theme()
        self.status = status
        
        # Clear canvas
        self.circle.delete("all")
        
        # All status indicators use the same grey color scheme
        if status == "active":
            color = theme["accent"]
        elif status == "error":
            color = theme["accent"]
        elif status == "warning":
            color = theme["accent"]
        elif status == "loading":
            color = theme["accent"]
        else:  # inactive
            color = theme["text_secondary"]
        
        # Draw circle
        self.circle.create_oval(2, 2, 10, 10, fill=color, outline="")
        
        # Update label
        self.label.configure(
            text=status.upper(),
            fg=color
        )

class ProgressBar(tk.Frame):
    """Modern progress bar"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = ModernTheme()
        self.progress = 0
        self.create_progress_bar()
    
    def create_progress_bar(self):
        """Create progress bar"""
        theme = self.theme.get_theme()
        
        # Background frame
        self.bg_frame = tk.Frame(
            self,
            bg=theme["secondary"],
            height=6,
            relief="flat"
        )
        self.bg_frame.pack(fill="x")
        
        # Progress frame
        self.progress_frame = tk.Frame(
            self.bg_frame,
            bg=theme["accent"],
            height=6
        )
        self.progress_frame.pack(side="left", fill="y")
    
    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress = max(0, min(100, value))
        
        # Calculate width
        width = int((self.progress / 100) * self.bg_frame.winfo_width())
        self.progress_frame.configure(width=width)

class AccountCard(ModernCard):
    """Account information card"""
    
    def __init__(self, parent, account_name: str, account_type: str, **kwargs):
        super().__init__(parent, title=f"{account_type} Account", **kwargs)
        self.account_name = account_name
        self.account_type = account_type
        self.create_account_info()
    
    def create_account_info(self):
        """Create account information display"""
        theme = self.theme.get_theme()
        
        # Account icon and name
        icon_frame = tk.Frame(self.content_frame, bg=theme["card"])
        icon_frame.pack(fill="x", pady=(0, 10))
        
        # Account icon
        icon_label = tk.Label(
            icon_frame,
            text=ModernIcons.MASTER if self.account_type == "MASTER" else ModernIcons.CHILD,
            font=('Segoe UI', 20),
            bg=theme["card"],
            fg=theme["accent"]
        )
        icon_label.pack(side="left")
        
        # Account name
        name_label = tk.Label(
            icon_frame,
            text=self.account_name,
            font=ModernFonts.SUBTITLE,
            bg=theme["card"],
            fg=theme["text"]
        )
        name_label.pack(side="left", padx=(10, 0))
        
        # Status indicator
        self.status_indicator = StatusIndicator(
            self.content_frame,
            status="inactive"
        )
        self.status_indicator.pack(fill="x", pady=(0, 10))
        
        # Action buttons
        self.create_action_buttons()
    
    def create_action_buttons(self):
        """Create action buttons for account"""
        button_frame = tk.Frame(self.content_frame, bg=self.theme.get_theme()["card"])
        button_frame.pack(fill="x")
        
        # Login button
        self.login_btn = ModernButton(
            button_frame,
            text="Login",
            icon=ModernIcons.LOGIN,
            style="primary",
            command=self.on_login
        )
        self.login_btn.pack(side="left", padx=(0, 5))
        
        # Status button
        self.status_btn = ModernButton(
            button_frame,
            text="Status",
            icon=ModernIcons.STATUS,
            style="primary",
            command=self.on_status
        )
        self.status_btn.pack(side="left", padx=5)
        
        # MTM button
        self.mtm_btn = ModernButton(
            button_frame,
            text="MTM",
            icon=ModernIcons.CHART,
            style="primary",
            command=self.on_mtm
        )
        self.mtm_btn.pack(side="left", padx=5)
    
    def on_login(self):
        """Handle login button click"""
        pass  # Override in parent
    
    def on_status(self):
        """Handle status button click"""
        pass  # Override in parent
    
    def on_mtm(self):
        """Handle MTM button click"""
        pass  # Override in parent
    
    def update_status(self, status: str):
        """Update account status"""
        self.status_indicator.update_status(status)
    
    def update_name(self, name: str):
        """Update account name"""
        self.account_name = name
        # Update the name label
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and child.cget("font") == ModernFonts.SUBTITLE:
                        child.configure(text=name)
                        break

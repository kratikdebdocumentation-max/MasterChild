"""
Modern theme system for PyQt6 Trading Application
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
import qdarkstyle

class ThemeManager(QObject):
    """Modern theme management system"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes = {
            "light": {
                "primary": "#f8f9fa",
                "secondary": "#e9ecef",
                "accent": "#007bff",
                "accent_hover": "#0056b3",
                "text": "#212529",
                "text_secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "border": "#dee2e6",
                "hover": "#e9ecef",
                "card": "#ffffff",
                "input_bg": "#ffffff",
                "input_border": "#ced4da",
                "button_bg": "#6c757d",
                "button_hover": "#5a6268",
                "button_text": "#ffffff"
            },
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
            }
        }
    
    def get_theme(self, theme_name=None):
        """Get theme colors"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["light"])
    
    def set_theme(self, theme_name):
        """Set current theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme_changed.emit(theme_name)
    
    def apply_theme(self, app):
        """Apply theme to application"""
        if self.current_theme == "dark":
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        else:
            app.setStyleSheet(self.get_light_theme_stylesheet())
    
    def get_light_theme_stylesheet(self):
        """Get light theme stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
                color: #212529;
            }
            
            QWidget {
                background-color: #f5f5f5;
                color: #212529;
            }
            
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
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
            }
            
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
            
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #ffffff;
            }
            
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            
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
    
    def get_button_style(self, style="primary"):
        """Get button style based on type"""
        theme = self.get_theme()
        
        if style == "success":
            return f"""
                QPushButton {{
                    background-color: {theme["success"]};
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #218838;
                }}
                QPushButton:pressed {{
                    background-color: #1e7e34;
                }}
            """
        elif style == "danger":
            return f"""
                QPushButton {{
                    background-color: {theme["danger"]};
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """
        elif style == "warning":
            return f"""
                QPushButton {{
                    background-color: {theme["warning"]};
                    color: #212529;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #e0a800;
                }}
                QPushButton:pressed {{
                    background-color: #d39e00;
                }}
            """
        else:  # primary
            return f"""
                QPushButton {{
                    background-color: {theme["button_bg"]};
                    color: {theme["button_text"]};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {theme["button_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: #495057;
                }}
            """

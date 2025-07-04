import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Callable, Optional


class UIManager:
    """
    A utility class to manage UI elements, provide consistent styling,
    and handle common UI operations.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the UI manager.
        
        Args:
            root: The root Tk window
        """
        self.root = root
        self.tooltips: Dict[tk.Widget, ToolTip] = {}
        self._setup_styles()
    
    def _setup_styles(self):
        """
        Set up consistent styles for UI elements.
        """
        style = ttk.Style()
        
        # Configure common element styles
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=2)
        style.configure('TFrame', padding=5)
        style.configure('TLabelframe', padding=5)
        
        # Create custom styles
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('SubHeader.TLabel', font=('Helvetica', 12))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
        # Create custom button styles
        style.configure('Primary.TButton', font=('Helvetica', 10, 'bold'))
    
    def create_tooltip(self, widget: tk.Widget, text: str):
        """
        Create a tooltip for a widget.
        
        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text
        """
        tooltip = ToolTip(widget, text)
        self.tooltips[widget] = tooltip
    
    def show_busy_cursor(self):
        """
        Show a busy cursor for the entire application.
        """
        self.root.config(cursor="watch")
        self.root.update()
    
    def restore_cursor(self):
        """
        Restore the default cursor.
        """
        self.root.config(cursor="")
        self.root.update()
    
    def run_with_progress(self, func: Callable, message: str = "Processing..."):
        """
        Run a function with a progress indicator.
        
        Args:
            func: The function to run
            message: The message to display during processing
        """
        # Create a progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Processing")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)  # Make it float on top of the main window
        
        # Center the window
        progress_window.withdraw()  # Hide initially to calculate position
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")
        progress_window.deiconify()  # Show again
        
        # Add message and progress bar
        tk.Label(progress_window, text=message, padx=20, pady=10).pack()
        progress_bar = ttk.Progressbar(progress_window, mode="indeterminate", length=250)
        progress_bar.pack(padx=20, pady=10)
        progress_bar.start(10)  # Start the animation
        
        # Update the UI
        self.root.update()
        
        try:
            # Run the function
            result = func()
            return result
        finally:
            # Clean up
            progress_bar.stop()
            progress_window.destroy()
            self.root.update()
    
    def confirm_action(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
            
        Returns:
            True if confirmed, False otherwise
        """
        return messagebox.askyesno(title, message)
    
    def show_error(self, title: str, message: str):
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Information message
        """
        messagebox.showinfo(title, message)
    
    def validate_date_format(self, date_str: str) -> bool:
        """
        Validate a date string in YYYY-MM-DD format.
        
        Args:
            date_str: The date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parts = date_str.split("-")
            if len(parts) != 3:
                return False
                
            year, month, day = map(int, parts)
            
            # Basic validation
            if not (1900 <= year <= 2100):
                return False
                
            if not (1 <= month <= 12):
                return False
                
            if not (1 <= day <= 31):
                return False
                
            # Additional validation for specific months
            days_in_month = [0, 31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                           
            if day > days_in_month[month]:
                return False
                
            return True
        except Exception:
            return False


class ToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget: tk.Widget, text: str):
        """
        Initialize the tooltip.
        
        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text
        """
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        
        # Bind events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """
        Display the tooltip.
        """
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(self.tooltip_window, text=self.text, background="#FFFFCC", 
                       relief="solid", borderwidth=1, padx=5, pady=2)
        label.pack()
    
    def hide_tooltip(self, event=None):
        """
        Hide the tooltip.
        """
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

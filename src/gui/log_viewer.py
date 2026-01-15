"""
Log Viewer - Real-time log display widget
"""
import tkinter as tk
from tkinter import scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class LogViewer(ttk.Frame):
    """Real-time log viewer widget."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize log viewer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        
        self._setup_ui()
        self._auto_scroll = True
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(header_frame, text="Nhật Ký", font=("", 10, "bold")).pack(side=LEFT)
        
        # Clear button
        clear_btn = ttk.Button(
            header_frame, 
            text="Xóa", 
            bootstyle="outline",
            command=self.clear
        )
        clear_btn.pack(side=RIGHT, padx=2)
        
        # Auto-scroll toggle
        self._auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(
            header_frame,
            text="Tự cuộn",
            variable=self._auto_scroll_var,
            bootstyle="round-toggle"
        )
        auto_scroll_cb.pack(side=RIGHT, padx=5)
        
        # Log text area
        self._log_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED,
            height=15
        )
        self._log_text.pack(fill=BOTH, expand=True)
        
        # Configure tags for different log levels
        self._log_text.tag_configure("INFO", foreground="#2196F3")
        self._log_text.tag_configure("DEBUG", foreground="#9E9E9E")
        self._log_text.tag_configure("WARN", foreground="#FF9800")
        self._log_text.tag_configure("ERROR", foreground="#F44336")
        self._log_text.tag_configure("OK", foreground="#4CAF50")
    
    def append_log(self, message: str):
        """
        Append a log message.
        
        Args:
            message: Log message to append
        """
        self._log_text.configure(state=tk.NORMAL)
        
        # Determine tag based on log level
        tag = None
        if "[INFO]" in message:
            tag = "INFO"
        elif "[DEBUG]" in message:
            tag = "DEBUG"
        elif "[WARN]" in message:
            tag = "WARN"
        elif "[ERROR]" in message:
            tag = "ERROR"
        elif "[OK]" in message:
            tag = "OK"
        
        # Insert message
        if tag:
            self._log_text.insert(tk.END, message + "\n", tag)
        else:
            self._log_text.insert(tk.END, message + "\n")
        
        self._log_text.configure(state=tk.DISABLED)
        
        # Auto-scroll to bottom
        if self._auto_scroll_var.get():
            self._log_text.see(tk.END)
    
    def clear(self):
        """Clear all log messages."""
        self._log_text.configure(state=tk.NORMAL)
        self._log_text.delete(1.0, tk.END)
        self._log_text.configure(state=tk.DISABLED)
    
    def get_log_callback(self):
        """Get callback function for logger."""
        def callback(message: str):
            # Schedule update on main thread
            self.after(0, lambda: self.append_log(message))
        return callback

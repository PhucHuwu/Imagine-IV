"""
Config Tab - Settings page
"""
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import get_config


class ConfigTab(ttk.Frame):
    """Configuration settings tab."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize config tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        
        self.config = get_config()
        self._vars = {}
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Main container with scrollbar
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        
        self._content_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        canvas.create_window((0, 0), window=self._content_frame, anchor=NW)
        
        self._content_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Thread Settings Section
        self._create_section("Cấu Hình Luồng")
        self._create_spinbox("thread_count", "Số luồng", 1, 20)
        
        # Image Settings Section
        self._create_section("Cấu Hình Ảnh")
        self._create_spinbox("images_per_download", "Số ảnh tải mỗi lần", 1, 20)
        self._create_spinbox("batch_size", "Kích thước batch", 1, 100)
        
        # Timing Section
        self._create_section("Thời Gian")
        self._create_spinbox("delay_ms", "Độ trễ (ms)", 100, 10000, increment=100)
        self._create_spinbox("timeout_seconds", "Thời gian chờ (giây)", 10, 300)
        
        # Chrome Section
        self._create_section("Chrome")
        self._create_combobox("chrome_position", "Vị trí cửa sổ", ["left", "right"])
        
        # Directories Section
        self._create_section("Thư Mục")
        self._create_path_input("images_dir", "Thư mục ảnh")
        self._create_path_input("videos_dir", "Thư mục video")
        self._create_path_input("profiles_dir", "Thư mục Chrome profiles")
        
        # OpenRouter Section
        self._create_section("OpenRouter API")
        self._create_entry("openrouter_api_key", "API Key", show="*")
        self._create_entry("openrouter_model", "Model")
        
        # Info label
        info_frame = ttk.Frame(self._content_frame)
        info_frame.pack(fill=X, padx=10, pady=5)
        
        info_label = ttk.Label(
            info_frame,
            text="Vào openrouter.ai/models > Lọc: Text input/output, Free pricing",
            font=("", 8),
            foreground="gray"
        )
        info_label.pack(anchor=W)
        
        # Logging Section
        self._create_section("Nhật Ký")
        self._create_checkbox("verbose_logging", "Log chi tiết")
    
    def _create_section(self, title: str):
        """Create a section header."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=10, pady=(15, 5))
        
        ttk.Label(
            frame, 
            text=title, 
            font=("", 11, "bold")
        ).pack(anchor=W)
        
        ttk.Separator(frame, orient=HORIZONTAL).pack(fill=X, pady=5)
    
    def _create_spinbox(self, key: str, label: str, from_: int, to: int, 
                        increment: int = 1):
        """Create a spinbox control."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=20, pady=3)
        
        ttk.Label(frame, text=label, width=25).pack(side=LEFT)
        
        var = tk.IntVar()
        self._vars[key] = var
        
        spinbox = ttk.Spinbox(
            frame,
            from_=from_,
            to=to,
            textvariable=var,
            width=10,
            increment=increment
        )
        spinbox.pack(side=LEFT, padx=5)
        
        # Auto-save on change
        var.trace_add("write", lambda *args, k=key: self._on_value_change(k))
    
    def _create_combobox(self, key: str, label: str, values: list):
        """Create a combobox control."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=20, pady=3)
        
        ttk.Label(frame, text=label, width=25).pack(side=LEFT)
        
        var = tk.StringVar()
        self._vars[key] = var
        
        combo = ttk.Combobox(
            frame,
            textvariable=var,
            values=values,
            state="readonly",
            width=15
        )
        combo.pack(side=LEFT, padx=5)
        
        combo.bind("<<ComboboxSelected>>", lambda e, k=key: self._on_value_change(k))
    
    def _create_entry(self, key: str, label: str, show: str = None):
        """Create an entry control."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=20, pady=3)
        
        ttk.Label(frame, text=label, width=25).pack(side=LEFT)
        
        var = tk.StringVar()
        self._vars[key] = var
        
        entry = ttk.Entry(frame, textvariable=var, width=40, show=show or "")
        entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # Auto-save on focus out
        entry.bind("<FocusOut>", lambda e, k=key: self._on_value_change(k))
    
    def _create_path_input(self, key: str, label: str):
        """Create a path input with browse button."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=20, pady=3)
        
        ttk.Label(frame, text=label, width=25).pack(side=LEFT)
        
        var = tk.StringVar()
        self._vars[key] = var
        
        entry = ttk.Entry(frame, textvariable=var, width=30)
        entry.pack(side=LEFT, padx=5)
        
        browse_btn = ttk.Button(
            frame,
            text="Chọn",
            bootstyle="outline",
            command=lambda k=key, v=var: self._browse_folder(k, v)
        )
        browse_btn.pack(side=LEFT, padx=2)
        
        entry.bind("<FocusOut>", lambda e, k=key: self._on_value_change(k))
    
    def _create_checkbox(self, key: str, label: str):
        """Create a checkbox control."""
        frame = ttk.Frame(self._content_frame)
        frame.pack(fill=X, padx=20, pady=3)
        
        var = tk.BooleanVar()
        self._vars[key] = var
        
        cb = ttk.Checkbutton(
            frame,
            text=label,
            variable=var,
            bootstyle="round-toggle"
        )
        cb.pack(anchor=W)
        
        var.trace_add("write", lambda *args, k=key: self._on_value_change(k))
    
    def _browse_folder(self, key: str, var: tk.StringVar):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
            self._on_value_change(key)
    
    def _load_config(self):
        """Load config values into controls."""
        for key, var in self._vars.items():
            value = self.config.get(key)
            if value is not None:
                var.set(value)
    
    def _on_value_change(self, key: str):
        """Handle value change - auto-save."""
        if key not in self._vars:
            return
        
        var = self._vars[key]
        value = var.get()
        
        # Save to config
        self.config.set(key, value)

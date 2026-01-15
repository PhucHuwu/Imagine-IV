"""
Image Tab - Image generation controls
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import get_config


class ImageTab(ttk.Frame):
    """Image generation tab."""
    
    def __init__(self, parent, on_start=None, on_stop=None, **kwargs):
        """
        Initialize image tab.
        
        Args:
            parent: Parent widget
            on_start: Callback when start is clicked
            on_stop: Callback when stop is clicked
        """
        super().__init__(parent, **kwargs)
        
        self.config = get_config()
        self._on_start = on_start
        self._on_stop = on_stop
        self._running = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=X, padx=20, pady=10)
        
        ttk.Label(
            title_frame,
            text="Tạo Ảnh",
            font=("", 16, "bold")
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text="Tạo ảnh tự động với Grok Imagine",
            foreground="gray"
        ).pack(anchor=W)
        
        # Settings frame
        settings_frame = ttk.Labelframe(self, text="Cài Đặt")
        settings_frame.pack(fill=X, padx=20, pady=10)
        settings_inner = ttk.Frame(settings_frame, padding=15)
        settings_inner.pack(fill=BOTH, expand=True)
        
        # Images per batch
        img_frame = ttk.Frame(settings_inner)
        img_frame.pack(fill=X, pady=5)
        
        ttk.Label(img_frame, text="Số ảnh tải về:", width=20).pack(side=LEFT)
        
        self._images_var = tk.IntVar(value=self.config.get("images_per_download", 4))
        spinbox = ttk.Spinbox(
            img_frame,
            from_=1,
            to=20,
            textvariable=self._images_var,
            width=10
        )
        spinbox.pack(side=LEFT, padx=5)
        
        # Batch size
        batch_frame = ttk.Frame(settings_inner)
        batch_frame.pack(fill=X, pady=5)
        
        ttk.Label(batch_frame, text="Số lượng mỗi batch:", width=20).pack(side=LEFT)
        
        self._batch_var = tk.IntVar(value=self.config.get("batch_size", 10))
        batch_spin = ttk.Spinbox(
            batch_frame,
            from_=1,
            to=100,
            textvariable=self._batch_var,
            width=10
        )
        batch_spin.pack(side=LEFT, padx=5)
        
        # Status frame
        status_outer = ttk.Labelframe(self, text="Trạng Thái")
        status_outer.pack(fill=X, padx=20, pady=10)
        status_frame = ttk.Frame(status_outer, padding=15)
        status_frame.pack(fill=BOTH, expand=True)
        
        self._status_label = ttk.Label(
            status_frame,
            text="Sẵn sàng",
            font=("", 12)
        )
        self._status_label.pack(anchor=W)
        
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(
            status_frame,
            variable=self._progress_var,
            maximum=100,
            bootstyle="success-striped"
        )
        self._progress.pack(fill=X, pady=10)
        
        self._count_label = ttk.Label(
            status_frame,
            text="0 / 0",
            foreground="gray"
        )
        self._count_label.pack(anchor=W)
        
        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, padx=20, pady=20)
        
        self._start_btn = ttk.Button(
            btn_frame,
            text="Bắt Đầu",
            bootstyle="success",
            command=self._on_start_click,
            width=15
        )
        self._start_btn.pack(side=LEFT, padx=5)
        
        self._stop_btn = ttk.Button(
            btn_frame,
            text="Dừng",
            bootstyle="danger",
            command=self._on_stop_click,
            width=15,
            state=DISABLED
        )
        self._stop_btn.pack(side=LEFT, padx=5)
    
    def _on_start_click(self):
        """Handle start button click."""
        if self._on_start:
            # Save settings
            self.config.set("images_per_download", self._images_var.get())
            self.config.set("batch_size", self._batch_var.get())
            
            self._running = True
            self._start_btn.configure(state=DISABLED)
            self._stop_btn.configure(state=NORMAL)
            self._status_label.configure(text="Đang chạy...")
            
            self._on_start("anh", {
                "images_per_download": self._images_var.get(),
                "batch_count": self._batch_var.get()
            })
    
    def _on_stop_click(self):
        """Handle stop button click."""
        if self._on_stop:
            self._running = False
            self._stop_btn.configure(state=DISABLED)
            self._status_label.configure(text="Đang dừng...")
            self._on_stop()
    
    def update_progress(self, current: int, total: int):
        """Update progress bar."""
        if total > 0:
            percent = (current / total) * 100
            self._progress_var.set(percent)
        
        self._count_label.configure(text=f"{current} / {total}")
    
    def update_status(self, status: str):
        """Update status label."""
        self._status_label.configure(text=status)
    
    def on_complete(self):
        """Called when generation is complete."""
        self._running = False
        self._start_btn.configure(state=NORMAL)
        self._stop_btn.configure(state=DISABLED)
        self._status_label.configure(text="Hoàn thành")
    
    def on_error(self, message: str):
        """Called on error."""
        self._running = False
        self._start_btn.configure(state=NORMAL)
        self._stop_btn.configure(state=DISABLED)
        self._status_label.configure(text=f"Lỗi: {message}")

"""
Image Tab - Image generation controls
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import get_config
from ..logger import get_logger
from .prompt_card import PromptCardsContainer


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
        self.logger = get_logger()
        self._on_start = on_start
        self._on_stop = on_stop
        self._running = False
        
        self._setup_ui()
        self._load_prompts_from_config()
    
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
        
        # Auto-prompt toggle checkbox
        auto_prompt_frame = ttk.Frame(settings_inner)
        auto_prompt_frame.pack(fill=X, pady=5)
        
        self._auto_prompt_var = tk.BooleanVar(value=self.config.get("auto_prompt_enabled", True))
        self._auto_prompt_check = ttk.Checkbutton(
            auto_prompt_frame,
            text="Tạo prompt tự động (OpenRouter)",
            variable=self._auto_prompt_var,
            bootstyle="success-round-toggle",
            command=self._on_auto_prompt_toggle
        )
        self._auto_prompt_check.pack(side=LEFT)
        
        # Batch size (shown when auto-prompt is enabled)
        self._batch_frame = ttk.Frame(settings_inner)
        self._batch_frame.pack(fill=X, pady=5)
        
        ttk.Label(self._batch_frame, text="Số lần tạo (batch):", width=22).pack(side=LEFT)
        
        self._batch_var = tk.IntVar(value=self.config.get("batch_size", 10))
        self._batch_spin = ttk.Spinbox(
            self._batch_frame,
            from_=1,
            to=100,
            textvariable=self._batch_var,
            width=10
        )
        self._batch_spin.pack(side=LEFT, padx=5)
        
        # Auto-save on change
        self._batch_var.trace_add("write", lambda *args: self._save_setting("batch_size", self._batch_var))
        
        ttk.Label(self._batch_frame, text="lần", foreground="gray").pack(side=LEFT)
        
        # Info label
        self._info_frame = ttk.Frame(settings_inner)
        self._info_frame.pack(fill=X, pady=5)
        ttk.Label(self._info_frame, text="Mỗi batch tải tối đa 12 ảnh", foreground="gray").pack(anchor=W)
        
        # Manual prompts section (shown when auto-prompt is disabled)
        self._manual_prompts_frame = ttk.Labelframe(self, text="Prompt Thủ Công")
        self._manual_prompts_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self._prompts_container = PromptCardsContainer(
            self._manual_prompts_frame,
            show_video2=False,
            on_change=self._on_prompts_change
        )
        self._prompts_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
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
        
        # Update UI based on initial toggle state
        self._update_ui_for_auto_prompt()
    
    def _load_prompts_from_config(self):
        """Load prompts từ config."""
        prompts = self.config.get("manual_prompts", [])
        if prompts:
            self._prompts_container.set_prompts(prompts)
    
    def _on_auto_prompt_toggle(self):
        """Xử lý khi toggle auto-prompt checkbox."""
        enabled = self._auto_prompt_var.get()
        self.config.set("auto_prompt_enabled", enabled)
        self._update_ui_for_auto_prompt()
        self.logger.info(f"Chế độ tạo prompt tự động: {'Bật' if enabled else 'Tắt'}")
    
    def _update_ui_for_auto_prompt(self):
        """Cập nhật UI dựa trên trạng thái auto-prompt."""
        if self._auto_prompt_var.get():
            # Auto-prompt enabled: show batch settings, hide manual prompts
            self._batch_frame.pack(fill=X, pady=5)
            self._info_frame.pack(fill=X, pady=5)
            self._manual_prompts_frame.pack_forget()
        else:
            # Auto-prompt disabled: hide batch settings, show manual prompts
            self._batch_frame.pack_forget()
            self._info_frame.pack_forget()
            self._manual_prompts_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    def _on_prompts_change(self):
        """Xử lý khi prompts thay đổi."""
        prompts = self._prompts_container.get_all_prompts()
        self.config.set("manual_prompts", prompts)
    
    def _save_setting(self, key: str, var: tk.IntVar):
        """Auto-save setting when value changes."""
        try:
            value = int(var.get())
            self.config.set(key, value)
        except (ValueError, tk.TclError):
            # Ignore invalid values (e.g., empty string during typing)
            pass
    
    def _on_start_click(self):
        """Handle start button click."""
        if self._on_start:
            auto_prompt = self._auto_prompt_var.get()
            
            if auto_prompt:
                # Auto mode: use batch size
                batch_size = int(self._batch_var.get())
                self.config.set("batch_size", batch_size)
                self.logger.info(f"Đã lưu cài đặt: batch_size={batch_size}")
            else:
                # Manual mode: use prompt count as batch size
                prompts = self._prompts_container.get_all_prompts()
                batch_size = len(prompts)
                
                if batch_size == 0:
                    self.logger.error("Vui lòng thêm ít nhất 1 prompt")
                    return
                
                self.config.set("manual_prompts", prompts)
                self.logger.info(f"Sử dụng {batch_size} prompt thủ công")
            
            self._running = True
            self._start_btn.configure(state=DISABLED)
            self._stop_btn.configure(state=NORMAL)
            self._status_label.configure(text="Đang chạy...")
            
            self._on_start("anh", {
                "batch_count": batch_size,
                "auto_prompt": auto_prompt
            })
    
    def _on_stop_click(self):
        """Handle stop button click."""
        if self._on_stop:
            self._running = False
            self._stop_btn.configure(state=DISABLED)
            self._status_label.configure(text="Đang dừng...")
            self._on_stop()
    
    def set_buttons_enabled(self, enabled: bool, allow_stop: bool = False):
        """Enable or disable buttons based on app state.
        
        Args:
            enabled: Whether to enable start button
            allow_stop: Whether to allow stop button (when generating)
        """
        if enabled:
            self._start_btn.configure(state=NORMAL)
            self._stop_btn.configure(state=DISABLED)
        else:
            self._start_btn.configure(state=DISABLED)
            if allow_stop and self._running:
                self._stop_btn.configure(state=NORMAL)
            else:
                self._stop_btn.configure(state=DISABLED)
    
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

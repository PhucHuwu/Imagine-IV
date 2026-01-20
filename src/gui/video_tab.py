"""
Video Tab - Video generation controls
"""
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import get_config
from ..logger import get_logger
from .prompt_card import PromptCardsContainer
from .scrollable_frame import ScrollableFrame


class VideoTab(ttk.Frame):
    """Video generation tab."""
    
    def __init__(self, parent, on_start=None, on_stop=None, **kwargs):
        """
        Initialize video tab.
        
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
        # Create scrollable container
        self._scrollable = ScrollableFrame(self)
        self._scrollable.pack(fill=BOTH, expand=True)
        
        # Use inner frame for all content
        container = self._scrollable.inner
        
        # Title
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=X, padx=20, pady=10)
        
        ttk.Label(
            title_frame,
            text="Tạo Video",
            font=("", 16, "bold")
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text="Tạo video với Grok Imagine",
            foreground="gray"
        ).pack(anchor=W)
        
        # Duration selection
        duration_outer = ttk.Labelframe(container, text="Thời Lượng Video")
        duration_outer.pack(fill=X, padx=20, pady=10)
        duration_frame = ttk.Frame(duration_outer, padding=15)
        duration_frame.pack(fill=BOTH, expand=True)
        
        self._duration_var = tk.IntVar(value=self.config.get("video_duration", 6))
        
        ttk.Radiobutton(
            duration_frame,
            text="6 giây (1 video)",
            variable=self._duration_var,
            value=6,
            bootstyle="info",
            command=self._on_duration_change
        ).pack(side=LEFT, padx=10)
        
        ttk.Radiobutton(
            duration_frame,
            text="12 giây (ghép 2 video 6s)",
            variable=self._duration_var,
            value=12,
            bootstyle="info",
            command=self._on_duration_change
        ).pack(side=LEFT, padx=10)
        
        # Mode selection
        mode_outer = ttk.Labelframe(container, text="Chế Độ")
        mode_outer.pack(fill=X, padx=20, pady=10)
        mode_frame = ttk.Frame(mode_outer, padding=15)
        mode_frame.pack(fill=BOTH, expand=True)
        
        self._mode_var = tk.StringVar(value="generate")
        
        ttk.Radiobutton(
            mode_frame,
            text="Option A: Tạo ảnh mới + video",
            variable=self._mode_var,
            value="generate",
            bootstyle="success"
        ).pack(anchor=W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="Option B: Dùng ảnh từ thư mục",
            variable=self._mode_var,
            value="folder",
            bootstyle="info"
        ).pack(anchor=W, pady=2)
        
        # Folder selection (for Option B)
        folder_frame = ttk.Frame(mode_frame)
        folder_frame.pack(fill=X, pady=10)
        
        ttk.Label(folder_frame, text="Thư mục ảnh:").pack(side=LEFT)
        
        self._folder_var = tk.StringVar(value=self.config.get("images_dir", "./images/"))
        folder_entry = ttk.Entry(folder_frame, textvariable=self._folder_var, width=30)
        folder_entry.pack(side=LEFT, padx=5)
        
        browse_btn = ttk.Button(
            folder_frame,
            text="Chọn",
            bootstyle="outline",
            command=self._browse_folder
        )
        browse_btn.pack(side=LEFT)
        
        # Settings
        settings_outer = ttk.Labelframe(container, text="Cài Đặt")
        settings_outer.pack(fill=X, padx=20, pady=10)
        settings_frame = ttk.Frame(settings_outer, padding=15)
        settings_frame.pack(fill=BOTH, expand=True)
        
        # Auto-prompt toggle
        auto_prompt_frame = ttk.Frame(settings_frame)
        auto_prompt_frame.pack(fill=X, pady=5)
        
        self._auto_prompt_var = tk.BooleanVar(value=self.config.get("video_auto_prompt_enabled", True))
        self._auto_prompt_check = ttk.Checkbutton(
            auto_prompt_frame,
            text="Tạo prompt tự động (OpenRouter)",
            variable=self._auto_prompt_var,
            bootstyle="success-round-toggle",
            command=self._on_auto_prompt_toggle
        )
        self._auto_prompt_check.pack(side=LEFT)
        
        # Batch size (shown when auto-prompt is enabled)
        self._batch_frame = ttk.Frame(settings_frame)
        self._batch_frame.pack(fill=X, pady=5)
        
        ttk.Label(self._batch_frame, text="Số video tạo:", width=20).pack(side=LEFT)
        
        self._batch_var = tk.IntVar(value=self.config.get("batch_size", 10))
        batch_spin = ttk.Spinbox(
            self._batch_frame,
            from_=1,
            to=100,
            textvariable=self._batch_var,
            width=10
        )
        batch_spin.pack(side=LEFT, padx=5)
        
        # Manual prompts section (shown when auto-prompt is disabled)
        self._manual_prompts_frame = ttk.Labelframe(container, text="Prompt Thủ Công")
        self._manual_prompts_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Prompt container - show_video2 depends on duration
        show_video2 = self._duration_var.get() == 12
        self._prompts_container = PromptCardsContainer(
            self._manual_prompts_frame,
            show_video2=show_video2,
            on_change=self._on_prompts_change
        )
        self._prompts_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Status frame
        status_outer = ttk.Labelframe(container, text="Trạng Thái")
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
            bootstyle="info-striped"
        )
        self._progress.pack(fill=X, pady=10)
        
        self._count_label = ttk.Label(
            status_frame,
            text="0 / 0",
            foreground="gray"
        )
        self._count_label.pack(anchor=W)
        
        # Control buttons
        btn_frame = ttk.Frame(container)
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
        
        # Update UI based on initial states
        self._update_ui_for_auto_prompt()
    
    def _load_prompts_from_config(self):
        """Load prompts từ config."""
        prompts = self.config.get("video_manual_prompts", [])
        if prompts:
            self._prompts_container.set_prompts(prompts)
    
    def _on_duration_change(self):
        """Xử lý khi thay đổi thời lượng video."""
        duration = self._duration_var.get()
        self.config.set("video_duration", duration)
        
        # Update prompt cards to show 1 or 2 text areas
        show_video2 = duration == 12
        self._prompts_container.set_show_video2(show_video2)
        
        self.logger.info(f"Đã chọn thời lượng video: {duration}s")
    
    def _on_auto_prompt_toggle(self):
        """Xử lý khi toggle auto-prompt checkbox."""
        enabled = self._auto_prompt_var.get()
        self.config.set("video_auto_prompt_enabled", enabled)
        self._update_ui_for_auto_prompt()
        self.logger.info(f"Chế độ tạo prompt tự động: {'Bật' if enabled else 'Tắt'}")
    
    def _update_ui_for_auto_prompt(self):
        """Cập nhật UI dựa trên trạng thái auto-prompt."""
        if self._auto_prompt_var.get():
            # Auto-prompt enabled: show batch settings, hide manual prompts
            self._batch_frame.pack(fill=X, pady=5)
            self._manual_prompts_frame.pack_forget()
        else:
            # Auto-prompt disabled: hide batch settings, show manual prompts
            self._batch_frame.pack_forget()
            self._manual_prompts_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    def _on_prompts_change(self):
        """Xử lý khi prompts thay đổi."""
        prompts = self._prompts_container.get_all_prompts()
        self.config.set("video_manual_prompts", prompts)
    
    def _browse_folder(self):
        """Open folder browser."""
        folder = filedialog.askdirectory()
        if folder:
            self._folder_var.set(folder)
    
    def _on_start_click(self):
        """Handle start button click."""
        if self._on_start:
            auto_prompt = self._auto_prompt_var.get()
            duration = self._duration_var.get()
            
            if auto_prompt:
                # Auto mode: use batch size
                batch_size = self._batch_var.get()
            else:
                # Manual mode: use prompt count as batch size
                prompts = self._prompts_container.get_all_prompts()
                batch_size = len(prompts)
                
                if batch_size == 0:
                    self.logger.error("Vui lòng thêm ít nhất 1 prompt")
                    return
                
                self.config.set("video_manual_prompts", prompts)
                self.logger.info(f"Sử dụng {batch_size} prompt thủ công")
            
            self._running = True
            self._start_btn.configure(state=DISABLED)
            self._stop_btn.configure(state=NORMAL)
            self._status_label.configure(text="Đang chạy...")
            
            self._on_start("video", {
                "mode": self._mode_var.get(),
                "folder": self._folder_var.get(),
                "batch_size": batch_size,
                "auto_prompt": auto_prompt,
                "duration": duration
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
    
    def set_buttons_enabled(self, enabled: bool, allow_stop: bool = False):
        """
        Enable or disable buttons.
        
        Args:
            enabled: True to enable, False to disable
            allow_stop: If True and enabled=False, keep stop button enabled
        """
        if enabled:
            self._start_btn.configure(state=NORMAL)
            self._stop_btn.configure(state=DISABLED)
        else:
            self._start_btn.configure(state=DISABLED)
            if allow_stop:
                self._stop_btn.configure(state=NORMAL)
            else:
                self._stop_btn.configure(state=DISABLED)

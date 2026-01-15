"""
Main Window - Application main window
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import get_config
from ..logger import init_logger, get_logger
from ..process_cleaner import get_cleaner

from .log_viewer import LogViewer
from .image_tab import ImageTab
from .video_tab import VideoTab
from .config_tab import ConfigTab


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        self.config = get_config()
        
        # Create main window
        self.root = ttk.Window(
            title="Grok Imagine - Tự Động Hoá Tạo Ảnh/Video",
            themename="darkly",
            size=(1000, 700),
            minsize=(800, 600)
        )
        
        # Center window
        self._center_window()
        
        # Setup logger with GUI callback
        self.log_viewer = None
        self._setup_ui()
        
        # Initialize logger after log viewer is created
        self.logger = init_logger(
            log_dir="./logs/",
            gui_callback=self.log_viewer.get_log_callback(),
            verbose=self.config.get("verbose_logging", True)
        )
        
        # Cleanup orphan processes
        get_cleaner().cleanup_orphans()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.logger.info("Ứng dụng đã khởi động")
    
    def _center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Tabs
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(left_frame, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=True)
        
        # Image tab
        self.image_tab = ImageTab(
            notebook,
            on_start=self._on_start,
            on_stop=self._on_stop
        )
        notebook.add(self.image_tab, text="  Tạo Ảnh  ")
        
        # Video tab
        self.video_tab = VideoTab(
            notebook,
            on_start=self._on_start,
            on_stop=self._on_stop
        )
        notebook.add(self.video_tab, text="  Tạo Video  ")
        
        # Config tab
        self.config_tab = ConfigTab(notebook)
        notebook.add(self.config_tab, text="  Cài Đặt  ")
        
        # Right panel - Log and controls
        right_frame = ttk.Frame(main_frame, width=350)
        right_frame.pack(side=RIGHT, fill=BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Login section
        login_outer = ttk.Labelframe(right_frame, text="Trạng Thái Đăng Nhập")
        login_outer.pack(fill=X, pady=(0, 10))
        login_frame = ttk.Frame(login_outer, padding=10)
        login_frame.pack(fill=BOTH, expand=True)
        
        self._logged_in_var = tk.BooleanVar(value=self.config.get("logged_in", False))
        
        logged_in_cb = ttk.Checkbutton(
            login_frame,
            text="Ghi nhớ đăng nhập",
            variable=self._logged_in_var,
            bootstyle="round-toggle",
            command=self._on_login_toggle
        )
        logged_in_cb.pack(anchor=W)
        
        self._login_btn = ttk.Button(
            login_frame,
            text="Mở Trình Duyệt Để Đăng Nhập",
            bootstyle="warning",
            command=self._on_login_click
        )
        self._login_btn.pack(fill=X, pady=5)
        
        self._confirm_btn = ttk.Button(
            login_frame,
            text="Xác Nhận Đã Đăng Nhập",
            bootstyle="success",
            command=self._on_confirm_login
        )
        self._confirm_btn.pack(fill=X)
        
        # Log viewer
        self.log_viewer = LogViewer(right_frame)
        self.log_viewer.pack(fill=BOTH, expand=True)
        
        # Status bar
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=X, side=BOTTOM, padx=10, pady=5)
        
        self._status_label = ttk.Label(
            status_bar,
            text="Sẵn sàng",
            foreground="gray"
        )
        self._status_label.pack(side=LEFT)
        
        version_label = ttk.Label(
            status_bar,
            text="v1.0.0",
            foreground="gray"
        )
        version_label.pack(side=RIGHT)
    
    def _on_start(self, mode: str, settings: dict):
        """Handle start button from tabs."""
        self.logger.info(f"Dang bat dau tao {mode} voi cai dat: {settings}")
        self._status_label.configure(text=f"Dang tao {mode}...")
        
        # Check if browser is open
        if not (hasattr(self, '_login_browser') and self._login_browser and self._login_browser.is_running()):
            self.logger.error("Trinh duyet chua mo. Hay nhan 'Mo Trinh Duyet De Dang Nhap' truoc!")
            self._status_label.configure(text="Loi: Chua mo trinh duyet")
            return
        
        # Navigate to Grok Imagine
        self._login_browser.navigate("https://grok.com/imagine")
        
        # Zoom browser to 25%
        self._login_browser.set_zoom(25)
        self.logger.info("Da zoom trinh duyet xuong 25%")
        
        if mode == "anh":
            self._start_image_generation(settings)
        elif mode == "video":
            self._start_video_generation(settings)
    
    def _start_image_generation(self, settings: dict):
        """Start image generation workflow."""
        from ..image_generator import ImageGenerator
        
        # Stop existing generator if running
        if hasattr(self, '_image_generator') and self._image_generator and self._image_generator.is_running():
            self.logger.warning("Dang chay, dung truoc...")
            self._image_generator.stop()
            return
        
        # Create and start generator
        self._image_generator = ImageGenerator(
            browser=self._login_browser,
            on_progress=self._on_generation_progress
        )
        
        batch_count = settings.get("batch_count", 10)
        images_per_batch = settings.get("images_per_download", 4)
        
        self._image_generator.start(batch_count=batch_count, images_per_batch=images_per_batch)
    
    def _start_video_generation(self, settings: dict):
        """Start video generation workflow."""
        # TODO: Implement video generation
        self.logger.info("Video generation chua duoc implement")
    
    def _on_generation_progress(self, current: int, total: int, status: str):
        """Handle progress updates from generator."""
        # Update UI in main thread
        self.root.after(0, lambda: self._update_progress_ui(current, total, status))
    
    def _update_progress_ui(self, current: int, total: int, status: str):
        """Update progress in UI (must be called from main thread)."""
        progress_text = f"{status} ({current}/{total})"
        self._status_label.configure(text=progress_text)
        
        # Update progress bar in image tab if exists
        if hasattr(self, 'image_tab') and hasattr(self.image_tab, 'update_progress'):
            self.image_tab.update_progress(current, total)
    
    def _on_stop(self):
        """Handle stop button."""
        self.logger.info("Dang dung...")
        self._status_label.configure(text="Dang dung...")
        
        # Stop image generator if running
        if hasattr(self, '_image_generator') and self._image_generator and self._image_generator.is_running():
            self._image_generator.stop()
        
        self._status_label.configure(text="Da dung")
    
    def _on_login_click(self):
        """Handle login button click - Open browser without navigating."""
        from ..browser_manager import BrowserManager
        
        self.logger.info("Đang mở trình duyệt...")
        
        # Store browser instance for later use
        self._login_browser = BrowserManager(thread_id=1)
        if self._login_browser.start():
            self.logger.info("Trình duyệt đã mở. Hãy đăng nhập Grok thủ công.")
            self.logger.info("Sau khi đăng nhập xong, nhấn 'Xác Nhận Đã Đăng Nhập'")
    
    def _on_confirm_login(self):
        """Handle confirm login button - Navigate to Grok Imagine."""
        self.config.set("logged_in", True)
        self._logged_in_var.set(True)
        
        # Navigate to Grok Imagine after login confirmed
        if hasattr(self, '_login_browser') and self._login_browser and self._login_browser.is_running():
            self._login_browser.navigate("https://grok.com/imagine")
            self.logger.success("Đã xác nhận đăng nhập! Đang chuyển đến Grok Imagine...")
        else:
            self.logger.success("Đã xác nhận đăng nhập!")
    
    def _on_login_toggle(self):
        """Handle login checkbox toggle."""
        self.config.set("logged_in", self._logged_in_var.get())
    
    def _on_close(self):
        """Handle window close."""
        self.logger.info("Đang tắt ứng dụng...")
        
        # Cleanup
        get_cleaner().cleanup_on_exit()
        
        if hasattr(self, 'logger'):
            self.logger.close()
        
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Application entry point."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()

"""
Image Generator - Orchestrate image generation workflow
"""
import time
import threading
from typing import Optional, Callable
from pathlib import Path

from .browser_manager import BrowserManager
from .grok_automation import GrokAutomation
from .prompt_generator import PromptGenerator
from .config import get_config
from .logger import get_logger


class ImageGenerator:
    """Orchestrate the image generation workflow."""
    
    def __init__(self, browser: BrowserManager, on_progress: Optional[Callable] = None):
        """
        Initialize image generator.
        
        Args:
            browser: Browser manager instance
            on_progress: Callback for progress updates (current, total, status)
        """
        self.browser = browser
        self.grok = GrokAutomation(browser)
        self.prompt_gen = PromptGenerator()
        self.config = get_config()
        self.logger = get_logger()
        self.on_progress = on_progress
        
        self._running = False
        self._stop_requested = False
    
    def _update_progress(self, current: int, total: int, status: str):
        """Update progress via callback."""
        if self.on_progress:
            try:
                self.on_progress(current, total, status)
            except Exception:
                pass
    
    def start(self, batch_count: int) -> bool:
        """
        Start image generation.
        
        Args:
            batch_count: Number of batches to generate
            
        Returns:
            True if started successfully
        """
        if self._running:
            self.logger.warning("Đang chạy, không thể bắt đầu lại")
            return False
        
        self._running = True
        self._stop_requested = False
        
        # Run in separate thread
        thread = threading.Thread(
            target=self._generation_loop,
            args=(batch_count,),
            daemon=True
        )
        thread.start()
        
        return True
    
    def stop(self):
        """Request to stop generation."""
        self._stop_requested = True
        self.logger.info("Đang dừng...")
    
    def is_running(self) -> bool:
        """Check if generation is running."""
        return self._running
    
    def _generation_loop(self, batch_count: int):
        """Main generation loop."""
        try:
            # Get output directory
            images_dir = self.config.get_path("images_dir")
            if images_dir is None:
                images_dir = Path("./images")
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Get delay between batches
            delay = self.config.get("delay_between_prompts", 5)
            
            total_downloaded = 0
            
            for batch_idx in range(batch_count):
                if self._stop_requested:
                    self.logger.info("Đã dừng theo yêu cầu")
                    break
                
                # Check for rate limit before proceeding
                if self.grok.check_rate_limit():
                    self.logger.error("Đã đạt rate limit - Dừng toàn bộ quá trình")
                    self._stop_requested = True
                    break
                
                self._update_progress(batch_idx, batch_count, f"Batch {batch_idx + 1}/{batch_count}")
                
                # Generate prompt
                self.logger.info(f"Đang tạo prompt cho batch {batch_idx + 1}...")
                prompts = self.prompt_gen.generate_prompts()
                
                if not prompts:
                    self.logger.error("Không thể tạo prompt, bỏ qua batch này")
                    continue
                
                image_prompt = prompts.get("image_prompt", "")
                if not image_prompt:
                    self.logger.error("Prompt ảnh trống, bỏ qua")
                    continue
                
                self.logger.info(f"Prompt: {image_prompt[:100]}...")
                
                # Enter prompt
                if not self.grok.enter_prompt(image_prompt):
                    self.logger.error("Không thể nhập prompt, bỏ qua batch này")
                    continue
                
                # Submit
                time.sleep(0.5)  # Small delay before submit
                if not self.grok.submit_prompt():
                    self.logger.error("Không thể gửi prompt, bỏ qua batch này")
                    continue
                
                # Không kiểm tra rate limit ở đây nữa - để wait_for_images xử lý
                
                # Wait for images (sẽ tự tải ảnh và xử lý rate limit)
                result = self.grok.wait_for_images(min_count=1)
                
                # Xử lý kết quả: có thể là số ảnh, tuple (số ảnh, "rate_limit"), hoặc False
                if isinstance(result, tuple):
                    # Rate limit detected after downloading
                    downloaded_count, status = result
                    total_downloaded += downloaded_count
                    if status == "rate_limit":
                        self.logger.error("Đã đạt rate limit - Dừng toàn bộ quá trình")
                        self._stop_requested = True
                        break
                elif isinstance(result, int):
                    # Số ảnh đã tải
                    total_downloaded += result
                    if result == 0:
                        self.logger.error("Không có ảnh nào được tạo, bỏ qua batch này")
                        continue
                elif not result:
                    self.logger.error("Không có ảnh nào được tạo, bỏ qua batch này")
                    continue
                
                # Ảnh đã được tải trong wait_for_images, không cần tải lại
                
                # Delay before next batch
                if batch_idx < batch_count - 1 and not self._stop_requested:
                    self.logger.info(f"Chờ {delay}s trước batch tiếp theo...")
                    for _ in range(delay):
                        if self._stop_requested:
                            break
                        time.sleep(1)
            
            self._update_progress(batch_count, batch_count, "Hoàn thành")
            self.logger.success(f"Hoàn thành tất cả! Tổng cộng {total_downloaded} ảnh từ {batch_count} batch")
            
        except Exception as e:
            self.logger.error(f"Lỗi trong quá trình tạo ảnh: {e}")
        finally:
            self._running = False
            self._stop_requested = False

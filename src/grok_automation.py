"""
Grok Automation - Interact with Grok Imagine website
"""
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .browser_manager import BrowserManager
from .config import get_config
from .logger import get_logger


class GrokAutomation:
    """Automate Grok Imagine for image and video generation."""
    
    # URLs
    GROK_URL = "https://grok.com"
    IMAGINE_URL = "https://grok.com/imagine"
    
    # Selectors (language-independent)
    PROMPT_INPUT = "div.tiptap.ProseMirror[contenteditable='true']"
    SUBMIT_BTN = "button[type='submit']"
    GENERATED_IMAGE = "img[src*='imagine-public']"
    GENERATED_VIDEO = "video[src*='imagine-public']"
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize Grok automation.
        
        Args:
            browser_manager: Browser manager instance
        """
        self.browser = browser_manager
        self.config = get_config()
        self.logger = get_logger()
        self.driver = browser_manager.get_driver()
    
    def navigate_to_imagine(self) -> bool:
        """Navigate to Grok Imagine page."""
        return self.browser.navigate(self.IMAGINE_URL)
    
    def enter_prompt(self, prompt: str) -> bool:
        """
        Enter prompt into the TipTap editor.
        
        Args:
            prompt: The prompt text to enter
            
        Returns:
            True if successful
        """
        if not self.driver:
            self.logger.error("Trình duyệt chưa khởi động")
            return False
        
        try:
            timeout = self.config.get("timeout_seconds", 60)
            
            # Wait for TipTap editor
            editor = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.PROMPT_INPUT))
            )
            
            # Clear existing content and enter new prompt via JavaScript
            # TipTap uses contenteditable, so we need JS to set content
            self.driver.execute_script("""
                const editor = arguments[0];
                editor.innerHTML = '<p>' + arguments[1] + '</p>';
                
                // Trigger input event to notify TipTap
                const event = new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                });
                editor.dispatchEvent(event);
            """, editor, prompt)
            
            self.logger.info("Đã nhập prompt thành công")
            return True
            
        except TimeoutException:
            self.logger.error("Hết thời gian chờ ô nhập liệu")
            return False
        except Exception as e:
            self.logger.error(f"Không thể nhập prompt: {e}")
            return False
    
    def submit_prompt(self) -> bool:
        """Submit the prompt by clicking send button."""
        try:
            timeout = self.config.get("timeout_seconds", 60)
            
            # Wait for submit button to be clickable
            submit_btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.SUBMIT_BTN))
            )
            
            submit_btn.click()
            
            self.logger.info("Đã gửi prompt")
            return True
            
        except TimeoutException:
            self.logger.error("Hết thời gian chờ nút gửi")
            return False
        except Exception as e:
            self.logger.error(f"Không thể gửi prompt: {e}")
            return False
    
    def count_current_images(self) -> int:
        """Count current valid images on page (including Base64 JPEGs which are completed images)."""
        try:
            # Find all images that might be generated results
            images = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img")
            count = 0
            for img in images:
                src = img.get_attribute("src") or ""
                # Valid images are either standard URLs containing 'imagine-public' (excluding thumbnails)
                # OR Base64 JPEGs (which user confirmed are "done" images)
                # We specifically exclude PNGs as those are placeholders
                is_valid_url = "imagine-public" in src and "_thumbnail" not in src
                is_valid_base64 = src.startswith("data:image/jpeg")
                
                if is_valid_url or is_valid_base64:
                    count += 1
            return count
        except Exception:
            return 0
    
    def is_generating(self) -> bool:
        """Check if generation is in progress by checking submit button disabled state."""
        try:
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, self.SUBMIT_BTN)
            # Check if button has disabled attribute
            is_disabled = submit_btn.get_attribute("disabled") is not None
            return is_disabled
        except Exception:
            return False
    
    def has_invisible_elements(self) -> bool:
        """Check if there are elements with class 'invisible' (generating placeholders)."""
        try:
            # Check for any element with class 'invisible' inside the masonry container
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".invisible")
            return len(elements) > 0
        except Exception:
            return False

    def wait_for_generation_complete(self, initial_count: int = 0, timeout: int = None) -> bool:
        """
        Wait for generation to complete, then scan and download images.
        Scans 5 times with 10s interval to ensure all images are captured.
        
        Args:
            initial_count: Number of images before submitting prompt
            timeout: Maximum wait time in seconds
            
        Returns:
            True if new images are generated
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 60)
        
        self.logger.info(f"Đang chờ tạo ảnh (ảnh hiện tại: {initial_count})...")
        
        start_time = time.time()
        was_generating = False
        
        # Helper to generate filename
        def get_timestamp_filename(idx):
            timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
            return f"{timestamp}_{idx:03d}.jpg"

        # Track processed images to prevent duplicates (persists across all scans)
        processed_srcs = set()
        output_dir = Path(self.config.get("images_dir", "./images"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Wait for generation to start and complete
        last_log_time = 0
        rate_limit_detected = False
        
        while time.time() - start_time < timeout:
            try:
                is_gen = self.is_generating()
                has_invisible = self.has_invisible_elements()
                has_placeholders = self.has_generating_placeholders()
                current_count = self.count_current_images()
                
                # Debug log every 5 seconds
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 5 == 0 and elapsed != last_log_time:
                    last_log_time = elapsed
                    self.logger.debug(f"[{elapsed}s] Generating={is_gen}, Invisible={has_invisible}, Placeholders={has_placeholders}, Images={current_count}")
                
                # Track states
                if is_gen or has_invisible or has_placeholders:
                    if not was_generating:
                        self.logger.info("Phát hiện đang tạo ảnh...")
                    was_generating = True
                
                # Check if generation completed FIRST
                # Điều kiện hoàn tất: không còn invisible, không còn placeholder, và có ảnh mới
                if was_generating and not has_invisible and not has_placeholders and current_count > initial_count:
                    self.logger.info("Tạo ảnh hoàn tất, bắt đầu quét và tải ảnh...")
                    break
                
                # Check for rate limit AFTER checking completion
                # Nếu ảnh chưa xong mà rate limit → dừng
                if self.check_rate_limit():
                    self.logger.warning("Phát hiện rate limit trong khi chờ tạo ảnh")
                    # Kiểm tra xem có ảnh mới không, nếu có thì vẫn tải
                    if current_count > initial_count:
                        self.logger.info("Có ảnh mới, tiếp tục tải trước khi dừng...")
                        rate_limit_detected = True
                        break
                    else:
                        self.logger.error("Đã đạt rate limit - Dừng toàn bộ quá trình")
                        return False
                
            except Exception as e:
                self.logger.debug(f"Lỗi khi kiểm tra: {e}")
            
            time.sleep(1)
        else:
            self.logger.error("Hết thời gian chờ tạo ảnh")
            return False
        
        # Scan and download images - 5 times with 10s interval
        # Nếu rate limit đã được phát hiện trước đó, chỉ quét 1 lần rồi dừng
        max_scans = 1 if rate_limit_detected else 5
        scan_interval = 10
        max_images = 12  # Số ảnh tối đa mỗi batch (cố định)
        
        if rate_limit_detected:
            self.logger.info("Rate limit đã phát hiện, tải ảnh 1 lần rồi dừng...")
        
        for scan_num in range(1, max_scans + 1):
            # Check if already reached max images
            if len(processed_srcs) >= max_images:
                self.logger.info(f"Đã đạt giới hạn {max_images} ảnh, dừng quét")
                break
            
            self.logger.info(f"Lần quét {scan_num}/{max_scans}...")
            
            # Không kiểm tra rate limit trong lúc tải ảnh - ưu tiên tải hết ảnh đã có
            
            # Find the latest batch section (highest ID number)
            # Sections have IDs like: imagine-masonry-section-0, imagine-masonry-section-1, etc.
            sections = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='imagine-masonry-section-']")
            
            if not sections:
                # Fallback to old method if no sections found
                self.logger.debug("Không tìm thấy section, sử dụng phương pháp cũ")
                all_images = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img")
            else:
                # Get the last section (latest batch)
                latest_section = sections[-1]
                section_id = latest_section.get_attribute("id")
                self.logger.debug(f"Đang quét section mới nhất: {section_id}")
                
                # Get images only from the latest section
                all_images = latest_section.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img")
            
            total_images = len(all_images)
            
            # Count and download images
            jpeg_count = 0
            png_count = 0
            new_downloads = 0
            
            for img in all_images:
                # Check limit before each download
                if len(processed_srcs) >= max_images:
                    self.logger.info(f"Đã đạt giới hạn {max_images} ảnh")
                    break
                
                src = img.get_attribute("src") or ""
                
                if src.startswith("data:image/jpeg"):
                    jpeg_count += 1
                    
                    # Download if not already processed
                    if src not in processed_srcs:
                        self.logger.info(f"Phát hiện ảnh JPEG mới, đang tải xuống...")
                        try:
                            self._save_base64_image(src, output_dir, get_timestamp_filename(len(processed_srcs) + 1))
                            processed_srcs.add(src)
                            new_downloads += 1
                            self.logger.success(f"Đã tải ảnh {len(processed_srcs)}/{max_images}")
                        except Exception as dl_err:
                            self.logger.error(f"Lỗi tải ảnh: {dl_err}")
                            
                elif src.startswith("data:image/png"):
                    # PNG = placeholder, skip
                    png_count += 1
                    
                elif "imagine-public" in src and "_thumbnail" not in src:
                    # URL-based image (also valid)
                    if src not in processed_srcs:
                        self.logger.info(f"Phát hiện ảnh URL mới, đang tải xuống...")
                        try:
                            self._download_single_image(src, output_dir, get_timestamp_filename(len(processed_srcs) + 1))
                            processed_srcs.add(src)
                            new_downloads += 1
                            self.logger.success(f"Đã tải ảnh {len(processed_srcs)}/{max_images}")
                        except Exception as dl_err:
                            self.logger.error(f"Lỗi tải ảnh: {dl_err}")
            
            self.logger.info(f"Lần quét {scan_num}: Tổng ảnh: {total_images} | JPEG: {jpeg_count} | PNG (bỏ qua): {png_count} | Mới tải: {new_downloads} | Tổng đã tải: {len(processed_srcs)}")
            
            # Wait 10s before next scan (except for last scan)
            if scan_num < max_scans:
                self.logger.info(f"Chờ {scan_interval}s trước lần quét tiếp theo...")
                time.sleep(scan_interval)
        
        self.logger.info(f"Batch hoàn thành! Đã tải {len(processed_srcs)} ảnh")
        
        # Nếu rate limit đã phát hiện, trả về tuple (số ảnh, "rate_limit") để dừng các batch tiếp theo
        if rate_limit_detected:
            self.logger.warning("Rate limit đã đạt - Dừng sau khi tải ảnh")
            return (len(processed_srcs), "rate_limit")
        
        return len(processed_srcs)

    def has_generating_placeholders(self) -> bool:
        """Check if there are generating placeholder images (Base64 PNGs) in the generation list."""
        try:
            # Check for images with data:image/png src inside list items
            # These are typically the blurred/loading placeholders
            elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img[src^='data:image/png']")
            return len(elements) > 0
        except Exception:
            return False
    
    def check_rate_limit(self) -> bool:
        """Check if rate limit notification is present on the page.
        
        Detects rate limit based on HTML attributes (language-independent):
        - Toast notification with data-type="error"
        - Contains triangle-alert icon (lucide-triangle-alert)
        - Contains "Upgrade" button
        
        Returns:
            True if rate limit detected
        """
        try:
            # Method 1: Check for error toast with Upgrade button (most reliable)
            # This is the rate limit toast structure from limmit.html
            error_toasts = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "li[data-sonner-toast][data-type='error']"
            )
            
            for toast in error_toasts:
                # Verify it's the rate limit toast by checking for Upgrade button
                try:
                    upgrade_btn = toast.find_element(By.CSS_SELECTOR, "button")
                    if upgrade_btn:
                        self.logger.warning("Phát hiện rate limit - Dừng toàn bộ quá trình")
                        return True
                except:
                    pass
            
            # Method 2: Check for triangle-alert icon inside toast (backup check)
            alert_icons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "li[data-sonner-toast] svg.lucide-triangle-alert"
            )
            
            if alert_icons:
                self.logger.warning("Phát hiện rate limit - Dừng toàn bộ quá trình")
                return True
                
            return False
            
        except Exception as e:
            self.logger.debug(f"Lỗi khi kiểm tra rate limit: {e}")
            return False
    
    def wait_for_images(self, timeout: int = None, min_count: int = 1) -> bool:
        """
        Wait for images to be generated (legacy method, uses smart polling internally).
        
        Args:
            timeout: Maximum wait time in seconds
            min_count: Minimum number of NEW images to wait for
            
        Returns:
            True if images are ready
        """
        initial_count = self.count_current_images()
        return self.wait_for_generation_complete(initial_count, timeout)
    
    def get_image_urls(self, count: int = 4) -> List[str]:
        """
        Get URLs of generated images.
        
        Args:
            count: Maximum number of images to get
            
        Returns:
            List of image URLs
        """
        try:
            images = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_IMAGE)
            
            urls = []
            for img in images:
                src = img.get_attribute("src")
                if src and "imagine-public" in src and "_thumbnail" not in src:
                    if src not in urls:  # Avoid duplicates
                        urls.append(src)
                        if len(urls) >= count:
                            break
            
            self.logger.info(f"Tìm thấy {len(urls)} ảnh")
            return urls
            
        except Exception as e:
            self.logger.error(f"Không thể lấy URL ảnh: {e}")
            return []
    
    def download_images(self, urls: List[str], output_dir: str) -> List[str]:
        """
        Download images from URLs.
        
        Args:
            urls: List of image URLs
            output_dir: Directory to save images
            
        Returns:
            List of saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
        
        for idx, url in enumerate(urls, 1):
            try:
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    filename = f"{timestamp}_{idx:03d}.jpg"
                    filepath = output_path / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    saved_files.append(str(filepath))
                    self.logger.info(f"Đã tải: {filename}")
                else:
                    self.logger.error(f"Không thể tải ảnh {idx}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Không thể tải ảnh {idx}: {e}")
        
        return saved_files
    
    def wait_for_video(self, timeout: int = None) -> bool:
        """
        Wait for video to be generated.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if video is ready
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 180)  # Videos take longer
        
        self.logger.info(f"Đang chờ video (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
                
                for video in videos:
                    src = video.get_attribute("src") or ""
                    if "imagine-public" in src and ".mp4" in src:
                        time.sleep(2)
                        self.logger.success("Video đã sẵn sàng")
                        return True
                        
            except Exception:
                pass
            
            time.sleep(2)
        
        self.logger.error("Hết thời gian chờ video")
        return False
    
    def get_video_url(self) -> Optional[str]:
        """Get the URL of the generated video."""
        try:
            videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
            
            for video in videos:
                src = video.get_attribute("src")
                if src and "imagine-public" in src and ".mp4" in src:
                    return src
            
            self.logger.error("Không tìm thấy URL video")
            return None
            
        except Exception as e:
            self.logger.error(f"Không thể lấy URL video: {e}")
            return None
    
    def download_video(self, url: str, output_path: str) -> bool:
        """
        Download video from URL.
        
        Args:
            url: Video URL
            output_path: Path to save video
            
        Returns:
            True if successful
        """
        try:
            self.logger.info("Đang tải video...")
            
            response = requests.get(url, timeout=180, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.success(f"Đã lưu video: {output_path}")
                return True
            else:
                self.logger.error(f"Không thể tải video: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Không thể tải video: {e}")
            return False
    
    def _save_base64_image(self, base64_data: str, output_dir: Path, filename: str) -> bool:
        """Save Base64 image data to file."""
        import base64
        try:
            # Remove header if present (e.g., "data:image/jpeg;base64,")
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            image_data = base64.b64decode(base64_data)
            filepath = output_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save Base64 image: {e}")
            return False

    def _download_single_image(self, url: str, output_dir: Path, filename: str) -> bool:
        """Download a single image from URL."""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = output_dir / filename
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to download image {url}: {e}")
            return False

    def refresh_driver(self):
        """Refresh driver reference after browser restart."""
        self.driver = self.browser.get_driver()

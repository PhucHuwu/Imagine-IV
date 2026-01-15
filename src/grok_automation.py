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
            self.logger.error("Trinh duyet chua khoi dong")
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
            
            self.logger.info("Da nhap prompt thanh cong")
            return True
            
        except TimeoutException:
            self.logger.error("Het thoi gian cho o nhap lieu")
            return False
        except Exception as e:
            self.logger.error(f"Khong the nhap prompt: {e}")
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
            
            self.logger.info("Da gui prompt")
            return True
            
        except TimeoutException:
            self.logger.error("Het thoi gian cho nut gui")
            return False
        except Exception as e:
            self.logger.error(f"Khong the gui prompt: {e}")
            return False
    
    def wait_for_images(self, timeout: int = None, min_count: int = 1) -> bool:
        """
        Wait for images to be generated.
        
        Args:
            timeout: Maximum wait time in seconds
            min_count: Minimum number of images to wait for
            
        Returns:
            True if images are ready
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 120)
        
        self.logger.info(f"Dang cho anh (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                images = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_IMAGE)
                
                # Filter out thumbnails and small images
                valid_images = []
                for img in images:
                    src = img.get_attribute("src") or ""
                    width = img.get_attribute("width") or "0"
                    
                    # Check if it's a real generated image (not thumbnail)
                    if "imagine-public" in src and "_thumbnail" not in src:
                        valid_images.append(img)
                
                if len(valid_images) >= min_count:
                    # Wait a bit more for images to fully load
                    time.sleep(2)
                    self.logger.success(f"Tim thay {len(valid_images)} anh")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(1)
        
        self.logger.error("Het thoi gian cho anh")
        return False
    
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
            
            self.logger.info(f"Tim thay {len(urls)} anh")
            return urls
            
        except Exception as e:
            self.logger.error(f"Khong the lay URL anh: {e}")
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
                    self.logger.info(f"Da tai: {filename}")
                else:
                    self.logger.error(f"Khong the tai anh {idx}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Khong the tai anh {idx}: {e}")
        
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
        
        self.logger.info(f"Dang cho video (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
                
                for video in videos:
                    src = video.get_attribute("src") or ""
                    if "imagine-public" in src and ".mp4" in src:
                        time.sleep(2)
                        self.logger.success("Video da san sang")
                        return True
                        
            except Exception:
                pass
            
            time.sleep(2)
        
        self.logger.error("Het thoi gian cho video")
        return False
    
    def get_video_url(self) -> Optional[str]:
        """Get the URL of the generated video."""
        try:
            videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
            
            for video in videos:
                src = video.get_attribute("src")
                if src and "imagine-public" in src and ".mp4" in src:
                    return src
            
            self.logger.error("Khong tim thay URL video")
            return None
            
        except Exception as e:
            self.logger.error(f"Khong the lay URL video: {e}")
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
            self.logger.info("Dang tai video...")
            
            response = requests.get(url, timeout=180, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.success(f"Da luu video: {output_path}")
                return True
            else:
                self.logger.error(f"Khong the tai video: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Khong the tai video: {e}")
            return False
    
    def refresh_driver(self):
        """Refresh driver reference after browser restart."""
        self.driver = self.browser.get_driver()

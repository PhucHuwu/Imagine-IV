"""
Grok Automation - Interact with Grok Imagine website
"""
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .browser_manager import BrowserManager
from .config import get_config
from .logger import get_logger


class GrokAutomation:
    """Automate Grok Imagine for image and video generation."""
    
    GROK_URL = "https://grok.x.ai"
    IMAGINE_URL = "https://grok.x.ai/imagine"
    
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
        Enter prompt into the text input.
        
        Args:
            prompt: The prompt text to enter
            
        Returns:
            True if successful
        """
        if not self.driver:
            self.logger.error("Browser not started")
            return False
        
        try:
            timeout = self.config.get("timeout_seconds", 60)
            
            # Wait for input field
            input_field = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, input[type='text']"))
            )
            
            # Clear and enter prompt
            input_field.clear()
            input_field.send_keys(prompt)
            
            self.logger.info("Prompt entered successfully")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout waiting for input field")
            return False
        except Exception as e:
            self.logger.error(f"Failed to enter prompt: {e}")
            return False
    
    def upload_image(self, image_path: str) -> bool:
        """
        Upload an image to Grok.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if successful
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            self.logger.error(f"Image not found: {image_path}")
            return False
        
        try:
            # Find file input
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(str(image_path.absolute()))
            
            self.logger.info(f"Image uploaded: {image_path.name}")
            time.sleep(1)  # Wait for upload
            return True
            
        except NoSuchElementException:
            self.logger.error("File upload button not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            return False
    
    def select_video_mode(self) -> bool:
        """Select video generation mode if available."""
        try:
            # Look for video mode toggle/button
            video_buttons = self.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'video') or contains(text(), 'Video')]"
            )
            
            if video_buttons:
                video_buttons[0].click()
                self.logger.info("Video mode selected")
                time.sleep(0.5)
                return True
            else:
                self.logger.warning("Video mode button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to select video mode: {e}")
            return False
    
    def submit_prompt(self) -> bool:
        """Submit the prompt (press Enter or click send button)."""
        try:
            # Try Enter key first
            input_field = self.driver.find_element(By.CSS_SELECTOR, "textarea, input[type='text']")
            input_field.send_keys(Keys.RETURN)
            
            self.logger.info("Prompt submitted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit prompt: {e}")
            return False
    
    def wait_for_images(self, timeout: int = None) -> bool:
        """
        Wait for images to be generated.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if images are ready
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 60)
        
        self.logger.info(f"Waiting for images (timeout: {timeout}s)...")
        
        try:
            # Wait for image elements to appear
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[src*='imagine-public']"))
            )
            
            # Additional wait for all images to load
            time.sleep(2)
            
            self.logger.success("Images ready")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout waiting for images")
            return False
    
    def wait_for_video(self, timeout: int = None) -> bool:
        """
        Wait for video to be generated.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if video is ready
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 120)  # Videos take longer
        
        self.logger.info(f"Waiting for video (timeout: {timeout}s)...")
        
        try:
            # Wait for video element or download button
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "video, a[href*='.mp4'], button[aria-label*='download']"
                ))
            )
            
            time.sleep(2)
            
            self.logger.success("Video ready")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout waiting for video")
            return False
    
    def get_image_urls(self, count: int = 4) -> List[str]:
        """
        Get URLs of generated images.
        
        Args:
            count: Number of images to get (left to right, top to bottom)
            
        Returns:
            List of image URLs
        """
        try:
            # Find all image elements
            images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='imagine-public']")
            
            urls = []
            for img in images[:count]:
                src = img.get_attribute("src")
                if src:
                    urls.append(src)
            
            self.logger.info(f"Found {len(urls)} image(s)")
            return urls
            
        except Exception as e:
            self.logger.error(f"Failed to get image URLs: {e}")
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
        timestamp = datetime.now().strftime("%d-%m_%H-%M")
        
        for idx, url in enumerate(urls, 1):
            try:
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    filename = f"{timestamp}_{idx:03d}.jpg"
                    filepath = output_path / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    saved_files.append(str(filepath))
                    self.logger.info(f"Downloaded: {filename}")
                else:
                    self.logger.error(f"Failed to download image {idx}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Failed to download image {idx}: {e}")
        
        return saved_files
    
    def click_create_video_button(self) -> bool:
        """Click 'Create Video' button on a generated image."""
        try:
            # Look for video creation button on images
            video_btn = self.driver.find_element(
                By.XPATH,
                "//*[contains(text(), 'video') or contains(text(), 'Video') or contains(@aria-label, 'video')]"
            )
            video_btn.click()
            
            self.logger.info("Clicked create video button")
            return True
            
        except NoSuchElementException:
            self.logger.error("Create video button not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to click create video: {e}")
            return False
    
    def get_video_url(self) -> Optional[str]:
        """Get the URL of the generated video."""
        try:
            # Try video element
            video = self.driver.find_element(By.CSS_SELECTOR, "video source")
            src = video.get_attribute("src")
            if src:
                return src
            
            # Try download link
            link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='.mp4']")
            return link.get_attribute("href")
            
        except NoSuchElementException:
            self.logger.error("Video URL not found")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get video URL: {e}")
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
            self.logger.info(f"Downloading video...")
            
            response = requests.get(url, timeout=120, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.success(f"Video saved: {output_path}")
                return True
            else:
                self.logger.error(f"Failed to download video: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to download video: {e}")
            return False

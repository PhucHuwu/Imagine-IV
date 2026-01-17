"""
Video Generator - Orchestrates video generation workflow
Creates 12s videos by combining two 6s video clips
"""
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict

from .browser_manager import BrowserManager
from .grok_automation import GrokAutomation
from .prompt_generator import PromptGenerator
from .video_processor import get_video_processor
from .config import get_config
from .logger import get_logger


class VideoGenerator:
    """Generate 12s videos using Grok Imagine."""
    
    VIDEO2_PREFIX = "Continue the motion smoothly from this exact frame. Maintain the same style, lighting, and camera angle. "
    
    def __init__(
        self,
        browser: BrowserManager,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        Initialize video generator.
        
        Args:
            browser: Browser manager instance
            on_progress: Callback (current, total, status)
        """
        self.browser = browser
        self.on_progress = on_progress
        
        self.config = get_config()
        self.logger = get_logger()
        self.grok = GrokAutomation(browser)
        self.prompt_gen = PromptGenerator()
        self.video_processor = get_video_processor()
        
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
    
    def start(self, mode: str = "generate", folder: str = None, batch_count: int = 10):
        """
        Start video generation.
        
        Args:
            mode: "generate" (create new images) or "folder" (use existing images)
            folder: Folder path for mode="folder"
            batch_count: Number of videos to create
        """
        if self._running:
            self.logger.warning("Video generator đang chạy")
            return
        
        self._stop_event.clear()
        self._running = True
        
        self._thread = threading.Thread(
            target=self._generation_loop,
            args=(mode, folder, batch_count),
            daemon=True
        )
        self._thread.start()
    
    def stop(self):
        """Stop video generation."""
        self._stop_event.set()
        self.logger.info("Đang dừng video generator...")
    
    def is_running(self) -> bool:
        """Check if generator is running."""
        return self._running
    
    def _report_progress(self, current: int, total: int, status: str):
        """Report progress via callback."""
        if self.on_progress:
            try:
                self.on_progress(current, total, status)
            except Exception as e:
                self.logger.error(f"Lỗi callback progress: {e}")
    
    def _generation_loop(self, mode: str, folder: str, batch_count: int):
        """Main generation loop."""
        try:
            self.logger.info(f"Bắt đầu tạo {batch_count} video (mode: {mode})")
            self._report_progress(0, batch_count, "Đang khởi tạo...")
            
            # Setup directories
            videos_dir = Path(self.config.get("videos_dir", "./videos"))
            temp_dir = videos_dir / "temp"
            videos_dir.mkdir(parents=True, exist_ok=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Get images list for folder mode
            image_list = []
            if mode == "folder" and folder:
                folder_path = Path(folder)
                if folder_path.exists():
                    image_list = list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.jpeg")) + list(folder_path.glob("*.png"))
                    self.logger.info(f"Tìm thấy {len(image_list)} ảnh trong thư mục")
            
            completed = 0
            
            for i in range(batch_count):
                if self._stop_event.is_set():
                    self.logger.info("Đã dừng theo yêu cầu")
                    break
                
                self.logger.info(f"===== Video {i + 1}/{batch_count} =====")
                self._report_progress(i, batch_count, f"Đang tạo video {i + 1}/{batch_count}")
                
                try:
                    # Generate prompts
                    self._report_progress(i, batch_count, "Đang tạo prompt AI...")
                    prompts = self.prompt_gen.generate_prompts()
                    
                    if not prompts:
                        self.logger.error("Không thể tạo prompt, bỏ qua video này")
                        continue
                    
                    image_prompt = prompts.get("image_prompt", "")
                    video1_prompt = prompts.get("video1_prompt", "")
                    video2_prompt = prompts.get("video2_prompt", "")
                    
                    # Determine source image
                    if mode == "folder" and image_list:
                        # Use image from folder
                        if i < len(image_list):
                            source_image = str(image_list[i])
                        else:
                            # Cycle through images if batch_count > image count
                            source_image = str(image_list[i % len(image_list)])
                        self.logger.info(f"Sử dụng ảnh: {Path(source_image).name}")
                    else:
                        # Generate new image
                        self._report_progress(i, batch_count, "Đang tạo ảnh nguồn...")
                        source_image = self._generate_source_image(image_prompt, temp_dir)
                        
                        if not source_image:
                            self.logger.error("Không thể tạo ảnh nguồn, bỏ qua video này")
                            self.grok.go_back_to_imagine()
                            continue
                    
                    # Create Video 1
                    self._report_progress(i, batch_count, "Đang tạo video 1/2...")
                    video1_path = temp_dir / f"video1_{i}.mp4"
                    
                    result1 = self._create_video(source_image, video1_prompt, str(video1_path))
                    if result1 == "moderated":
                        self.logger.error("Video 1 bị nhạy cảm, kết thúc batch")
                        self.grok.go_back_to_imagine()
                        break
                    if not result1:
                        self.logger.error("Không thể tạo video 1, bỏ qua")
                        self.grok.go_back_to_imagine()
                        continue
                    
                    if self._stop_event.is_set():
                        break
                    
                    # Extract last frame from Video 1
                    self._report_progress(i, batch_count, "Đang trích xuất frame cuối...")
                    last_frame_path = temp_dir / f"last_frame_{i}.jpg"
                    
                    if not self.video_processor.extract_last_frame(str(video1_path), str(last_frame_path)):
                        self.logger.error("Không thể trích xuất frame cuối, bỏ qua")
                        self.grok.go_back_to_imagine()
                        continue
                    
                    # Create Video 2 from last frame
                    self._report_progress(i, batch_count, "Đang tạo video 2/2...")
                    video2_path = temp_dir / f"video2_{i}.mp4"
                    video2_full_prompt = self.VIDEO2_PREFIX + video2_prompt
                    
                    result2 = self._create_video(str(last_frame_path), video2_full_prompt, str(video2_path))
                    if result2 == "moderated":
                        self.logger.error("Video 2 bị nhạy cảm, kết thúc batch")
                        self.grok.go_back_to_imagine()
                        break
                    if not result2:
                        self.logger.error("Không thể tạo video 2, bỏ qua")
                        self.grok.go_back_to_imagine()
                        continue
                    
                    if self._stop_event.is_set():
                        break
                    
                    # Concatenate videos
                    self._report_progress(i, batch_count, "Đang ghép video...")
                    timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
                    final_video = videos_dir / f"{timestamp}_{i + 1:03d}.mp4"
                    
                    if self.video_processor.concat_videos(str(video1_path), str(video2_path), str(final_video)):
                        completed += 1
                        self.logger.success(f"Đã tạo video hoàn chỉnh: {final_video.name}")
                    else:
                        self.logger.error("Không thể ghép video")
                    
                    # Cleanup temp files for this iteration
                    self._cleanup_temp_files([video1_path, video2_path, last_frame_path])
                    
                    # Small delay between videos
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Lỗi tạo video {i + 1}: {e}")
                    continue
            
            self.logger.success(f"Hoàn thành! Đã tạo {completed}/{batch_count} video")
            self._report_progress(batch_count, batch_count, f"Hoàn thành: {completed}/{batch_count} video")
            
        except Exception as e:
            self.logger.error(f"Lỗi trong quá trình tạo video: {e}")
            self._report_progress(0, batch_count, f"Lỗi: {e}")
        finally:
            self._running = False
    
    def _generate_source_image(self, image_prompt: str, temp_dir: Path) -> Optional[str]:
        """
        Generate source image using Grok Imagine.
        
        Returns:
            Path to downloaded image or None
        """
        try:
            # Clear any existing input
            self.grok.clear_prompt_input()
            time.sleep(0.5)
            
            # Enter image prompt
            if not self.grok.enter_prompt(image_prompt):
                return None
            
            # Get initial image count
            initial_count = self.grok.count_current_images()
            
            # Submit prompt
            if not self.grok.submit_prompt():
                return None
            
            # Wait for generation
            result = self.grok.wait_for_generation_complete(initial_count)
            
            if not result:
                return None
            
            # Check for rate limit
            if isinstance(result, tuple) and result[1] == "rate_limit":
                self.logger.warning("Rate limit đạt khi tạo ảnh")
                return None
            
            # Download first image
            timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
            image_path = temp_dir / f"source_{timestamp}.jpg"
            
            if self.grok.get_first_image_from_batch(str(image_path)):
                self.logger.success(f"Đã tạo ảnh nguồn: {image_path.name}")
                return str(image_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Lỗi tạo ảnh nguồn: {e}")
            return None
    
    def _create_video(self, image_path: str, prompt: str, output_path: str) -> Optional[str]:
        """
        Create video(s) from image.
        
        Flow:
        1. Navigate to Imagine
        2. Upload image → Grok auto-generates 2 videos
        3. Wait for video to complete
        4. Check if video is moderated, try switching if needed
        5. Download the auto-generated video (if not moderated)
        6. Enter custom prompt and generate new video
        7. Download video from prompt (if not moderated)
        
        Args:
            image_path: Source image path
            prompt: Video prompt
            output_path: Where to save video (will add _auto suffix for auto video)
            
        Returns:
            "success" if at least one video created
            "moderated" if both auto videos are moderated (should skip batch)
            None if other error
        """
        try:
            downloaded_any = False
            output_path_obj = Path(output_path)
            
            # Navigate to Imagine page first
            self.grok.navigate_to_imagine()
            time.sleep(2)
            
            # Upload image with retry (moderation service can fail temporarily)
            max_retries = 3
            upload_success = False
            
            for attempt in range(max_retries):
                if self.grok.upload_image(image_path):
                    upload_success = True
                    break
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Upload thất bại, thử lại ({attempt + 2}/{max_retries})...")
                        # Go back and try again
                        self.grok.navigate_to_imagine()
                        time.sleep(2)
            
            if not upload_success:
                self.logger.error("Không thể upload ảnh sau nhiều lần thử")
                return None
            
            # Wait for video creation page to load
            if not self.grok.wait_for_video_page(timeout=30):
                self.logger.error("Trang tạo video không tải được")
                return None
            
            # Make sure Video mode is selected (click film icon)
            self.grok.click_video_mode()
            time.sleep(1)
            
            # Wait for Grok's automatic first video generation to complete
            self.logger.info("Đang chờ video tự động tạo...")
            if not self.grok.wait_for_initial_video():
                self.logger.error("Video tự động không được tạo")
                return None
            
            # Check for moderated content - try to find a non-moderated video
            time.sleep(1)
            if not self.grok.find_non_moderated_video():
                self.logger.error("Cả 2 video tự động đều bị nhạy cảm")
                return "moderated"
            
            # === STEP 1: Download auto-generated video via Download button ===
            time.sleep(1)
            
            # Create path for auto video with _auto suffix
            auto_output_path = output_path_obj.parent / f"{output_path_obj.stem}_auto{output_path_obj.suffix}"
            
            # Use download button to avoid 403 errors
            if self.grok.download_video_via_button(str(auto_output_path)):
                self.logger.success(f"Đã tải video tự động: {auto_output_path.name}")
                downloaded_any = True
            else:
                self.logger.warning("Không thể tải video tự động qua nút Download")
            
            # === STEP 2: Generate video from prompt ===
            time.sleep(1)
            
            # Enter video prompt into textarea
            if not self.grok.enter_video_prompt(prompt):
                self.logger.error("Không thể nhập prompt video")
                # Still return success if we downloaded auto video
                if downloaded_any:
                    self.grok.go_back_to_imagine()
                    time.sleep(1)
                    return "success"
                return None
            
            # Submit prompt to generate new video with our prompt
            if not self.grok.submit_video_prompt():
                self.logger.error("Không thể gửi prompt")
                if downloaded_any:
                    self.grok.go_back_to_imagine()
                    time.sleep(1)
                    return "success"
                return None
            
            # Wait for our custom video to be generated
            video_url = self.grok.wait_for_video_generation()
            
            # Check if video from prompt is moderated
            if video_url == "moderated":
                self.logger.warning("Video từ prompt bị nhạy cảm, bỏ qua")
                # Still success if we got auto video
                if downloaded_any:
                    self.grok.go_back_to_imagine()
                    time.sleep(1)
                    return "success"
            elif video_url:
                # Download video from prompt via Download button
                if self.grok.download_video_via_button(output_path):
                    self.logger.success(f"Đã tải video từ prompt: {output_path_obj.name}")
                    downloaded_any = True
                else:
                    self.logger.warning("Không thể tải video từ prompt")
            else:
                self.logger.warning("Video từ prompt không được tạo")
            
            # Go back to Imagine page for next operation
            self.grok.go_back_to_imagine()
            time.sleep(1)
            
            return "success" if downloaded_any else None
            
        except Exception as e:
            self.logger.error(f"Lỗi tạo video: {e}")
            # Always go back to Imagine page even on error
            try:
                self.grok.go_back_to_imagine()
            except:
                pass
            return None
    
    def _cleanup_temp_files(self, files: list):
        """Clean up temporary files."""
        for file_path in files:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
            except Exception:
                pass

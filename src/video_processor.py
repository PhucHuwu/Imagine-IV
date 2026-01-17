"""
Video Processor - FFmpeg operations for video processing
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

from .logger import get_logger


class VideoProcessor:
    """Process videos using FFmpeg."""
    
    # FFmpeg download URLs
    FFMPEG_URLS = {
        "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "Darwin": "https://evermeet.cx/ffmpeg/getrelease/zip",
    }
    FFPROBE_MAC_URL = "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    
    def __init__(self):
        """Initialize video processor."""
        self.logger = get_logger()
        self.ffmpeg_dir = Path(__file__).parent.parent / "ffmpeg" / "bin"
        self._setup_ffmpeg()
    
    def _setup_ffmpeg(self):
        """Setup FFmpeg - check local or download."""
        import platform
        system = platform.system()
        
        ext = ".exe" if system == "Windows" else ""
        self.ffmpeg_path = self.ffmpeg_dir / f"ffmpeg{ext}"
        self.ffprobe_path = self.ffmpeg_dir / f"ffprobe{ext}"
        
        if self.ffmpeg_path.exists():
            self.logger.info(f"Đã tìm thấy FFmpeg: {self.ffmpeg_path}")
            return
        
        # Download FFmpeg
        self.logger.info("FFmpeg chưa có, đang tải về...")
        self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        
        if system == "Windows":
            self._download_windows()
        elif system == "Darwin":
            self._download_mac()
        else:
            self.logger.error(f"Không hỗ trợ tự động tải cho {system}")
    
    def _download_windows(self):
        """Download FFmpeg for Windows."""
        import requests, zipfile, io, shutil
        
        try:
            self.logger.info("Đang tải FFmpeg cho Windows (~100MB)...")
            response = requests.get(self.FFMPEG_URLS["Windows"], stream=True, timeout=300)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for name in zf.namelist():
                    if name.endswith("ffmpeg.exe"):
                        with zf.open(name) as src, open(self.ffmpeg_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                    elif name.endswith("ffprobe.exe"):
                        with zf.open(name) as src, open(self.ffprobe_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
            
            self.logger.success(f"Đã cài FFmpeg: {self.ffmpeg_path}")
        except Exception as e:
            self.logger.error(f"Lỗi tải FFmpeg: {e}")
    
    def _download_mac(self):
        """Download FFmpeg for Mac."""
        import requests, zipfile, io, stat
        
        try:
            # Download ffmpeg
            self.logger.info("Đang tải FFmpeg cho Mac...")
            response = requests.get(self.FFMPEG_URLS["Darwin"], timeout=120)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for name in zf.namelist():
                    if "ffmpeg" in name.lower() and not name.endswith('/'):
                        with zf.open(name) as src, open(self.ffmpeg_path, 'wb') as dst:
                            dst.write(src.read())
                        self.ffmpeg_path.chmod(self.ffmpeg_path.stat().st_mode | stat.S_IEXEC)
            
            # Download ffprobe
            self.logger.info("Đang tải FFprobe cho Mac...")
            response = requests.get(self.FFPROBE_MAC_URL, timeout=120)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for name in zf.namelist():
                    if "ffprobe" in name.lower() and not name.endswith('/'):
                        with zf.open(name) as src, open(self.ffprobe_path, 'wb') as dst:
                            dst.write(src.read())
                        self.ffprobe_path.chmod(self.ffprobe_path.stat().st_mode | stat.S_IEXEC)
            
            self.logger.success(f"Đã cài FFmpeg: {self.ffmpeg_path}")
        except Exception as e:
            self.logger.error(f"Lỗi tải FFmpeg: {e}")
    
    def _get_ffmpeg_cmd(self) -> str:
        return str(self.ffmpeg_path)
    
    def _get_ffprobe_cmd(self) -> str:
        return str(self.ffprobe_path)
    
    def is_available(self) -> bool:
        return self.ffmpeg_path.exists()
    
    def extract_last_frame(self, video_path: str, output_path: str) -> bool:
        """
        Extract the last frame from a video.
        
        Args:
            video_path: Path to input video
            output_path: Path to save the frame (jpg)
            
        Returns:
            True if successful
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        if not video_path.exists():
            self.logger.error(f"Không tìm thấy video: {video_path}")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get video duration first
            duration = self._get_video_duration(str(video_path))
            
            if duration is None or duration <= 0:
                self.logger.error("Không lấy được thời lượng video")
                return False
            
            # Extract frame at the last second
            last_second = max(0, duration - 0.1)
            
            cmd = [
                self._get_ffmpeg_cmd(), '-y',
                '-ss', str(last_second),
                '-i', str(video_path),
                '-frames:v', '1',
                '-q:v', '2',
                str(output_path)
            ]
            
            self.logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                self.logger.success(f"Đã trích xuất frame cuối: {output_path}")
                return True
            else:
                self.logger.error(f"FFmpeg lỗi: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Không thể trích xuất frame: {e}")
            return False
    
    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                self._get_ffprobe_cmd(),
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return None
                
        except (ValueError, subprocess.SubprocessError):
            return None
    
    def concat_videos(self, video1_path: str, video2_path: str, output_path: str) -> bool:
        """
        Concatenate two videos into one.
        
        Args:
            video1_path: Path to first video
            video2_path: Path to second video
            output_path: Path to output video
            
        Returns:
            True if successful
        """
        video1_path = Path(video1_path)
        video2_path = Path(video2_path)
        output_path = Path(output_path)
        
        if not video1_path.exists():
            self.logger.error(f"Không tìm thấy Video 1: {video1_path}")
            return False
        
        if not video2_path.exists():
            self.logger.error(f"Không tìm thấy Video 2: {video2_path}")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create concat file
            concat_file = output_path.parent / "concat_list.txt"
            
            with open(concat_file, 'w') as f:
                f.write(f"file '{video1_path.absolute()}'\n")
                f.write(f"file '{video2_path.absolute()}'\n")
            
            cmd = [
                self._get_ffmpeg_cmd(), '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                str(output_path)
            ]
            
            self.logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Cleanup concat file
            if concat_file.exists():
                concat_file.unlink()
            
            if result.returncode == 0 and output_path.exists():
                self.logger.success(f"Đã ghép video: {output_path}")
                return True
            else:
                self.logger.error(f"FFmpeg lỗi: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Không thể ghép video: {e}")
            return False
    
    def cleanup_temp_videos(self, temp_dir: str):
        """Clean up temporary video files."""
        temp_path = Path(temp_dir)
        
        if not temp_path.exists():
            return
        
        try:
            for file in temp_path.glob("*.mp4"):
                file.unlink()
            
            for file in temp_path.glob("*.jpg"):
                file.unlink()
            
            self.logger.info(f"Đã dọn file tạm trong: {temp_dir}")
            
        except Exception as e:
            self.logger.warning(f"Không thể dọn file tạm: {e}")


# Global instance
_processor_instance = None


def get_video_processor() -> VideoProcessor:
    """Get global video processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = VideoProcessor()
    return _processor_instance

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
    
    def __init__(self):
        """Initialize video processor."""
        self.logger = get_logger()
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("Đã tìm thấy FFmpeg")
                return True
            else:
                self.logger.warning("Không tìm thấy FFmpeg trong PATH")
                return False
        except FileNotFoundError:
            self.logger.warning("FFmpeg chưa cài hoặc không có trong PATH")
            return False
    
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
                'ffmpeg', '-y',
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
                'ffprobe',
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
                'ffmpeg', '-y',
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

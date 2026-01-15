"""
Process Cleaner - Kill orphan Chrome processes
"""
import os
import signal
import subprocess
from pathlib import Path
from typing import List

from .logger import get_logger


class ProcessCleaner:
    """Manage and cleanup Chrome processes."""
    
    def __init__(self, pids_file: str = "./chrome_pids.txt"):
        """Initialize process cleaner."""
        self.pids_file = Path(pids_file)
        self.logger = get_logger()
        self._current_pids: List[int] = []
    
    def save_pid(self, pid: int):
        """Save a Chrome PID to track."""
        self._current_pids.append(pid)
        self._save_pids_to_file()
    
    def _save_pids_to_file(self):
        """Save all current PIDs to file."""
        try:
            with open(self.pids_file, 'w') as f:
                for pid in self._current_pids:
                    f.write(f"{pid}\n")
        except IOError as e:
            self.logger.error(f"Không thể lưu PIDs: {e}")
    
    def _load_pids_from_file(self) -> List[int]:
        """Load PIDs from file."""
        pids = []
        if self.pids_file.exists():
            try:
                with open(self.pids_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.isdigit():
                            pids.append(int(line))
            except IOError as e:
                self.logger.error(f"Không thể đọc PIDs: {e}")
        return pids
    
    def cleanup_orphans(self):
        """Kill orphan Chrome processes from previous session."""
        old_pids = self._load_pids_from_file()
        
        if not old_pids:
            self.logger.info("Không tìm thấy tiến trình Chrome còn sót")
            return
        
        self.logger.info(f"Tìm thấy {len(old_pids)} tiến trình Chrome còn sót")
        
        killed = 0
        for pid in old_pids:
            if self._kill_process(pid):
                killed += 1
        
        if killed > 0:
            self.logger.success(f"Đã dọn dẹp {killed} tiến trình Chrome")
        
        # Clear the file
        self._clear_pids_file()
    
    def _kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        try:
            # Check if process exists
            if os.name == 'nt':  # Windows
                # Use taskkill on Windows
                result = subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.logger.debug(f"Đã dừng tiến trình {pid}")
                    return True
                else:
                    # Process might not exist anymore
                    return False
            else:  # Unix
                os.kill(pid, signal.SIGTERM)
                self.logger.debug(f"Đã dừng tiến trình {pid}")
                return True
        except (OSError, subprocess.SubprocessError):
            # Process doesn't exist or access denied
            return False
    
    def _clear_pids_file(self):
        """Clear the PIDs file."""
        self._current_pids = []
        if self.pids_file.exists():
            try:
                self.pids_file.unlink()
            except IOError:
                pass
    
    def kill_all_chromedriver(self) -> int:
        """Kill all chromedriver.exe processes."""
        killed = 0
        
        if os.name == 'nt':  # Windows
            try:
                result = subprocess.run(
                    ['taskkill', '/F', '/IM', 'chromedriver.exe'],
                    capture_output=True,
                    text=True
                )
                if 'SUCCESS' in result.stdout:
                    self.logger.info("Đã dừng tất cả chromedriver.exe")
                    killed = 1
            except subprocess.SubprocessError as e:
                self.logger.error(f"Không thể dừng chromedriver: {e}")
        else:
            try:
                subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True)
                killed = 1
            except subprocess.SubprocessError:
                pass
        
        return killed
    
    def cleanup_on_exit(self):
        """Cleanup when app exits normally."""
        self.logger.info("Đang dọn dẹp tiến trình Chrome...")
        
        for pid in self._current_pids:
            self._kill_process(pid)
        
        self._clear_pids_file()
        self.logger.success("Đã dọn dẹp xong")


# Global instance
_cleaner_instance = None


def get_cleaner() -> ProcessCleaner:
    """Get global process cleaner instance."""
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = ProcessCleaner()
    return _cleaner_instance

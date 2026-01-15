"""
Thread Manager - Multi-threading management for parallel processing
"""
import threading
import queue
from typing import Callable, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, Future

from .config import get_config
from .logger import get_logger


class Task:
    """Represents a task to be executed."""
    
    def __init__(self, func: Callable, args: tuple = (), kwargs: dict = None):
        """
        Create a task.
        
        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.result = None
        self.error = None
        self.completed = False


class ThreadManager:
    """Manage multiple worker threads."""
    
    def __init__(self, max_workers: int = None):
        """
        Initialize thread manager.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.config = get_config()
        self.logger = get_logger()
        
        if max_workers is None:
            max_workers = self.config.get("thread_count", 1)
        
        self.max_workers = min(max_workers, 20)  # Cap at 20
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: List[Future] = []
        self._running = False
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the thread pool."""
        if self._running:
            self.logger.warning("Thread manager đang chạy rồi")
            return
        
        self.logger.info(f"Đang khởi động thread manager với {self.max_workers} luồng")
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="Thread"
        )
        self._running = True
        self._stop_event.clear()
    
    def submit(self, func: Callable, *args, **kwargs) -> Optional[Future]:
        """
        Submit a task for execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Future object or None if not running
        """
        if not self._running or not self._executor:
            self.logger.error("Thread manager chưa chạy")
            return None
        
        future = self._executor.submit(self._wrap_task, func, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def _wrap_task(self, func: Callable, *args, **kwargs) -> Any:
        """Wrap task with error handling."""
        thread_name = threading.current_thread().name
        
        try:
            self.logger.debug(f"Task bắt đầu")
            result = func(*args, **kwargs)
            self.logger.debug(f"Task hoàn thành")
            return result
        except Exception as e:
            self.logger.error(f"Task thất bại: {e}")
            raise
    
    def should_stop(self) -> bool:
        """Check if tasks should stop."""
        return self._stop_event.is_set()
    
    def stop(self):
        """Signal all tasks to stop."""
        self.logger.info("Đang dừng thread manager...")
        self._stop_event.set()
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool.
        
        Args:
            wait: Wait for tasks to complete
        """
        if not self._running:
            return
        
        self._stop_event.set()
        
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
        
        self._running = False
        self._futures.clear()
        
        self.logger.info("Đã tắt thread manager")
    
    def wait_all(self, timeout: float = None) -> List[Any]:
        """
        Wait for all submitted tasks to complete.
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            List of results
        """
        results = []
        
        for future in self._futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                results.append(None)
                self.logger.error(f"Task lỗi: {e}")
        
        return results
    
    def get_active_count(self) -> int:
        """Get number of active tasks."""
        if not self._running:
            return 0
        
        active = sum(1 for f in self._futures if not f.done())
        return active
    
    def is_running(self) -> bool:
        """Check if thread manager is running."""
        return self._running


class WorkerThread(threading.Thread):
    """Individual worker thread for task execution."""
    
    def __init__(self, thread_id: int, task_queue: queue.Queue, 
                 stop_event: threading.Event):
        """
        Create worker thread.
        
        Args:
            thread_id: Thread identifier
            task_queue: Queue to get tasks from
            stop_event: Event to signal stop
        """
        super().__init__(name=f"Thread-{thread_id}")
        self.thread_id = thread_id
        self.task_queue = task_queue
        self.stop_event = stop_event
        self.logger = get_logger()
        self.daemon = True
    
    def run(self):
        """Run the worker thread."""
        self.logger.info(f"Worker đã bắt đầu")
        
        while not self.stop_event.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                
                if task is None:  # Poison pill
                    break
                
                try:
                    task.result = task.func(*task.args, **task.kwargs)
                    task.completed = True
                except Exception as e:
                    task.error = e
                    self.logger.error(f"Task thất bại: {e}")
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
        
        self.logger.info(f"Worker đã dừng")


# Global instance
_manager_instance = None


def get_thread_manager() -> ThreadManager:
    """Get global thread manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ThreadManager()
    return _manager_instance

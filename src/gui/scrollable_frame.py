"""
Scrollable Frame Widget - Provides scrollable container for tabs
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ScrollableFrame(ttk.Frame):
    """
    Frame có thể cuộn được với scrollbar.
    Sử dụng Canvas và Frame bên trong để tạo scrollable area.
    """
    
    def __init__(self, parent, **kwargs):
        """Khởi tạo scrollable frame."""
        super().__init__(parent, **kwargs)
        
        # Create canvas
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Create vertical scrollbar
        self._scrollbar = ttk.Scrollbar(
            self,
            orient=VERTICAL,
            command=self._canvas.yview,
            bootstyle="rounded"
        )
        self._scrollbar.pack(side=RIGHT, fill=Y)
        
        # Configure canvas
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        # Create inner frame for content
        self.inner = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self.inner,
            anchor=NW
        )
        
        # Bind events
        self.inner.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)
    
    def _on_frame_configure(self, event):
        """Cập nhật scroll region khi inner frame thay đổi kích thước."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Cập nhật inner frame width khi canvas thay đổi kích thước."""
        self._canvas.itemconfig(self._canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Xử lý cuộn chuột."""
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _bind_mousewheel(self, event):
        """Binding mouse wheel khi chuột vào frame."""
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_mousewheel(self, event):
        """Unbind mouse wheel khi chuột rời frame."""
        self._canvas.unbind_all("<MouseWheel>")
    
    def scroll_to_top(self):
        """Cuộn lên đầu."""
        self._canvas.yview_moveto(0)
    
    def scroll_to_bottom(self):
        """Cuộn xuống cuối."""
        self._canvas.yview_moveto(1)

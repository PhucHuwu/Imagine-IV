"""
Prompt Card Widget - Reusable expandable prompt input card
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Callable, Optional


class PromptCard(ttk.Frame):
    """
    Prompt card widget với chức năng expand/collapse.
    
    Có thể dùng cho cả Image Tab (1 text area) và Video Tab (1 hoặc 2 text areas).
    """
    
    def __init__(
        self,
        parent,
        index: int,
        initial_text: str = "",
        show_video2: bool = False,
        video2_text: str = "",
        on_delete: Optional[Callable[[int], None]] = None,
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Khởi tạo prompt card.
        
        Args:
            parent: Widget cha
            index: Số thứ tự card (1-based)
            initial_text: Text ban đầu cho prompt 1
            show_video2: Nếu True, hiện text area thứ 2 cho video 12s
            video2_text: Text ban đầu cho prompt 2 (video 12s)
            on_delete: Callback khi nhấn nút xóa
            on_change: Callback khi text thay đổi
        """
        super().__init__(parent, **kwargs)
        
        self.index = index
        self._on_delete = on_delete
        self._on_change = on_change
        self._show_video2 = show_video2
        self._expanded = False
        
        self._setup_ui(initial_text, video2_text)
    
    def _setup_ui(self, initial_text: str, video2_text: str):
        """Thiết lập UI components."""
        # Outer frame with border
        self.configure(bootstyle="secondary", padding=5)
        
        # Header frame
        header = ttk.Frame(self)
        header.pack(fill=X, pady=(0, 5))
        
        # Title label
        title_text = f"Prompt {self.index}" if not self._show_video2 else f"Batch {self.index}"
        self._title_label = ttk.Label(
            header,
            text=title_text,
            font=("", 10, "bold")
        )
        self._title_label.pack(side=LEFT)
        
        # Delete button (X)
        self._delete_btn = ttk.Button(
            header,
            text="X",
            bootstyle="danger-outline",
            width=3,
            command=self._on_delete_click
        )
        self._delete_btn.pack(side=RIGHT, padx=2)
        
        # Expand/Collapse button
        self._expand_btn = ttk.Button(
            header,
            text="▼",
            bootstyle="secondary-outline",
            width=3,
            command=self._toggle_expand
        )
        self._expand_btn.pack(side=RIGHT, padx=2)
        
        # Content frame for text areas
        content = ttk.Frame(self)
        content.pack(fill=BOTH, expand=True)
        
        # Text area 1 (main prompt or video1_prompt)
        if self._show_video2:
            ttk.Label(content, text="Prompt Video 1:", foreground="gray").pack(anchor=W)
        
        self._text1_frame = ttk.Frame(content)
        self._text1_frame.pack(fill=X, pady=2)
        
        self._text1 = tk.Text(
            self._text1_frame,
            height=1,
            wrap=tk.WORD,
            font=("", 10)
        )
        self._text1.pack(fill=X, expand=True)
        self._text1.insert("1.0", initial_text)
        self._text1.bind("<<Modified>>", self._on_text_change)
        self._text1.bind("<KeyRelease>", self._on_text_change)
        
        # Text area 2 (for video 12s)
        self._text2 = None
        if self._show_video2:
            ttk.Label(content, text="Prompt Video 2:", foreground="gray").pack(anchor=W, pady=(5, 0))
            
            self._text2_frame = ttk.Frame(content)
            self._text2_frame.pack(fill=X, pady=2)
            
            self._text2 = tk.Text(
                self._text2_frame,
                height=1,
                wrap=tk.WORD,
                font=("", 10)
            )
            self._text2.pack(fill=X, expand=True)
            self._text2.insert("1.0", video2_text)
            self._text2.bind("<<Modified>>", self._on_text_change)
            self._text2.bind("<KeyRelease>", self._on_text_change)
    
    def _toggle_expand(self):
        """Toggle expand/collapse text areas."""
        self._expanded = not self._expanded
        
        if self._expanded:
            self._expand_btn.configure(text="▲")
            self._auto_resize_text(self._text1)
            if self._text2:
                self._auto_resize_text(self._text2)
        else:
            self._expand_btn.configure(text="▼")
            self._text1.configure(height=1)
            if self._text2:
                self._text2.configure(height=1)
    
    def _auto_resize_text(self, text_widget: tk.Text):
        """Tự động resize text area theo nội dung."""
        content = text_widget.get("1.0", tk.END)
        lines = content.count('\n') + 1
        # Tính số dòng dựa trên độ dài text và wrap
        char_count = len(content)
        # Ước tính khoảng 80 ký tự / dòng
        estimated_lines = max(lines, (char_count // 80) + 1)
        # Giới hạn tối đa 10 dòng
        height = min(max(estimated_lines, 2), 10)
        text_widget.configure(height=height)
    
    def _on_delete_click(self):
        """Xử lý khi nhấn nút xóa."""
        if self._on_delete:
            self._on_delete(self.index)
    
    def _on_text_change(self, event=None):
        """Xử lý khi text thay đổi."""
        # Reset modified flag
        if hasattr(event, 'widget'):
            event.widget.edit_modified(False)
        
        if self._on_change:
            self._on_change()
    
    def get_prompts(self) -> dict:
        """
        Lấy nội dung prompts.
        
        Returns:
            Dict với keys: 'video1' (và 'video2' nếu show_video2=True)
            hoặc chỉ text string nếu là image prompt
        """
        text1 = self._text1.get("1.0", tk.END).strip()
        
        if self._show_video2:
            text2 = self._text2.get("1.0", tk.END).strip() if self._text2 else ""
            return {"video1": text1, "video2": text2}
        else:
            return text1
    
    def set_prompts(self, video1: str, video2: str = ""):
        """Set nội dung prompts."""
        self._text1.delete("1.0", tk.END)
        self._text1.insert("1.0", video1)
        
        if self._text2 and video2:
            self._text2.delete("1.0", tk.END)
            self._text2.insert("1.0", video2)
    
    def update_index(self, new_index: int):
        """Cập nhật số thứ tự card."""
        self.index = new_index
        title_text = f"Prompt {self.index}" if not self._show_video2 else f"Batch {self.index}"
        self._title_label.configure(text=title_text)
    
    def set_show_video2(self, show: bool):
        """
        Thay đổi chế độ hiển thị (1 hay 2 text areas).
        Cần rebuild UI nếu thay đổi.
        """
        if self._show_video2 != show:
            self._show_video2 = show
            # Lấy text hiện tại
            current_text1 = self._text1.get("1.0", tk.END).strip()
            current_text2 = self._text2.get("1.0", tk.END).strip() if self._text2 else ""
            
            # Clear và rebuild
            for widget in self.winfo_children():
                widget.destroy()
            
            self._setup_ui(current_text1, current_text2)


class PromptCardsContainer(ttk.Frame):
    """
    Container quản lý nhiều PromptCard widgets.
    """
    
    def __init__(
        self,
        parent,
        show_video2: bool = False,
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Khởi tạo container.
        
        Args:
            parent: Widget cha
            show_video2: Nếu True, mỗi card có 2 text areas (cho video 12s)
            on_change: Callback khi có thay đổi (thêm/xóa/edit)
        """
        super().__init__(parent, **kwargs)
        
        self._show_video2 = show_video2
        self._on_change = on_change
        self._cards: list[PromptCard] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Thiết lập UI."""
        # Scrollable frame for cards
        self._cards_frame = ttk.Frame(self)
        self._cards_frame.pack(fill=BOTH, expand=True)
        
        # Add button frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, pady=10)
        
        self._add_btn = ttk.Button(
            btn_frame,
            text="+ Thêm prompt",
            bootstyle="success-outline",
            command=self._add_card
        )
        self._add_btn.pack(side=LEFT)
        
        # Count label
        self._count_label = ttk.Label(
            btn_frame,
            text="Số batch: 0",
            foreground="gray"
        )
        self._count_label.pack(side=RIGHT)
    
    def _add_card(self, initial_text: str = "", video2_text: str = ""):
        """Thêm một prompt card mới."""
        index = len(self._cards) + 1
        
        card = PromptCard(
            self._cards_frame,
            index=index,
            initial_text=initial_text,
            show_video2=self._show_video2,
            video2_text=video2_text,
            on_delete=self._delete_card,
            on_change=self._on_card_change
        )
        card.pack(fill=X, pady=5)
        
        self._cards.append(card)
        self._update_count()
        self._notify_change()
    
    def _delete_card(self, index: int):
        """Xóa card theo index."""
        # Tìm card với index tương ứng
        card_to_remove = None
        for card in self._cards:
            if card.index == index:
                card_to_remove = card
                break
        
        if card_to_remove:
            card_to_remove.destroy()
            self._cards.remove(card_to_remove)
            
            # Re-index remaining cards
            for i, card in enumerate(self._cards):
                card.update_index(i + 1)
            
            self._update_count()
            self._notify_change()
    
    def _on_card_change(self):
        """Callback khi một card thay đổi."""
        self._notify_change()
    
    def _notify_change(self):
        """Thông báo thay đổi ra ngoài."""
        if self._on_change:
            self._on_change()
    
    def _update_count(self):
        """Cập nhật label số batch."""
        count = len(self._cards)
        self._count_label.configure(text=f"Số batch: {count}")
    
    def get_all_prompts(self) -> list:
        """
        Lấy tất cả prompts từ các cards.
        
        Returns:
            List of prompts (strings cho image, dicts cho video)
        """
        return [card.get_prompts() for card in self._cards]
    
    def set_prompts(self, prompts: list):
        """
        Set prompts từ list (load từ config).
        
        Args:
            prompts: List of prompts (strings hoặc dicts)
        """
        # Clear existing cards
        self.clear()
        
        # Add cards với data
        for prompt in prompts:
            if isinstance(prompt, dict):
                self._add_card(
                    initial_text=prompt.get("video1", ""),
                    video2_text=prompt.get("video2", "")
                )
            else:
                self._add_card(initial_text=str(prompt))
    
    def clear(self):
        """Xóa tất cả cards."""
        for card in self._cards:
            card.destroy()
        self._cards.clear()
        self._update_count()
    
    def set_show_video2(self, show: bool):
        """
        Thay đổi chế độ hiển thị cho tất cả cards.
        """
        if self._show_video2 != show:
            self._show_video2 = show
            for card in self._cards:
                card.set_show_video2(show)
            
            # Update add button text
            self._add_btn.configure(
                text="+ Thêm batch" if show else "+ Thêm prompt"
            )
    
    def get_count(self) -> int:
        """Lấy số lượng cards."""
        return len(self._cards)

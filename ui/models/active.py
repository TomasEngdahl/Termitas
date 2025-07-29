import customtkinter as ctk
from config import config
from ui.common.label_with_border import LabelWithBorder

class ActiveBody:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame
        self.is_expanded = True
        self.content_frame = None

    def create_active_body(self):
        # Header with collapse/expand functionality
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Clickable header label
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="➖ Active Model",
            font=(config.header_font, 16),
            text_color=config.blue,
            cursor="hand2"
        )
        self.header_label.pack(side="left", anchor="w")
        self.header_label.bind("<Button-1>", self.toggle_section)

        # Create compact content frame - just one row
        self.content_frame = ctk.CTkFrame(self.frame)
        self.content_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Compact content - single line
        content_label = ctk.CTkLabel(
            self.content_frame,
            text="No active model selected",
            font=(config.body_font, 12),
            text_color=config.header_font_color
        )
        content_label.pack(pady=10)

    def toggle_section(self, event=None):
        """Toggle the visibility of the content section."""
        if self.is_expanded:
            # Collapse - only show header
            self.content_frame.pack_forget()
            self.header_label.configure(text="➕ Active Model")
            self.is_expanded = False
        else:
            # Expand - show content
            self.content_frame.pack(fill="x", padx=5, pady=(0, 5))
            self.header_label.configure(text="➖ Active Model")
            self.is_expanded = True




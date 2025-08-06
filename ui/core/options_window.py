import customtkinter as ctk
from config import config
from ui.models.active import ActiveBody
from ui.models.downloaded import DownloadedBody
from ui.models.list_models import ListModels

class OptionsWindow:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame

    def create_options_window(self):
        # Ensure the main frame respects grid.py hardcoded sizes (580x780)
        self.frame.pack_propagate(False)
        
        # Create dedicated frames for each section with proper sizing
        
        # Active Model Section - Small initial height, like Downloaded Models
        self.active_frame = ctk.CTkFrame(self.frame, height=80)
        self.active_frame.pack(fill="x", padx=0, pady=(5, 2))
        # Allow this frame to adjust height naturally like Downloaded Models
        
        self.active_body = ActiveBody(self.app, self.active_frame)
        self.active_body.create_active_body()

        # Downloaded Models Section - Small initial height, full width  
        self.downloaded_frame = ctk.CTkFrame(self.frame, height=80)
        self.downloaded_frame.pack(fill="x", padx=0, pady=2)
        # Allow this frame to grow with content when models are added
        
        self.downloaded_body = DownloadedBody(self.app, self.downloaded_frame)
        self.downloaded_body.create_downloaded_body()

        # Model Browser Section - Starts expanded (takes remaining space)
        self.browser_frame = ctk.CTkFrame(self.frame)
        self.browser_frame.pack(fill="both", expand=True, padx=0, pady=(2, 5))
        
        self.list_models = ListModels(self.app, self.browser_frame)
        # Pass reference to the outer frame so it can change packing behavior
        self.list_models.outer_frame = self.browser_frame
        # Pass reference to downloaded models for refresh notifications
        self.list_models.downloaded_body = self.downloaded_body
        self.list_models.create_list_models()

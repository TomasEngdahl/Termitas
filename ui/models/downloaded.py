from ui.common.label_with_border import LabelWithBorder
import customtkinter as ctk
from config import config

class DownloadedBody:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame

    def create_downloaded_body(self):
        self.label_with_border = LabelWithBorder(self.app,
                                                 self.frame,
                                                 border_color=config.blue,
                                                 text="Choose Model",
                                                 font=(config.header_font, 16),
                                                 text_color=config.blue,
                                                 corner_radius=5,
                                                 anchor="w")
        self.label_with_border.create_label_with_border()
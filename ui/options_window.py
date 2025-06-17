import customtkinter as ctk
from config import config

class OptionsWindow:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame

    def create_options_window(self):

        self.frame.pack_propagate(False)
        self.label = ctk.CTkLabel(self.frame, text="Options", font=(config.header_font, config.header_font_size), text_color=config.header_font_color)
        self.label.pack(padx=20, pady=5)
import customtkinter as ctk
from config import config
from ui.common.label_with_border import LabelWithBorder

class ActiveBody:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame

    def create_active_body(self):
        self.frame.pack_propagate(False)

        self.label_with_border = LabelWithBorder(self.app,
                                                 self.frame,
                                                 border_color=config.blue,
                                                 text="Active Model",
                                                 font=(config.header_font, 16),
                                                 text_color=config.blue,
                                                 corner_radius=5,
                                                 anchor="w")
        self.label_with_border.create_label_with_border()




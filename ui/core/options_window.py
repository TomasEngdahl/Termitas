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
        self.active_body = ActiveBody(self.app, self.frame)
        self.active_body.create_active_body()

        self.downloaded_body = DownloadedBody(self.app, self.frame)
        self.downloaded_body.create_downloaded_body()

        self.list_models = ListModels(self.app, self.frame)
        self.list_models.create_list_models()

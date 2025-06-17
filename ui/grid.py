import customtkinter as ctk
from ui.terminal_window import TerminalWindow
from ui.chat_window import ChatWindow
from ui.options_window import OptionsWindow

class Grid:
    def __init__(self, app: ctk.CTk):
        super().__init__()
        self.app = app
        self.app.frame_1 = ctk.CTkFrame(self.app, width=580, height=780)
        self.app.frame_2 = ctk.CTkFrame(self.app, width=580, height=780)
        self.app.frame_3 = ctk.CTkFrame(self.app, width=580, height=780)


    def create_grid(self):

        self.app.frame_1.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.app.frame_2.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
        self.app.frame_3.grid(row=0, column=2, padx=10, pady=(10, 0), sticky="w")
        
        self.app.terminal_window = TerminalWindow(self.app, self.app.frame_3)
        self.app.terminal_window.create_terminal_window()

        self.app.chat_window = ChatWindow(self.app, self.app.frame_2)
        self.app.chat_window.create_chat_window()

        self.app.options_window = OptionsWindow(self.app, self.app.frame_1)
        self.app.options_window.create_options_window()

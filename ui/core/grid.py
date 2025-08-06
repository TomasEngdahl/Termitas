import customtkinter as ctk
from ui.core.terminal_window import TerminalWindow
from ui.core.chat_window import ChatWindow
from ui.core.options_window import OptionsWindow

class Grid:
    def __init__(self, app: ctk.CTk):
        super().__init__()
        self.app = app
        self.app.frame_1 = ctk.CTkFrame(self.app)
        self.app.frame_2 = ctk.CTkFrame(self.app)
        self.app.frame_3 = ctk.CTkFrame(self.app)


    def create_grid(self):
        # Configure grid weights for proper expansion
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_columnconfigure(2, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        self.app.frame_1.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        self.app.frame_2.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")
        self.app.frame_3.grid(row=0, column=2, padx=10, pady=(10, 0), sticky="nsew")
        
        # Create components
        self.app.terminal_window = TerminalWindow(self.app, self.app.frame_3)
        self.app.chat_window = ChatWindow(self.app, self.app.frame_2)
        self.app.options_window = OptionsWindow(self.app, self.app.frame_1)
        
        # Initialize all windows first
        self.app.terminal_window.create_terminal_window()
        self.app.chat_window.create_chat_window()
        self.app.options_window.create_options_window()
        
        # Set up cross-references for communication after initialization
        self.app.chat_window.terminal_window = self.app.terminal_window
        self.app.terminal_window.chat_window = self.app.chat_window
        self.app.chat_window.active_model_section = self.app.options_window.active_body
        
        # Store reference to options window in main app for GPU status updates
        self.app.options_window_ref = self.app.options_window

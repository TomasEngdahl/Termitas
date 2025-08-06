import customtkinter as ctk
from config import config
from typing import List, Dict
import subprocess
import threading
from datetime import datetime

class TerminalWindow:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        self.app = app
        self.frame = frame
        
        # Terminal state
        self.command_history: List[Dict] = []
        self.active_tasks: List[Dict] = []
        
        # UI components
        self.terminal_display = None
        self.status_label = None
        
        # References to other components
        self.chat_window = None
        
    def create_terminal_window(self):
        """Create the terminal interface."""
        
        # Configure main frame to respect parent dimensions
        self.frame.pack_propagate(False)
        
        # Header section
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="💻 Terminal Execution",
            font=(config.header_font, 18, "bold"),
            text_color=config.blue
        )
        title_label.pack(anchor="w", pady=(5, 0))
        
        # Status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Ready to execute commands",
            font=(config.body_font, 11),
            text_color=config.green
        )
        self.status_label.pack(anchor="w", pady=(5, 0))
        
        # Terminal display area
        terminal_frame = ctk.CTkFrame(self.frame)
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.terminal_display = ctk.CTkScrollableFrame(terminal_frame)
        self.terminal_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Show initial message
        self.show_welcome_message()
    
    def show_welcome_message(self):
        """Show welcome message in terminal display."""
        welcome_text = """💻 Terminal Ready

This panel will show:
• 🚀 Commands executed by the AI agent
• 📊 Real-time command output
• ⚡ Task progress and results
• 🔧 System status information

Commands will appear here when you chat with the AI agent and request terminal operations.

Ready to execute commands! 🎯"""
        
        self.add_terminal_message("system", welcome_text, show_timestamp=False)
    
    def add_terminal_message(self, sender: str, content: str, show_timestamp: bool = True):
        """Add a system message to the terminal display."""
        message_frame = ctk.CTkFrame(self.terminal_display)
        message_frame.pack(fill="x", pady=5, padx=10)
        
        # Message header
        header_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(8, 2))
        
        # Sender info
        if sender == "system":
            sender_text = "🔧 System"
            sender_color = config.yellow
        elif sender == "command":
            sender_text = "💻 Command"
            sender_color = config.blue
        elif sender == "output":
            sender_text = "📊 Output"
            sender_color = config.green
        else:
            sender_text = "💻 Terminal"
            sender_color = config.blue
        
        sender_label = ctk.CTkLabel(
            header_frame,
            text=sender_text,
            font=(config.body_font, 11, "bold"),
            text_color=sender_color
        )
        sender_label.pack(side="left")
        
        # Timestamp
        if show_timestamp:
            timestamp = datetime.now().strftime("%H:%M")
            time_label = ctk.CTkLabel(
                header_frame,
                text=timestamp,
                font=(config.body_font, 9),
                text_color="#666666"
            )
            time_label.pack(side="right")
        
        # Message content
        content_label = ctk.CTkLabel(
            message_frame,
            text=content,
            font=(config.body_font, 11),
            text_color=config.header_font_color,
            wraplength=400,
            justify="left"
        )
        content_label.pack(fill="x", padx=10, pady=(0, 8), anchor="w")
        
        # Scroll to bottom
        self.app.after(10, lambda: self.terminal_display._parent_canvas.yview_moveto(1.0))
        
        return message_frame
    
    def add_command_output(self, command: str, source: str = "User"):
        """Add a command and its output to the terminal display."""
        # Add command
        self.add_terminal_message("command", f"$ {command}")
        
        # TODO: Execute command and show output
        # For now, just show a placeholder
        self.add_terminal_message("output", f"Command from {source} - Execution pending...")
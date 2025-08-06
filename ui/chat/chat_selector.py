import customtkinter as ctk
from config import config
from database.chat_db import get_chat_sessions, create_chat_session, delete_chat_session
from typing import Callable, Optional

class ChatSelector:
    def __init__(self, parent_frame: ctk.CTkFrame, on_session_change: Callable[[int], None]):
        self.parent_frame = parent_frame
        self.on_session_change = on_session_change
        self.current_session_id: Optional[int] = None
        
        # UI components
        self.selector_frame = None
        self.session_var = None
        self.session_menu = None
        self.new_chat_button = None
        self.delete_chat_button = None
        
        self.create_selector()
        self.refresh_sessions()
    
    def create_selector(self):
        """Create the chat selector UI."""
        self.selector_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self.selector_frame.pack(fill="x", pady=(0, 5))
        
        # Session selector
        self.session_var = ctk.StringVar(value="New Chat")
        
        self.session_menu = ctk.CTkOptionMenu(
            self.selector_frame,
            variable=self.session_var,
            command=self._on_session_selected,
            width=200,
            height=30,
            font=(config.body_font, 11)
        )
        self.session_menu.pack(side="left", padx=(0, 10))
        
        # New chat button
        self.new_chat_button = ctk.CTkButton(
            self.selector_frame,
            text="🆕 New",
            width=60,
            height=30,
            font=(config.body_font, 10),
            command=self.create_new_chat,
            fg_color="#4682b4",
            hover_color="#4169e1"
        )
        self.new_chat_button.pack(side="left", padx=(0, 5))
        
        # Delete chat button
        self.delete_chat_button = ctk.CTkButton(
            self.selector_frame,
            text="🗑️",
            width=30,
            height=30,
            font=(config.body_font, 10),
            command=self.delete_current_chat,
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        self.delete_chat_button.pack(side="left")
    
    def refresh_sessions(self):
        """Refresh the list of available chat sessions."""
        sessions = get_chat_sessions()
        
        # Clear existing options
        self.session_menu.configure(values=[])
        
        # Add sessions to menu
        session_options = ["New Chat"]
        session_ids = [None]
        
        for session in sessions:
            name = session['name']
            if session.get('message_count', 0) > 0:
                name += f" ({session['message_count']} messages)"
            session_options.append(name)
            session_ids.append(session['id'])
        
        self.session_menu.configure(values=session_options)
        self.session_ids = session_ids
        
        # Update delete button state
        self.delete_chat_button.configure(state="normal" if self.current_session_id else "disabled")
    
    def _on_session_selected(self, selection: str):
        """Handle session selection."""
        if selection == "New Chat":
            self.create_new_chat()
        else:
            # Find the session ID for the selected session
            try:
                index = self.session_menu.cget("values").index(selection)
                session_id = self.session_ids[index]
                if session_id:
                    self.current_session_id = session_id
                    self.on_session_change(session_id)
            except (ValueError, IndexError):
                pass
    
    def create_new_chat(self):
        """Create a new chat session."""
        # For now, create with default name - will be updated when model is selected
        session_id = create_chat_session("New Chat", "unknown")
        self.current_session_id = session_id
        self.refresh_sessions()
        self.on_session_change(session_id)
    
    def delete_current_chat(self):
        """Delete the current chat session."""
        if self.current_session_id:
            if delete_chat_session(self.current_session_id):
                self.current_session_id = None
                self.refresh_sessions()
                self.on_session_change(None)
    
    def set_current_session(self, session_id: Optional[int]):
        """Set the current session ID."""
        self.current_session_id = session_id
        self.delete_chat_button.configure(state="normal" if session_id else "disabled")
    
    def update_session_name(self, session_id: int, name: str):
        """Update the name of a chat session."""
        # This would require adding an update function to chat_db.py
        # For now, just refresh the sessions
        self.refresh_sessions() 
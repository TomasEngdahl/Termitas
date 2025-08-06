import customtkinter as ctk
from config import config
from database.models_db import get_db
from database.chat_db import get_chat_messages, add_chat_message, get_chat_session
from ui.chat.chat_selector import ChatSelector
from llm.simple_inference import simple_inference
from typing import Optional, List, Dict
import threading
import time
from datetime import datetime
from ui.common.label_with_border import LabelWithBorder
from ui.core.window_utils import center_window

class ChatWindow:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        self.app = app
        self.frame = frame
        self.db = get_db()
        
        # Chat state
        self.active_model = None
        self.current_session_id: Optional[int] = None
        self.is_processing = False
        
        # UI components
        self.model_status_label = None
        self.chat_display = None
        self.input_field = None
        self.send_button = None
        self.clear_button = None
        self.model_selector = None
        
        # References to other components (set by main app)
        self.terminal_window = None
        self.active_model_section = None
        
        # Chat selector
        self.chat_selector = None

    def create_chat_window(self):
        """Create the chat interface."""

        # Configure main frame to respect parent dimensions
        self.frame.pack_propagate(False)
        
        # Header section
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 Terminal Agent Chat",
            font=(config.header_font, 18, "bold"),
            text_color=config.blue
        )
        title_label.pack(anchor="w", pady=(5, 0))
        
        # Chat selector
        self.chat_selector = ChatSelector(header_frame, self._on_session_change)
        
        # Model status display
        model_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        model_frame.pack(fill="x", pady=(5, 0))
        
        # Active model display
        self.model_status_label = ctk.CTkLabel(
            model_frame,
            text="No model selected",
            font=(config.body_font, 11),
            text_color=config.red
        )
        self.model_status_label.pack(side="left", anchor="w")
        
        # Chat display area
        chat_frame = ctk.CTkFrame(self.frame)
        chat_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.chat_display = ctk.CTkScrollableFrame(chat_frame)
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=80)
        input_frame.pack(fill="x", padx=10, pady=(5, 10))
        input_frame.pack_propagate(False)
        
        # Input field
        self.input_field = ctk.CTkTextbox(
            input_frame,
            height=50,
            font=(config.body_font, 12),
            wrap="word"
        )
        self.input_field.pack(fill="x", side="left", expand=True, padx=(0, 5))
        self.input_field.bind("<Return>", self._on_enter_key)
        self.input_field.bind("<Shift-Return>", self._on_shift_enter)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        buttons_frame.pack(side="right", fill="y")
        
        # Send button
        self.send_button = ctk.CTkButton(
            buttons_frame,
            text="🚀 Send",
            width=80,
            height=35,
            font=(config.body_font, 11),
            command=self.send_message,
            fg_color="#228b22",
            hover_color="#1e6b1e"
        )
        self.send_button.pack(pady=(0, 5))
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Clear",
            width=80,
            height=35,
            font=(config.body_font, 11),
            command=self.clear_chat,
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        self.clear_button.pack()
        
        # Show initial message
        self.show_welcome_message()
        
        # Check for available models
        self.refresh_model_status()
    
    def _on_session_change(self, session_id: Optional[int]):
        """Handle chat session change."""
        self.current_session_id = session_id
        self.load_session_messages(session_id)
    
    def load_session_messages(self, session_id: Optional[int]):
        """Load messages for the specified session."""
        # Clear current display
        for widget in self.chat_display.winfo_children():
            widget.destroy()
        
        if session_id:
            # Load messages from database
            messages = get_chat_messages(session_id)
            for message in messages:
                self.add_message(message['sender'], message['content'], show_timestamp=True, from_db=True)
        else:
            # Show welcome message for new chat
            self.show_welcome_message()
    
    def show_welcome_message(self):
        """Show welcome message in chat."""
        welcome_text = """🎯 Welcome to Terminal Agent!

I'm your AI assistant for terminal operations. I can help you:

• 📁 Navigate and manage files
• 🔍 Search and find content  
• 📊 Monitor system resources
• ⚙️ Configure applications
• 🚀 Automate tasks with scripts
• 💻 Execute complex command sequences

Select a model above and start chatting! Ask me things like:
• "Find all Python files larger than 1MB"
• "Show me disk usage and free space"
• "Create a backup of my project folder"
• "List running processes using high CPU"
"""
        
        self.add_message("assistant", welcome_text, show_timestamp=False)
    
    def refresh_model_status(self):
        """Update model status display."""
        # Get active model from active model section
        if self.active_model_section:
            self.active_model = self.active_model_section.active_model
        
        downloaded_models = self.db.get_all_models()
        
        if not downloaded_models:
            self.model_status_label.configure(
                text="❌ No models downloaded - Download models first",
                text_color=config.red
            )
            self.send_button.configure(state="disabled")
        elif not self.active_model:
            self.model_status_label.configure(
                text=f"⚠️ Select a model ({len(downloaded_models)} available)",
                text_color=config.yellow
            )
            self.send_button.configure(state="disabled")
        else:
            self.model_status_label.configure(
                text=f"✅ Active: {self.active_model['display_name']}",
                text_color=config.green
            )
            self.send_button.configure(state="normal")
    

    
    def _on_enter_key(self, event):
        """Handle Enter key (send message)."""
        self.send_message()
        return "break"  # Prevent default behavior
    
    def _on_shift_enter(self, event):
        """Handle Shift+Enter (new line)."""
        return None  # Allow default behavior (new line)
    
    def send_message(self):
        """Send user message and get AI response."""
        # Get active model from active model section
        if self.active_model_section:
            self.active_model = self.active_model_section.active_model
        
        if not self.active_model:
            self.show_message("No Model", "Please select a model first.")
            return
        
        user_input = self.input_field.get("1.0", "end-1c").strip()
        if not user_input:
            return
        
        # Clear input
        self.input_field.delete("1.0", "end")
        
        # Add user message
        self.add_message("user", user_input)
        
        # Show typing indicator
        thinking_message = self.add_message("assistant", "🤔 Thinking... (this may take 30-60 seconds on CPU)", temporary=True)
        
        # Process in background
        self.is_processing = True
        self.send_button.configure(state="disabled", text="🤔 Thinking...")
        
        threading.Thread(
            target=self._process_message,
            args=(user_input, thinking_message),
            daemon=True
        ).start()
    
    def _process_message(self, user_input: str, thinking_message):
        """Process user message and generate response."""
        try:
            # Get conversation history for context
            messages = []
            if self.current_session_id:
                db_messages = get_chat_messages(self.current_session_id)
                for msg in db_messages:
                    messages.append({
                        'role': msg['sender'],  # Convert sender to role
                        'content': msg['content']
                    })
            
            # Add current user message
            messages.append({
                'role': 'user',
                'content': user_input
            })
            
            print(f"Processing message with {len(messages)} messages in history")
            for i, msg in enumerate(messages):
                print(f"  Message {i}: {msg.get('role', 'unknown')} - '{msg.get('content', '')[:50]}...'")
            
            # Generate response using simple inference
            response = simple_inference.generate_response(messages)
            
            print(f"Handling AI response: '{response[:50]}...' (length: {len(response)})")
            
            # Save the response to database
            if self.current_session_id:
                add_chat_message(self.current_session_id, 'assistant', response)
            
            # Handle the response in the main thread
            self.app.after(0, lambda: self._handle_ai_response(response, thinking_message))
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()
            error_response = f"❌ Error generating response: {str(e)}"
            self.app.after(0, lambda: self._handle_ai_response(error_response, thinking_message))
    

    
    def _handle_ai_response(self, response: str, thinking_message):
        """Handle AI response in main thread."""
        print(f"Handling AI response: '{response[:100]}...' (length: {len(response)})")
        
        # Remove thinking message
        thinking_message.destroy()
        
        # Add AI response
        self.add_message("assistant", response)
        
        # Re-enable send button
        self.is_processing = False
        self.send_button.configure(state="normal", text="🚀 Send")
    
    def add_message(self, sender: str, content: str, show_timestamp: bool = True, temporary: bool = False, from_db: bool = False):
        """Add a message to the chat display."""
        message_frame = ctk.CTkFrame(self.chat_display)
        message_frame.pack(fill="x", pady=5, padx=10)
        
        # Message header
        header_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(8, 2))
        
        # Sender info
        if sender == "user":
            sender_text = "👤 You"
            sender_color = config.blue
        elif sender == "assistant":
            sender_text = f"🤖 {self.active_model['display_name'] if self.active_model else 'Assistant'}"
            sender_color = config.green
        else:  # system
            sender_text = "🔧 System"
            sender_color = config.yellow
        
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
        
        # Save message to database if not from database and we have an active session
        if not from_db and self.current_session_id and not temporary:
            add_chat_message(self.current_session_id, sender, content)
        
        # Scroll to bottom
        self.app.after(10, lambda: self.chat_display._parent_canvas.yview_moveto(1.0))
        
        return message_frame
    
    def clear_chat(self):
        """Clear chat history."""
        for widget in self.chat_display.winfo_children():
            widget.destroy()
        
        # Clear messages from database if we have an active session
        if self.current_session_id:
            from database.chat_db import clear_chat_messages
            clear_chat_messages(self.current_session_id)
        
        self.show_welcome_message()
    
    def show_message(self, title: str, message: str):
        """Show a message dialog."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(title)
        dialog.geometry("350x150")
        dialog.transient(self.app)
        dialog.grab_set()
        
        label = ctk.CTkLabel(
            dialog,
            text=message,
            font=(config.header_font, 12),
            text_color=config.header_font_color,
            wraplength=300
        )
        label.pack(pady=30)
        
        ok_button = ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy
        )
        ok_button.pack(pady=10)

    def show_error_dialog(self, title, message):
        """Show an error dialog."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.app)
        dialog.grab_set()
        
        # Center the window
        center_window(dialog, 400, 200)
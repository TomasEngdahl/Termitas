#!/usr/bin/env python3
"""
Settings Dialog for application configuration
"""

import customtkinter as ctk
from config import config
from ui.core.window_utils import center_window
from typing import Optional

class SettingsDialog:
    """Dialog for application settings."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        center_window(self.dialog, 500, 400)
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._center_dialog()
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="⚙️ Settings", font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # API Key section
        api_frame = ctk.CTkFrame(main_frame)
        api_frame.pack(fill="x", padx=10, pady=10)
        
        api_label = ctk.CTkLabel(api_frame, text="🔑 Hugging Face API Key", font=("Arial", 14, "bold"))
        api_label.pack(pady=(10, 5))
        
        self.api_key_entry = ctk.CTkEntry(api_frame, placeholder_text="Enter your Hugging Face API key", width=400, show="*")
        self.api_key_entry.pack(pady=5)
        self.api_key_entry.insert(0, self.api_key)
        
        api_help = ctk.CTkLabel(api_frame, text="Get your API key from: https://huggingface.co/settings/tokens", 
                               font=("Arial", 10), text_color="gray")
        api_help.pack(pady=5)
        
        # System Prompt section
        prompt_frame = ctk.CTkFrame(main_frame)
        prompt_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        prompt_label = ctk.CTkLabel(prompt_frame, text="🤖 System Prompt", font=("Arial", 14, "bold"))
        prompt_label.pack(pady=(10, 5))
        
        self.prompt_text = ctk.CTkTextbox(prompt_frame, height=150)
        self.prompt_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.prompt_text.insert("1.0", self.system_prompt)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Save button
        save_button = ctk.CTkButton(button_frame, text="💾 Save", command=self._save_settings)
        save_button.pack(side="right", padx=5)
        
        # Cancel button
        cancel_button = ctk.CTkButton(button_frame, text="❌ Cancel", command=self._cancel)
        cancel_button.pack(side="right", padx=5)
        
        # Test API button
        test_button = ctk.CTkButton(button_frame, text="🧪 Test API", command=self._test_api)
        test_button.pack(side="left", padx=5)
    
    def _center_dialog(self):
        """Center the dialog on screen."""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save_settings(self):
        """Save the settings."""
        self.api_key = self.api_key_entry.get().strip()
        self.system_prompt = self.prompt_text.get("1.0", "end-1c").strip()
        
        self.result = {
            'api_key': self.api_key,
            'system_prompt': self.system_prompt
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
    
    def _test_api(self):
        """Test the API key."""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self._show_message("❌ Please enter an API key first.")
            return
        
        # Simple API test
        import requests
        try:
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                username = user_info.get('name', 'Unknown')
                self._show_message(f"✅ API key is valid! Logged in as: {username}")
            else:
                self._show_message(f"❌ Invalid API key: {response.status_code}")
                
        except Exception as e:
            self._show_message(f"❌ Error testing API: {str(e)}")
    
    def _show_message(self, message: str):
        """Show a message to the user."""
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Message")
        dialog.geometry("400x150")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(expand=True, fill="both", padx=20, pady=20)
        
        button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
        button.pack(pady=10)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def show(self) -> Optional[dict]:
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result 

    def show_help_dialog(self):
        """Show help dialog."""
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Help")
        dialog.geometry("400x300")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Center the window
        center_window(dialog, 400, 300) 
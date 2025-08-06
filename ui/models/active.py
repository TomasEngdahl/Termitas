import customtkinter as ctk
from config import config
from ui.common.label_with_border import LabelWithBorder

class ActiveBody:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame
        self.is_expanded = True
        self.content_frame = None
        self.active_model = None
        self.status_label = None

    def create_active_body(self):
        # Header with collapse/expand functionality
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Clickable header label
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="➖ Active Model",
                                                 font=(config.header_font, 16),
                                                 text_color=config.blue,
            cursor="hand2"
        )
        self.header_label.pack(side="left", anchor="w")
        self.header_label.bind("<Button-1>", self.toggle_section)

        # Create compact content frame - just one row
        self.content_frame = ctk.CTkFrame(self.frame)
        self.content_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Status and selection area
        status_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="No active model selected",
            font=(config.body_font, 12),
            text_color=config.header_font_color
        )
        self.status_label.pack(side="left", anchor="w")
        
        # Select model button
        self.select_button = ctk.CTkButton(
            status_frame,
            text="📋 Select Model",
            width=100,
            height=25,
            font=(config.body_font, 10),
            command=self.show_model_selector,
            fg_color="#4682b4",
            hover_color="#4169e1"
        )
        self.select_button.pack(side="right")

    def toggle_section(self, event=None):
        """Toggle the visibility of the content section."""
        if self.is_expanded:
            # Collapse - only show header
            self.content_frame.pack_forget()
            self.header_label.configure(text="➕ Active Model")
            self.is_expanded = False
        else:
            # Expand - show content
            self.content_frame.pack(fill="x", padx=5, pady=(0, 5))
            self.header_label.configure(text="➖ Active Model")
            self.is_expanded = True
    
    def set_active_model(self, model):
        """Set the active model and update display."""
        self.active_model = model
        if model:
            self.status_label.configure(
                text=f"✅ {model['display_name']}",
                text_color=config.green
            )
        else:
            self.status_label.configure(
                text="No active model selected",
                text_color=config.header_font_color
            )
        
        # Notify chat window to refresh model status
        if hasattr(self.app, 'chat_window') and self.app.chat_window:
            self.app.chat_window.refresh_model_status()
    
    def show_model_selector(self):
        """Show model selection dialog."""
        from database.models_db import get_db
        db = get_db()
        downloaded_models = db.get_all_models()
        
        print(f"Found {len(downloaded_models)} downloaded models")
        for model in downloaded_models:
            print(f"Model: {model['display_name']} - Path: {model.get('local_path', 'No path')}")
        
        if not downloaded_models:
            self.show_message("No Models", "Please download models first from the Model Browser.")
            return
        
        # Create selection dialog
        selector_window = ctk.CTkToplevel(self.app)
        selector_window.title("Select AI Model")
        selector_window.geometry("500x400")
        selector_window.transient(self.app)
        selector_window.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            selector_window,
            text="🤖 Choose AI Model for Terminal Agent",
            font=(config.header_font, 16, "bold"),
            text_color=config.blue
        )
        title_label.pack(pady=20)
        
        # Models list
        models_frame = ctk.CTkScrollableFrame(selector_window)
        models_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for model in downloaded_models:
            model_card = ctk.CTkFrame(models_frame)
            model_card.pack(fill="x", pady=5, padx=5)
            
            # Model info
            info_frame = ctk.CTkFrame(model_card, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=8)
            
            name_label = ctk.CTkLabel(
                info_frame,
                text=model['display_name'],
                font=(config.body_font, 14, "bold"),
                text_color=config.header_font_color
            )
            name_label.pack(anchor="w")
            
            id_label = ctk.CTkLabel(
                info_frame,
                text=f"📦 {model['model_id']}",
                font=(config.body_font, 10),
                text_color="#8888aa"
            )
            id_label.pack(anchor="w")
            
            if model.get('description'):
                desc_label = ctk.CTkLabel(
                    info_frame,
                    text=f"🎯 {model['description']}",
                    font=(config.body_font, 10),
                    text_color="#8888aa"
                )
                desc_label.pack(anchor="w")
            
            # Select button
            select_button = ctk.CTkButton(
                info_frame,
                text="✅ Select This Model",
                command=lambda m=model: self.select_model(m, selector_window),
                fg_color="#228b22",
                hover_color="#1e6b1e"
            )
            select_button.pack(anchor="e", pady=(5, 0))
        
        # Close button
        close_button = ctk.CTkButton(
            selector_window,
            text="Cancel",
            command=selector_window.destroy
        )
        close_button.pack(pady=10)
    
    def select_model(self, model, dialog_window):
        """Select a model for chat."""
        print(f"Selecting model: {model['display_name']}")
        print(f"Model path: {model.get('local_path', 'No path')}")
        
        self.active_model = model
        
        # Set model for simple inference
        model_path = model.get('local_path')
        if model_path:
            print(f"Setting model for simple inference: {model_path}")
            from llm.simple_inference import simple_inference
            success = simple_inference.set_model(model_path)
            if not success:
                print(f"❌ Failed to load model: {model['display_name']}")
                self.show_message("Model Loading Error", 
                               f"Failed to load model '{model['display_name']}'. This might be due to:\n"
                               f"• Missing model files\n"
                               f"• Insufficient memory\n"
                               f"• Incompatible model architecture\n"
                               f"• Missing dependencies\n\n"
                               f"Check the console for detailed error messages.")
                return
        
        # Update the active model display
        self.set_active_model(model)
        
        # Notify chat window to refresh model status
        if hasattr(self.app, 'chat_window') and self.app.chat_window:
            self.app.chat_window.refresh_model_status()
        
        # Close the dialog
        if dialog_window:
            dialog_window.destroy()
        
        print(f"✅ Model selected: {model['display_name']}")
        self.show_message("Model Selected", f"Model '{model['display_name']}' is now active!")
    
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




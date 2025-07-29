import threading
import customtkinter as ctk
from config import config
from ui.common.label_with_border import LabelWithBorder
from hf.list import list_models_hf, format_model_size, format_downloads, get_model_description
from hf.system_info import get_vram_info, get_compatibility_info, get_system_summary
from typing import Optional

class ListModels:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        self.app = app
        self.frame = frame
        self.scrollable_frame = None
        self.label_with_border = None
        self.search_entry = None
        self.search_button = None
        self.tag_buttons = {}
        self.is_fetching = False
        self.current_fetch_id = 0
        self.current_search_term = ""
        
        # System info
        self.vram_info = None
        self.system_label = None

    def create_list_models(self):
        # Detect VRAM at startup
        self.detect_system_info()
        
        self.label_with_border = LabelWithBorder(
            self.app,
            self.frame,
            text="Model Browser & Downloader",
            font=(config.header_font, 16),
            text_color=config.blue,
            border_color=config.blue,
            corner_radius=5,
            anchor="w"
        )
        self.label_with_border.create_label_with_border()

        # System info display
        system_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        system_frame.pack(fill="x", padx=10, pady=2)

        self.system_label = ctk.CTkLabel(
            system_frame,
            text="🔍 Detecting system specifications...",
            font=(config.body_font, 11),
            text_color=config.yellow
        )
        self.system_label.pack(anchor="w")

        # Search controls frame
        search_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=5)

        # Search bar
        search_label = ctk.CTkLabel(search_frame, text="🔍 Search:", font=(config.body_font, 12))
        search_label.pack(side="left", padx=(0, 5))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Enter model name or keyword...",
            width=200,
            height=30
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.start_search())

        # Search button
        self.search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            width=80,
            height=30,
            command=self.start_search
        )
        self.search_button.pack(side="left", padx=5)

        # Popular button to get trending models
        popular_button = ctk.CTkButton(
            search_frame,
            text="📈 Popular",
            width=80,
            height=30,
            command=self.search_popular,
            fg_color="#666666",
            hover_color="#555555"
        )
        popular_button.pack(side="left", padx=5)

        # Tag buttons frame
        tags_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=10, pady=5)

        tags_label = ctk.CTkLabel(tags_frame, text="🏷️ Quick tags:", font=(config.body_font, 12))
        tags_label.pack(side="left", padx=(0, 10))

        # Popular model family tags
        model_tags = [
            ("Qwen", "#ff6b35"),
            ("Mistral", "#4a90e2"), 
            ("Llama", "#7b68ee"),
            ("DeepSeek", "#32cd32"),
            ("Gemma", "#ff69b4"),
            ("Phi", "#ffa500"),
            ("StarCoder", "#20b2aa"),
            ("WizardCoder", "#9370db")
        ]

        for tag_name, color in model_tags:
            button = ctk.CTkButton(
                tags_frame,
                text=tag_name,
                width=50,
                height=20,
                font=(config.body_font, 11),
                command=lambda name=tag_name: self.search_by_tag(name),
                fg_color="transparent",  # Use default frame background
                text_color=color,  # Colored text
                border_color=color,  # Colored border
                border_width=1,  # Visible border
                hover_color=("#f0f0f0", "#2b2b2b"),  # Subtle hover effect
                corner_radius=3
            )
            button.pack(side="left", padx=1)
            self.tag_buttons[tag_name] = button

        # Create the persistent scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.show_initial_message()

    def detect_system_info(self):
        """Detect system VRAM in background thread."""
        def detect_in_background():
            self.vram_info = get_vram_info()
            # Update UI in main thread
            self.app.after(0, self.update_system_display)
        
        threading.Thread(target=detect_in_background, daemon=True).start()

    def update_system_display(self):
        """Update the system info display."""
        if self.system_label and self.vram_info:
            summary = get_system_summary(self.vram_info)
            self.system_label.configure(text=summary, text_color=config.green)

    def search_by_tag(self, tag_name):
        """Search for models by tag name."""
        self.search_entry.delete(0, 'end')
        self.search_entry.insert(0, tag_name.lower())
        self.current_search_term = tag_name.lower()
        self.start_search()

    def search_popular(self):
        """Search for popular models."""
        self.search_entry.delete(0, 'end')
        self.current_search_term = ""
        self.start_search()

    def start_search(self):
        """Start searching with current search term."""
        if self.is_fetching:
            return
            
        search_term = self.search_entry.get().strip() or self.current_search_term
        self.current_search_term = search_term
            
        self.is_fetching = True
        self.current_fetch_id += 1
        current_id = self.current_fetch_id
        
        self.show_loading_message(search_term)
        self.search_button.configure(state="disabled", text="Searching...")
        
        threading.Thread(target=self.search_models_in_background, args=(current_id, search_term), daemon=True).start()

    def show_initial_message(self):
        self.clear_content()
        
        initial_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="🔍 Search for any model by name or keyword\n\n🏷️ Use quick tags to find popular model families\n\n📈 Click 'Popular' to see trending models\n\n💡 Compatibility info will show for each model",
            font=(config.body_font, 14),
            text_color=config.header_font_color,
            wraplength=500,
            justify="center"
        )
        initial_label.pack(pady=30)

    def clear_content(self):
        for widget in self.scrollable_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        self.app.update_idletasks()

    def show_loading_message(self, search_term):
        self.clear_content()
        
        if search_term:
            message = f"🔄 Searching for '{search_term}' models..."
        else:
            message = "🔄 Fetching popular models..."
            
        loading_label = ctk.CTkLabel(
            self.scrollable_frame,
            text=message,
            text_color=config.yellow,
            font=(config.header_font, 14)
        )
        loading_label.pack(pady=20)

    def search_models_in_background(self, fetch_id, search_term):
        try:
            if search_term:
                # Search with specific term
                models = list_models_hf(limit=30, search_term=search_term)
            else:
                # Get popular models
                models = list_models_hf(limit=20, filter_for_coding=False)
            
            if fetch_id == self.current_fetch_id:
                self.app.after(0, lambda: self.show_models_content(models, fetch_id, search_term))
            else:
                self.app.after(0, lambda: self.reset_search_state())
            
        except Exception as e:
            if fetch_id == self.current_fetch_id:
                self.app.after(0, lambda: self.show_error_content(str(e), fetch_id))
            else:
                self.app.after(0, lambda: self.reset_search_state())

    def reset_search_state(self):
        self.search_button.configure(state="normal", text="Search")
        self.is_fetching = False

    def show_error_content(self, error_message, fetch_id):
        if fetch_id != self.current_fetch_id:
            return
        
        self.reset_search_state()
        self.clear_content()
        
        error_label = ctk.CTkLabel(
            self.scrollable_frame,
            text=f"❌ Search failed:\n{error_message}",
            font=(config.header_font, 14),
            text_color=config.red,
            wraplength=500
        )
        error_label.pack(pady=10)
        
        retry_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="💡 Check your internet connection and try again",
            font=(config.body_font, 12),
            text_color=config.yellow
        )
        retry_label.pack(pady=5)

    def show_models_content(self, models, fetch_id, search_term):
        if fetch_id != self.current_fetch_id:
            return
        
        self.reset_search_state()
        self.clear_content()

        if not models:
            no_results_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=f"❌ No models found for '{search_term}'\n\nTry a different search term or check spelling.",
                font=(config.header_font, 14),
                text_color=config.red,
                wraplength=500,
                justify="center"
            )
            no_results_label.pack(pady=20)
            return

        # Success message
        if search_term:
            result_text = f"✅ Found {len(models)} models matching '{search_term}':"
        else:
            result_text = f"✅ Found {len(models)} popular models:"
            
        success_label = ctk.CTkLabel(
            self.scrollable_frame,
            text=result_text,
            font=(config.header_font, 14),
            text_color=config.green
        )
        success_label.pack(anchor="w", padx=10, pady=(10, 5))

        # List models
        for i, model in enumerate(models):
            self.create_model_card(model, i + 1)

    def create_model_card(self, model, index):
        """Create an enhanced model card with size, downloads, and compatibility info."""
        model_frame = ctk.CTkFrame(self.scrollable_frame)
        model_frame.pack(fill="x", padx=10, pady=3)
        
        # Main model info frame
        info_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=8)
        
        # Header row with model name and compatibility
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")
        
        # Model name and index
        name_label = ctk.CTkLabel(
            header_frame,
            text=f"{index}. {model.modelId}",
            font=(config.body_font, 14, "bold"),
            text_color=config.header_font_color
        )
        name_label.pack(side="left", anchor="w")
        
        # Compatibility info (if VRAM detected)
        if self.vram_info and self.vram_info.get("total_vram_gb", 0) > 0:
            # Safely extract parameter count
            param_count = None
            try:
                safetensors_data = getattr(model, 'safetensors', None)
                if safetensors_data and isinstance(safetensors_data, dict):
                    param_count = safetensors_data.get('total', None)
            except:
                pass
            
            if not param_count:
                # Try to estimate from model name
                param_count = self.estimate_params_from_name(model.modelId)
            
            compatibility = get_compatibility_info(param_count, self.vram_info["total_vram_gb"])
            
            compat_label = ctk.CTkLabel(
                header_frame,
                text=f"{compatibility['icon']} {compatibility['message']}",
                font=(config.body_font, 10),
                text_color=compatibility['color']
            )
            compat_label.pack(side="right", anchor="e")
        
        # Stats row (downloads, likes)
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(3, 0))
        
        # Safely get attributes with fallbacks
        downloads = getattr(model, 'downloads', 0) or 0
        likes = getattr(model, 'likes', 0) or 0
        
        stats_text = f"📥 {format_downloads(downloads)} downloads"
        if likes > 0:
            stats_text += f"  •  ❤️ {likes}"
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=(config.body_font, 11),
            text_color=config.yellow
        )
        stats_label.pack(anchor="w")
        
        # Description
        description = get_model_description(model)
        desc_label = ctk.CTkLabel(
            info_frame,
            text=f"🎯 {description}",
            font=(config.body_font, 11),
            text_color="#8888aa"
        )
        desc_label.pack(anchor="w", pady=(2, 0))
        
        # Download button
        download_button = ctk.CTkButton(
            info_frame,
            text="📦 Download",
            width=100,
            height=25,
            font=(config.body_font, 11),
            command=lambda m=model: self.download_model(m),
            fg_color="#2b5a87",
            hover_color="#1e3d5c"
        )
        download_button.pack(anchor="e", pady=(5, 0))

    def estimate_params_from_name(self, model_name: str) -> Optional[int]:
        """Estimate parameter count from model name."""
        import re
        
        model_lower = model_name.lower()
        
        # Common patterns in model names (more comprehensive)
        patterns = [
            r'(\d+(?:\.\d+)?)[_\-\s]*b(?:illion)?',  # 7b, 7-b, 7_b, 7 billion
            r'(\d+(?:\.\d+)?)[_\-\s]*B',             # 7B, 7-B, 7_B
            r'(\d+)[_\-\s]*(\d+)[_\-\s]*b',          # 7-5-b, 7_5_b
            r'(\d+)[_\-\s]*k(?:ilo)?',               # 7k, 7-k, 7 kilo
            r'(\d+)[_\-\s]*m(?:illion)?',            # 7m, 7-m, 7 million
        ]
        
        # First try the pattern matching
        for pattern in patterns:
            match = re.search(pattern, model_lower)
            if match:
                try:
                    if 'k' in pattern:
                        return int(float(match.group(1)) * 1000)
                    elif 'm' in pattern:
                        return int(float(match.group(1)) * 1000000)
                    elif 'b' in pattern:
                        if len(match.groups()) > 1 and match.group(2):
                            # Handle patterns like "7-5-b" -> 7.5B
                            number = float(f"{match.group(1)}.{match.group(2)}")
                        else:
                            number = float(match.group(1))
                        return int(number * 1000000000)
                except (ValueError, IndexError):
                    continue
        
        # Common model size defaults if no pattern found
        common_sizes = {
            'tiny': 1000000,      # 1M
            'small': 7000000000,  # 7B
            'medium': 13000000000, # 13B
            'large': 33000000000,  # 33B
            'xl': 70000000000,     # 70B
        }
        
        for size_name, param_count in common_sizes.items():
            if size_name in model_lower:
                return param_count
        
        return None

    def download_model(self, model):
        """Placeholder for model download functionality."""
        print(f"Would download: {model.modelId}")
        self.show_download_message(model.modelId)

    def show_download_message(self, model_id):
        """Show a temporary download message."""
        message_window = ctk.CTkToplevel(self.app)
        message_window.title("Download")
        message_window.geometry("400x150")
        message_window.transient(self.app)
        message_window.grab_set()
        
        label = ctk.CTkLabel(
            message_window,
            text=f"Download feature coming soon!\n\nModel: {model_id}",
            font=(config.header_font, 14),
            text_color=config.header_font_color
        )
        label.pack(pady=30)
        
        close_button = ctk.CTkButton(
            message_window,
            text="Close",
            command=message_window.destroy
        )
        close_button.pack(pady=10)
        

        
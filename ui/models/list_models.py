import threading
import customtkinter as ctk
from config import config
from ui.common.label_with_border import LabelWithBorder
from hf.list import list_models_hf, format_model_size, format_downloads, get_model_description
from hf.system_info import get_vram_info, get_compatibility_info, get_system_summary
from hf.auth import is_authenticated, get_user_info, authenticate, logout
from database.models_db import get_db
from typing import Optional, Dict
from llm.model_downloader import pytorch_model_downloader, DownloadProgress

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
        
        # Download management
        self.downloader = pytorch_model_downloader
        self.db = get_db()
        self.model_cards: Dict[str, Dict] = {}  # model_id -> card widgets
        self.last_downloaded_refresh = 0  # Throttle downloaded models refreshes
        
        # Authentication
        self.auth_button = None
        
        # Cross-component references (set by options_window)
        self.downloaded_body = None  # Reference to downloaded models section
        
        # Collapsible functionality
        self.is_expanded = True
        self.content_frame = None
        self.header_label = None
        self.outer_frame = None  # Will be set by options_window

    def create_list_models(self):
        # Detect VRAM at startup
        self.detect_system_info()
        
        # Header with collapse/expand functionality
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Clickable header label
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="➖ Model Browser & Downloader",
            font=(config.header_font, 16),
            text_color=config.blue,
            cursor="hand2"
        )
        self.header_label.pack(side="left", anchor="w")
        self.header_label.bind("<Button-1>", self.toggle_section)

        # Create content frame to hold all the existing content
        self.content_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # System info display
        system_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        system_frame.pack(fill="x", padx=0, pady=2)

        self.system_label = ctk.CTkLabel(
            system_frame,
            text="🔍 Detecting system specifications...",
            font=(config.body_font, 11),
            text_color=config.yellow
        )
        self.system_label.pack(anchor="w")

        # Search controls frame
        search_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=0, pady=5)
        
        # Open models only toggle
        open_only_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        open_only_frame.pack(fill="x", pady=(0, 5))
        
        self.open_only_var = ctk.BooleanVar(value=True)  # Default to open models only
        open_only_checkbox = ctk.CTkCheckBox(
            open_only_frame,
            text="🔓 Show only open models (no login required)",
            variable=self.open_only_var,
            font=(config.body_font, 11),
            text_color=config.header_font_color
        )
        open_only_checkbox.pack(anchor="w")

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
        
        # Auth button for accessing gated models
        self.auth_button = ctk.CTkButton(
            search_frame,
            text="🔑 Login",
            width=70,
            height=30,
            command=self.show_auth_dialog,
            fg_color="#8b4513",
            hover_color="#654321"
        )
        self.auth_button.pack(side="right", padx=5)
        
        # Check authentication status
        self.update_auth_status()

        # Tag buttons frame
        tags_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=0, pady=5)

        # Create icon and text separately to control spacing
        tags_icon = ctk.CTkLabel(tags_frame, text="🏆", font=(config.body_font, 12))
        tags_icon.pack(side="left")
        
        tags_text = ctk.CTkLabel(tags_frame, text="Quick tags:", font=(config.body_font, 12))
        tags_text.pack(side="left", padx=(1, 5))

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
        self.scrollable_frame = ctk.CTkScrollableFrame(self.content_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=10)
        
        self.show_initial_message()

    def toggle_section(self, event=None):
        """Toggle the visibility of the content section."""
        if self.is_expanded:
            # Collapse - hide content and make frame small
            self.content_frame.pack_forget()
            self.header_label.configure(text="➕ Model Browser & Downloader")
            self.is_expanded = False
            # Change outer frame to small height
            if self.outer_frame:
                self.outer_frame.pack_forget()
                self.outer_frame.pack(fill="x", padx=0, pady=(2, 5))
        else:
            # Expand - show content and make frame take remaining space
            self.content_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.header_label.configure(text="➖ Model Browser & Downloader")
            self.is_expanded = True
            # Change outer frame to take remaining space
            if self.outer_frame:
                self.outer_frame.pack_forget()
                self.outer_frame.pack(fill="both", expand=True, padx=0, pady=(2, 5))

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
            text="🔍 Search for any model by name or keyword\n\n🏷️ Use quick tags to find popular model families\n\n📈 Click 'Popular' to see trending models\n\n🤖 Only PyTorch models are shown (compatible with this app)\n\n💡 Compatibility info will show for each model",
            font=(config.body_font, 14),
            text_color=config.header_font_color,
            wraplength=500,
            justify="center"
        )
        initial_label.pack(pady=30)

    def clear_content(self):
        # Clear model cards tracking
        self.model_cards.clear()
        
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
            # Get open models only setting
            only_open = self.open_only_var.get()
            
            if search_term:
                # Search with specific term
                models = list_models_hf(limit=30, search_term=search_term, only_open=only_open)
            else:
                # Get popular models
                models = list_models_hf(limit=20, filter_for_coding=False, only_open=only_open)
            
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
            result_text = f"✅ Found {len(models)} PyTorch models matching '{search_term}':"
        else:
            result_text = f"✅ Found {len(models)} popular PyTorch models:"
            
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
        """Create an enhanced model card with download progress and controls."""
        model_id = model.modelId
        
        model_frame = ctk.CTkFrame(self.scrollable_frame)
        model_frame.pack(fill="x", padx=10, pady=3)
        
        # Main model info frame
        info_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=8)
        
        # Header row with model name
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")
        
        # Left side: Model name (with reserved space for right side content)
        name_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)
        
        # Model name and index (balanced truncation for readability)
        full_name = f"{index}. {model.modelId}"
        display_name = self.truncate_model_name(full_name, max_length=45)  # 30% more than 35
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=display_name,
            font=(config.body_font, 14, "bold"),
            text_color=config.header_font_color
        )
        name_label.pack(side="left", anchor="w")
        
        # Add tooltip if name was truncated
        if display_name != full_name:
            self.create_tooltip(name_label, model.modelId)
        
        # Right side: Status and compatibility in a vertical stack
        right_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_frame.pack(side="right", anchor="e")
        
        # Status indicator (downloaded/downloading/available)
        status_label = ctk.CTkLabel(
            right_frame, 
            text="", 
            font=(config.body_font, 10),
            anchor="e"
        )
        status_label.pack(anchor="e")
        
        # Compatibility info (if VRAM detected)
        compat_label = None
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
                right_frame,
                text=f"{compatibility['icon']} {compatibility['message']}",
                font=(config.body_font, 9),  # Slightly smaller font
                text_color=compatibility['color'],
                anchor="e"
            )
            compat_label.pack(anchor="e")
        
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
        
        # Download controls frame
        controls_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(5, 0))
        
        # Progress bar (initially hidden)
        progress_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        
        progress_bar = ctk.CTkProgressBar(progress_frame, width=300, height=10)
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        progress_bar.set(0)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=(config.body_font, 10),
            text_color=config.yellow
        )
        progress_label.pack(side="right")
        
        # Download details (speed, ETA, etc.)
        details_label = ctk.CTkLabel(
            controls_frame,
            text="",
            font=(config.body_font, 9),
            text_color="#666666"
        )
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.pack(anchor="e")
        
        # Download button
        download_button = ctk.CTkButton(
            buttons_frame,
            text="📦 Download",
            width=100,
            height=25,
            font=(config.body_font, 11),
            command=lambda: self.start_download(model),
            fg_color="#2b5a87",
            hover_color="#1e3d5c"
        )
        
        # Pause button
        pause_button = ctk.CTkButton(
            buttons_frame,
            text="⏸️ Pause",
            width=80,
            height=25,
            font=(config.body_font, 11),
            command=lambda: self.pause_download(model_id),
            fg_color="#b8860b",
            hover_color="#9a7209"
        )
        
        # Resume button
        resume_button = ctk.CTkButton(
            buttons_frame,
            text="▶️ Resume",
            width=80,
            height=25,
            font=(config.body_font, 11),
            command=lambda: self.resume_download(model_id),
            fg_color="#228b22",
            hover_color="#1e6b1e"
        )
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancel",
            width=80,
            height=25,
            font=(config.body_font, 11),
            command=lambda: self.cancel_download(model_id),
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        
        # Open folder button (for downloaded models)
        open_button = ctk.CTkButton(
            buttons_frame,
            text="📁 Open",
            width=80,
            height=25,
            font=(config.body_font, 11),
            command=lambda: self.open_model_folder(model_id),
            fg_color="#4682b4",
            hover_color="#4169e1"
        )
        
        # Store widget references for updates
        card_widgets = {
            'model_frame': model_frame,
            'status_label': status_label,
            'compat_label': compat_label,  # May be None if no VRAM detected
            'progress_frame': progress_frame,
            'progress_bar': progress_bar,
            'progress_label': progress_label,
            'details_label': details_label,
            'buttons_frame': buttons_frame,
            'download_button': download_button,
            'pause_button': pause_button,
            'resume_button': resume_button,
            'cancel_button': cancel_button,
            'open_button': open_button
        }
        
        self.model_cards[model_id] = card_widgets
        
        # Update initial state
        self.update_model_card_state(model_id, model)

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

    def truncate_model_name(self, name: str, max_length: int = 50) -> str:
        """Truncate model name if it's too long."""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."

    def create_tooltip(self, widget, text: str):
        """Create a tooltip for a widget."""
        tooltip_window = None
        
        def show_tooltip(event):
            nonlocal tooltip_window
            # Hide any existing tooltip first
            hide_tooltip(None)
            
            # Create tooltip window
            tooltip_window = ctk.CTkToplevel()
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.configure(fg_color="#2b2b2b")
            
            # Position tooltip near cursor
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip_window.geometry(f"+{x}+{y}")
            
            # Add text to tooltip
            label = ctk.CTkLabel(
                tooltip_window,
                text=text,
                font=(config.body_font, 11),
                text_color="#ffffff",
                fg_color="#2b2b2b"
            )
            label.pack(padx=8, pady=4)
            
        def hide_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window:
                try:
                    tooltip_window.destroy()
                except:
                    pass
                tooltip_window = None
        
        def hide_on_motion(event):
            # Hide tooltip if mouse moves significantly away
            if tooltip_window:
                try:
                    # Get current mouse position relative to widget
                    x, y = event.x, event.y
                    # If mouse is outside widget bounds, hide tooltip
                    if x < 0 or y < 0 or x > widget.winfo_width() or y > widget.winfo_height():
                        hide_tooltip(event)
                except:
                    pass
        
        # Bind mouse events
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        widget.bind("<Motion>", hide_on_motion)

    # Download management methods
    def start_download(self, model):
        """Start downloading a model."""
        try:
            # Extract model ID from different possible formats
            if hasattr(model, 'modelId'):
                # ModelInfo object from Hugging Face
                model_id = model.modelId
            elif isinstance(model, dict):
                # Dictionary format
                model_id = model.get('modelId', model.get('model_id', ''))
            else:
                print(f"❌ Unknown model format: {type(model)}")
                return
            
            if not model_id:
                print("❌ Could not extract model ID")
                return
            
            print(f"🔄 Starting download of {model_id}")
            
            # Start the download
            success = self.downloader.start_download(
                model,
                progress_callback=lambda progress: self.update_download_progress(model_id, progress)
            )
            
            if success:
                print(f"✅ Download started for {model_id}")
            else:
                print(f"❌ Failed to start download for {model_id}")
                
        except Exception as e:
            print(f"❌ Error starting download: {e}")
            self.show_message("Download Error", f"Failed to start download: {str(e)}")
    
    def pause_download(self, model_id):
        """Pause a download."""
        if self.downloader.pause_download(model_id):
            print(f"Paused download of {model_id}")
            self.update_model_card_state(model_id, None)
            # Refresh downloaded models section to update download status
            if self.downloaded_body:
                self.downloaded_body.refresh_downloaded_models()
    
    def resume_download(self, model_id):
        """Resume a download."""
        if self.downloader.resume_download(model_id):
            print(f"Resumed download of {model_id}")
            self.update_model_card_state(model_id, None)
            # Refresh downloaded models section to update download status
            if self.downloaded_body:
                self.downloaded_body.refresh_downloaded_models()
    
    def cancel_download(self, model_id):
        """Cancel a download."""
        if self.downloader.cancel_download(model_id):
            print(f"Cancelled download of {model_id}")
            self.update_model_card_state(model_id, None)
            # Refresh downloaded models section to remove cancelled download
            if self.downloaded_body:
                self.downloaded_body.refresh_downloaded_models()
    
    def open_model_folder(self, model_id):
        """Open the folder where the model is stored."""
        model_info = self.db.get_model(model_id)
        if model_info and model_info['local_path']:
            import subprocess
            import os
            
            path = model_info['local_path']
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', path])
                elif os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', path])
                else:  # Linux
                    subprocess.run(['xdg-open', path])
            except Exception as e:
                self.show_message("Error", f"Failed to open folder: {str(e)}")
        else:
            self.show_message("Not Found", f"Model {model_id} folder not found")
    
    def update_model_card_state(self, model_id, model):
        """Update the state of a model card (downloaded, downloading, available)."""
        if model_id not in self.model_cards:
            return
        
        widgets = self.model_cards[model_id]
        
        # Check if model is downloaded
        try:
            is_downloaded = self.db.is_model_downloaded(model_id)
        except Exception as e:
            print(f"⚠️ Error checking if model is downloaded: {e}")
            is_downloaded = False
        
        # Check if model is currently downloading
        try:
            is_downloading = self.downloader.is_downloading(model_id) and not is_downloaded  # Don't show downloading if already downloaded
        except AttributeError as e:
            print(f"⚠️ Downloader method not available: {e}")
            is_downloading = False
        except Exception as e:
            print(f"⚠️ Error checking download status: {e}")
            is_downloading = False
        
        # Get download progress if downloading
        try:
            download_progress = self.downloader.get_download_progress(model_id) if is_downloading else None
        except Exception as e:
            print(f"⚠️ Error getting download progress: {e}")
            download_progress = None
        
        # Handle edge case: if both downloaded and downloading, prioritize downloaded
        if is_downloaded and is_downloading:
            print(f"⚠️ Model {model_id} shows as both downloaded and downloading, prioritizing downloaded")
            is_downloading = False
        
        # Update status label
        if is_downloaded:
            widgets['status_label'].configure(text="✅ Downloaded", text_color=config.green)
        elif is_downloading:
            if download_progress and download_progress.status == 'paused':
                widgets['status_label'].configure(text="⏸️ Paused", text_color=config.yellow)
            else:
                widgets['status_label'].configure(text="⬇️ Downloading", text_color=config.blue)
        else:
            widgets['status_label'].configure(text="📦 Available", text_color=config.header_font_color)
        
        # Show/hide progress bar
        if is_downloading and download_progress:
            widgets['progress_frame'].pack(fill="x", pady=(3, 0))
            widgets['details_label'].pack(fill="x", pady=(2, 0))
        else:
            widgets['progress_frame'].pack_forget()
            widgets['details_label'].pack_forget()
        
        # Show appropriate buttons
        for button in ['download_button', 'pause_button', 'resume_button', 'cancel_button', 'open_button']:
            widgets[button].pack_forget()
        
        if is_downloaded:
            widgets['open_button'].pack(side="right", padx=2)
        elif is_downloading:
            if download_progress and download_progress.status == 'paused':
                widgets['resume_button'].pack(side="right", padx=2)
                widgets['cancel_button'].pack(side="right", padx=2)
            else:
                widgets['pause_button'].pack(side="right", padx=2)
                widgets['cancel_button'].pack(side="right", padx=2)
        else:
            widgets['download_button'].pack(side="right", padx=2)
    
    def update_download_progress(self, model_id, progress):
        """Update download progress UI."""
        if model_id not in self.model_cards:
            return
        
        widgets = self.model_cards[model_id]
        
        # Update progress bar
        progress_value = progress.progress
        widgets['progress_bar'].set(progress_value)
        widgets['progress_label'].configure(text=f"{progress.progress * 100:.1f}%")
        
        # Update details
        details_text = ""
        if progress.speed > 0:
            speed_mb = progress.speed / (1024 * 1024)
            details_text += f"Speed: {speed_mb:.1f} MB/s"
        
        if progress.eta and progress.eta > 0:
            eta_minutes = int(progress.eta // 60)
            eta_seconds = int(progress.eta % 60)
            details_text += f"  •  ETA: {eta_minutes}m {eta_seconds}s"
        
        if progress.downloaded_bytes > 0 and progress.total_bytes > 0:
            downloaded_mb = progress.downloaded_bytes / (1024 * 1024)
            total_mb = progress.total_bytes / (1024 * 1024)
            details_text += f"  •  {downloaded_mb:.1f} / {total_mb:.1f} MB"
        
        widgets['details_label'].configure(text=details_text)
        
        # Update card state if status changed
        self.update_model_card_state(model_id, None)
        
        # Refresh downloaded models section periodically to show live progress (throttled)
        import time
        current_time = time.time()
        if self.downloaded_body and (current_time - self.last_downloaded_refresh) >= 3:
            self.downloaded_body.refresh_downloaded_models()
            self.last_downloaded_refresh = current_time
        
        # If download completed, refresh the card and downloaded models list
        if progress.status in ['completed', 'error']:
            # Small delay then refresh card and notify downloaded models section
            self.app.after(1000, lambda: self._handle_download_completion(model_id, progress.status))
    
    def show_message(self, title, message):
        """Show a message dialog."""
        message_window = ctk.CTkToplevel(self.app)
        message_window.title(title)
        message_window.geometry("400x150")
        message_window.transient(self.app)
        message_window.grab_set()
        
        # Center the window
        message_window.lift()
        message_window.focus()
        
        label = ctk.CTkLabel(
            message_window,
            text=message,
            font=(config.header_font, 12),
            text_color=config.header_font_color,
            wraplength=350
        )
        label.pack(pady=30)
        
        close_button = ctk.CTkButton(
            message_window,
            text="OK",
            command=message_window.destroy,
            width=80
        )
        close_button.pack(pady=10)
    
    def _handle_download_completion(self, model_id, status):
        """Handle download completion - update UI and refresh downloaded models."""
        print(f"Handling download completion for {model_id}: {status}")
        
        # Force update the model card state
        self.update_model_card_state(model_id, None)
        
        # If successful, refresh the downloaded models section
        if status == 'completed':
            print("Download completed successfully - model should now appear in Downloaded Models section")
            # Refresh downloaded models section to move from downloading to downloaded
            if self.downloaded_body:
                self.downloaded_body.refresh_downloaded_models()
        elif status == 'failed':
            print("Download failed - removing from Downloaded Models section")
            # Refresh downloaded models section to remove failed download
            if self.downloaded_body:
                self.downloaded_body.refresh_downloaded_models()
    
    # Authentication methods
    def update_auth_status(self):
        """Update authentication button based on current status."""
        if is_authenticated():
            user_info = get_user_info()
            username = user_info.get('name', 'User') if user_info else 'User'
            self.auth_button.configure(
                text=f"👤 {username[:8]}",
                fg_color="#228b22",
                hover_color="#1e6b1e"
            )
        else:
            self.auth_button.configure(
                text="🔑 Login",
                fg_color="#8b4513",
                hover_color="#654321"
            )
    
    def show_auth_dialog(self):
        """Show authentication dialog or logout if already authenticated."""
        if is_authenticated():
            # Show logout confirmation
            self.show_logout_dialog()
        else:
            # Show login dialog
            self.show_login_dialog()
    
    def show_login_dialog(self):
        """Show HuggingFace login dialog."""
        auth_window = ctk.CTkToplevel(self.app)
        auth_window.title("Hugging Face Authentication")
        auth_window.geometry("500x300")
        auth_window.transient(self.app)
        auth_window.grab_set()
        
        # Center the window
        auth_window.lift()
        auth_window.focus()
        
        # Main content frame
        content_frame = ctk.CTkFrame(auth_window, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="🔑 Access Gated Models",
            font=(config.header_font, 16, "bold"),
            text_color=config.blue
        )
        title_label.pack(pady=(0, 10))
        
        # Explanation
        explanation = """To download gated models (like official Mistral, Llama models), 
you need a Hugging Face account and access token.

1. Create account at https://huggingface.co
2. Go to Settings → Access Tokens
3. Create a new token with 'Read' permission
4. Paste the token below"""
        
        explanation_label = ctk.CTkLabel(
            content_frame,
            text=explanation,
            font=(config.body_font, 11),
            text_color=config.header_font_color,
            wraplength=450,
            justify="left"
        )
        explanation_label.pack(pady=(0, 15))
        
        # Token input
        token_label = ctk.CTkLabel(
            content_frame,
            text="Access Token:",
            font=(config.body_font, 12),
            text_color=config.header_font_color
        )
        token_label.pack(anchor="w")
        
        token_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            width=450,
            height=30,
            show="*"  # Hide token for security
        )
        token_entry.pack(fill="x", pady=(5, 15))
        
        # Status label
        status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=(config.body_font, 11),
            wraplength=450
        )
        status_label.pack()
        
        # Buttons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(15, 0))
        
        def attempt_login():
            token = token_entry.get().strip()
            if not token:
                status_label.configure(text="Please enter your access token", text_color=config.red)
                return
            
            status_label.configure(text="🔄 Authenticating...", text_color=config.yellow)
            auth_window.update()
            
            # Attempt authentication
            result = authenticate(token)
            
            if result['success']:
                status_label.configure(text=f"✅ {result['message']}", text_color=config.green)
                self.update_auth_status()
                auth_window.after(1500, auth_window.destroy)
            else:
                status_label.configure(text=f"❌ {result['message']}", text_color=config.red)
        
        login_button = ctk.CTkButton(
            buttons_frame,
            text="🔑 Login",
            command=attempt_login,
            fg_color="#228b22",
            hover_color="#1e6b1e"
        )
        login_button.pack(side="left")
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=auth_window.destroy
        )
        cancel_button.pack(side="right")
        
        # Handle Enter key
        token_entry.bind("<Return>", lambda e: attempt_login())
    
    def show_logout_dialog(self):
        """Show logout confirmation dialog."""
        logout_window = ctk.CTkToplevel(self.app)
        logout_window.title("Logout")
        logout_window.geometry("350x150")
        logout_window.transient(self.app)
        logout_window.grab_set()
        
        user_info = get_user_info()
        username = user_info.get('name', 'User') if user_info else 'User'
        
        label = ctk.CTkLabel(
            logout_window,
            text=f"Logout from Hugging Face?\n\nCurrently logged in as: {username}",
            font=(config.header_font, 12),
            text_color=config.header_font_color,
            wraplength=300
        )
        label.pack(pady=30)
        
        buttons_frame = ctk.CTkFrame(logout_window, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        def confirm_logout():
            if logout():
                self.update_auth_status()
                logout_window.destroy()
        
        logout_btn = ctk.CTkButton(
            buttons_frame,
            text="🚪 Logout",
            command=confirm_logout,
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        logout_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=logout_window.destroy
        )
        cancel_btn.pack(side="right", padx=5)

        
from ui.common.label_with_border import LabelWithBorder
import customtkinter as ctk
from config import config
from database.models_db import get_db
from hf.list import format_downloads
from hf.downloader import get_downloader
import subprocess
import os
from pathlib import Path
from datetime import datetime
from llm.simple_inference import simple_inference

class DownloadedBody:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame
        self.is_expanded = True
        self.content_frame = None
        self.scrollable_frame = None
        self.db = get_db()
        self.downloader = get_downloader()

    def create_downloaded_body(self):
        # Header with collapse/expand functionality
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)

        # Clickable header label
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="➖ Downloaded Models",
                                                 font=(config.header_font, 16),
                                                 text_color=config.blue,
            cursor="hand2"
        )
        self.header_label.pack(side="left", anchor="w")
        self.header_label.bind("<Button-1>", self.toggle_section)
        
        # Status label for download count
        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=(config.body_font, 11),
            text_color=config.yellow
        )
        self.status_label.pack(side="right", anchor="e")

        # Create content frame - compact initially, will grow with models
        self.content_frame = ctk.CTkFrame(self.frame)
        self.content_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Refresh button
        refresh_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        refresh_frame.pack(fill="x", padx=5, pady=5)
        
        refresh_button = ctk.CTkButton(
            refresh_frame,
            text="🔄 Refresh",
            width=80,
            height=25,
            font=(config.body_font, 11),
            command=self.refresh_downloaded_models,
            fg_color="#666666",
            hover_color="#555555"
        )
        refresh_button.pack(anchor="w")

        # Scrollable frame for models
        self.scrollable_frame = ctk.CTkScrollableFrame(self.content_frame, height=100)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Load initial content
        self.refresh_downloaded_models()

    def toggle_section(self, event=None):
        """Toggle the visibility of the content section."""
        if self.is_expanded:
            # Collapse - only show header
            self.content_frame.pack_forget()
            self.header_label.configure(text="➕ Downloaded Models")
            self.is_expanded = False
        else:
            # Expand - will grow dynamically as models are added
            self.content_frame.pack(fill="x", padx=5, pady=(0, 5))
            self.header_label.configure(text="➖ Downloaded Models")
            self.is_expanded = True

    def refresh_downloaded_models(self):
        """Refresh the list of downloaded and downloading models."""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Get downloaded models from database
        downloaded_models = self.db.get_all_models()
        
        # Get active downloads
        active_downloads = list(self.downloader.active_downloads.items())
        
        # Update status label
        download_count = len(active_downloads)
        model_count = len(downloaded_models)
        
        status_parts = []
        if model_count > 0:
            status_parts.append(f"{model_count} downloaded")
        if download_count > 0:
            status_parts.append(f"{download_count} downloading")
        
        if status_parts:
            self.status_label.configure(text=" • ".join(status_parts))
        else:
            self.status_label.configure(text="")

        # Show active downloads first (they're most important to track)
        for model_id, download_info in active_downloads:
            self.create_downloading_model_card(model_id, download_info)

        # Then show downloaded models
        for model in downloaded_models:
            self.create_downloaded_model_card(model)
        
        # Show placeholder if nothing at all
        if not downloaded_models and not active_downloads:
            placeholder = ctk.CTkLabel(
                self.scrollable_frame,
                text="No models downloaded yet\n\nDownload models from the Model Browser above",
                font=(config.body_font, 12),
                text_color=config.header_font_color,
                justify="center"
            )
            placeholder.pack(pady=20)

    def create_downloading_model_card(self, model_id, download_info):
        """Create a card for a downloading model."""
        model_frame = ctk.CTkFrame(self.scrollable_frame)
        model_frame.pack(fill="x", padx=5, pady=2)

        # Main info frame
        info_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=8, pady=6)

        # Header with model name and status
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        # Model name
        model_name = model_id.split('/')[-1] if '/' in model_id else model_id
        name_label = ctk.CTkLabel(
            header_frame,
            text=f"⬇️ {model_name}",
            font=(config.body_font, 13, "bold"),
            text_color=config.blue
        )
        name_label.pack(side="left", anchor="w")

        # Download status (without percentage)
        progress = download_info['progress']
        if progress.status == 'paused':
            status_text = "⏸️ Paused"
        elif progress.status == 'downloading':
            status_text = "⬇️ Downloading"
        else:
            status_text = "📥 Starting"

        status_label = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=(config.body_font, 10),
            text_color=config.blue
        )
        status_label.pack(side="right", anchor="e")

        # Model ID
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(3, 0))

        model_id_label = ctk.CTkLabel(
            details_frame,
            text=f"📦 {model_id}",
            font=(config.body_font, 10),
            text_color="#8888aa"
        )
        model_id_label.pack(anchor="w")

        # Progress bar with percentage
        progress_bar_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        progress_bar_frame.pack(fill="x", pady=(5, 0))

        progress_bar = ctk.CTkProgressBar(progress_bar_frame, width=300, height=8)
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        progress_bar.set(progress.progress_percent / 100.0)

        # Percentage label next to progress bar
        progress_percent_label = ctk.CTkLabel(
            progress_bar_frame,
            text=f"{progress.progress_percent:.1f}%",
            font=(config.body_font, 10),
            text_color=config.yellow
        )
        progress_percent_label.pack(side="right")

        # Download details
        details_text = ""
        if progress.download_speed > 0:
            speed_mb = progress.download_speed / (1024 * 1024)
            details_text = f"Speed: {speed_mb:.1f} MB/s"
        
        if progress.downloaded_bytes > 0:
            downloaded_mb = progress.downloaded_bytes / (1024 * 1024)
            details_text += f"  •  Downloaded: {downloaded_mb:.1f} MB"
        
        if progress.eta_seconds and progress.eta_seconds > 0:
            eta_minutes = progress.eta_seconds // 60
            eta_seconds = progress.eta_seconds % 60
            details_text += f"  •  ETA: {eta_minutes}m {eta_seconds}s"

        if details_text:
            details_label = ctk.CTkLabel(
                details_frame,
                text=details_text,
                font=(config.body_font, 9),
                text_color="#666666"
            )
            details_label.pack(anchor="w", pady=(2, 0))

        # Control buttons
        buttons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(5, 0))

        if progress.status == 'paused':
            resume_button = ctk.CTkButton(
                buttons_frame,
                text="▶️ Resume",
                width=80,
                height=22,
                font=(config.body_font, 10),
                command=lambda: self.resume_download(model_id),
                fg_color="#228b22",
                hover_color="#1e6b1e"
            )
            resume_button.pack(side="left", padx=(0, 5))
        else:
            pause_button = ctk.CTkButton(
                buttons_frame,
                text="⏸️ Pause",
                width=80,
                height=22,
                font=(config.body_font, 10),
                command=lambda: self.pause_download(model_id),
                fg_color="#b8860b",
                hover_color="#9a7209"
            )
            pause_button.pack(side="left", padx=(0, 5))

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancel",
            width=80,
            height=22,
            font=(config.body_font, 10),
            command=lambda: self.cancel_download(model_id),
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        cancel_button.pack(side="left", padx=2)

    def create_downloaded_model_card(self, model):
        """Create a card for a downloaded model."""
        model_frame = ctk.CTkFrame(self.scrollable_frame)
        model_frame.pack(fill="x", padx=5, pady=2)

        # Main info frame
        info_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=8, pady=6)

        # Header with model name and status
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        # Model name
        name_label = ctk.CTkLabel(
            header_frame,
            text=model['display_name'],
            font=(config.body_font, 13, "bold"),
            text_color=config.header_font_color
        )
        name_label.pack(side="left", anchor="w")

        # Status and size
        status_text = "✅ Downloaded"
        if model.get('size_bytes', 0) > 0:
            size_gb = model['size_bytes'] / (1024**3)
            status_text += f"  •  {size_gb:.1f} GB"

        status_label = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=(config.body_font, 10),
            text_color=config.green
        )
        status_label.pack(side="right", anchor="e")

        # Model ID and description
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(3, 0))

        model_id_label = ctk.CTkLabel(
            details_frame,
            text=f"📦 {model['model_id']}",
            font=(config.body_font, 10),
            text_color="#8888aa"
        )
        model_id_label.pack(anchor="w")

        if model.get('description'):
            desc_label = ctk.CTkLabel(
                details_frame,
                text=f"🎯 {model['description']}",
                font=(config.body_font, 10),
                text_color="#8888aa"
            )
            desc_label.pack(anchor="w")

        # Download info
        if model.get('download_date'):
            try:
                download_date = datetime.fromisoformat(model['download_date'])
                date_str = download_date.strftime("%Y-%m-%d %H:%M")
                date_label = ctk.CTkLabel(
                    details_frame,
                    text=f"📅 Downloaded: {date_str}",
                    font=(config.body_font, 9),
                    text_color="#666666"
                )
                date_label.pack(anchor="w")
            except:
                pass

        # Action buttons
        buttons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(5, 0))

        # Open folder button
        open_button = ctk.CTkButton(
            buttons_frame,
            text="📁 Open Folder",
            width=100,
            height=22,
            font=(config.body_font, 10),
            command=lambda: self.open_model_folder(model['local_path']),
            fg_color="#4682b4",
            hover_color="#4169e1"
        )
        open_button.pack(side="left", padx=(0, 5))

        # Delete button
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete",
            width=80,
            height=22,
            font=(config.body_font, 10),
            command=lambda: self.delete_model(model['model_id']),
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        delete_button.pack(side="left", padx=2)

        # Use model button (placeholder for future functionality)
        use_button = ctk.CTkButton(
            buttons_frame,
            text="🚀 Use Model",
            width=90,
            height=22,
            font=(config.body_font, 10),
            command=lambda: self.use_model(model['model_id']),
            fg_color="#228b22",
            hover_color="#1e6b1e"
        )
        use_button.pack(side="right")

    def open_model_folder(self, local_path):
        """Open the model folder in file explorer."""
        try:
            path = Path(local_path)
            if not path.exists():
                self.show_message("Not Found", "Model folder no longer exists")
                return

            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', str(path)])
            elif os.uname().sysname == 'Darwin':  # macOS
                subprocess.run(['open', str(path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(path)])
        except Exception as e:
            self.show_message("Error", f"Failed to open folder: {str(e)}")

    def delete_model(self, model_id):
        """Delete a downloaded model."""
        # Show confirmation dialog
        confirm_window = ctk.CTkToplevel(self.app)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x150")
        confirm_window.transient(self.app)
        confirm_window.grab_set()

        label = ctk.CTkLabel(
            confirm_window,
            text=f"Delete model '{model_id}'?\n\nThis will remove all files permanently.",
            font=(config.header_font, 12),
            text_color=config.header_font_color,
            wraplength=350
        )
        label.pack(pady=20)

        buttons_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        buttons_frame.pack(pady=10)

        def confirm_delete():
            if self.db.delete_model(model_id):
                self.show_message("Success", f"Model '{model_id}' deleted successfully")
                self.refresh_downloaded_models()  # Refresh the list
            else:
                self.show_message("Error", f"Failed to delete model '{model_id}'")
            confirm_window.destroy()

        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            command=confirm_delete,
            fg_color="#dc143c",
            hover_color="#b22234"
        )
        delete_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=confirm_window.destroy
        )
        cancel_btn.pack(side="right", padx=5)

    def pause_download(self, model_id):
        """Pause a download."""
        if self.downloader.pause_download(model_id):
            print(f"Paused download of {model_id}")
            self.refresh_downloaded_models()  # Refresh to update UI
    
    def resume_download(self, model_id):
        """Resume a download."""
        if self.downloader.resume_download(model_id):
            print(f"Resumed download of {model_id}")
            self.refresh_downloaded_models()  # Refresh to update UI
    
    def cancel_download(self, model_id):
        """Cancel a download."""
        if self.downloader.cancel_download(model_id):
            print(f"Cancelled download of {model_id}")
            self.refresh_downloaded_models()  # Refresh to update UI

    def use_model(self, model_id):
        """Activate a model for use."""
        try:
            # Get the model from database
            model = self.db.get_model(model_id)
            if not model:
                self.show_message("Error", f"Model '{model_id}' not found in database.")
                return
            
            print(f"Activating model: {model['display_name']}")
            print(f"Model path: {model.get('local_path', 'No path')}")
            
            # Set model for simple inference
            model_path = model.get('local_path')
            if model_path:
                print(f"Setting model for simple inference: {model_path}")
                
                # Check if model directory exists
                if not os.path.exists(model_path):
                    self.show_message("Error", f"Model directory not found: {model_path}")
                    return
                
                # Use simple inference instead of terminal inference
                success = simple_inference.set_model(model_path)
                
                if success:
                    print(f"✅ Model activated successfully: {model['display_name']}")
                    self.show_message("Success", f"Model '{model['display_name']}' activated successfully!")
                    
                    # Update the active model in the main application
                    if hasattr(self, 'parent') and hasattr(self.parent, 'active_model'):
                        self.parent.active_model = model
                        print(f"✅ Active model updated: {model['display_name']}")
                else:
                    print(f"❌ Failed to activate model: {model['display_name']}")
                    self.show_message("Error", f"Failed to activate model '{model['display_name']}'. Please try again.")
            else:
                print(f"❌ No local path found for model: {model_id}")
                self.show_message("Error", f"No local path found for model '{model['display_name']}'.")
                
        except Exception as e:
            print(f"❌ Error activating model: {e}")
            import traceback
            traceback.print_exc()
            self.show_message("Error", f"Error activating model: {str(e)}")

    def show_message(self, title, message):
        """Show a message dialog."""
        message_window = ctk.CTkToplevel(self.app)
        message_window.title(title)
        message_window.geometry("400x150")
        message_window.transient(self.app)
        message_window.grab_set()

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
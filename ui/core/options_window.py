import customtkinter as ctk
from config import config
from ui.models.active import ActiveBody
from ui.models.downloaded import DownloadedBody
from ui.models.list_models import ListModels
from ui.core.gpu_settings import GPUSettingsDialog

class OptionsWindow:
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame):
        super().__init__()
        self.app = app
        self.frame = frame

    def create_options_window(self):
        # Ensure the main frame respects grid.py hardcoded sizes (580x780)
        self.frame.pack_propagate(False)
        
        # Create dedicated frames for each section with proper sizing
        
        # Active Model Section - Small initial height, like Downloaded Models
        self.active_frame = ctk.CTkFrame(self.frame, height=80)
        self.active_frame.pack(fill="x", padx=0, pady=(5, 2))
        # Allow this frame to adjust height naturally like Downloaded Models
        
        self.active_body = ActiveBody(self.app, self.active_frame)
        self.active_body.create_active_body()

        # Downloaded Models Section - Small initial height, full width  
        self.downloaded_frame = ctk.CTkFrame(self.frame, height=80)
        self.downloaded_frame.pack(fill="x", padx=0, pady=2)
        # Allow this frame to grow with content when models are added
        
        self.downloaded_body = DownloadedBody(self.app, self.downloaded_frame)
        self.downloaded_body.create_downloaded_body()

        # Model Browser Section - Starts expanded (takes remaining space)
        self.browser_frame = ctk.CTkFrame(self.frame)
        self.browser_frame.pack(fill="both", expand=True, padx=0, pady=(2, 5))
        
        self.list_models = ListModels(self.app, self.browser_frame)
        # Pass reference to the outer frame so it can change packing behavior
        self.list_models.outer_frame = self.browser_frame
        # Pass reference to downloaded models for refresh notifications
        self.list_models.downloaded_body = self.downloaded_body
        self.list_models.create_list_models()
        
        # GPU Status and Settings Section
        gpu_frame = ctk.CTkFrame(self.frame, height=60)
        gpu_frame.pack(side="bottom", fill="x", pady=5)
        
        # GPU Status Indicator
        self.gpu_status_label = ctk.CTkLabel(
            gpu_frame,
            text="🔄 Checking GPU status...",
            font=(config.body_font, 12),
            text_color=config.yellow
        )
        self.gpu_status_label.pack(side="left", padx=10, pady=5)
        
        # GPU Settings Button
        self.gpu_button = ctk.CTkButton(
            gpu_frame,
            text="⚙️ GPU Settings",
            command=self.open_gpu_settings,
            fg_color="purple",
            height=30
        )
        self.gpu_button.pack(side="right", padx=10, pady=5)
        
        # Update GPU status
        self.update_gpu_status()
    
    def update_gpu_status(self):
        """Update the GPU status indicator."""
        try:
            import torch
            
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
                torch_version = torch.__version__
                
                # Check if this is CUDA version (not CPU-only)
                if "+cu" in torch_version:
                    self.gpu_status_label.configure(
                        text=f"✅ GPU: {device_name} (CUDA {cuda_version})",
                        text_color=config.green
                    )
                else:
                    self.gpu_status_label.configure(
                        text=f"⚠️  GPU: {device_name} (CPU-only PyTorch)",
                        text_color=config.yellow
                    )
            else:
                self.gpu_status_label.configure(
                    text="❌ No GPU detected",
                    text_color=config.red
                )
                
        except ImportError:
            self.gpu_status_label.configure(
                text="❌ PyTorch not installed",
                text_color=config.red
            )
        except Exception as e:
            self.gpu_status_label.configure(
                text=f"❌ GPU error: {str(e)[:30]}...",
                text_color=config.red
            )
    
    def open_gpu_settings(self):
        """Open GPU settings dialog."""
        gpu_dialog = GPUSettingsDialog(self.app)
        gpu_dialog.show()
        # Refresh GPU status after settings dialog closes
        self.update_gpu_status()

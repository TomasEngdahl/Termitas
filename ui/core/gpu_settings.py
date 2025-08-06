#!/usr/bin/env python3
"""
GPU Settings Dialog for PyTorch configuration
"""

import customtkinter as ctk
import subprocess
import sys
import threading
from typing import Optional
from ui.core.window_utils import center_window

class GPUSettingsDialog:
    """Dialog for configuring GPU settings and PyTorch installation."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("GPU Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        center_window(self.dialog, 600, 500)
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.check_gpu_status()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="GPU Configuration", font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # GPU Status Frame
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        status_label = ctk.CTkLabel(status_frame, text="GPU Status:", font=("Arial", 14, "bold"))
        status_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.status_text = ctk.CTkTextbox(status_frame, height=150, font=("Consolas", 10))
        self.status_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Installation Frame
        install_frame = ctk.CTkFrame(main_frame)
        install_frame.pack(fill="x", padx=10, pady=10)
        
        install_label = ctk.CTkLabel(install_frame, text="PyTorch Installation:", font=("Arial", 14, "bold"))
        install_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Installation buttons
        button_frame = ctk.CTkFrame(install_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # CUDA button (universal for all modern GPUs)
        self.cuda_button = ctk.CTkButton(
            button_frame, 
            text="Install PyTorch with CUDA 12.8", 
            command=self.install_cuda_pytorch,
            fg_color="green"
        )
        self.cuda_button.pack(side="left", padx=(0, 10), pady=5)
        
        # CPU button
        self.cpu_button = ctk.CTkButton(
            button_frame, 
            text="Install CPU-only PyTorch", 
            command=self.install_cpu_pytorch,
            fg_color="blue"
        )
        self.cpu_button.pack(side="left", padx=(0, 10), pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.install_status = ctk.CTkLabel(main_frame, text="", font=("Arial", 12))
        self.install_status.pack(pady=5)
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            main_frame,
            text="🔄 Refresh GPU Status",
            command=self.refresh_gpu_status,
            fg_color="blue",
            height=30
        )
        refresh_button.pack(pady=5)
        
        # Close button
        close_button = ctk.CTkButton(main_frame, text="Close", command=self.dialog.destroy)
        close_button.pack(pady=10)
    
    def check_gpu_status(self):
        """Check and display GPU status."""
        try:
            import torch
            
            status_info = f"PyTorch Version: {torch.__version__}\n"
            status_info += f"CUDA Available: {torch.cuda.is_available()}\n"
            
            # Check if this is CPU-only PyTorch
            if "+cpu" in torch.__version__:
                status_info += f"⚠️  CPU-only PyTorch detected!\n"
                status_info += f"💡 To enable GPU acceleration, install CUDA version:\n"
                status_info += f"   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128\n"
                status_info += f"💡 The app will work on CPU until then\n"
            elif torch.cuda.is_available():
                status_info += f"CUDA Version: {torch.version.cuda}\n"
                status_info += f"Device Count: {torch.cuda.device_count()}\n"
                
                for i in range(torch.cuda.device_count()):
                    device_name = torch.cuda.get_device_name(i)
                    device_capability = torch.cuda.get_device_capability(i)
                    status_info += f"Device {i}: {device_name}\n"
                    status_info += f"  CUDA Capability: sm_{device_capability[0]}{device_capability[1]}\n"
                    
                    # Check if PyTorch version supports this GPU
                    torch_version = torch.__version__
                    if "2.8" in torch_version and "cu128" in torch_version:
                        status_info += f"  ✅ PyTorch 2.8+cu128 supports all modern GPUs\n"
                    elif "2.7" in torch_version and "cu128" in torch_version:
                        status_info += f"  ✅ PyTorch 2.7+cu128 supports most modern GPUs\n"
                    else:
                        status_info += f"  ⚠️  Consider upgrading to PyTorch 2.7+cu128 or 2.8+cu128\n"
                
                # Test basic GPU operations
                try:
                    x = torch.randn(100, 100).cuda()
                    y = torch.randn(100, 100).cuda()
                    z = torch.mm(x, y)
                    status_info += "\n✅ Basic GPU operations working\n"
                    status_info += "✅ GPU acceleration available\n"
                except Exception as e:
                    status_info += f"\n❌ GPU operations failed: {e}\n"
                    status_info += "💡 The app will automatically fall back to CPU\n"
            else:
                status_info += "\n❌ No CUDA devices found\n"
                status_info += "💡 CPU-only mode will be used\n"
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", status_info)
            
        except ImportError:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "PyTorch not installed")
    
    def install_cuda_pytorch(self):
        """Install PyTorch with CUDA support."""
        self.install_pytorch("--index-url https://download.pytorch.org/whl/cu128")
    
    def install_cpu_pytorch(self):
        """Install CPU-only PyTorch."""
        self.install_pytorch("--index-url https://download.pytorch.org/whl/cpu")
    
    def install_pytorch(self, index_url: str):
        """Install PyTorch with the specified index URL."""
        def install_thread():
            try:
                self.install_status.configure(text="Installing PyTorch...")
                self.progress_bar.set(0.2)
                
                cmd = [sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", index_url, "--force-reinstall"]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                self.progress_bar.set(0.5)
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.install_status.configure(text="✅ PyTorch installed successfully!")
                    self.progress_bar.set(1.0)
                    # Refresh GPU status
                    self.check_gpu_status()
                else:
                    self.install_status.configure(text=f"❌ Installation failed: {stderr}")
                    self.progress_bar.set(0)
                    
            except Exception as e:
                self.install_status.configure(text=f"❌ Error: {str(e)}")
                self.progress_bar.set(0)
        
        # Run installation in a separate thread
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()
    
    def refresh_gpu_status(self):
        """Refresh GPU status in the options window."""
        if hasattr(self.parent, 'options_window_ref') and self.parent.options_window_ref:
            self.parent.options_window_ref.update_gpu_status()
            self.check_gpu_status()  # Also refresh the dialog's status
            self.install_status.configure(text="✅ GPU status refreshed!")
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()
        
        # Refresh GPU status in options window if it exists
        if hasattr(self.parent, 'options_window_ref') and self.parent.options_window_ref:
            self.parent.options_window_ref.update_gpu_status()
        
        return self.dialog 
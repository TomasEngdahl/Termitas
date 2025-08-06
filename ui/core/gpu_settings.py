#!/usr/bin/env python3
"""
GPU Settings Dialog for PyTorch configuration
"""

import customtkinter as ctk
import subprocess
import sys
import threading
from typing import Optional

class GPUSettingsDialog:
    """Dialog for configuring GPU settings and PyTorch installation."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("GPU Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # Center the dialog
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
        
        # CUDA button
        self.cuda_button = ctk.CTkButton(
            button_frame, 
            text="Install PyTorch with CUDA", 
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
        
        # Nightly button
        self.nightly_button = ctk.CTkButton(
            button_frame, 
            text="Install Nightly Build", 
            command=self.install_nightly_pytorch,
            fg_color="orange"
        )
        self.nightly_button.pack(side="left", pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.install_status = ctk.CTkLabel(main_frame, text="Ready to install", font=("Arial", 12))
        self.install_status.pack(pady=5)
        
        # Close button
        close_button = ctk.CTkButton(main_frame, text="Close", command=self.dialog.destroy)
        close_button.pack(pady=10)
    
    def check_gpu_status(self):
        """Check GPU status and display results."""
        try:
            import torch
            
            status_info = f"PyTorch Version: {torch.__version__}\n"
            status_info += f"CUDA Available: {torch.cuda.is_available()}\n"
            
            if torch.cuda.is_available():
                status_info += f"CUDA Version: {torch.version.cuda}\n"
                status_info += f"Device Count: {torch.cuda.device_count()}\n"
                
                for i in range(torch.cuda.device_count()):
                    device_name = torch.cuda.get_device_name(i)
                    device_capability = torch.cuda.get_device_capability(i)
                    status_info += f"Device {i}: {device_name}\n"
                    status_info += f"  CUDA Capability: {device_capability}\n"
                    
                    # Check RTX 5090 compatibility
                    if "RTX 5090" in device_name:
                        status_info += f"  ⚠️  RTX 5090 detected!\n"
                        status_info += f"  ⚠️  PyTorch {torch.__version__} only supports up to sm_90\n"
                        status_info += f"  ⚠️  Your GPU has sm_{device_capability[0]}{device_capability[1]}\n"
                        status_info += f"  💡 Use CPU fallback or wait for PyTorch 2.8+\n"
                
                # Test basic GPU operations
                try:
                    x = torch.randn(100, 100).cuda()
                    y = torch.randn(100, 100).cuda()
                    z = torch.mm(x, y)
                    status_info += "\n✅ Basic GPU operations working\n"
                except Exception as e:
                    status_info += f"\n❌ GPU operations failed: {e}\n"
                    if "RTX 5090" in str(e):
                        status_info += f"  💡 This is expected for RTX 5090 with PyTorch 2.7.0\n"
                        status_info += f"  💡 The app will automatically fall back to CPU\n"
            else:
                status_info += "\n❌ No CUDA devices found\n"
            
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", status_info)
            
        except ImportError:
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", "PyTorch not installed")
    
    def install_cuda_pytorch(self):
        """Install PyTorch with CUDA support."""
        self.install_pytorch("--index-url https://download.pytorch.org/whl/cu121")
    
    def install_cpu_pytorch(self):
        """Install CPU-only PyTorch."""
        self.install_pytorch("--index-url https://download.pytorch.org/whl/cpu")
    
    def install_nightly_pytorch(self):
        """Install PyTorch nightly build."""
        self.install_pytorch("--pre --index-url https://download.pytorch.org/whl/nightly/cu121")
    
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
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()
        return self.dialog 
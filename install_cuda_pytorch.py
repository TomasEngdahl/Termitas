#!/usr/bin/env python3
"""
Helper script to install CUDA-enabled PyTorch after uv installation
"""

import subprocess
import sys
import os

def install_cuda_pytorch():
    """Install PyTorch with CUDA 12.8 support."""
    print("🔧 Installing PyTorch with CUDA 12.8 support...")
    print("📦 This will install the CUDA version that works with RTX 5090")
    
    try:
        # Install PyTorch with CUDA 12.8
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu128",
            "--force-reinstall"
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyTorch with CUDA 12.8 installed successfully!")
            print("🎯 Your RTX 5090 should now work with GPU acceleration")
            
            # Verify installation
            try:
                import torch
                print(f"📊 PyTorch version: {torch.__version__}")
                print(f"📊 CUDA available: {torch.cuda.is_available()}")
                if torch.cuda.is_available():
                    print(f"📊 CUDA version: {torch.version.cuda}")
                    print(f"📊 GPU detected: {torch.cuda.get_device_name(0)}")
                    print("✅ GPU acceleration ready!")
                else:
                    print("⚠️  CUDA not available - check your GPU drivers")
            except ImportError:
                print("❌ PyTorch not found after installation")
                
        else:
            print(f"❌ Installation failed:")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error during installation: {e}")

if __name__ == "__main__":
    install_cuda_pytorch() 
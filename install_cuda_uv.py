#!/usr/bin/env python3
"""
Script to install CUDA PyTorch using uv
"""

import subprocess
import sys
import os

def install_cuda_with_uv():
    """Install PyTorch with CUDA 12.8 using uv."""
    print("🔧 Installing PyTorch with CUDA 12.8 using uv...")
    print("📦 This will install the CUDA version that works with RTX 5090")
    
    try:
        # Method 1: Try using uv pip if available
        try:
            cmd = ["uv", "pip", "install", "torch", "torchvision", "torchaudio", 
                   "--index-url", "https://download.pytorch.org/whl/cu128", "--force-reinstall"]
            print(f"🚀 Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PyTorch with CUDA 12.8 installed successfully using uv!")
                verify_installation()
                return True
            else:
                print(f"⚠️  uv pip failed: {result.stderr}")
                print("🔄 Trying alternative method...")
                
        except FileNotFoundError:
            print("⚠️  uv not found in PATH, trying alternative method...")
        
        # Method 2: Use regular pip with uv run
        cmd = ["uv", "run", "python", "-m", "pip", "install", "torch", "torchvision", "torchaudio",
               "--index-url", "https://download.pytorch.org/whl/cu128", "--force-reinstall"]
        print(f"🚀 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyTorch with CUDA 12.8 installed successfully!")
            verify_installation()
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def verify_installation():
    """Verify the PyTorch installation."""
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

if __name__ == "__main__":
    install_cuda_with_uv() 
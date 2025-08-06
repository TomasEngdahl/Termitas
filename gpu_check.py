#!/usr/bin/env python3
"""
GPU detection and PyTorch compatibility checker
"""

import torch
import sys

def check_gpu_compatibility():
    """Check GPU compatibility and provide installation guidance."""
    print("🔍 GPU Compatibility Check")
    print("=" * 50)
    
    # Check PyTorch version
    print(f"PyTorch version: {torch.__version__}")
    
    # Check CUDA availability
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            device_name = torch.cuda.get_device_name(i)
            device_capability = torch.cuda.get_device_capability(i)
            print(f"Device {i}: {device_name} (CUDA capability: {device_capability})")
        
        # Test basic GPU operations
        try:
            x = torch.randn(100, 100).cuda()
            y = torch.randn(100, 100).cuda()
            z = torch.mm(x, y)
            print("✅ Basic GPU operations working")
        except Exception as e:
            print(f"❌ GPU operations failed: {e}")
            return False
    else:
        print("❌ No CUDA devices found")
        return False
    
    return True

def get_installation_guide():
    """Provide installation guidance based on GPU."""
    print("\n📋 Installation Guide")
    print("=" * 50)
    
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        print(f"Detected GPU: {device_name}")
        
        if "RTX 5090" in device_name:
            print("\n🎯 RTX 5090 detected!")
            print("For RTX 5090, you need the latest PyTorch nightly build:")
            print("\nInstall with:")
            print("pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121")
            print("\nOr try the latest stable:")
            print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        else:
            print("\nFor your GPU, install PyTorch with CUDA support:")
            print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    else:
        print("\nNo GPU detected. Install CPU-only PyTorch:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")

def main():
    """Main function."""
    print("🚀 Termitas GPU Compatibility Checker")
    print("=" * 50)
    
    success = check_gpu_compatibility()
    get_installation_guide()
    
    if success:
        print("\n✅ GPU setup looks good!")
    else:
        print("\n❌ GPU setup needs attention")
        print("Follow the installation guide above to fix issues.")

if __name__ == "__main__":
    main() 
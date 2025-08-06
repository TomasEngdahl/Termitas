#!/usr/bin/env python3
"""
Build script for creating Termitas executable.
"""

import subprocess
import sys
import os
import shutil

def check_dependencies():
    """Check if required tools are installed."""
    try:
        result = subprocess.run(["pyinstaller", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PyInstaller found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found")
        print("Install with: pip install pyinstaller")
        return False

def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous build...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")

def build_exe():
    """Build the executable."""
    print("🔨 Building executable...")
    
    # PyInstaller command with optimizations for ONNX
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single exe file
        "--windowed",                   # No console window
        "--name=Termitas",              # Exe name
        "--add-data=logo3.ico;.",      # Include icon
        "--exclude-module=PIL",         # Reduce size
        "--exclude-module=matplotlib",  # Reduce size
        "--exclude-module=tkinter.test", # Reduce size
        "--exclude-module=unittest",    # Reduce size
        "--exclude-module=test",        # Reduce size
        "--exclude-module=distutils",   # Reduce size
        "--exclude-module=setuptools",  # Reduce size
        "main_exe.py"                   # Use exe-optimized version
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_exe():
    """Check if exe was created successfully."""
    exe_path = "dist/Termitas.exe"
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ Executable created: {exe_path}")
        print(f"📦 File size: {size_mb:.1f} MB")
        return True
    else:
        print("❌ Executable not found")
        return False

def main():
    """Main build process."""
    print("🎯 Termitas Build Script")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Clean previous builds
    clean_build()
    
    # Build exe
    if not build_exe():
        return False
    
    # Check result
    if not check_exe():
        return False
    
    print("\n🎉 Build completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the exe: ./dist/Termitas.exe")
    print("2. Check ONNX model loading works")
    print("3. Distribute the exe file")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
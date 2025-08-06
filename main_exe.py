#!/usr/bin/env python3
"""
Termitas - AI Terminal Agent (Exe Version)
Optimized for packaging as standalone executable.
"""

import customtkinter as ctk
import tkinter as tk
import os
import sys
from ui.core.grid import Grid

def setup_exe_environment():
    """Setup environment variables for exe packaging."""
    # Optimize memory usage for exe
    os.environ['ONNXRUNTIME_PROVIDER_PRIORITY'] = 'CPUExecutionProvider'
    
    # Reduce memory fragmentation
    os.environ['ONNXRUNTIME_DISABLE_MEMORY_PATTERN'] = '1'
    
    # Disable some heavy features for exe
    if getattr(sys, 'frozen', False):
        # Running as exe
        os.environ['HF_HUB_OFFLINE'] = '1'
        print("🚀 Running as packaged executable")
    else:
        print("🔧 Running in development mode")

def main():
    """Main application entry point."""
    print("🎯 Termitas - AI Terminal Agent")
    print("=" * 40)
    
    # Setup environment for exe
    setup_exe_environment()
    
    # Configure CustomTkinter
    ctk.set_appearance_mode("System")
    
    # Create main window
    app = ctk.CTk()
    app.title("Termitas")
    
    # Set icon (handle missing file gracefully)
    try:
        icon_path = "logo3.ico"
        if os.path.exists(icon_path):
            app.iconbitmap(icon_path)
        else:
            print("⚠️ Icon file not found, using default")
    except Exception as e:
        print(f"⚠️ Could not load icon: {e}")
    
    # Set window properties
    app.geometry("1800x800")
    app.resizable(True, True)
    
    # Create and setup grid
    try:
        grid = Grid(app)
        grid.create_grid()
        print("✅ UI initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing UI: {e}")
        # Show error dialog
        tk.messagebox.showerror("Error", f"Failed to initialize UI: {e}")
        return
    
    # Start application
    print("🚀 Starting application...")
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main() 
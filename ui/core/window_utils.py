#!/usr/bin/env python3
"""
Utility functions for window management
"""

import customtkinter as ctk

def center_window(window: ctk.CTkToplevel, width: int = None, height: int = None):
    """
    Center a popup window on the screen.
    
    Args:
        window: The CTkToplevel window to center
        width: Optional width to set (if not already set)
        height: Optional height to set (if not already set)
    """
    # Update window to get accurate dimensions
    window.update_idletasks()
    
    # Get window dimensions
    if width and height:
        window.geometry(f"{width}x{height}")
    else:
        # Get current geometry
        geometry = window.geometry()
        if 'x' in geometry:
            width, height = map(int, geometry.split('+')[0].split('x'))
        else:
            # Default size if geometry not set
            width, height = 400, 300
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate center position
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    # Ensure window doesn't go off screen
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))
    
    # Set window position
    window.geometry(f"{width}x{height}+{x}+{y}") 
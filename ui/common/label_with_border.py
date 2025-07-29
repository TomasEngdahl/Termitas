import customtkinter as ctk
from config import config

class LabelWithBorder:
    """
    This class is used to create a label with a border.
    Args:
        app: The main application instance.
        frame: The frame to pack the label with border.
        text: The text to display in the label.
        font: The font to use for the label.
        text_color: The color of the text.
        bg_color: The background color of the label. Transparent by default to inherit from parent.
        border_color: The color of the border. Green by default.
        border_width: The width of the border. 2 by default.
        corner_radius: The radius of the border. 0 by default.
        anchor: The anchor of the label. c by default. w = left, e = right, n = top, s = bottom, ne = top right, nw = top left, se = bottom right, sw = bottom left, c = center
        padding_x: The padding of the border frame. 10 by default.
        padding_y: The padding of the border frame. 10 by default.
    """
    def __init__(self, app: ctk.CTk, frame: ctk.CTkFrame, text, font, text_color, bg_color="transparent", border_color="green", border_width=2, corner_radius=0, anchor="c", padding_x=10, padding_y=10):
        super().__init__()
        self.app = app
        self.frame = frame
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.corner_radius = corner_radius
        self.anchor = anchor
        self.padding_x = padding_x
        self.padding_y = padding_y

    def create_label_with_border(self):
        self.frame.pack_propagate(False)

        self.border_frame = ctk.CTkFrame(self.frame,
                                         fg_color=self.bg_color,  
                                         border_width=self.border_width,           
                                         border_color=self.border_color, 
                                         corner_radius=self.corner_radius)     
        self.border_frame.pack(anchor=self.anchor, padx=self.padding_x, pady=self.padding_y)  # Left-align the entire border frame

        
        self.label = ctk.CTkLabel(self.border_frame,
                                  text=self.text,
                                  font=self.font,
                                  text_color=self.text_color,     
                                  fg_color="transparent")       
        self.label.pack(padx=8, pady=4)
                                           
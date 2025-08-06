import customtkinter as ctk
import tkinter as tk
from ui.core.grid import Grid

def main():
    ctk.set_appearance_mode("System")
     
    app = ctk.CTk()
    app.title("Termitas")
    icon_path = "logo3.ico"
    app.iconbitmap(icon_path)
    app.geometry("1800x800")
    app.resizable(True, True)
    grid = Grid(app)
    grid.create_grid()
    app.mainloop()

if __name__ == "__main__":
    main()






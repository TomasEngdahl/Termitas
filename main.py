import customtkinter as ctk
import tkinter as tk
from ui.grid import Grid

def main():

    ctk.set_appearance_mode("System")
     
    app = ctk.CTk()
    app.title("Termitas")
    icon_path = "logo.png"
    icon = tk.PhotoImage(file=icon_path)
    app.iconphoto(True, icon)
    app.geometry("1800x800")
    app.resizable(False, False)
    grid = Grid(app)
    grid.create_grid()
    app.mainloop()

if __name__ == "__main__":
    main()






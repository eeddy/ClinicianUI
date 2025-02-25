from tkinter import Tk, Button, Frame
from GameViewer import launch_game_viewer
from DataCollection import collect_data
from GestureViewer import view_data
import libemg 

def create_button(root, text, command):
    button_frame = Frame(root, padx=20, pady=20, bg="white") 
    button_frame.pack(side="top", fill="x") 
    button = Button(button_frame, text=text, command=command, font=("Arial", 16), padx=20, pady=10, bg="white") 
    button.pack(expand=True, fill="both")

def main(odh = None):
    if odh is None:
        str, smm = libemg.streamers.myo_streamer()
        odh = libemg.data_handler.OnlineDataHandler(smm)

    root = Tk()
    root.title("Game Launcher")
    root.geometry("200x300")
    root.configure(bg="white")
    root.attributes("-topmost", True)
    root.focus_force() 

    # Create three buttons with sample commands (replace with your actual functions)
    create_button(root, "Record Data", lambda: [root.destroy(), collect_data(odh)])
    create_button(root, "Manage Data", lambda: [root.destroy(), view_data(odh)])
    create_button(root, "Games", lambda: [root.destroy(), launch_game_viewer(odh)])

    root.mainloop()

if __name__ == "__main__":
    main()
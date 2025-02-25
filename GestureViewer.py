import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class GestureApp:
    def __init__(self, root, odh):
        self.root = root
        self.odh = odh 
        self.root.title("Gesture Visualization")
        self.root.geometry("800x600")
        self.root.configure(bg="#f5f5f5")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 

        # Create outer frame to center everything
        self.outer_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.outer_frame.pack(fill="both", expand=True)
        
        # Configure column and row weights to center content
        self.outer_frame.grid_columnconfigure(0, weight=1)
        self.outer_frame.grid_rowconfigure(0, weight=1)

        # Create scrollable frame
        self.scrollable_frame = tk.Frame(self.outer_frame, bg="#f5f5f5")
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        # Create scrollbar
        self.scrollbar = tk.Scrollbar(self.scrollable_frame)
        self.scrollbar.pack(side="right", fill="y")

        # Create canvas
        self.canvas = tk.Canvas(
            self.scrollable_frame,
            yscrollcommand=self.scrollbar.set,
            bg="#f5f5f5",
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar.config(command=self.canvas.yview)

        # Create content frame
        self.content_frame = tk.Frame(self.canvas, bg="#f5f5f5")
        
        # Center the content frame in the canvas
        self.canvas_frame = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="center",
            tags="content"
        )

        # Add title
        self.title_label = tk.Label(
            self.content_frame,
            text="Gesture Library",
            font=("Helvetica", 24, "bold"),
            bg="#f5f5f5",
            fg="#333333"
        )
        self.title_label.pack(pady=(20, 5))

        # Create button to delete all gestures - fixing button style
        self.delete_all_button = tk.Button(
            self.content_frame,
            text="Delete All",
            command=self.delete_all_gestures,
            bg="white",
            fg="black",
            relief="flat",
            font=("Helvetica", 10),
            width=20,
            highlightthickness=0,  # Remove highlight border
            activebackground="white"  # Keep white when clicked
        )
        self.delete_all_button.pack(pady=5)

        # Create frame for cards
        self.cards_frame = tk.Frame(self.content_frame, bg="#f5f5f5")
        self.cards_frame.pack(expand=True)

        # Bind resize event
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.content_frame.bind('<Configure>', self.on_frame_configure)

        self.load_gestures()
    
    def on_closing(self):
        self.root.destroy()
        from Main import main
        main(self.odh)

    def on_canvas_configure(self, event):
        # Update the width of the canvas window
        self.canvas.itemconfig(
            "content",
            width=event.width
        )
        
    def on_frame_configure(self, event):
        # Reset the scroll region to encompass the content
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_gestures(self):
        # Clear existing gestures
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Get and sort gestures
        filenames = sorted(os.listdir("Data/"))

        # Create gesture cards in a grid layout
        row = 0
        col = 0
        for filename in filenames:
            # Create card frame
            card = tk.Frame(
                self.cards_frame,
                bg="white",
                relief="solid",
                borderwidth=1
            )
            card.grid(row=row, column=col, padx=10, pady=10)

            # Gesture type label
            title_label = tk.Label(
                card,
                text=filename.split("_")[1].capitalize(),
                bg="white",
                fg="#333333",
                font=("Helvetica", 16, "bold")
            )
            title_label.pack(pady=(10, 5))

            # Create plot
            fig = Figure(figsize=(2.5, 1.5))
            ax = fig.add_subplot(111)
            
            data = pd.read_csv("Data/" + filename)
            ax.plot(data, linewidth=1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor('#ffffff')
            fig.patch.set_facecolor('#ffffff')
            
            # Remove spines
            for spine in ax.spines.values():
                spine.set_visible(False)

            # Add plot to card
            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(pady=5, padx=10)

            # Delete button - fix button styling
            delete_button = tk.Button(
                card,
                text="Delete",
                command=lambda f=filename: self.delete_gesture(f),
                bg="white",
                fg="black",
                relief="flat",
                font=("Helvetica", 10),
                width=10,
                highlightthickness=0,  # Remove highlight border
                activebackground="white",  # Keep white when clicked
                activeforeground="black",  # Keep text black when clicked
                bd=0  # Remove any border
            )
            delete_button.pack(pady=(5, 10))

            # Update grid position
            col += 1
            if col == 3:  # 3 cards per row
                col = 0
                row += 1

        # Configure grid columns to be equal width
        for i in range(3):
            self.cards_frame.grid_columnconfigure(i, weight=1)
        
        self.root.after(100, lambda: self.canvas.yview_moveto(0))

    def delete_all_gestures(self):
        if messagebox.askyesno("Confirm Delete", 
                            f"Are you sure you want to delete all gestures?"):
            for filename in os.listdir("Data"):
                os.remove(os.path.join("Data", filename))
            self.load_gestures()


    def delete_gesture(self, filename):
        if messagebox.askyesno("Confirm Delete", 
                            f"Are you sure you want to delete {filename}?"):
            os.remove(os.path.join("Data", filename))
            self.cards_frame.after(100, self.load_gestures)

def view_data(odh):
    root = tk.Tk()
    app = GestureApp(root, odh)
    root.mainloop()
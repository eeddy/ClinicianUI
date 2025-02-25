import tkinter as tk
from tkinter import ttk
from tkinter import Canvas
from PIL import Image, ImageTk
import time
import numpy as np
import os 
import matplotlib.pyplot as plt 

class DataCollectionApp:
    def __init__(self, root, odh):
        self.root = root
        self.root.title("Data Collection")
        self.root.geometry("400x500")
        self.root.configure(bg="white")
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 

        self.odh = odh 
        self.data = []

        self.gesture_var = tk.StringVar()

        # Add dropdown value label
        self.dropdown_label = tk.Label(
            root, 
            textvariable=self.gesture_var, 
            font=("Arial", 24, "bold"), 
            fg="#008000", 
            bg="white"
        )
        self.dropdown_label.pack()

        # Create canvas for circular progress
        self.canvas = Canvas(root, width=250, height=250, bg="white", highlightthickness=0)
        self.canvas.pack(pady=0)

        # Add progress text label
        self.progress_label = tk.Label(
            root, 
            text="0%", 
            font=("Arial", 24, "bold"), 
            fg="#008000", 
            bg="white"
        )
        self.progress_label.pack()

        # Gesture selection dropdown
        self.gesture_var.set("Rest")  # Default value
        self.gesture_options = ["Rest", "Open", "Close", "Pronation", "Supination"]

        self.gesture_dropdown = ttk.Combobox(root, textvariable=self.gesture_var)
        self.gesture_dropdown['values'] = self.gesture_options
        self.gesture_dropdown['state'] = 'normal'
        self.gesture_dropdown.bind("<<ComboboxSelected>>", self.update_image)
        self.gesture_dropdown.pack(pady=10)

        # Style the dropdown
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TMenubutton', background="#ffffff")

        # Progress tracking
        self.progress = 0
        self.total_time = 5
        self.recording = False
        self.after_id = None
        self.start_time = None

        # Record button
        self.record_button = tk.Button(
            root, 
            text="Record",
            command=self.toggle_recording,
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            font=("Arial", 12)
        )
        self.record_button.pack(pady=10)

        # self.checkbox_frame = tk.Frame(root, bg="white")
        # self.checkbox_frame.pack(pady=(0, 10))

        # self.plot_var = tk.BooleanVar()
        # self.plot_checkbox = tk.Checkbutton(self.checkbox_frame, text="Plot", variable=self.plot_var, bg="white", fg="black")
        # self.plot_checkbox.pack(side=tk.LEFT, padx=10)

        # self.pca_var = tk.BooleanVar()
        # self.pca_checkbox = tk.Checkbutton(self.checkbox_frame, text="PCA", variable=self.pca_var, bg="white", fg="black")
        # self.pca_checkbox.pack(side=tk.LEFT, padx=10)

        # Store images in memory
        self.images = {}
        self.load_images()

        # Initialize the progress arc
        self.draw_progress(0)

    def on_closing(self):
        self.root.destroy()
        from Main import main
        main(self.odh)

    def load_images(self):
        for gesture in self.gesture_options:
            try:
                img = Image.open(f"Gestures/{gesture}.png")
                img.thumbnail((150, 75))
                self.images[gesture] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image for {gesture}:", e)

    def toggle_recording(self):
        """Toggle between recording and stopped states"""
        if not self.recording:
            # Start recording
            self.odh.reset()
            self.data = []
            self.recording = True
            self.start_time = time.time()
            self.record_button.configure(text="Stop", bg="#ff4444", fg="white")
            self.update_progress()
        else:
            # Stop recording
            self.stop_recording()

    def stop_recording(self):
        """Stop the recording process"""
        self.recording = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.progress = 0
        self.record_button.configure(text="Record", bg="SystemButtonFace", fg="black")
        self.draw_progress(0)
        self.progress_label.configure(text="0%")

    def update_progress(self):
        """Update the progress display"""
        if self.recording:
            elapsed = time.time() - self.start_time
            progress = (elapsed / self.total_time) * 100
            new_data, amount = self.odh.get_data()
            if amount['emg'][0][0] > 0:
                if len(self.data) == 0:
                    self.data = new_data['emg'][:amount['emg'][0][0]]
                else:
                    self.data = np.vstack([self.data, new_data['emg'][:amount['emg'][0][0]]])
            self.odh.reset()
            
            if progress >= 100:
                if not os.path.exists('Data/'):
                    os.makedirs('Data/')
                reps = lambda d, k: sum(1 for f in os.listdir(d) if k in f and os.path.isfile(os.path.join(d, f)))
                file_count = reps('Data', self.gesture_var.get()) 
                reps = lambda d, k: sum(1 for f in os.listdir(d) if k in f and os.path.isfile(os.path.join(d, f)))
                np.savetxt('Data/C_' + self.gesture_var.get() + "_R_" + str(file_count) + '_T_' + str(time.time()) + ".csv", self.data, delimiter=",")
                self.stop_recording()
                # if self.plot_var.get():
                #     self.plot_channels(self.data)
            else:
                self.draw_progress(progress)
                self.progress_label.configure(text=f"{int(progress)}%")
                self.after_id = self.root.after(100, self.update_progress)

    def draw_progress(self, percent):
        """Draws a clockwise circular progress arc with outline."""
        self.canvas.delete("all")
        
        # Constants for circle dimensions
        x1, y1 = 25, 25  # Top-left coordinates
        x2, y2 = 225, 225  # Bottom-right coordinates
        start_angle = -90
        extent_angle = (percent / 100) * 360
        
        # Draw outer circle border (black outline)
        self.canvas.create_oval(x1-2, y1-2, x2+2, y2+2, outline="black", width=2)
        
        # Draw background arc (grey)
        self.canvas.create_arc(x1, y1, x2, y2,
                            start=start_angle,
                            extent=-360,
                            outline="#cccccc",
                            width=20,
                            style=tk.ARC)
        
        # Draw progress arc (green)
        if extent_angle > 0:
            self.canvas.create_arc(x1, y1, x2, y2,
                                start=start_angle,
                                extent=-extent_angle,
                                outline="#008000",
                                width=20,
                                style=tk.ARC)

        self.update_image()

    def update_image(self, event=None):
        # Draw current gesture image
        self.canvas.delete("image")
        current_gesture = self.gesture_var.get()
        if current_gesture in self.images:
            self.canvas.create_image(125, 125, image=self.images[current_gesture], tags="image")

    def plot_channels(self, data):
        num_channels = data.shape[1]
        inter_channel_amount = 1.5 * np.max(data)
        for j in range(num_channels):
            y_data = data[:, j]
            plt.plot(y_data + inter_channel_amount * j)
        plt.xlabel('Time')
        plt.ylabel('EMG')
        plt.show()

def collect_data(odh):
    # odh = None 
    root = tk.Tk()
    app = DataCollectionApp(root, odh)
    root.mainloop()
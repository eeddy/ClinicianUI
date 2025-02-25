import libemg
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import Tk, Toplevel, Frame, Label, messagebox, PhotoImage, Canvas, Scrollbar

from Games.emg_hero import start_game as start_emg_hero
from Games.snake import start_game as start_snake
from Games.penguin.main import start_game as start_penguins
from Games.OneDFitts import OneDFitts
from Games.ISOFitts import FittsLawTest

class GameViewer:
    def __init__(self, root, odh):
        # Initialize main window
        self.root = root
        self.odh = odh
        self.root.title("Game Launcher")
        self.root.geometry("800x600")
        self.root.configure(bg="white")
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 

        # Setup classifier 
        self.set_up_classifier()

        # Add title
        self.title_label = tk.Label(
            self.root,
            text="Games",
            font=("Helvetica", 24, "bold"),
            bg="white",
            fg="#333333"
        )
        self.title_label.pack(pady=(20, 5))
        
        # Setup UI frames and scrolling
        self.setup_ui_framework()
        
        # Dictionary to store game information
        self.games = {
            'pacman': {
                'title': 'Penguin Jumper',
                'thumbnail': 'Icons/Penguin.png',
                'module': start_penguins
            },
            'snake': {
                'title': 'Snake',
                'thumbnail': 'Icons/Snake.png',
                'module': start_snake
            },
            'guitar_hero': {
                'title': 'Guitar Hero',
                'thumbnail': 'Icons/GuitarHero.png',
                'module': start_emg_hero
            },
            'raw_data': {
                'title': 'Raw Data',
                'thumbnail': 'Icons/RawData.png',
                'module': self.odh.visualize
            },
            'one_d_fitts': {
                'title': '1D Fitts',
                'thumbnail': 'Icons/1dfitts.png',
                'module': OneDFitts().start_game
            },
            'two_d_fitts': {
                'title': '2D Fitts',
                'thumbnail': 'Icons/2dfitts.png',
                'module': FittsLawTest().run
            },
            'pca': {
                'title': 'PCA',
                'thumbnail': 'Icons/pca.png',
                'module': None
            }
        }
        
        # Store images to prevent garbage collection
        self.image_cache = {}

        self.create_game_cards()
    
    def on_closing(self):
        self.root.destroy()
        from Main import main
        main(self.odh)

    def set_up_classifier(self):
        WINDOW_SIZE = 30 
        WINDOW_INCREMENT = 5

        self.names = ["Rest", "Close", "Open", "Pronation", "Supination"]

        # Step 1: Parse offline training data 
        #TODO: This is currently hardcoded. 
        dataset_folder = 'Data/'
        regex_filters = [
            libemg.data_handler.RegexFilter(left_bound = "C_", right_bound="_R", values = self.names, description='classes'),
            libemg.data_handler.RegexFilter(left_bound = "R_", right_bound="_T_", values = ["0", "1"], description='reps'),
        ]

        offline_dh = libemg.data_handler.OfflineDataHandler()
        offline_dh.get_data(folder_location=dataset_folder, regex_filters=regex_filters, delimiter=",")
        train_windows, train_metadata = offline_dh.parse_windows(WINDOW_SIZE, WINDOW_INCREMENT)
        self.labels = train_metadata['classes']

        # Step 2: Extract features from offline data
        fe = libemg.feature_extractor.FeatureExtractor()
        feature_list = fe.get_feature_groups()['HTD']
        self.training_features = fe.extract_features(feature_list, train_windows)

        # Step 3: Dataset creation
        data_set = {}
        data_set['training_features'] = self.training_features
        data_set['training_labels'] = train_metadata['classes']

        # Step 4: Create the EMG Classifier
        o_classifier = libemg.emg_predictor.EMGClassifier(model="LDA")
        o_classifier.fit(feature_dictionary=data_set)

        # Step 5: Create online EMG classifier and start classifying.
        self.classifier = libemg.emg_predictor.OnlineEMGClassifier(o_classifier, WINDOW_SIZE, WINDOW_INCREMENT, self.odh, feature_list, std_out=False)
        self.classifier.run(block=False) 

    def setup_ui_framework(self):
        """Creates a scrollable frame for holding game cards."""
        # Create a frame to hold the canvas and scrollbar
        self.container_frame = Frame(self.root, bg="white")
        self.container_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        # Create canvas - removing border with highlightthickness=0
        self.canvas = Canvas(self.container_frame, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Add vertical scrollbar to canvas
        self.scrollbar = Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        # Configure the canvas to use the scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Create a frame inside the canvas to hold the game cards
        self.cards_frame = Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Make the cards frame expand to fill canvas width
        self.canvas.bind('<Configure>', self._configure_canvas)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _configure_canvas(self, event):
        """Configure the canvas when the window is resized."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # After cards are created, configure grid to center content
        for i in range(3):  # 3 columns
            self.cards_frame.columnconfigure(i, weight=1)

    def create_game_cards(self):
        """Creates game selection cards in a 3x3 grid layout."""
        row = 0
        col = 0
        
        # Create a parent frame to center the grid
        center_frame = Frame(self.cards_frame, bg="white")
        center_frame.pack(expand=True)
        
        for game_id, game_info in self.games.items():
            # Create card frame
            card = Frame(center_frame, bg="white")
            card.grid(row=row, column=col, padx=20, pady=20)  # Increased padding for better spacing

            # Create a frame for the thumbnail with padding
            thumbnail_frame = Frame(card, bg="white", relief="solid", borderwidth=1)
            thumbnail_frame.pack(padx=10, pady=5)
            
            # Game thumbnail
            thumbnail_image = self.load_thumbnail(game_info['thumbnail'])
            if thumbnail_image:
                thumbnail = Label(thumbnail_frame, image=thumbnail_image, cursor="hand2", bg="white")
                thumbnail.image = thumbnail_image  # Prevent garbage collection
                self.image_cache[game_id] = thumbnail_image  # Store in cache
                thumbnail.pack(padx=10, pady=10)  # Add padding inside the frame
                
                # Bind click events to both the frame and thumbnail
                thumbnail_frame.bind('<Button-1>', lambda e, g=game_id: self.launch_game(g))
                thumbnail.bind('<Button-1>', lambda e, g=game_id: self.launch_game(g))
                
                # Add hover effect to the frame
                thumbnail_frame.bind('<Enter>', lambda e, frame=thumbnail_frame: self.on_hover(frame))
                thumbnail_frame.bind('<Leave>', lambda e, frame=thumbnail_frame: self.on_leave(frame))
                thumbnail.bind('<Enter>', lambda e, frame=thumbnail_frame: self.on_hover(frame))
                thumbnail.bind('<Leave>', lambda e, frame=thumbnail_frame: self.on_leave(frame))
            
            # Add game title below thumbnail
            title_label = Label(card, text=game_info['title'], bg="white", fg="#333333", font=("Helvetica", 12))
            title_label.pack(pady=(0, 5))
            
            # Update grid position
            col += 1
            if col == 3:  # 3 cards per row (3x3 grid)
                col = 0
                row += 1
        
        # Configure grid columns for center frame
        for i in range(3):
            center_frame.columnconfigure(i, weight=1)

    def load_thumbnail(self, image_path):
        """Loads and returns a PhotoImage for the given image path."""
        try:
            image = Image.open(image_path)
            image = image.resize((150, 150), Image.LANCZOS)  # Resize with high-quality downscaling
            return ImageTk.PhotoImage(image) 
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None  # Return None if image fails to load

    def on_hover(self, frame):
        """Add hover effect to the thumbnail frame."""
        frame.configure(relief="raised", borderwidth=2)

    def on_leave(self, frame):
        """Remove hover effect from the thumbnail frame."""
        frame.configure(relief="solid", borderwidth=1)

    def launch_game(self, game_id):
        """Launch the selected game in a new window."""
        try:
            self.root.destroy()
            self.root.quit()
            if game_id == 'pca':
                self.classifier.stop_running()
                self.odh.visualize_feature_space(self.training_features, 30, 20, 200, classes = self.labels, class_labels=self.names)
            else:
                self.games[game_id]['module']()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {self.games[game_id]['title']}: {str(e)}")

def launch_game_viewer(odh):
    root = Tk()
    app = GameViewer(root, odh)
    root.mainloop()
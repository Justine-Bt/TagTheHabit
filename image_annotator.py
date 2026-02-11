
"""
Tag the Habit! 
An image annotation tool for hard single-label classification of HVPS-4 data.

Usage:
    1. Run the script: python image_annotator.py
    2. Click "Select Image Folder" and choose your folder
    3. Use keyboard shortcuts (1-9) or click to annotate
    4. Navigate with arrow keys
    5. Annotations auto-save to annotations.csv
    
Configuration:
    Edit config.json to customize classes and image sizes
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import csv
import json


class ImageAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tag The Habit -- Cloud particle habit annotation tool for HVPS-4 data")
        
        # Load configuration
        self.load_config()
        
        self.image_folder = ""
        self.images = []
        self.current_index = 0
        self.annotations = {}
        
        self.selected_class = tk.IntVar(value=-1)
        
        self.setup_ui()
        self.load_previous_annotations()
        # Initialize statistics display
        self.update_statistics()
    
    def load_config(self):
        """Load config file using config.json - stops execution if config is invalid"""
        # Look for config.json in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, "config.json")
        
        # Check if config file exists
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found.\n"
                f"Please create a config.json file in the same directory as the script."
            )
        
        # Load configuration
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON format error in configuration file: {e}\n"
                f"Please verify that config.json is valid JSON."
            )
        except Exception as e:
            raise Exception(
                f"Error reading configuration file: {e}"
            )
        
        # Validate required fields
        if "classes" not in config:
            raise KeyError(
                "The 'classes' field is required in the configuration file."
            )
        
        self.classes = config["classes"]
        
        # Validate number of classes
        if not isinstance(self.classes, list):
            raise TypeError(
                "The 'classes' field must be a list of strings."
            )
        
        if len(self.classes) == 0:
            raise ValueError(
                "The configuration file must contain at least one class."
            )
        
        if len(self.classes) > 9:
            raise ValueError(
                f"Number of classes must not exceed 9 (currently {len(self.classes)}).\n"
                f"Keyboard shortcuts are limited to keys 1-9."
            )
        
        # Load other required fields
        if "annotations_file" not in config:
            raise KeyError(
                "The 'annotations_file' field is required in the configuration file."
            )
        self.annotations_file = config["annotations_file"]
        
        if "resized_image_size" not in config:
            raise KeyError(
                "The 'resized_image_size' field is required in the configuration file."
            )
        self.resized_image_size = config["resized_image_size"]
        
        if "max_original_display_size" not in config:
            raise KeyError(
                "The 'max_original_display_size' field is required in the configuration file."
            )
        self.max_display_size = config["max_original_display_size"]
    
    def setup_ui(self):
        """Create user interface"""
        
        # Main frame with 2 columns: images on left, controls on right
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left frame: images
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=(0, 10), sticky=(tk.N, tk.W))
        
        # Button to select folder
        ttk.Button(left_frame, text="Select Image Folder", 
                   command=self.select_folder).grid(row=0, column=0, pady=(0, 10))
        
        # Frame for two images side by side
        images_frame = ttk.Frame(left_frame)
        images_frame.grid(row=1, column=0, pady=10)
        
        # Original image (or message if too large)
        original_frame = ttk.LabelFrame(images_frame, text="Original Size", padding="5")
        original_frame.grid(row=0, column=0, padx=5)
        
        # Label to display either image or message
        self.original_display = ttk.Label(original_frame, text="", justify=tk.CENTER)
        self.original_display.pack()
        
        # Resized image
        resized_frame = ttk.LabelFrame(images_frame, text=f"Longest side = {self.resized_image_size}px", padding="5")
        resized_frame.grid(row=0, column=1, padx=5)
        self.resized_image_label = ttk.Label(resized_frame)
        self.resized_image_label.pack()
        
        # Filename and dimensions
        self.filename_label = ttk.Label(left_frame, text="", font=('Arial', 10, 'bold'), wraplength=800)
        self.filename_label.grid(row=2, column=0, pady=5)
        
        # Navigation
        nav_frame = ttk.Frame(left_frame)
        nav_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(nav_frame, text="← Previous", 
                   command=self.previous_image).grid(row=0, column=0, padx=5)
        ttk.Button(nav_frame, text="Next →", 
                   command=self.next_image).grid(row=0, column=1, padx=5)
        
        # Right frame: Annotation
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.N, tk.W, tk.E))
        
        # Progress label
        self.progress_label = ttk.Label(right_frame, text="No images loaded", 
                                       font=('Arial', 11, 'bold'))
        self.progress_label.grid(row=0, column=0, pady=(0, 20))
        
        # Frame for classes
        classes_frame = ttk.LabelFrame(right_frame, text="Select Class", padding="15")
        classes_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Radio buttons for each class
        for i, class_name in enumerate(self.classes):
            rb = ttk.Radiobutton(
                classes_frame, 
                text=f"{i+1}. {class_name}",
                variable=self.selected_class,
                value=i,
                command=self.on_class_selected
            )
            rb.grid(row=i, column=0, sticky=tk.W, pady=3, padx=5)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(right_frame, text="Keyboard Shortcuts", padding="10")
        instructions_frame.grid(row=2, column=0, pady=20, sticky=(tk.W, tk.E))
        
        ttk.Label(instructions_frame, text=f"1-{len(self.classes)}: Select class", 
                 font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(instructions_frame, text="← →: Navigate", 
                 font=('Arial', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(instructions_frame, text="Ctrl+S: Save", 
                 font=('Arial', 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Display CSV file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, self.annotations_file)
        
        csv_info_frame = ttk.LabelFrame(right_frame, text="Save File", padding="10")
        csv_info_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(csv_info_frame, text="Saving path:", 
                 font=('Arial', 8)).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(csv_info_frame, text=csv_path, 
                 font=('Arial', 8), foreground='blue', wraplength=300).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Statistics frame showing count per class
        stats_frame = ttk.LabelFrame(right_frame, text="Annotation Statistics", padding="10")
        stats_frame.grid(row=1, column=1, padx=10, pady=0, sticky=(tk.W, tk.E))
        
        # Create labels for each class count
        self.stats_labels = []
        for i, class_name in enumerate(self.classes):
            label = ttk.Label(stats_frame, text=f"{class_name}: 0", 
                            font=('Arial', 9))
            label.grid(row=i, column=0, sticky=tk.W, pady=1, padx=5)
            self.stats_labels.append(label)
        
        # Keyboard Shortcuts
        self.root.bind('<Left>', lambda e: self.previous_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Control-s>', lambda e: self.save_annotations())
        
        for i in range(1, len(self.classes)+1):
            self.root.bind(str(i), lambda e, idx=i-1: self.select_class_by_key(idx))
    
    def select_folder(self):
        """Select folder containing images"""
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            self.image_folder = folder
            self.load_images()
    
    def load_images(self):
        """Load all images from the folder"""
        extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
        self.images = [
            f for f in os.listdir(self.image_folder)
            if f.lower().endswith(extensions)
        ]
        self.images.sort()
        
        if self.images:
            self.current_index = 0
            self.display_image()
        else:
            messagebox.showwarning("Warning", "No images found in this folder")
    
    def load_previous_annotations(self):
        """Load previous annotations if they exist"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        annotations_path = os.path.join(script_dir, self.annotations_file)
        
        if os.path.exists(annotations_path):
            with open(annotations_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.annotations[row['filename']] = int(row['class_index'])
    
    def display_image(self):
        """Load and display current image"""
        if not self.images:
            return
        
        image_path = os.path.join(self.image_folder, self.images[self.current_index])
        
        try:
            # Load the original image
            img_original = Image.open(image_path)
            original_size = img_original.size
            max_original_side = max(original_size)
            
            # Decide if we display original or a message
            if max_original_side <= self.resized_image_size:
                # Small image: display at original size on left
                photo_original = ImageTk.PhotoImage(img_original)
                self.original_display.config(image=photo_original, text="")
                self.original_display.image = photo_original
            else:
                # Large image: display a message on left
                message = f"Image too large\n({original_size[0]}x{original_size[1]}px)\n\n→ See resized\nversion"
                self.original_display.config(text=message, image="", font=('Arial', 11), 
                                            foreground='gray40', wraplength=350)
                self.original_display.image = None
            
            # Resized image on right
            img_resized = img_original.copy()
            
            if max_original_side < self.resized_image_size:
                # Image smaller than target size: enlarge
                scale = self.resized_image_size / max_original_side
                new_width = int(img_resized.size[0] * scale)
                new_height = int(img_resized.size[1] * scale)
                img_resized = img_resized.resize((new_width, new_height), Image.Resampling.NEAREST)
            elif max_original_side > self.resized_image_size:
                # Image larger than target size: reduce
                img_resized.thumbnail((self.resized_image_size, self.resized_image_size), Image.Resampling.NEAREST)
            # If max_side == target size, keep as is
            resized_size = img_resized.size
            photo_resized = ImageTk.PhotoImage(img_resized)
            self.resized_image_label.config(image=photo_resized)
            self.resized_image_label.image = photo_resized
            
            # Update filename and progress labels
            self.filename_label.config(
                text=f"{self.images[self.current_index]} - Original: {original_size[0]}x{original_size[1]}px | Resized: {resized_size[0]}x{resized_size[1]}px"
            )
            self.progress_label.config(
                text=f"Image {self.current_index + 1} / {len(self.images)} "
                     f"({len(self.annotations)} annotated)"
            )
            
            # Load annotation if it exists
            current_image = self.images[self.current_index]
            if current_image in self.annotations:
                self.selected_class.set(self.annotations[current_image])
            else:
                self.selected_class.set(-1)
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load image: {e}")
    
    def select_class_by_key(self, class_index):
        """Select a class using keyboard shortcut"""
        self.selected_class.set(class_index)
        self.on_class_selected()
    
    def on_class_selected(self):
        """Called when a class is selected"""
        if self.images and self.selected_class.get() >= 0:
            current_image = self.images[self.current_index]
            self.annotations[current_image] = self.selected_class.get()
            self.save_annotations()
            self.update_statistics()
            self.progress_label.config(
                text=f"Image {self.current_index + 1} / {len(self.images)} "
                     f"({len(self.annotations)} annotated)"
            )
    
    def update_statistics(self):
        """Update the annotation statistics display"""
        # Count annotations per class
        class_counts = [0] * len(self.classes)
        for class_idx in self.annotations.values():
            if 0 <= class_idx < len(self.classes):
                class_counts[class_idx] += 1
        
        # Update labels
        for i, count in enumerate(class_counts):
            self.stats_labels[i].config(text=f"{self.classes[i]}: {count}")
    
    def save_annotations(self):
        """Save annotations to CSV file"""
        # Save in the same folder as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        annotations_path = os.path.join(script_dir, self.annotations_file)
        
        with open(annotations_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'class_index', 'class_name'])
            for image, class_idx in sorted(self.annotations.items()):
                writer.writerow([image, class_idx, self.classes[class_idx]])
    
    def previous_image(self):
        """Go to previous image"""
        if self.images and self.current_index > 0:
            self.current_index -= 1
            self.display_image()
    
    def next_image(self):
        """Go to next image"""
        if self.images and self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.display_image()


def main():
    try:
        root = tk.Tk()
        app = ImageAnnotator(root)
        root.mainloop()
    except (FileNotFoundError, ValueError, KeyError, TypeError) as e:
        # Show error in messagebox if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showerror("Configuration Error", str(e))
            root.destroy()
        except:
            # If tkinter not available, print to console
            print(f"\nCONFIGURATION ERROR\n{str(e)}\n")
        # Exit with error code
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR\n{str(e)}\n")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()

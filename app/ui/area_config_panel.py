import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class AreaConfigPanel:
    def __init__(self, parent, health_selector, minimap_selector, coordinates_selector, main_app):
        self.parent = parent
        self.health_selector = health_selector
        self.minimap_selector = minimap_selector
        self.coordinates_selector = coordinates_selector
        self.main_app = main_app
        
        self._create_ui()
    
    def _create_ui(self):
        areas_frame = tk.Frame(self.parent, bg="#2d2d2d")
        areas_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        title_label = tk.Label(areas_frame, text="Area Configuration", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=12)
        
        for name, color, selector in [
            ("Health Bar", "#dc3545", self.health_selector),
            ("Minimap Area", "#17a2b8", self.minimap_selector),
            ("Coordinates Area", "#ffc107", self.coordinates_selector)
        ]:
            self._create_area_card(areas_frame, name, color, selector)
        
        self.config_status_label = tk.Label(areas_frame, text="Configure areas to continue",
                                           font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffc107")
        self.config_status_label.pack(pady=12)
        
        self._create_info_displays(areas_frame)
    
    def _create_area_card(self, parent, title, color, selector):
        card = tk.Frame(parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, padx=4, pady=4)
        
        header = tk.Frame(card, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=8)
        
        title_label = tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), 
                              bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                             bg="#3d3d3d", fg="#dc3545")
        status_dot.pack(side=tk.RIGHT)
        setattr(selector, 'status_dot', status_dot)
        
        preview_frame = tk.Frame(card, bg="#1a1a1a", height=40)
        preview_frame.pack(fill=tk.X, padx=8, pady=4)
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Not Configured",
                               bg="#1a1a1a", fg="#666666", font=("Segoe UI", 9))
        preview_label.pack(expand=True)
        setattr(selector, 'preview_label', preview_label)
        
        btn_frame = tk.Frame(card, bg="#3d3d3d")
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        
        select_btn = tk.Button(btn_frame, text=f"Select {title}",
                             bg=color, fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 9), activebackground=color,
                             command=lambda: self.main_app.start_area_selection(title, color, selector))
        select_btn.pack(fill=tk.X)
    
    def _create_info_displays(self, parent):
        health_info_frame = tk.Frame(parent, bg="#2d2d2d")
        health_info_frame.pack(fill=tk.X, pady=12)
        
        tk.Label(health_info_frame, text="Current Health:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.health_percentage_var = tk.StringVar(value="100.0%")
        tk.Label(health_info_frame, textvariable=self.health_percentage_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        
        coords_info_frame = tk.Frame(parent, bg="#2d2d2d")
        coords_info_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(coords_info_frame, text="Current Position:", bg="#2d2d2d", fg="#ffc107",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.coordinates_var = tk.StringVar(value="Not detected")
        tk.Label(coords_info_frame, textvariable=self.coordinates_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
    
    def update_area_status(self, selector):
        if hasattr(selector, 'status_dot') and hasattr(selector, 'preview_label'):
            if selector.is_setup():
                selector.status_dot.config(fg="#28a745")
                selector.preview_label.config(text="Configured", fg="#28a745")
                
                if hasattr(selector, 'preview_image') and selector.preview_image:
                    try:
                        img = selector.preview_image.resize((80, 40), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        selector.preview_label.config(image=photo, text="")
                        selector.preview_label.image = photo
                    except Exception:
                        pass
            else:
                selector.status_dot.config(fg="#dc3545")
                selector.preview_label.config(text="Not Configured", fg="#666666")
    
    def set_config_status(self, text, color):
        self.config_status_label.config(text=text, fg=color)
    
    def update_health_percentage(self, percentage):
        self.health_percentage_var.set(f"{percentage:.1f}%")
    
    def update_coordinates(self, coordinates):
        self.coordinates_var.set(coordinates)
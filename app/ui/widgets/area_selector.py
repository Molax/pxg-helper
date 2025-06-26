import tkinter as tk
from PIL import Image, ImageTk
import logging

logger = logging.getLogger('PokeXHelper')

class AreaSelectorWidget:
    def __init__(self, parent, title, color, selector, main_app):
        self.parent = parent
        self.title = title
        self.color = color
        self.selector = selector
        self.main_app = main_app
        
        self.card_frame = None
        self.status_dot = None
        self.preview_label = None
        
        self._create_widget()
        self._update_status()
    
    def _create_widget(self):
        self.card_frame = tk.Frame(self.parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        self.card_frame.pack(fill=tk.X, padx=4, pady=4)
        
        self._create_header()
        self._create_preview_area()
        self._create_controls()
    
    def _create_header(self):
        header = tk.Frame(self.card_frame, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=8)
        
        title_label = tk.Label(header, text=self.title, font=("Segoe UI", 10, "bold"), 
                              bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        self.status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                                  bg="#3d3d3d", fg="#dc3545")
        self.status_dot.pack(side=tk.RIGHT)
    
    def _create_preview_area(self):
        preview_frame = tk.Frame(self.card_frame, bg="#1a1a1a", height=80)
        preview_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(preview_frame, text="No preview available",
                                     bg="#1a1a1a", fg="#888888", font=("Segoe UI", 9))
        self.preview_label.pack(expand=True, fill=tk.BOTH)
    
    def _create_controls(self):
        controls_frame = tk.Frame(self.card_frame, bg="#3d3d3d")
        controls_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        config_btn = tk.Button(controls_frame, text="Configure",
                              command=self._start_selection,
                              font=("Segoe UI", 9), bg=self.color, fg="white",
                              relief=tk.FLAT, padx=12, pady=4)
        config_btn.pack(side=tk.LEFT)
        
        if self.selector.is_setup():
            clear_btn = tk.Button(controls_frame, text="Clear",
                                 command=self._clear_selection,
                                 font=("Segoe UI", 9), bg="#6c757d", fg="white",
                                 relief=tk.FLAT, padx=12, pady=4)
            clear_btn.pack(side=tk.LEFT, padx=(8, 0))
    
    def _start_selection(self):
        if self.main_app and hasattr(self.main_app, 'start_area_selection'):
            self.main_app.start_area_selection(self.title, self.color, self.selector)
    
    def _clear_selection(self):
        try:
            self.selector.clear()
            self._update_status()
            self._update_preview()
            self.main_app.log(f"{self.title} area cleared")
            if self.main_app and hasattr(self.main_app, 'check_configuration'):
                self.main_app.check_configuration()
        except Exception as e:
            logger.error(f"Error clearing {self.title}: {e}")
    
    def _update_status(self):
        if self.selector.is_setup():
            self.status_dot.configure(fg="#28a745")
        else:
            self.status_dot.configure(fg="#dc3545")
    
    def _update_preview(self):
        try:
            if self.selector.is_setup() and hasattr(self.selector, 'preview_image') and self.selector.preview_image:
                preview_img = self.selector.preview_image
                
                display_size = (200, 60)
                preview_img = preview_img.resize(display_size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(preview_img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
            else:
                self.preview_label.configure(image="", text="No preview available")
                if hasattr(self.preview_label, 'image'):
                    delattr(self.preview_label, 'image')
        except Exception as e:
            logger.debug(f"Could not update preview for {self.title}: {e}")
            self.preview_label.configure(image="", text="Preview unavailable")
    
    def update_area_status(self):
        self._update_status()
        self._update_preview()
        self._recreate_controls()
    
    def _recreate_controls(self):
        for widget in self.card_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        widget.destroy()
                        self._create_controls()
                        return
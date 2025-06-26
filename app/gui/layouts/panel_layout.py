import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('PokeXHelper')

class PanelLayout:
    def __init__(self, main_app):
        self.main_app = main_app
        self.left_panel = None
        self.right_panel = None
        self.notebook = None
    
    def create_left_panel(self, parent):
        self.left_panel = tk.Frame(parent, bg="#2d2d2d", relief=tk.RIDGE, bd=1)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        config_frame = tk.Frame(self.notebook, bg="#2d2d2d")
        nav_frame = tk.Frame(self.notebook, bg="#2d2d2d")
        
        self.notebook.add(config_frame, text="Configuration")
        self.notebook.add(nav_frame, text="Navigation")
        
        return config_frame, nav_frame
    
    def create_right_panel(self, parent):
        self.right_panel = tk.Frame(parent, bg="#2d2d2d", relief=tk.RIDGE, bd=1, width=500)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self.right_panel.pack_propagate(False)
        
        controls_container = tk.Frame(self.right_panel, bg="#2d2d2d")
        controls_container.pack(fill=tk.X, padx=8, pady=8)
        
        log_container = tk.Frame(self.right_panel, bg="#2d2d2d")
        log_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        return controls_container, log_container
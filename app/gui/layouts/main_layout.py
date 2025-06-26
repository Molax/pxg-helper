import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('PokeXHelper')

class MainLayout:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.main_container = None
    
    def create_main_layout(self):
        self._setup_window()
        self._create_main_container()
        return self.main_container
    
    def _setup_window(self):
        self.root.title("PokeXGames Helper v1.0")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a1a")
        self.root.protocol("WM_DELETE_WINDOW", self.main_app.on_closing)
    
    def _create_main_container(self):
        self.main_container = tk.Frame(self.root, bg="#1a1a1a")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        return self.main_container
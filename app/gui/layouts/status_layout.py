import tkinter as tk
import logging

logger = logging.getLogger('PokeXHelper')

class StatusLayout:
    def __init__(self, main_app):
        self.main_app = main_app
        self.status_frame = None
        self.status_indicator = None
        self.status_text = None
    
    def create_status_bar(self, parent):
        self.status_frame = tk.Frame(parent, bg="#1a1a1a", height=30)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        self.status_frame.pack_propagate(False)
        
        status_content = tk.Frame(self.status_frame, bg="#1a1a1a")
        status_content.pack(side=tk.LEFT, padx=8, pady=5)
        
        status_label = tk.Label(status_content, text="Status:", 
                               font=("Segoe UI", 10), bg="#1a1a1a", fg="#b3b3b3")
        status_label.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Label(status_content, text="●", 
                                       font=("Segoe UI", 16), bg="#1a1a1a", fg="#28a745")
        self.status_indicator.pack(side=tk.LEFT, padx=(5, 0))
        
        self.status_text = tk.Label(status_content, text="Ready", 
                                   font=("Segoe UI", 10, "bold"), bg="#1a1a1a", fg="#28a745")
        self.status_text.pack(side=tk.LEFT, padx=(5, 0))
        
        return self.status_frame
    
    def update_status(self, text, color="#28a745"):
        if self.status_indicator and self.status_text:
            self.status_indicator.configure(fg=color)
            self.status_text.configure(text=text, fg=color)
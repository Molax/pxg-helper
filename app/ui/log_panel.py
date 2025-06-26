import tkinter as tk
from tkinter import ttk, scrolledtext
import time

class LogPanel:
    def __init__(self, parent):
        self.parent = parent
        self._create_ui()
    
    def _create_ui(self):
        log_frame = tk.Frame(self.parent, bg="#2d2d2d")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        title_label = tk.Label(log_frame, text="Activity Log", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=8)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff",
            selectbackground="#ff6b35", selectforeground="#ffffff",
            relief=tk.FLAT, borderwidth=0, font=("Consolas", 9), wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.add_log("PokeXGames Helper initialized")
    
    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
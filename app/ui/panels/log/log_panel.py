import tkinter as tk
from tkinter import scrolledtext
import time
from ...base.panel_base import PanelBase

class LogPanel(PanelBase):
    def __init__(self, parent):
        self.log_text = None
        self.max_entries = 1000
        self.entry_count = 0
        super().__init__(parent, None)
    
    def _create_ui(self):
        self.main_frame.configure(padx=12, pady=12)
        
        title_label = self._create_title_label(self.main_frame, "Activity Log")
        title_label.pack(anchor=tk.W, pady=8)
        
        self._create_log_area()
        self._create_controls()
        
        self.add_log("PokeXGames Helper initialized")
    
    def _create_log_area(self):
        self.log_text = scrolledtext.ScrolledText(
            self.main_frame, bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff",
            selectbackground="#ff6b35", selectforeground="#ffffff",
            relief=tk.FLAT, borderwidth=0, font=("Consolas", 9), wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_controls(self):
        controls_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        controls_frame.pack(fill=tk.X, pady=(8, 0))
        
        clear_btn = self._create_button(controls_frame, "Clear Log", 
                                       self.clear_log, bg="#6c757d")
        clear_btn.pack(side=tk.RIGHT)
    
    def add_log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        if self.log_text:
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            
            self.entry_count += 1
            if self.entry_count > self.max_entries:
                self._trim_logs()
    
    def _trim_logs(self):
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > self.max_entries:
            trimmed_lines = lines[-self.max_entries:]
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", '\n'.join(trimmed_lines))
            self.entry_count = self.max_entries
    
    def clear_log(self):
        if self.log_text:
            self.log_text.delete(1.0, tk.END)
            self.entry_count = 0
            self.add_log("Log cleared")
    
    def add_log_entry(self, message, level="INFO"):
        self.add_log(message, level)
    
    def clear_logs(self):
        self.clear_log()
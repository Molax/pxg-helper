import tkinter as tk
import logging
import abc

logger = logging.getLogger('PokeXHelper')

class PanelBase(abc.ABC):
    def __init__(self, parent, main_app=None):
        self.parent = parent
        self.main_app = main_app
        self.logger = logging.getLogger('PokeXHelper')
        self.widgets = {}
        
        self._create_main_frame()
        self._create_ui()
    
    def _create_main_frame(self):
        self.main_frame = tk.Frame(self.parent, bg="#2d2d2d")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    @abc.abstractmethod
    def _create_ui(self):
        pass
    
    def _create_section_frame(self, parent, title=None, bg="#2d2d2d"):
        if title:
            frame = tk.LabelFrame(parent, text=title, 
                                 font=("Segoe UI", 10, "bold"),
                                 bg=bg, fg="#ffffff", bd=2, relief=tk.RIDGE)
        else:
            frame = tk.Frame(parent, bg=bg)
        return frame
    
    def _create_title_label(self, parent, text, font_size=14):
        return tk.Label(parent, text=text, 
                       font=("Segoe UI", font_size, "bold"), 
                       bg="#2d2d2d", fg="#ffffff")
    
    def _create_button(self, parent, text, command, bg="#007acc", fg="white", **kwargs):
        return tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", 9), bg=bg, fg=fg,
                        relief=tk.FLAT, padx=12, pady=4, **kwargs)
    
    def _create_status_label(self, parent, text="Not configured", color="#ffc107"):
        return tk.Label(parent, text=text, 
                       font=("Segoe UI", 10), 
                       bg="#2d2d2d", fg=color)
    
    def log(self, message):
        if self.main_app and hasattr(self.main_app, 'log'):
            self.main_app.log(message)
        else:
            self.logger.info(message)
    
    def update_status(self, text, color="#28a745"):
        if self.main_app and hasattr(self.main_app, 'update_status'):
            self.main_app.update_status(text, color)
    
    def show(self):
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        self.main_frame.pack_forget()
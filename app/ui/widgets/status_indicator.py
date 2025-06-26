import tkinter as tk

class StatusIndicator:
    def __init__(self, parent, text="Ready", color="#28a745"):
        self.parent = parent
        self.current_text = text
        self.current_color = color
        
        self._create_widget()
    
    def _create_widget(self):
        self.frame = tk.Frame(self.parent, bg="#2d2d2d")
        
        self.indicator_dot = tk.Label(self.frame, text="●", 
                                     font=("Segoe UI", 12), 
                                     bg="#2d2d2d", fg=self.current_color)
        self.indicator_dot.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(self.frame, text=self.current_text,
                                    font=("Segoe UI", 10), 
                                    bg="#2d2d2d", fg=self.current_color)
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
    
    def update_status(self, text, color="#28a745"):
        self.current_text = text
        self.current_color = color
        self.indicator_dot.configure(fg=color)
        self.status_label.configure(text=text, fg=color)
    
    def set_ready(self):
        self.update_status("Ready", "#28a745")
    
    def set_running(self):
        self.update_status("Running", "#28a745")
    
    def set_error(self, message="Error"):
        self.update_status(message, "#dc3545")
    
    def set_warning(self, message="Warning"):
        self.update_status(message, "#ff9800")
    
    def set_configuring(self, message="Configuring"):
        self.update_status(message, "#ffc107")
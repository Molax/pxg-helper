import tkinter as tk
from ...base.panel_base import PanelBase

class HelperControls(PanelBase):
    def __init__(self, parent, main_app):
        self.start_button = None
        self.stop_button = None
        super().__init__(parent, main_app)
    
    def _create_ui(self):
        self.main_frame.configure(pady=12)
        
        title_label = self._create_title_label(self.main_frame, "Helper Controls", 12)
        title_label.pack(pady=(0, 12))
        
        self._create_control_buttons()
    
    def _create_control_buttons(self):
        buttons_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        buttons_frame.pack(fill=tk.X, padx=12)
        
        self.start_button = tk.Button(buttons_frame, text="START HELPER",
                                     command=self._start_helper,
                                     font=("Segoe UI", 12, "bold"), 
                                     bg="#28a745", fg="white",
                                     relief=tk.FLAT, padx=20, pady=10,
                                     state=tk.DISABLED)
        self.start_button.pack(fill=tk.X, pady=(0, 8))
        
        self.stop_button = tk.Button(buttons_frame, text="STOP HELPER",
                                    command=self._stop_helper,
                                    font=("Segoe UI", 12, "bold"), 
                                    bg="#dc3545", fg="white",
                                    relief=tk.FLAT, padx=20, pady=10,
                                    state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X)
    
    def _start_helper(self):
        if self.main_app and hasattr(self.main_app, 'start_helper'):
            self.main_app.start_helper()
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
    
    def _stop_helper(self):
        if self.main_app and hasattr(self.main_app, 'stop_helper'):
            self.main_app.stop_helper()
            self.start_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)
    
    def enable_start_button(self):
        if self.start_button:
            self.start_button.configure(state=tk.NORMAL)
    
    def disable_start_button(self):
        if self.start_button:
            self.start_button.configure(state=tk.DISABLED)
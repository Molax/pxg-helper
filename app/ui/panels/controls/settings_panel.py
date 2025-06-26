import tkinter as tk
from tkinter import ttk
from ...base.config_panel_base import ConfigPanelBase

class SettingsPanel(ConfigPanelBase):
    def __init__(self, parent, main_app):
        super().__init__(parent, main_app)
        self._initialize_variables()
    
    def _initialize_variables(self):
        self._auto_heal_var = tk.BooleanVar(value=True)
        self._health_threshold_var = tk.IntVar(value=30)
        self._heal_key_var = tk.StringVar(value="F1")
        self._auto_nav_var = tk.BooleanVar(value=False)
    
    def _create_ui(self):
        auto_frame = self._create_section_frame(self.main_frame, "Auto Settings")
        auto_frame.pack(fill=tk.X, padx=12, pady=12)
        
        self._create_heal_settings(auto_frame)
        self._create_navigation_settings(auto_frame)
    
    def _create_heal_settings(self, parent):
        heal_frame = tk.Frame(parent, bg="#2d2d2d")
        heal_frame.pack(fill=tk.X, padx=8, pady=8)
        
        auto_heal_check = self._create_checkbox(heal_frame, "Auto Heal", self._auto_heal_var)
        auto_heal_check.pack(side=tk.LEFT)
        
        threshold_frame = tk.Frame(heal_frame, bg="#2d2d2d")
        threshold_frame.pack(side=tk.RIGHT)
        
        tk.Label(threshold_frame, text="Health %:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 4))
        
        threshold_spin = self._create_spinbox(threshold_frame, from_=10, to=90, 
                                             textvariable=self._health_threshold_var)
        threshold_spin.pack(side=tk.LEFT)
        
        key_frame = tk.Frame(parent, bg="#2d2d2d")
        key_frame.pack(fill=tk.X, padx=8, pady=4)
        
        tk.Label(key_frame, text="Heal Key:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        heal_key_combo = self._create_combobox(key_frame, self._heal_key_var,
                                              ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"])
        heal_key_combo.pack(side=tk.RIGHT)
    
    def _create_navigation_settings(self, parent):
        nav_frame = tk.Frame(parent, bg="#2d2d2d")
        nav_frame.pack(fill=tk.X, padx=8, pady=4)
        
        auto_nav_check = self._create_checkbox(nav_frame, "Auto Navigate", self._auto_nav_var)
        auto_nav_check.pack(side=tk.LEFT)
    
    def get_settings(self):
        return {
            'auto_heal': self._auto_heal_var.get(),
            'health_threshold': self._health_threshold_var.get(),
            'heal_key': self._heal_key_var.get(),
            'auto_nav': self._auto_nav_var.get()
        }
    
    def load_settings(self, settings):
        self._auto_heal_var.set(settings.get('auto_heal', True))
        self._health_threshold_var.set(settings.get('health_threshold', 30))
        self._heal_key_var.set(settings.get('heal_key', 'F1'))
        self._auto_nav_var.set(settings.get('auto_nav', False))
import tkinter as tk
from .panel_base import PanelBase

class ConfigPanelBase(PanelBase):
    def __init__(self, parent, main_app=None):
        self.settings = {}
        super().__init__(parent, main_app)
    
    def load_settings_from_config(self, config):
        for setting_name, setting_value in config.items():
            if hasattr(self, f'_{setting_name}_var'):
                var = getattr(self, f'_{setting_name}_var')
                try:
                    if isinstance(var, tk.BooleanVar):
                        var.set(bool(setting_value))
                    elif isinstance(var, tk.IntVar):
                        var.set(int(setting_value))
                    elif isinstance(var, tk.StringVar):
                        var.set(str(setting_value))
                except Exception as e:
                    self.logger.error(f"Error loading setting {setting_name}: {e}")
    
    def save_settings_to_config(self, config):
        for attr_name in dir(self):
            if attr_name.endswith('_var') and attr_name.startswith('_'):
                setting_name = attr_name[1:-4]
                try:
                    var = getattr(self, attr_name)
                    config[setting_name] = var.get()
                except Exception as e:
                    self.logger.error(f"Error saving setting {setting_name}: {e}")
    
    def _create_checkbox(self, parent, text, variable, **kwargs):
        return tk.Checkbutton(parent, text=text, variable=variable,
                             bg="#2d2d2d", fg="#ffffff",
                             selectcolor="#1a1a1a", activebackground="#2d2d2d",
                             activeforeground="#ffffff", font=("Segoe UI", 9),
                             **kwargs)
    
    def _create_spinbox(self, parent, from_=0, to=100, textvariable=None, **kwargs):
        return tk.Spinbox(parent, from_=from_, to=to, width=5,
                         textvariable=textvariable, font=("Segoe UI", 8),
                         **kwargs)
    
    def _create_combobox(self, parent, textvariable, values, **kwargs):
        from tkinter import ttk
        return ttk.Combobox(parent, textvariable=textvariable,
                           values=values, width=8, font=("Segoe UI", 9),
                           state="readonly", **kwargs)
import tkinter as tk
from ...base.panel_base import PanelBase
from .helper_controls import HelperControls
from .settings_panel import SettingsPanel

class ControlsPanel(PanelBase):
    def __init__(self, parent, health_detector, main_app):
        self.health_detector = health_detector
        self.helper_controls = None
        self.settings_panel = None
        
        super().__init__(parent, main_app)
    
    def _create_ui(self):
        title_label = self._create_title_label(self.main_frame, "Helper Controls")
        title_label.pack(pady=12)
        
        self._create_settings_section()
        self._create_controls_section()
    
    def _create_settings_section(self):
        self.settings_panel = SettingsPanel(self.main_frame, self.main_app)
    
    def _create_controls_section(self):
        self.helper_controls = HelperControls(self.main_frame, self.main_app)
    
    def enable_start_button(self):
        if self.helper_controls:
            self.helper_controls.enable_start_button()
    
    def disable_start_button(self):
        if self.helper_controls:
            self.helper_controls.disable_start_button()
    
    def load_settings_from_config(self, config):
        if self.settings_panel:
            helper_settings = config.get("helper_settings", {})
            self.settings_panel.load_settings(helper_settings)
    
    def save_settings_to_config(self, config):
        if self.settings_panel:
            if "helper_settings" not in config:
                config["helper_settings"] = {}
            config["helper_settings"].update(self.settings_panel.get_settings())
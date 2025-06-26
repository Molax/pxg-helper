import tkinter as tk
from ...base.panel_base import PanelBase
from ...widgets.area_selector import AreaSelectorWidget
from ...widgets.status_indicator import StatusIndicator

class AreaConfigPanel(PanelBase):
    def __init__(self, parent, health_selector, minimap_selector, battle_area_selector, main_app):
        self.health_selector = health_selector
        self.minimap_selector = minimap_selector
        self.battle_area_selector = battle_area_selector
        
        self.area_widgets = {}
        self.config_status = None
        
        super().__init__(parent, main_app)
        self._update_all_areas()
    
    def _create_ui(self):
        self.main_frame.configure(padx=12, pady=12)
        
        title_label = self._create_title_label(self.main_frame, "Area Configuration")
        title_label.pack(anchor=tk.W, pady=12)
        
        self._create_area_widgets()
        self._create_status_section()
        self._create_info_section()
    
    def _create_area_widgets(self):
        areas_config = [
            ("Health Bar", "#dc3545", self.health_selector),
            ("Minimap Area", "#17a2b8", self.minimap_selector),
            ("Battle Area", "#9c27b0", self.battle_area_selector)
        ]
        
        for name, color, selector in areas_config:
            area_widget = AreaSelectorWidget(self.main_frame, name, color, selector, self.main_app)
            self.area_widgets[name] = area_widget
    
    def _create_status_section(self):
        status_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        status_frame.pack(pady=12)
        
        self.config_status = StatusIndicator(status_frame, "Configure areas to continue", "#ffc107")
        self.config_status.pack()
    
    def _create_info_section(self):
        info_frame = self._create_section_frame(self.main_frame, "Area Information")
        info_frame.pack(fill=tk.X, pady=(12, 0))
        
        info_text = (
            "Configure screen areas for the helper to monitor:\n\n"
            "• Health Bar: Area containing Pokemon health information\n"
            "• Minimap Area: Game minimap for navigation\n"
            "• Battle Area: Combat interface area"
        )
        
        info_label = tk.Label(info_frame, text=info_text, 
                             font=("Segoe UI", 9), bg="#2d2d2d", fg="#cccccc",
                             justify=tk.LEFT, wraplength=400)
        info_label.pack(padx=12, pady=12)
    
    def _update_all_areas(self):
        for area_widget in self.area_widgets.values():
            area_widget.update_area_status()
    
    def update_area_status(self, selector):
        for name, area_widget in self.area_widgets.items():
            if area_widget.selector == selector:
                area_widget.update_area_status()
                break
    
    def refresh_all_previews(self):
        for area_widget in self.area_widgets.values():
            area_widget._update_preview()
    
    def set_config_status(self, text, color="#28a745"):
        if self.config_status:
            self.config_status.update_status(text, color)
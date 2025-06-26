from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum

class ConfigSection(Enum):
    AREAS = "areas"
    HELPER_SETTINGS = "helper_settings"
    NAVIGATION = "navigation_steps"
    COORDINATE_AREA = "coordinate_area"
    UI_SETTINGS = "ui_settings"
    ADVANCED = "advanced_settings"

@dataclass
class AreaConfig:
    name: str
    x1: Optional[int] = None
    y1: Optional[int] = None
    x2: Optional[int] = None
    y2: Optional[int] = None
    configured: bool = False
    
    def is_valid(self) -> bool:
        if not self.configured:
            return True
        return all([
            self.x1 is not None,
            self.y1 is not None,
            self.x2 is not None,
            self.y2 is not None,
            self.x1 < self.x2,
            self.y1 < self.y2,
            self.x1 >= 0,
            self.y1 >= 0
        ])

@dataclass
class HelperSettings:
    auto_heal: bool = True
    auto_navigation: bool = False
    battle_detection_enabled: bool = True
    auto_battle: bool = False
    step_timeout: float = 30.0
    coordinate_validation: bool = True
    image_matching_threshold: float = 0.8
    navigation_check_interval: float = 0.5

@dataclass
class UISettings:
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 9
    window_geometry: Optional[str] = None
    panel_states: Dict[str, bool] = field(default_factory=lambda: {
        "controls_expanded": True,
        "areas_expanded": True,
        "navigation_expanded": True,
        "log_expanded": True
    })
    log_level: str = "INFO"
    auto_save_enabled: bool = True

@dataclass
class AdvancedSettings:
    debug_enabled: bool = True
    health_healing_key: str = "F1"
    health_threshold: int = 60
    scan_interval: float = 0.5
    max_log_lines: int = 1000
    auto_save_interval: float = 30.0
    backup_configs: bool = True
    max_backups: int = 5
    detection_sensitivity: float = 0.8
    performance_mode: bool = False

@dataclass
class NavigationStep:
    id: str
    name: str
    x: int
    y: int
    icon_path: Optional[str] = None
    delay: float = 1.0
    enabled: bool = True
    step_id: Optional[int] = None
    icon_image_path: Optional[str] = None

class ConfigSchema:
    def __init__(self):
        self.areas_schema = {
            "health_bar": AreaConfig("Health Bar"),
            "minimap": AreaConfig("Minimap"),
            "battle_area": AreaConfig("Battle Area")
        }
        self.helper_settings = HelperSettings()
        self.ui_settings = UISettings()
        self.advanced_settings = AdvancedSettings()
        self.navigation_steps: List[NavigationStep] = []
        self.coordinate_area = AreaConfig("Coordinate Display Area")
        self.version = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "areas": {k: asdict(v) for k, v in self.areas_schema.items()},
            "helper_settings": asdict(self.helper_settings),
            "ui_settings": asdict(self.ui_settings),
            "advanced_settings": asdict(self.advanced_settings),
            "navigation_steps": [asdict(step) for step in self.navigation_steps],
            "coordinate_area": asdict(self.coordinate_area)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigSchema':
        schema = cls()
        schema.version = data.get("version", "1.0")
        
        areas_data = data.get("areas", {})
        for area_name in schema.areas_schema.keys():
            if area_name in areas_data:
                area_data = areas_data[area_name].copy()
                
                valid_keys = {field.name for field in AreaConfig.__dataclass_fields__.values()}
                invalid_keys = [key for key in area_data.keys() if key not in valid_keys]
                
                for key in invalid_keys:
                    del area_data[key]
                
                # Handle missing required fields
                if "name" not in area_data:
                    area_data["name"] = area_name.replace("_", " ").title()
                
                schema.areas_schema[area_name] = AreaConfig(**area_data)
        
        if "helper_settings" in data:
            helper_data = data["helper_settings"].copy()
            
            valid_keys = {field.name for field in HelperSettings.__dataclass_fields__.values()}
            invalid_keys = [key for key in helper_data.keys() if key not in valid_keys]
            
            for key in invalid_keys:
                del helper_data[key]
            
            schema.helper_settings = HelperSettings(**helper_data)
        
        if "ui_settings" in data:
            ui_data = data["ui_settings"].copy()
            if "panel_states" not in ui_data:
                ui_data["panel_states"] = schema.ui_settings.panel_states
            
            valid_keys = {field.name for field in UISettings.__dataclass_fields__.values()}
            invalid_keys = [key for key in ui_data.keys() if key not in valid_keys]
            
            for key in invalid_keys:
                del ui_data[key]
            
            schema.ui_settings = UISettings(**ui_data)
        
        if "advanced_settings" in data:
            advanced_data = data["advanced_settings"].copy()
            
            valid_keys = {field.name for field in AdvancedSettings.__dataclass_fields__.values()}
            invalid_keys = [key for key in advanced_data.keys() if key not in valid_keys]
            
            for key in invalid_keys:
                del advanced_data[key]
            
            schema.advanced_settings = AdvancedSettings(**advanced_data)
        
        if "coordinate_area" in data:
            coord_data = data["coordinate_area"].copy()
            
            valid_keys = {field.name for field in AreaConfig.__dataclass_fields__.values()}
            invalid_keys = [key for key in coord_data.keys() if key not in valid_keys]
            
            for key in invalid_keys:
                del coord_data[key]
            
            schema.coordinate_area = AreaConfig(**coord_data)
        
        if "navigation_steps" in data:
            navigation_steps = []
            valid_keys = {field.name for field in NavigationStep.__dataclass_fields__.values()}
            
            for step_data in data["navigation_steps"]:
                if isinstance(step_data, dict):
                    clean_step_data = step_data.copy()
                    invalid_keys = [key for key in clean_step_data.keys() if key not in valid_keys]
                    
                    for key in invalid_keys:
                        del clean_step_data[key]
                    
                    # Handle missing required fields
                    if "id" not in clean_step_data:
                        clean_step_data["id"] = str(len(navigation_steps) + 1)
                    if "name" not in clean_step_data:
                        clean_step_data["name"] = f"Step {len(navigation_steps) + 1}"
                    if "x" not in clean_step_data:
                        clean_step_data["x"] = 0
                    if "y" not in clean_step_data:
                        clean_step_data["y"] = 0
                    
                    navigation_steps.append(NavigationStep(**clean_step_data))
            
            schema.navigation_steps = navigation_steps
        
        return schema
import logging
import json
import os

logger = logging.getLogger('PokeXHelper')

def load_config():
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    return {}

def save_config(config):
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

class ConfigManager:
    def __init__(self, main_app):
        self.main_app = main_app
    
    def load_configuration(self):
        try:
            config = load_config()
            self._load_areas_config(config)
            self._load_coordinate_area_config(config)
            self._load_navigation_config(config)
            self._load_helper_settings(config)
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.main_app.log("Error loading configuration - using defaults")
    
    def _load_areas_config(self, config):
        areas = config.get("areas", {})
        areas_loaded = 0
        
        area_selectors = {
            "health_bar": self.main_app.health_bar_selector,
            "minimap": self.main_app.minimap_selector,
            "battle_area": self.main_app.battle_area_selector
        }
        
        for area_name, selector in area_selectors.items():
            if area_name in areas:
                area_config = areas[area_name]
                if area_config.get("configured", False):
                    x1, y1, x2, y2 = area_config.get("x1"), area_config.get("y1"), area_config.get("x2"), area_config.get("y2")
                    
                    if all(coord is not None for coord in [x1, y1, x2, y2]):
                        if selector.configure_from_coordinates(x1, y1, x2, y2):
                            areas_loaded += 1
                            self.main_app.log(f"Loaded {area_name}: ({x1},{y1}) to ({x2},{y2})")
                            
                            try:
                                from PIL import ImageGrab
                                preview_img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
                                selector.preview_image = preview_img
                            except Exception as e:
                                logger.warning(f"Could not create preview for {area_name}: {e}")
                            
                            if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'area_config_panel'):
                                self.main_app.interface_manager.area_config_panel.update_area_status(selector)
                        else:
                            logger.warning(f"Failed to configure {area_name} from saved data")
                    else:
                        logger.warning(f"Invalid coordinates for {area_name}: {area_config}")
                else:
                    logger.debug(f"Area {area_name} not configured in saved data")
        
        if areas_loaded > 0:
            self.main_app.log(f"Configuration loaded: {areas_loaded}/3 areas restored")
        else:
            self.main_app.log("No saved areas found - using default configuration")
    
    def _load_coordinate_area_config(self, config):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel')):
                navigation_panel = self.main_app.interface_manager.navigation_panel
                if hasattr(navigation_panel, 'load_coordinate_area_config'):
                    navigation_panel.load_coordinate_area_config()
        except Exception as e:
            logger.debug(f"Could not load coordinate area config: {e}")
    
    def _load_navigation_config(self, config):
        navigation_steps = config.get("navigation_steps", [])
        if navigation_steps:
            self.main_app.navigation_manager.load_steps_data(navigation_steps)
            if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'navigation_panel'):
                self.main_app.interface_manager.navigation_panel.refresh_steps_display()
                self.main_app.interface_manager.navigation_panel.check_navigation_ready()
            self.main_app.log(f"Loaded {len(navigation_steps)} navigation steps")
    
    def _load_helper_settings(self, config):
        if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'controls_panel'):
            self.main_app.interface_manager.controls_panel.load_settings_from_config(config)
    
    def save_configuration(self):
        try:
            config = load_config()
            
            if "areas" not in config:
                config["areas"] = {}
            
            areas_saved = 0
            area_selectors = {
                "health_bar": self.main_app.health_bar_selector,
                "minimap": self.main_app.minimap_selector,
                "battle_area": self.main_app.battle_area_selector
            }
            
            for area_name, selector in area_selectors.items():
                if selector.is_setup():
                    config["areas"][area_name] = {
                        "name": area_name.replace("_", " ").title(),
                        "x1": selector.x1,
                        "y1": selector.y1,
                        "x2": selector.x2,
                        "y2": selector.y2,
                        "configured": True
                    }
                    areas_saved += 1
                    logger.info(f"Saving {area_name}: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
                else:
                    if area_name not in config["areas"]:
                        config["areas"][area_name] = {}
                    config["areas"][area_name]["configured"] = False
                    logger.debug(f"Area {area_name} not configured, marked as unconfigured")
            
            self._save_coordinate_area(config)
            self._save_other_settings(config)
            
            save_config(config)
            logger.info(f"Configuration saved successfully - {areas_saved}/3 areas saved")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise
    
    def _save_coordinate_area(self, config):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel') and
                hasattr(self.main_app.interface_manager.navigation_panel, 'coordinate_area')):
                
                coord_area = self.main_app.interface_manager.navigation_panel.coordinate_area
                if coord_area and coord_area.is_setup():
                    config["coordinate_area"] = {
                        "name": "Coordinate Display Area",
                        "x1": coord_area.x1,
                        "y1": coord_area.y1,
                        "x2": coord_area.x2,
                        "y2": coord_area.y2,
                        "configured": True
                    }
                    logger.info(f"Saving coordinate area: ({coord_area.x1},{coord_area.y1}) to ({coord_area.x2},{coord_area.y2})")
                else:
                    if "coordinate_area" not in config:
                        config["coordinate_area"] = {}
                    config["coordinate_area"]["configured"] = False
        except Exception as e:
            logger.debug(f"Could not save coordinate area: {e}")
    
    def _save_other_settings(self, config):
        if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'controls_panel'):
            self.main_app.interface_manager.controls_panel.save_settings_to_config(config)
        config["navigation_steps"] = self.main_app.navigation_manager.get_steps_data()
    
    def save_on_exit(self):
        try:
            self.save_configuration()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
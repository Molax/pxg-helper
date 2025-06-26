import logging
from PIL import ImageGrab

logger = logging.getLogger('PokeXHelper')

class ConfigManager:
    def __init__(self, main_app):
        self.main_app = main_app
    
    def load_configuration(self):
        try:
            from app.config import load_config
            config = load_config()
            
            self._load_areas_config(config)
            self._load_coordinate_area_config(config)
            self._load_navigation_config(config)
            self._load_helper_settings(config)
            
            self.main_app.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.main_app.log("Error loading configuration - using defaults")
    
    def _load_areas_config(self, config):
        """Load main area configurations (health bar, minimap, battle area)"""
        areas_config = config.get("areas", {})
        areas_loaded = 0
        
        for area_name, selector in [
            ("health_bar", self.main_app.health_bar_selector),
            ("minimap", self.main_app.minimap_selector),
            ("battle_area", self.main_app.battle_area_selector)
        ]:
            area_config = areas_config.get(area_name, {})
            if area_config.get("configured", False):
                x1 = area_config.get("x1")
                y1 = area_config.get("y1")
                x2 = area_config.get("x2")
                y2 = area_config.get("y2")
                
                if all([x1 is not None, y1 is not None, x2 is not None, y2 is not None]):
                    if selector.configure_from_saved(x1, y1, x2, y2):
                        selector.title = area_config.get("name", area_name.replace("_", " ").title())
                        areas_loaded += 1
                        self.main_app.log(f"Loaded {area_name}: ({x1},{y1}) to ({x2},{y2})")
                        
                        try:
                            selector.preview_image = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
                        except Exception as e:
                            logger.warning(f"Could not create preview for {area_name}: {e}")
                        
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
        """Load coordinate area configuration"""
        try:
            # Try to load coordinate area config after navigation panel is created
            if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'navigation_panel'):
                navigation_panel = self.main_app.interface_manager.navigation_panel
                if hasattr(navigation_panel, 'load_coordinate_area_config'):
                    navigation_panel.load_coordinate_area_config()
        except Exception as e:
            logger.debug(f"Could not load coordinate area config: {e}")
    
    def _load_navigation_config(self, config):
        """Load navigation steps configuration"""
        navigation_steps = config.get("navigation_steps", [])
        if navigation_steps:
            self.main_app.navigation_manager.load_steps_data(navigation_steps)
            self.main_app.interface_manager.navigation_panel.refresh_steps_display()
            self.main_app.interface_manager.navigation_panel.check_navigation_ready()
            self.main_app.log(f"Loaded {len(navigation_steps)} navigation steps")
    
    def _load_helper_settings(self, config):
        """Load helper settings"""
        self.main_app.interface_manager.controls_panel.load_settings_from_config(config)
    
    def save_settings(self):
        try:
            self.main_app.log("Starting settings save...")
            
            try:
                self.main_app.navigation_manager.cleanup_unused_icons()
                self.main_app.log("Icon cleanup completed")
            except Exception as e:
                self.main_app.log(f"Icon cleanup failed: {e}")
            
            try:
                self.save_configuration()
                self.main_app.log("Settings saved successfully")
            except Exception as e:
                self.main_app.log(f"Configuration save failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in save_settings: {e}", exc_info=True)
            self.main_app.log(f"Error saving settings: {e}")
    
    def save_configuration(self):
        try:
            from app.config import load_config, save_config
            config = load_config()
            
            areas_saved = 0
            
            # Save main areas
            for area_name, selector in [
                ("health_bar", self.main_app.health_bar_selector),
                ("minimap", self.main_app.minimap_selector),
                ("battle_area", self.main_app.battle_area_selector)
            ]:
                if selector.is_setup():
                    config["areas"][area_name] = {
                        "name": getattr(selector, 'title', area_name.replace("_", " ").title()),
                        "x1": selector.x1,
                        "y1": selector.y1,
                        "x2": selector.x2,
                        "y2": selector.y2,
                        "configured": True
                    }
                    areas_saved += 1
                    logger.info(f"Saving {area_name}: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
                else:
                    config["areas"][area_name]["configured"] = False
                    logger.debug(f"Area {area_name} not configured, marked as unconfigured")
            
            # Save coordinate area if it exists
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
            
            # Save other settings
            self.main_app.interface_manager.controls_panel.save_settings_to_config(config)
            config["navigation_steps"] = self.main_app.navigation_manager.get_steps_data()
            
            save_config(config)
            logger.info(f"Configuration saved successfully - {areas_saved}/3 areas saved")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise
    
    def save_on_exit(self):
        try:
            if self.main_app.running:
                self.main_app.interface_manager.stop_helper()
            
            if self.main_app.navigation_manager.is_navigating:
                self.main_app.navigation_manager.stop_navigation()
            
            self.save_configuration()
            logger.info("Application closing gracefully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def _load_areas_config(self, config):
        """Load area configurations with proper preview updates"""
        areas_config = config.get("areas", {})
        areas_loaded = 0
        
        for area_name, selector in [
            ("health_bar", self.main_app.health_bar_selector),
            ("minimap", self.main_app.minimap_selector),
            ("battle_area", self.main_app.battle_area_selector)
        ]:
            area_config = areas_config.get(area_name, {})
            if area_config.get("configured", False):
                x1 = area_config.get("x1")
                y1 = area_config.get("y1") 
                x2 = area_config.get("x2")
                y2 = area_config.get("y2")
                
                if all([x1 is not None, y1 is not None, x2 is not None, y2 is not None]):
                    try:
                        if selector.configure_from_saved(x1, y1, x2, y2):
                            areas_loaded += 1
                            self.main_app.log(f"Loaded {area_name}: ({x1},{y1}) to ({x2},{y2})")
                            
                            # Force create preview image for loaded areas
                            try:
                                from PIL import ImageGrab
                                bbox = (selector.x1, selector.y1, selector.x2, selector.y2)
                                try:
                                    preview_img = ImageGrab.grab(bbox=bbox, all_screens=True)
                                except TypeError:
                                    preview_img = ImageGrab.grab(bbox=bbox)
                                selector.preview_image = preview_img
                                logger.debug(f"Created preview for loaded {area_name}")
                            except Exception as e:
                                logger.warning(f"Could not create preview for {area_name}: {e}")
                            
                            # Update area status in UI
                            try:
                                if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'area_config_panel'):
                                    self.main_app.interface_manager.area_config_panel.update_area_status(selector)
                            except Exception as e:
                                logger.debug(f"Could not update area status for {area_name}: {e}")
                        else:
                            logger.warning(f"Failed to configure {area_name} from saved data")
                    except Exception as e:
                        logger.error(f"Error configuring {area_name}: {e}")
                else:
                    logger.warning(f"Invalid coordinates for {area_name}: {area_config}")
            else:
                logger.debug(f"Area {area_name} not configured in saved data")
        
        if areas_loaded > 0:
            self.main_app.log(f"Configuration loaded: {areas_loaded}/3 areas restored")
            # Refresh all area previews after loading
            try:
                if hasattr(self.main_app, 'interface_manager') and hasattr(self.main_app.interface_manager, 'area_config_panel'):
                    # Small delay to ensure UI is ready
                    self.main_app.root.after(100, lambda: self.main_app.interface_manager.area_config_panel.refresh_all_previews())
            except Exception as e:
                logger.debug(f"Could not refresh previews: {e}")
        else:
            self.main_app.log("No saved areas found - using default configuration")
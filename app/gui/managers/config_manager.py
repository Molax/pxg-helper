import logging
from typing import Dict, Any, Optional
from PIL import ImageGrab

logger = logging.getLogger('PokeXHelper')

class ConfigManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self._config_core = None
        self._init_config_core()
    
    def _init_config_core(self):
        try:
            from app.config import ConfigManager as CoreConfigManager
            self._config_core = CoreConfigManager()
        except ImportError:
            logger.warning("New config system not available, using legacy system")
            self._config_core = None
    
    def load_configuration(self):
        try:
            if self._config_core:
                schema = self._config_core.load_config()
                self._load_from_schema(schema)
            else:
                self._load_legacy_config()
                
            self.main_app.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.main_app.log("Error loading configuration - using defaults")
    
    def _load_from_schema(self, schema):
        self._load_areas_config_from_schema(schema)
        self._load_coordinate_area_config_from_schema(schema)
        self._load_navigation_config_from_schema(schema)
        self._load_helper_settings_from_schema(schema)
    
    def _load_legacy_config(self):
        from app.config import load_config
        config = load_config()
        
        self._load_areas_config(config)
        self._load_coordinate_area_config(config)
        self._load_navigation_config(config)
        self._load_helper_settings(config)
    
    def _load_areas_config_from_schema(self, schema):
        areas_loaded = 0
        
        for area_name, selector in [
            ("health_bar", self.main_app.health_bar_selector),
            ("minimap", self.main_app.minimap_selector),
            ("battle_area", self.main_app.battle_area_selector)
        ]:
            area_config = schema.areas_schema.get(area_name)
            if area_config and area_config.configured and area_config.is_valid():
                try:
                    if selector.configure_from_saved(area_config.x1, area_config.y1, area_config.x2, area_config.y2):
                        selector.title = area_config.name
                        areas_loaded += 1
                        self.main_app.log(f"Loaded {area_name}: ({area_config.x1},{area_config.y1}) to ({area_config.x2},{area_config.y2})")
                        
                        try:
                            selector.preview_image = ImageGrab.grab(
                                bbox=(area_config.x1, area_config.y1, area_config.x2, area_config.y2), 
                                all_screens=True
                            )
                        except Exception as e:
                            logger.warning(f"Could not create preview for {area_name}: {e}")
                        
                        self._update_area_ui_status(selector)
                    else:
                        logger.warning(f"Failed to configure {area_name} from saved data")
                except Exception as e:
                    logger.error(f"Error configuring {area_name}: {e}")
        
        if areas_loaded > 0:
            self.main_app.log(f"Configuration loaded: {areas_loaded}/3 areas restored")
            self.main_app.root.after(100, self._refresh_area_previews)
        else:
            self.main_app.log("No saved areas found - using default configuration")
    
    def _load_areas_config(self, config):
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
                            selector.title = area_config.get("name", area_name.replace("_", " ").title())
                            areas_loaded += 1
                            self.main_app.log(f"Loaded {area_name}: ({x1},{y1}) to ({x2},{y2})")
                            
                            try:
                                selector.preview_image = ImageGrab.grab(
                                    bbox=(x1, y1, x2, y2), all_screens=True)
                            except Exception as e:
                                logger.warning(f"Could not create preview for {area_name}: {e}")
                            
                            self._update_area_ui_status(selector)
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
            self.main_app.root.after(100, self._refresh_area_previews)
        else:
            self.main_app.log("No saved areas found - using default configuration")
    
    def _update_area_ui_status(self, selector):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'area_config_panel')):
                self.main_app.interface_manager.area_config_panel.update_area_status(selector)
        except Exception as e:
            logger.debug(f"Could not update area UI status: {e}")
    
    def _refresh_area_previews(self):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'area_config_panel')):
                self.main_app.interface_manager.area_config_panel.refresh_all_previews()
        except Exception as e:
            logger.debug(f"Could not refresh previews: {e}")
    
    def _load_coordinate_area_config_from_schema(self, schema):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel')):
                navigation_panel = self.main_app.interface_manager.navigation_panel
                if hasattr(navigation_panel, 'load_coordinate_area_from_schema'):
                    navigation_panel.load_coordinate_area_from_schema(schema.coordinate_area)
                elif hasattr(navigation_panel, 'load_coordinate_area_config'):
                    navigation_panel.load_coordinate_area_config()
        except Exception as e:
            logger.debug(f"Could not load coordinate area config: {e}")
    
    def _load_coordinate_area_config(self, config):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel')):
                navigation_panel = self.main_app.interface_manager.navigation_panel
                if hasattr(navigation_panel, 'load_coordinate_area_config'):
                    navigation_panel.load_coordinate_area_config()
        except Exception as e:
            logger.debug(f"Could not load coordinate area config: {e}")
    
    def _load_navigation_config_from_schema(self, schema):
        if schema.navigation_steps:
            try:
                steps_data = [step.__dict__ for step in schema.navigation_steps]
                self.main_app.navigation_manager.load_steps_data(steps_data)
                if hasattr(self.main_app, 'interface_manager'):
                    self.main_app.interface_manager.navigation_panel.refresh_steps_display()
                    self.main_app.interface_manager.navigation_panel.check_navigation_ready()
                self.main_app.log(f"Loaded {len(schema.navigation_steps)} navigation steps")
            except Exception as e:
                logger.error(f"Error loading navigation config: {e}")
    
    def _load_navigation_config(self, config):
        navigation_steps = config.get("navigation_steps", [])
        if navigation_steps:
            try:
                self.main_app.navigation_manager.load_steps_data(navigation_steps)
                if hasattr(self.main_app, 'interface_manager'):
                    self.main_app.interface_manager.navigation_panel.refresh_steps_display()
                    self.main_app.interface_manager.navigation_panel.check_navigation_ready()
                self.main_app.log(f"Loaded {len(navigation_steps)} navigation steps")
            except Exception as e:
                logger.error(f"Error loading navigation config: {e}")
    
    def _load_helper_settings_from_schema(self, schema):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                controls_panel = self.main_app.interface_manager.controls_panel
                if hasattr(controls_panel, 'load_settings_from_schema'):
                    controls_panel.load_settings_from_schema(schema.helper_settings, schema.advanced_settings)
                elif hasattr(controls_panel, 'load_settings_from_config'):
                    legacy_config = self._schema_to_legacy_config(schema)
                    controls_panel.load_settings_from_config(legacy_config)
        except Exception as e:
            logger.debug(f"Could not load helper settings: {e}")
    
    def _load_helper_settings(self, config):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                self.main_app.interface_manager.controls_panel.load_settings_from_config(config)
        except Exception as e:
            logger.debug(f"Could not load helper settings: {e}")
    
    def _schema_to_legacy_config(self, schema):
        legacy_config = {
            "helper_settings": schema.helper_settings.__dict__,
            "debug_enabled": schema.advanced_settings.debug_enabled,
            "health_healing_key": schema.advanced_settings.health_healing_key,
            "health_threshold": schema.advanced_settings.health_threshold,
            "scan_interval": schema.advanced_settings.scan_interval
        }
        return legacy_config
    
    def save_settings(self):
        try:
            self.main_app.log("Starting settings save...")
            
            try:
                if hasattr(self.main_app, 'navigation_manager'):
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
            if self._config_core:
                self._save_to_schema()
            else:
                self._save_legacy_config()
                
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise
    
    def _save_to_schema(self):
        self._update_areas_in_schema()
        self._update_coordinate_area_in_schema()
        self._update_helper_settings_in_schema()
        self._update_navigation_in_schema()
        self._update_ui_settings_in_schema()
        
        self._config_core.save_config()
    
    def _save_legacy_config(self):
        from app.config import load_config, save_config
        config = load_config()
        
        areas_saved = 0
        
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
        
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                self.main_app.interface_manager.controls_panel.save_settings_to_config(config)
        except Exception as e:
            logger.debug(f"Could not save helper settings: {e}")
        
        if hasattr(self.main_app, 'navigation_manager'):
            config["navigation_steps"] = self.main_app.navigation_manager.get_steps_data()
        
        save_config(config)
        logger.info(f"Configuration saved successfully - {areas_saved}/3 areas saved")
    
    def _update_areas_in_schema(self):
        if not self._config_core:
            return
            
        from app.config import AreaConfig
        
        for area_name, selector in [
            ("health_bar", self.main_app.health_bar_selector),
            ("minimap", self.main_app.minimap_selector),
            ("battle_area", self.main_app.battle_area_selector)
        ]:
            if selector.is_setup():
                area_config = AreaConfig(
                    name=getattr(selector, 'title', area_name.replace("_", " ").title()),
                    x1=selector.x1,
                    y1=selector.y1,
                    x2=selector.x2,
                    y2=selector.y2,
                    configured=True
                )
                self._config_core.update_area(area_name, area_config)
                logger.info(f"Saving {area_name}: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
            else:
                area_config = AreaConfig(
                    name=area_name.replace("_", " ").title(),
                    configured=False
                )
                self._config_core.update_area(area_name, area_config)
                logger.debug(f"Area {area_name} not configured, marked as unconfigured")
    
    def _update_coordinate_area_in_schema(self):
        if not self._config_core:
            return
            
        from app.config import AreaConfig
        
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel') and
                hasattr(self.main_app.interface_manager.navigation_panel, 'coordinate_area')):
                
                coord_area = self.main_app.interface_manager.navigation_panel.coordinate_area
                if coord_area and coord_area.is_setup():
                    area_config = AreaConfig(
                        name="Coordinate Display Area",
                        x1=coord_area.x1,
                        y1=coord_area.y1,
                        x2=coord_area.x2,
                        y2=coord_area.y2,
                        configured=True
                    )
                    self._config_core.update_coordinate_area(area_config)
                    logger.info(f"Saving coordinate area: ({coord_area.x1},{coord_area.y1}) to ({coord_area.x2},{coord_area.y2})")
                else:
                    area_config = AreaConfig(name="Coordinate Display Area", configured=False)
                    self._config_core.update_coordinate_area(area_config)
        except Exception as e:
            logger.debug(f"Could not save coordinate area: {e}")
    
    def _update_helper_settings_in_schema(self):
        if not self._config_core:
            return
            
        from app.config import HelperSettings, AdvancedSettings
        
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                controls_panel = self.main_app.interface_manager.controls_panel
                
                if hasattr(controls_panel, 'get_settings_for_schema'):
                    helper_settings, advanced_settings = controls_panel.get_settings_for_schema()
                    self._config_core.update_helper_settings(helper_settings)
                    self._config_core.update_advanced_settings(advanced_settings)
                else:
                    helper_settings = HelperSettings()
                    advanced_settings = AdvancedSettings()
                    self._config_core.update_helper_settings(helper_settings)
                    self._config_core.update_advanced_settings(advanced_settings)
        except Exception as e:
            logger.debug(f"Could not save helper settings: {e}")
    
    def _update_navigation_in_schema(self):
        if not self._config_core:
            return
            
        from app.config import NavigationStep
        
        try:
            if hasattr(self.main_app, 'navigation_manager'):
                steps_data = self.main_app.navigation_manager.get_steps_data()
                navigation_steps = []
                for step in steps_data:
                    nav_step = NavigationStep(
                        id=step.get('id', ''),
                        name=step.get('name', ''),
                        x=step.get('x', 0),
                        y=step.get('y', 0),
                        icon_path=step.get('icon_path'),
                        delay=step.get('delay', 1.0),
                        enabled=step.get('enabled', True),
                        step_id=step.get('step_id'),
                        icon_image_path=step.get('icon_image_path')
                    )
                    navigation_steps.append(nav_step)
                self._config_core.update_navigation_steps(navigation_steps)
        except Exception as e:
            logger.debug(f"Could not save navigation steps: {e}")
    
    def _update_ui_settings_in_schema(self):
        if not self._config_core:
            return
            
        from app.config import UISettings
        
        try:
            ui_settings = UISettings()
            
            if hasattr(self.main_app, 'root'):
                ui_settings.window_geometry = self.main_app.root.geometry()
            
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'get_ui_settings')):
                ui_settings = self.main_app.interface_manager.get_ui_settings()
            
            self._config_core.update_ui_settings(ui_settings)
        except Exception as e:
            logger.debug(f"Could not save UI settings: {e}")
    
    def export_configuration(self, file_path: str) -> bool:
        if self._config_core:
            return self._config_core.export_config(file_path)
        return False
    
    def import_configuration(self, file_path: str) -> bool:
        if self._config_core:
            success = self._config_core.import_config(file_path)
            if success:
                self.load_configuration()
            return success
        return False
    
    def create_backup(self, reason: str = "manual") -> Optional[str]:
        if self._config_core:
            backup_path = self._config_core.backup_manager.create_backup(reason)
            return str(backup_path) if backup_path else None
        return None
    
    def get_validation_status(self) -> Dict[str, Any]:
        if self._config_core:
            errors, warnings = self._config_core.validator.validate_schema(self._config_core.schema)
            return {
                "is_valid": len(errors) == 0,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": [str(error) for error in errors],
                "warnings": [str(warning) for warning in warnings]
            }
        return {"is_valid": True, "error_count": 0, "warning_count": 0, "errors": [], "warnings": []}
import logging
from typing import Dict, Any, Optional
from PIL import ImageGrab
from app.config import ConfigManager as CoreConfigManager, AreaConfig, HelperSettings, AdvancedSettings, UISettings, NavigationStep

logger = logging.getLogger('PokeXHelper')

class ConfigManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.config_core = CoreConfigManager()
    
    def load_configuration(self):
        try:
            schema = self.config_core.load_config()
            self._load_from_schema(schema)
            self.main_app.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.main_app.log("Error loading configuration - using defaults")
    
    def _load_from_schema(self, schema):
        self._load_areas_config(schema)
        self._load_coordinate_area_config(schema)
        self._load_navigation_config(schema)
        self._load_helper_settings(schema)
        self._load_ui_settings(schema)
    
    def _load_areas_config(self, schema):
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
    
    def _load_coordinate_area_config(self, schema):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'navigation_panel')):
                navigation_panel = self.main_app.interface_manager.navigation_panel
                if hasattr(navigation_panel, 'load_coordinate_area_from_schema'):
                    navigation_panel.load_coordinate_area_from_schema(schema.coordinate_area)
        except Exception as e:
            logger.debug(f"Could not load coordinate area config: {e}")
    
    def _load_navigation_config(self, schema):
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
    
    def _load_helper_settings(self, schema):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                controls_panel = self.main_app.interface_manager.controls_panel
                if hasattr(controls_panel, 'load_settings_from_schema'):
                    controls_panel.load_settings_from_schema(schema.helper_settings, schema.advanced_settings)
        except Exception as e:
            logger.debug(f"Could not load helper settings: {e}")
    
    def _load_ui_settings(self, schema):
        try:
            ui_settings = schema.ui_settings
            if ui_settings.window_geometry and hasattr(self.main_app, 'root'):
                self.main_app.root.geometry(ui_settings.window_geometry)
            
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'apply_ui_settings')):
                self.main_app.interface_manager.apply_ui_settings(ui_settings)
        except Exception as e:
            logger.debug(f"Could not apply UI settings: {e}")
    
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
            self._update_areas_in_schema()
            self._update_coordinate_area_in_schema()
            self._update_helper_settings_in_schema()
            self._update_navigation_in_schema()
            self._update_ui_settings_in_schema()
            
            self.config_core.save_config()
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise
    
    def _update_areas_in_schema(self):
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
                self.config_core.update_area(area_name, area_config)
                logger.info(f"Saving {area_name}: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
            else:
                area_config = AreaConfig(
                    name=area_name.replace("_", " ").title(),
                    configured=False
                )
                self.config_core.update_area(area_name, area_config)
    
    def _update_coordinate_area_in_schema(self):
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
                    self.config_core.update_coordinate_area(area_config)
                    logger.info(f"Saving coordinate area: ({coord_area.x1},{coord_area.y1}) to ({coord_area.x2},{coord_area.y2})")
                else:
                    area_config = AreaConfig(name="Coordinate Display Area", configured=False)
                    self.config_core.update_coordinate_area(area_config)
        except Exception as e:
            logger.debug(f"Could not save coordinate area: {e}")
    
    def _update_helper_settings_in_schema(self):
        try:
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'controls_panel')):
                controls_panel = self.main_app.interface_manager.controls_panel
                
                if hasattr(controls_panel, 'get_settings_for_schema'):
                    helper_settings, advanced_settings = controls_panel.get_settings_for_schema()
                    self.config_core.update_helper_settings(helper_settings)
                    self.config_core.update_advanced_settings(advanced_settings)
                else:
                    helper_settings = HelperSettings()
                    advanced_settings = AdvancedSettings()
                    self.config_core.update_helper_settings(helper_settings)
                    self.config_core.update_advanced_settings(advanced_settings)
        except Exception as e:
            logger.debug(f"Could not save helper settings: {e}")
    
    def _update_navigation_in_schema(self):
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
                self.config_core.update_navigation_steps(navigation_steps)
        except Exception as e:
            logger.debug(f"Could not save navigation steps: {e}")
    
    def _update_ui_settings_in_schema(self):
        try:
            ui_settings = UISettings()
            
            if hasattr(self.main_app, 'root'):
                ui_settings.window_geometry = self.main_app.root.geometry()
            
            if (hasattr(self.main_app, 'interface_manager') and 
                hasattr(self.main_app.interface_manager, 'get_ui_settings')):
                ui_settings = self.main_app.interface_manager.get_ui_settings()
            
            self.config_core.update_ui_settings(ui_settings)
        except Exception as e:
            logger.debug(f"Could not save UI settings: {e}")
    
    def export_configuration(self, file_path: str) -> bool:
        return self.config_core.export_config(file_path)
    
    def import_configuration(self, file_path: str) -> bool:
        success = self.config_core.import_config(file_path)
        if success:
            self.load_configuration()
        return success
    
    def create_backup(self, reason: str = "manual") -> Optional[str]:
        backup_path = self.config_core.backup_manager.create_backup(reason)
        return str(backup_path) if backup_path else None
    
    def get_validation_status(self) -> Dict[str, Any]:
        errors, warnings = self.config_core.validator.validate_schema(self.config_core.schema)
        return {
            "is_valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [str(error) for error in errors],
            "warnings": [str(warning) for warning in warnings]
        }
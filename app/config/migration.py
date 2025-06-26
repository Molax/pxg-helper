from typing import Dict, Any, List, Callable
import logging
from .schemas import ConfigSchema, AreaConfig, HelperSettings, UISettings, AdvancedSettings, NavigationStep

logger = logging.getLogger('PokeXHelper')

class MigrationError(Exception):
    pass

class ConfigMigration:
    def __init__(self, from_version: str, to_version: str, migration_func: Callable):
        self.from_version = from_version
        self.to_version = to_version
        self.migration_func = migration_func
    
    def apply(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Applying migration from {self.from_version} to {self.to_version}")
        return self.migration_func(config_data)

class ConfigMigrator:
    def __init__(self):
        self.migrations: List[ConfigMigration] = []
        self._register_migrations()
    
    def _register_migrations(self):
        self.migrations = [
            ConfigMigration("1.0", "1.1", self._migrate_1_0_to_1_1),
            ConfigMigration("1.1", "2.0", self._migrate_1_1_to_2_0),
        ]
    
    def get_current_version(self, config_data: Dict[str, Any]) -> str:
        return config_data.get("version", "1.0")
    
    def needs_migration(self, config_data: Dict[str, Any]) -> bool:
        current_version = self.get_current_version(config_data)
        target_version = "2.0"
        return current_version != target_version
    
    def migrate(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        current_version = self.get_current_version(config_data)
        target_version = "2.0"
        
        if current_version == target_version:
            logger.debug("Configuration is already at target version")
            return config_data
        
        migrated_data = config_data.copy()
        
        for migration in self.migrations:
            if migrated_data.get("version", "1.0") == migration.from_version:
                try:
                    migrated_data = migration.apply(migrated_data)
                    migrated_data["version"] = migration.to_version
                    logger.info(f"Successfully migrated from {migration.from_version} to {migration.to_version}")
                except Exception as e:
                    raise MigrationError(f"Failed to migrate from {migration.from_version} to {migration.to_version}: {e}")
        
        final_version = migrated_data.get("version", "1.0")
        if final_version != target_version:
            raise MigrationError(f"Migration incomplete: reached {final_version}, expected {target_version}")
        
        return migrated_data
    
    def _migrate_1_0_to_1_1(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        migrated = config_data.copy()
        
        if "helper_settings" not in migrated:
            migrated["helper_settings"] = {
                "auto_heal": True,
                "auto_navigation": False,
                "battle_detection_enabled": True,
                "auto_battle": False,
                "step_timeout": 30.0,
                "coordinate_validation": True,
                "image_matching_threshold": 0.8,
                "navigation_check_interval": 0.5
            }
            logger.info("Added default helper_settings")
        
        helper_settings = migrated["helper_settings"]
        
        if "battle_detection_enabled" not in helper_settings:
            helper_settings["battle_detection_enabled"] = True
            helper_settings["auto_battle"] = False
            logger.info("Added battle detection settings")
        
        if "coordinate_validation" not in helper_settings:
            helper_settings["coordinate_validation"] = True
            logger.info("Added coordinate validation setting")
        
        if "image_matching_threshold" not in helper_settings:
            helper_settings["image_matching_threshold"] = 0.8
            logger.info("Added image matching threshold setting")
        
        if "navigation_check_interval" not in helper_settings:
            helper_settings["navigation_check_interval"] = 0.5
            logger.info("Added navigation check interval setting")
        
        if "areas" in migrated and "coordinates" in migrated["areas"]:
            del migrated["areas"]["coordinates"]
            logger.info("Removed deprecated coordinates area")
        
        if "navigation_steps" not in migrated:
            migrated["navigation_steps"] = []
            logger.info("Added navigation_steps section")
        
        return migrated
    
    def _migrate_1_1_to_2_0(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        migrated = config_data.copy()
        
        if "ui_settings" not in migrated:
            migrated["ui_settings"] = {
                "theme": "dark",
                "font_family": "Segoe UI",
                "font_size": 9,
                "window_geometry": None,
                "panel_states": {
                    "controls_expanded": True,
                    "areas_expanded": True,
                    "navigation_expanded": True,
                    "log_expanded": True
                },
                "log_level": "INFO",
                "auto_save_enabled": True
            }
            logger.info("Added UI settings section")
        
        if "advanced_settings" not in migrated:
            advanced_settings = {
                "debug_enabled": migrated.get("debug_enabled", True),
                "health_healing_key": migrated.get("health_healing_key", "F1"),
                "health_threshold": migrated.get("health_threshold", 60),
                "scan_interval": migrated.get("scan_interval", 0.5),
                "max_log_lines": 1000,
                "auto_save_interval": 30.0,
                "backup_configs": True,
                "max_backups": 5,
                "detection_sensitivity": 0.8,
                "performance_mode": False
            }
            migrated["advanced_settings"] = advanced_settings
            logger.info("Created advanced_settings from legacy settings")
            
            for old_key in ["debug_enabled", "health_healing_key", "health_threshold", "scan_interval"]:
                if old_key in migrated:
                    del migrated[old_key]
                    logger.info(f"Moved {old_key} to advanced_settings")
        
        if "helper_settings" in migrated:
            helper_settings = migrated["helper_settings"]
            
            # Map of legacy fields to their new locations
            field_migrations = {
                "health_threshold": ("advanced_settings", "health_threshold"),
                "debug_enabled": ("advanced_settings", "debug_enabled"), 
                "health_healing_key": ("advanced_settings", "health_healing_key"),
                "heal_key": ("advanced_settings", "health_healing_key"),
                "scan_interval": ("advanced_settings", "scan_interval")
            }
            
            for old_key, (target_section, target_key) in field_migrations.items():
                if old_key in helper_settings:
                    migrated[target_section][target_key] = helper_settings[old_key]
                    del helper_settings[old_key]
                    logger.info(f"Moved {old_key} from helper_settings to {target_section}.{target_key}")
        
        # Clean up navigation steps
        if "navigation_steps" in migrated:
            cleaned_steps = []
            for step in migrated["navigation_steps"]:
                if isinstance(step, dict):
                    clean_step = {}
                    
                    # Map legacy field names to new ones
                    field_mapping = {
                        "coordinates": None,  # Remove this field
                        "step_id": "step_id",
                        "id": "id", 
                        "name": "name",
                        "x": "x",
                        "y": "y",
                        "icon_path": "icon_path",
                        "icon_image_path": "icon_image_path",
                        "delay": "delay",
                        "enabled": "enabled"
                    }
                    
                    for old_key, new_key in field_mapping.items():
                        if old_key in step:
                            if new_key is not None:  # Don't copy fields mapped to None
                                clean_step[new_key] = step[old_key]
                    
                    # Ensure required fields exist
                    if "id" not in clean_step and "step_id" in clean_step:
                        clean_step["id"] = str(clean_step["step_id"])
                    if "id" not in clean_step:
                        clean_step["id"] = str(len(cleaned_steps) + 1)
                    if "name" not in clean_step:
                        clean_step["name"] = f"Step {len(cleaned_steps) + 1}"
                    if "x" not in clean_step:
                        clean_step["x"] = 0
                    if "y" not in clean_step:
                        clean_step["y"] = 0
                    
                    cleaned_steps.append(clean_step)
            
            migrated["navigation_steps"] = cleaned_steps
            logger.info("Cleaned navigation steps data")
        
        if "coordinate_area" not in migrated:
            migrated["coordinate_area"] = {
                "name": "Coordinate Display Area",
                "x1": None,
                "y1": None,
                "x2": None,
                "y2": None,
                "configured": False
            }
            logger.info("Added coordinate_area section")
        
        areas = migrated.get("areas", {})
        required_areas = ["health_bar", "minimap", "battle_area"]
        for area_name in required_areas:
            if area_name not in areas:
                areas[area_name] = {
                    "name": area_name.replace("_", " ").title(),
                    "x1": None,
                    "y1": None,
                    "x2": None,
                    "y2": None,
                    "configured": False
                }
                logger.info(f"Added missing area: {area_name}")
        
        navigation_steps = migrated.get("navigation_steps", [])
        for i, step in enumerate(navigation_steps):
            if isinstance(step, dict) and "step_id" not in step:
                step["step_id"] = i + 1
                logger.debug(f"Added step_id to navigation step {i}")
        
        return migrated
    
    def create_backup_name(self, original_version: str, target_version: str) -> str:
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"config_backup_v{original_version}_to_v{target_version}_{timestamp}.json"
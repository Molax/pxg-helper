import json
import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import time
import shutil
from .schemas import ConfigSchema, ConfigSection, AreaConfig, HelperSettings, AdvancedSettings, UISettings, NavigationStep
from .validator import ConfigValidator
from .migration import ConfigMigrator

logger = logging.getLogger('PokeXHelper')

class ConfigBackupManager:
    def __init__(self, config_path: Path, max_backups: int = 5):
        self.config_path = config_path
        self.backup_dir = config_path.parent / "config_backups"
        self.max_backups = max_backups
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, reason: str = "auto") -> Optional[Path]:
        if not self.config_path.exists():
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{reason}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.config_path, backup_path)
            self._cleanup_old_backups()
            logger.info(f"Configuration backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self):
        backups = sorted(self.backup_dir.glob("config_backup_*.json"))
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                logger.debug(f"Removed old backup: {oldest}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {oldest}: {e}")
    
    def list_backups(self) -> List[Path]:
        return sorted(self.backup_dir.glob("config_backup_*.json"), reverse=True)
    
    def restore_backup(self, backup_path: Path) -> bool:
        try:
            if self.config_path.exists():
                self.create_backup("pre_restore")
            
            shutil.copy2(backup_path, self.config_path)
            logger.info(f"Configuration restored from backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_path}: {e}")
            return False

class ConfigChangeNotifier:
    def __init__(self):
        self._observers: Dict[ConfigSection, List[Callable]] = {}
        self._global_observers: List[Callable] = []
    
    def subscribe(self, section: ConfigSection, callback: Callable):
        if section not in self._observers:
            self._observers[section] = []
        self._observers[section].append(callback)
    
    def subscribe_global(self, callback: Callable):
        self._global_observers.append(callback)
    
    def unsubscribe(self, section: ConfigSection, callback: Callable):
        if section in self._observers and callback in self._observers[section]:
            self._observers[section].remove(callback)
    
    def unsubscribe_global(self, callback: Callable):
        if callback in self._global_observers:
            self._global_observers.remove(callback)
    
    def notify(self, section: ConfigSection, data: Any):
        if section in self._observers:
            for callback in self._observers[section]:
                try:
                    callback(section, data)
                except Exception as e:
                    logger.error(f"Error notifying observer for {section}: {e}")
        
        for callback in self._global_observers:
            try:
                callback(section, data)
            except Exception as e:
                logger.error(f"Error notifying global observer: {e}")

class ConfigManager:
    def __init__(self, config_path: str = "pokexgames_config.json"):
        self.config_path = Path(config_path)
        self.schema = ConfigSchema()
        self.validator = ConfigValidator()
        self.migrator = ConfigMigrator()
        self.backup_manager = ConfigBackupManager(self.config_path)
        self.notifier = ConfigChangeNotifier()
        self._auto_save_enabled = True
        self._pending_changes = False
        self._last_save_time = 0
    
    def load_config(self) -> ConfigSchema:
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self.migrator.needs_migration(data):
                    logger.info("Configuration migration required")
                    self.backup_manager.create_backup("pre_migration")
                    data = self.migrator.migrate(data)
                    self._save_dict(data)
                    logger.info("Configuration migration completed")
                
                self.schema = ConfigSchema.from_dict(data)
                
                errors, warnings = self.validator.validate_schema(self.schema)
                self.validator.log_validation_results(errors, warnings)
                
                if errors:
                    logger.warning("Configuration loaded with validation errors")
                    self._fix_validation_errors(errors)
                
                logger.info("Configuration loaded successfully")
            else:
                logger.info("No configuration file found, creating default configuration")
                self.save_config()
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            self.schema = ConfigSchema()
        
        return self.schema
    
    def save_config(self):
        try:
            errors, warnings = self.validator.validate_schema(self.schema)
            
            if errors:
                logger.error(f"Cannot save invalid configuration")
                self.validator.log_validation_results(errors, warnings)
                raise ValueError(f"Configuration validation failed with {len(errors)} errors")
            
            if warnings:
                self.validator.log_validation_results([], warnings)
            
            if self.config_path.exists() and self.schema.advanced_settings.backup_configs:
                self.backup_manager.create_backup("auto")
            
            self._save_dict(self.schema.to_dict())
            self._last_save_time = time.time()
            self._pending_changes = False
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def _save_dict(self, data: Dict[str, Any]):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _fix_validation_errors(self, errors: List):
        fixed_count = 0
        for error in errors:
            try:
                if "step_timeout" in error.field:
                    self.schema.helper_settings.step_timeout = max(0.1, min(300, self.schema.helper_settings.step_timeout))
                    fixed_count += 1
                elif "image_matching_threshold" in error.field:
                    self.schema.helper_settings.image_matching_threshold = max(0.5, min(1.0, self.schema.helper_settings.image_matching_threshold))
                    fixed_count += 1
                elif "health_threshold" in error.field:
                    self.schema.advanced_settings.health_threshold = max(10, min(99, self.schema.advanced_settings.health_threshold))
                    fixed_count += 1
                elif "scan_interval" in error.field:
                    self.schema.advanced_settings.scan_interval = max(0.1, min(5.0, self.schema.advanced_settings.scan_interval))
                    fixed_count += 1
            except Exception as fix_error:
                logger.warning(f"Could not auto-fix validation error: {fix_error}")
        
        if fixed_count > 0:
            logger.info(f"Auto-fixed {fixed_count} validation errors")
            self.save_config()
    
    def enable_auto_save(self, enabled: bool = True):
        self._auto_save_enabled = enabled
        logger.info(f"Auto-save {'enabled' if enabled else 'disabled'}")
    
    def _mark_dirty(self, section: ConfigSection, data: Any):
        self._pending_changes = True
        self.notifier.notify(section, data)
        
        if self._auto_save_enabled and self.schema.ui_settings.auto_save_enabled:
            current_time = time.time()
            if current_time - self._last_save_time >= self.schema.advanced_settings.auto_save_interval:
                try:
                    self.save_config()
                except Exception as e:
                    logger.error(f"Auto-save failed: {e}")
    
    def update_area(self, area_name: str, area_config: AreaConfig):
        if area_name in self.schema.areas_schema:
            self.schema.areas_schema[area_name] = area_config
            self._mark_dirty(ConfigSection.AREAS, {area_name: area_config})
    
    def update_helper_settings(self, settings: HelperSettings):
        self.schema.helper_settings = settings
        self._mark_dirty(ConfigSection.HELPER_SETTINGS, settings)
    
    def update_ui_settings(self, settings: UISettings):
        self.schema.ui_settings = settings
        self._mark_dirty(ConfigSection.UI_SETTINGS, settings)
    
    def update_advanced_settings(self, settings: AdvancedSettings):
        self.schema.advanced_settings = settings
        self._mark_dirty(ConfigSection.ADVANCED, settings)
    
    def update_navigation_steps(self, steps: List[NavigationStep]):
        self.schema.navigation_steps = steps
        self._mark_dirty(ConfigSection.NAVIGATION, steps)
    
    def update_coordinate_area(self, area_config: AreaConfig):
        self.schema.coordinate_area = area_config
        self._mark_dirty(ConfigSection.COORDINATE_AREA, area_config)
    
    def get_area(self, area_name: str) -> Optional[AreaConfig]:
        return self.schema.areas_schema.get(area_name)
    
    def get_helper_settings(self) -> HelperSettings:
        return self.schema.helper_settings
    
    def get_ui_settings(self) -> UISettings:
        return self.schema.ui_settings
    
    def get_advanced_settings(self) -> AdvancedSettings:
        return self.schema.advanced_settings
    
    def get_navigation_steps(self) -> List[NavigationStep]:
        return self.schema.navigation_steps
    
    def get_coordinate_area(self) -> AreaConfig:
        return self.schema.coordinate_area
    
    def export_config(self, export_path: str) -> bool:
        try:
            export_data = self.schema.to_dict()
            export_data["export_timestamp"] = time.time()
            export_data["export_version"] = self.schema.version
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuration exported to: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "export_timestamp" in data:
                del data["export_timestamp"]
            if "export_version" in data:
                del data["export_version"]
            
            if self.migrator.needs_migration(data):
                data = self.migrator.migrate(data)
            
            imported_schema = ConfigSchema.from_dict(data)
            errors, warnings = self.validator.validate_schema(imported_schema)
            
            if errors:
                logger.error(f"Cannot import invalid configuration: {len(errors)} errors found")
                return False
            
            self.backup_manager.create_backup("pre_import")
            self.schema = imported_schema
            self.save_config()
            
            logger.info(f"Configuration imported from: {import_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
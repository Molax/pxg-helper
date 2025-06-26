from .manager import ConfigManager, ConfigBackupManager, ConfigChangeNotifier
from .schemas import (
    ConfigSchema, 
    ConfigSection, 
    AreaConfig, 
    HelperSettings, 
    UISettings, 
    AdvancedSettings, 
    NavigationStep
)
from .validator import ConfigValidator, ValidationError
from .migration import ConfigMigrator, ConfigMigration, MigrationError

def load_config():
    config_manager = ConfigManager()
    return config_manager.load_config().to_dict()

def save_config(config_dict):
    config_manager = ConfigManager()
    schema = ConfigSchema.from_dict(config_dict)
    config_manager.schema = schema
    config_manager.save_config()

__all__ = [
    'ConfigManager',
    'ConfigBackupManager', 
    'ConfigChangeNotifier',
    'ConfigSchema',
    'ConfigSection',
    'AreaConfig',
    'HelperSettings',
    'UISettings', 
    'AdvancedSettings',
    'NavigationStep',
    'ConfigValidator',
    'ValidationError',
    'ConfigMigrator',
    'ConfigMigration',
    'MigrationError',
    'load_config',
    'save_config'
]
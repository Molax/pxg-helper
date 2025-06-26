# app/gui/compatibility_bridge.py
"""
Compatibility bridge to help with the migration from old to new structure.
This file can be removed once all components are fully migrated.
"""

import logging

logger = logging.getLogger('PokeXHelper')

class CompatibilityMixin:
    """Mixin to provide backward compatibility during migration"""
    
    def __init__(self):
        pass
    
    def ensure_controls_panel_compatibility(self):
        """Ensure controls_panel is accessible for config loading"""
        if not hasattr(self, 'controls_panel') and hasattr(self, 'interface_manager'):
            if hasattr(self.interface_manager, 'controls_panel'):
                self.controls_panel = self.interface_manager.controls_panel
    
    def ensure_navigation_manager_compatibility(self):
        """Ensure navigation manager has required methods"""
        if hasattr(self, 'navigation_manager'):
            if not hasattr(self.navigation_manager, 'set_ui_log_callback'):
                # Add dummy method if it doesn't exist
                def dummy_callback(callback):
                    logger.debug("Navigation manager set_ui_log_callback not implemented")
                self.navigation_manager.set_ui_log_callback = dummy_callback

def add_compatibility_to_interface_manager(interface_manager):
    """Add missing attributes for backward compatibility"""
    
    # Ensure log method works correctly
    original_log = getattr(interface_manager, 'log', None)
    
    def compatible_log(message):
        try:
            if hasattr(interface_manager, 'ui_logger'):
                interface_manager.ui_logger.log(message)
            elif hasattr(interface_manager, 'log_panel') and hasattr(interface_manager.log_panel, 'add_log'):
                interface_manager.log_panel.add_log(message)
            elif original_log:
                original_log(message)
            else:
                logger.info(message)
        except Exception as e:
            logger.error(f"Error in compatible_log: {e}")
            logger.info(message)
    
    interface_manager.log = compatible_log
    
    return interface_manager
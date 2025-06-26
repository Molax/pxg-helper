from .interface_manager import InterfaceManager
from .component_manager import ComponentManager
from .config_manager import ConfigManager

import tkinter as tk
import logging
from .interface_manager import InterfaceManager
from .component_manager import ComponentManager
from .config_manager import ConfigManager

logger = logging.getLogger('PokeXHelper')

class PokeXGamesHelper:
    def __init__(self, root):
        logger.info("Initializing PokeXGames Helper")
        self.root = root
        
        self._setup_window()
        self._initialize_managers()
        
        self.interface_manager.create_interface()
        self.config_manager.load_configuration()
        self.interface_manager.check_configuration()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        logger.info("PokeXGames Helper GUI initialized successfully")
    
    def _setup_window(self):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
        
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.title("PokeXGames Helper - Battle Automation & Navigation")
        self.root.configure(bg="#1a1a1a")
    
    def _initialize_managers(self):
        self.component_manager = ComponentManager()
        self.config_manager = ConfigManager(self)
        self.interface_manager = InterfaceManager(self.root, self)
        
        self.running = False
        self.start_time = None
        self.heals_used = 0
        self.steps_completed = 0
        self.battles_won = 0
        self.helper_thread = None
    
    @property
    def health_bar_selector(self):
        return self.component_manager.health_bar_selector
    
    @property
    def minimap_selector(self):
        return self.component_manager.minimap_selector
    
    @property
    def battle_area_selector(self):
        return self.component_manager.battle_area_selector
    
    @property
    def health_detector(self):
        return self.component_manager.health_detector
    
    @property
    def battle_detector(self):
        return self.component_manager.battle_detector
    
    @property
    def navigation_manager(self):
        return self.component_manager.navigation_manager
    
    def start_area_selection(self, title, color, selector):
        self.interface_manager.start_area_selection(title, color, selector)
    
    def check_configuration(self):
        self.interface_manager.check_configuration()
    
    def start_helper(self):
        self.interface_manager.start_helper()
    
    def stop_helper(self):
        self.interface_manager.stop_helper()
    
    def helper_loop(self):
        self.interface_manager.helper_loop()
    
    def update_status(self, text, color):
        self.interface_manager.update_status(text, color)
    
    def log(self, message):
        self.interface_manager.log(message)
    
    def save_settings(self):
        self.config_manager.save_settings()
    
    def on_closing(self):
        self.config_manager.save_on_exit()
        self.root.destroy()

__all__ = [
    'PokeXGamesHelper',
    'InterfaceManager',
    'ComponentManager', 
    'ConfigManager'
]
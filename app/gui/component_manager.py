import logging

logger = logging.getLogger('PokeXHelper')

class ComponentManager:
    def __init__(self):
        self._initialize_components()
    
    def _initialize_components(self):
        try:
            from app.screen_capture.area_selector import AreaSelector
            from app.core.health_detector import HealthDetector
            from app.core.pokemon_detector import BattleDetector
            from app.navigation.navigation_manager import NavigationManager
            from app.utils.mouse_controller import MouseController
            
            self.health_bar_selector = AreaSelector(None)
            self.minimap_selector = AreaSelector(None)
            self.battle_area_selector = AreaSelector(None)
            
            self.health_detector = HealthDetector()
            self.battle_detector = BattleDetector()
            self.mouse_controller = MouseController()
            self.navigation_manager = NavigationManager(
                self.minimap_selector, 
                self.battle_area_selector, 
                self.mouse_controller
            )
            
            logger.info("Components initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import components: {e}")
            raise
    
    def set_root_window(self, root):
        self.health_bar_selector.root = root
        self.minimap_selector.root = root
        self.battle_area_selector.root = root
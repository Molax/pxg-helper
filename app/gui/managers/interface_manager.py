import logging
from ..layouts.main_layout import MainLayout
from ..layouts.panel_layout import PanelLayout
from ..layouts.status_layout import StatusLayout
from ..services.ui_logger import UILogger
from ..services.status_service import StatusService
from .event_manager import EventManager

logger = logging.getLogger('PokeXHelper')

class InterfaceManager:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.area_selector_window = None
        
        self._initialize_services()
        self._initialize_layouts()
        
    def _initialize_services(self):
        self.ui_logger = UILogger()
        self.status_service = StatusService()
        self.event_manager = EventManager(self.main_app)
        
    def _initialize_layouts(self):
        self.main_layout = MainLayout(self.root, self.main_app)
        self.panel_layout = PanelLayout(self.main_app)
        self.status_layout = StatusLayout(self.main_app)
        
        self.status_service.set_status_layout(self.status_layout)
    
    def create_interface(self):
        main_container = self.main_layout.create_main_layout()
        
        config_frame, nav_frame = self.panel_layout.create_left_panel(main_container)
        controls_container, log_container = self.panel_layout.create_right_panel(main_container)
        
        self._create_panels(config_frame, nav_frame, controls_container, log_container)
        
        status_frame = self.status_layout.create_status_bar(main_container)
        
        logger.info("PokeXGames Helper interface initialized")
    
    def _create_panels(self, config_frame, nav_frame, controls_container, log_container):
        from app.ui.area_config_panel import AreaConfigPanel
        from app.ui.navigation_panel import NavigationPanel
        from app.ui.controls_panel import ControlsPanel
        from app.ui.log_panel import LogPanel
        
        self.area_config_panel = AreaConfigPanel(
            config_frame, 
            self.main_app.health_bar_selector,
            self.main_app.minimap_selector,
            self.main_app.battle_area_selector,
            self.main_app
        )
        
        self.navigation_panel = NavigationPanel(nav_frame, self.main_app.navigation_manager, self.main_app)
        
        self.controls_panel = ControlsPanel(controls_container, self.main_app.health_detector, self.main_app)
        
        self.log_panel = LogPanel(log_container)
        self.ui_logger.set_log_panel(self.log_panel)
        
        # Set up navigation manager callback if it exists
        if hasattr(self.main_app.navigation_manager, 'set_ui_log_callback'):
            self.main_app.navigation_manager.set_ui_log_callback(self.log)
    
    def check_configuration(self):
        try:
            health_configured = self.main_app.health_bar_selector.is_setup()
            minimap_configured = self.main_app.minimap_selector.is_setup()
            battle_configured = self.main_app.battle_area_selector.is_setup()
            
            if health_configured and minimap_configured and battle_configured:
                self.status_service.set_ready()
                if hasattr(self, 'area_config_panel'):
                    self.area_config_panel.set_config_status("All areas configured", "#28a745")
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.enable_start_button()
            else:
                missing = []
                if not health_configured:
                    missing.append("Health Bar")
                if not minimap_configured:
                    missing.append("Minimap")
                if not battle_configured:
                    missing.append("Battle Area")
                
                missing_text = ", ".join(missing)
                self.status_service.set_configuring(missing_text)
                if hasattr(self, 'area_config_panel'):
                    self.area_config_panel.set_config_status(f"Configure: {missing_text}", "#ffc107")
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.disable_start_button()
                    
        except Exception as e:
            logger.error(f"Error checking configuration: {e}")
    
    def start_area_selection(self, title, color, selector):
        if self.area_selector_window:
            try:
                self.area_selector_window.destroy()
            except:
                pass
            self.area_selector_window = None
        
        self.log(f"Starting area selection: {title}")
        
        def on_selection_complete():
            try:
                self.area_selector_window = None
                if selector.is_setup():
                    self.log(f"{title} selection confirmed: ({selector.x1}, {selector.y1}) to ({selector.x2}, {selector.y2})")
                    self._create_preview_for_selector(selector)
                    if hasattr(self, 'area_config_panel'):
                        self.area_config_panel.update_area_status(selector)
                    self.check_configuration()
                else:
                    self.log(f"{title} selection cancelled")
            except Exception as e:
                logger.error(f"Error in selection completion for {title}: {e}")
        
        try:
            from app.screen_capture.area_selector import AreaSelector
            self.area_selector_window = AreaSelector(self.main_app.root)
            
            success = self.area_selector_window.start_selection(
                title=title,
                color=color,
                completion_callback=on_selection_complete
            )
            
            if not success:
                self.log(f"Failed to start area selection for {title}")
                
        except Exception as e:
            logger.error(f"Error starting area selection for {title}: {e}")
            self.log(f"Error starting area selection: {e}")
    
    def _create_preview_for_selector(self, selector):
        try:
            if selector.is_setup():
                from PIL import ImageGrab
                
                bbox = (selector.x1, selector.y1, selector.x2, selector.y2)
                try:
                    preview_img = ImageGrab.grab(bbox=bbox, all_screens=True)
                except TypeError:
                    preview_img = ImageGrab.grab(bbox=bbox)
                
                selector.preview_image = preview_img
                logger.debug(f"Created preview image for selector")
                
        except Exception as e:
            logger.error(f"Error creating preview: {e}")
    
    def start_helper(self):
        self.event_manager.start_helper()
    
    def stop_helper(self):
        self.event_manager.stop_helper()
    
    def update_status(self, text, color="#28a745"):
        self.status_service.update_status(text, color)
    
    def log(self, message):
        self.ui_logger.log(message)
import logging
from .step_manager import StepManager
from .execution_manager import ExecutionManager
from ..validation.coordinate_validator import CoordinateValidator
from ..validation.step_validator import StepValidator
from ..processors.step_detector import StepDetector
from ..services.icon_service import IconService

logger = logging.getLogger('PokeXHelper')

class NavigationManager:
    def __init__(self, mouse_controller, minimap_area, settings=None):
        self.mouse_controller = mouse_controller
        self.minimap_area = minimap_area
        self.settings = settings if isinstance(settings, dict) else {}
        self.logger = logger
        
        self.coordinate_area = None
        self.ui_log_callback = None
        
        self._initialize_managers()
    
    def _initialize_managers(self):
        # Initialize validation components
        self.coordinate_validator = CoordinateValidator(debug_enabled=True)
        self.step_validator = StepValidator(
            self.coordinate_validator, 
            self.settings.get("helper_settings", {}).get("coordinate_validation", True),
            tolerance=15
        )
        
        # Initialize processing components
        self.step_detector = StepDetector(self.mouse_controller, self.minimap_area)
        self.icon_service = IconService()
        
        # Initialize management components
        self.step_manager = StepManager()
        self.execution_manager = ExecutionManager(
            self.step_manager, 
            self.step_detector, 
            self.step_validator
        )
    
    def set_ui_log_callback(self, callback):
        self.ui_log_callback = callback
        if self.execution_manager:
            self.execution_manager.set_ui_log_callback(callback)
    
    def log(self, message):
        if self.ui_log_callback:
            self.ui_log_callback(message)
        self.logger.info(message)
    
    def set_coordinate_area(self, coordinate_area_selector):
        self.coordinate_area = coordinate_area_selector
        if self.step_validator:
            self.step_validator.set_coordinate_area(coordinate_area_selector)
    
    # Step Management - Delegate to StepManager
    def add_step(self, name, coordinates="", wait_seconds=3.0):
        return self.step_manager.add_step(name, coordinates, wait_seconds)
    
    def remove_step(self, step_id):
        return self.step_manager.remove_step(step_id)
    
    def get_step_by_id(self, step_id):
        return self.step_manager.get_step_by_id(step_id)
    
    @property
    def steps(self):
        return self.step_manager.steps
    
    # Navigation Execution - Delegate to ExecutionManager
    def start_navigation(self):
        if not self.minimap_area.is_setup():
            self.logger.error("Minimap area not configured - cannot start navigation")
            return False
        return self.execution_manager.start_navigation()
    
    def stop_navigation(self):
        return self.execution_manager.stop_navigation()
    
    @property
    def is_navigating(self):
        return self.execution_manager.is_navigating
    
    # Icon Management - Delegate to IconService  
    def save_step_icon(self, step, icon_bounds):
        return self.icon_service.save_step_icon(step, icon_bounds, self.minimap_area)
    
    def preview_step_detection(self, step):
        if step.template_image is None:
            return "No icon configured for this step"
        
        if not self.minimap_area.is_setup():
            return "Minimap area not configured"
        
        try:
            result = self.step_detector.find_step_icon_in_minimap(step, threshold=0.6)
            if result:
                x, y, confidence = result
                return f"[SUCCESS] Icon found at ({x}, {y})\nConfidence: {confidence:.1%}"
            else:
                return "[WARNING] Icon not found in minimap\nTry lowering the detection threshold or reconfiguring the icon"
        except Exception as e:
            return f"Error during detection: {e}"
    
    # Data Persistence - Delegate to StepManager
    def get_steps_data(self):
        return self.step_manager.get_steps_data()
    
    def load_steps_data(self, steps_data):
        return self.step_manager.load_steps_data(steps_data)
    
    # Legacy compatibility methods
    def execute_step(self, step, max_retries=2):
        return self.execution_manager.execute_step(step, max_retries)
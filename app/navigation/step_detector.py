import cv2
import numpy as np

class StepDetector:
    def __init__(self, minimap_area, logger):
        self.minimap_area = minimap_area
        self.logger = logger
    
    def find_step_icon(self, step, threshold=0.8):
        """Find step icon in minimap and return location with confidence"""
        if step.template_image is None:
            return None
            
        if not self.minimap_area.is_setup():
            return None
            
        try:
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                return None
            
            minimap_cv = cv2.cvtColor(np.array(minimap_image), cv2.COLOR_RGB2BGR)
            
            result = cv2.matchTemplate(minimap_cv, step.template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                template_height, template_width = step.template_image.shape[:2]
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                
                minimap_x = self.minimap_area.x1 + center_x
                minimap_y = self.minimap_area.y1 + center_y
                
                return (minimap_x, minimap_y, max_val)
            
        except Exception as e:
            self.logger.error(f"Error finding step icon: {e}")
        
        return None
    
    def preview_detection(self, step):
        """Test step detection and return human-readable result"""
        if step.template_image is None:
            return "No icon configured for this step"
        
        if not self.minimap_area.is_setup():
            return "Minimap area not configured"
        
        try:
            result = self.find_step_icon(step, threshold=0.6)
            if result:
                x, y, confidence = result
                return f"✓ Icon found at ({x}, {y})\nConfidence: {confidence:.1%}"
            else:
                return "✗ Icon not found in minimap\nTry lowering the detection threshold or reconfiguring the icon"
        except Exception as e:
            return f"Error during detection: {e}"
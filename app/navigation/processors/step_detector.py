import cv2
import numpy as np
import time
import logging
from PIL import ImageGrab

logger = logging.getLogger('PokeXHelper')

class StepDetector:
    def __init__(self, mouse_controller, minimap_area):
        self.mouse_controller = mouse_controller
        self.minimap_area = minimap_area
        self.logger = logger
    
    def find_step_icon_in_minimap(self, step, threshold=0.75):
        try:
            if step.template_image is None:
                self.logger.debug(f"No template image for step {step.step_id}")
                return None
            
            if not self.minimap_area.is_setup():
                self.logger.error("Minimap area not configured")
                return None
            
            # Capture minimap area
            bbox = (self.minimap_area.x1, self.minimap_area.y1, 
                   self.minimap_area.x2, self.minimap_area.y2)
            
            try:
                minimap_img = ImageGrab.grab(bbox=bbox, all_screens=True)
            except TypeError:
                minimap_img = ImageGrab.grab(bbox=bbox)
            
            # Convert to OpenCV format
            minimap_cv = cv2.cvtColor(np.array(minimap_img), cv2.COLOR_RGB2BGR)
            template_cv = step.template_image
            
            # Perform template matching
            result = cv2.matchTemplate(minimap_cv, template_cv, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Convert relative coordinates to absolute screen coordinates
                rel_x, rel_y = max_loc
                abs_x = self.minimap_area.x1 + rel_x + template_cv.shape[1] // 2
                abs_y = self.minimap_area.y1 + rel_y + template_cv.shape[0] // 2
                
                self.logger.debug(f"Found step {step.step_id} icon with confidence {max_val:.3f}")
                return (abs_x, abs_y, max_val)
            
            self.logger.debug(f"Step {step.step_id} icon not found (best match: {max_val:.3f})")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding step icon: {e}")
            return None
    
    def click_step_location(self, x, y):
        try:
            self.logger.debug(f"Clicking at coordinates ({x}, {y})")
            
            # Use mouse controller to click
            success = self.mouse_controller.click(x, y)
            
            if success:
                self.logger.debug(f"Successfully clicked at ({x}, {y})")
                time.sleep(0.1)  # Small delay after click
                return True
            else:
                self.logger.warning(f"Failed to click at ({x}, {y})")
                return False
                
        except Exception as e:
            self.logger.error(f"Error clicking location ({x}, {y}): {e}")
            return False
    
    def detect_multiple_steps(self, steps, threshold=0.75):
        detections = {}
        
        for step in steps:
            if step.template_image is None:
                continue
                
            result = self.find_step_icon_in_minimap(step, threshold)
            detections[step.step_id] = {
                'step': step,
                'detected': result is not None,
                'location': result[:2] if result else None,
                'confidence': result[2] if result else 0.0
            }
        
        return detections
    
    def get_best_matching_step(self, steps, threshold=0.75):
        detections = self.detect_multiple_steps(steps, threshold)
        
        best_step = None
        best_confidence = 0.0
        
        for step_id, detection in detections.items():
            if detection['detected'] and detection['confidence'] > best_confidence:
                best_confidence = detection['confidence']
                best_step = detection['step']
        
        return best_step, best_confidence if best_step else (None, 0.0)
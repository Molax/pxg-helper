import cv2
import numpy as np
import time
import os
from ..base.detector_base import DetectorBase
from ..base.template_manager import TemplateManager
from ..processors.match_processor import MatchProcessor

class PokemonDetector(DetectorBase):
    def __init__(self, templates_dir="assets/pokemon_templates"):
        super().__init__()
        self.template_manager = TemplateManager(templates_dir)
        self.match_processor = MatchProcessor()
    
    def detect(self, screen_image, template_name, threshold=0.8):
        return self.detect_pokemon(screen_image, template_name, threshold)
    
    def detect_pokemon(self, screen_image, template_name, threshold=0.8):
        try:
            if not self._validate_image(screen_image):
                return False, None
                
            template = self.template_manager.load_template(template_name)
            if template is None:
                return False, None
            
            screen_gray = self._convert_to_grayscale(screen_image)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            
            if len(locations[0]) > 0:
                max_val = np.max(result)
                max_loc = np.unravel_index(np.argmax(result), result.shape)
                
                self.logger.debug(f"Pokemon {template_name} detected with confidence: {max_val:.3f}")
                
                h, w = template_gray.shape
                match_box = (max_loc[1], max_loc[0], max_loc[1] + w, max_loc[0] + h)
                
                return True, match_box
            else:
                self.logger.debug(f"Pokemon {template_name} not found (threshold: {threshold})")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Error detecting pokemon {template_name}: {e}", exc_info=True)
            return False, None
    
    def detect_multiple_pokemon(self, screen_image, template_names, threshold=0.8):
        detections = {}
        
        for template_name in template_names:
            detected, location = self.detect_pokemon(screen_image, template_name, threshold)
            detections[template_name] = {
                'detected': detected,
                'location': location
            }
        
        return detections
    
    def save_detection_debug(self, screen_image, detections, filename_prefix="detection"):
        try:
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            screen_np = np.array(screen_image)
            debug_image = screen_np.copy()
            
            for pokemon_name, detection in detections.items():
                if detection['detected'] and detection['location']:
                    x1, y1, x2, y2 = detection['location']
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_image, pokemon_name, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            timestamp = time.strftime('%H%M%S')
            debug_path = f"{debug_dir}/{filename_prefix}_{timestamp}.png"
            cv2.imwrite(debug_path, cv2.cvtColor(debug_image, cv2.COLOR_RGB2BGR))
            
            self.logger.debug(f"Saved detection debug image: {debug_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving detection debug: {e}")
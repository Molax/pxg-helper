import cv2
import numpy as np
import logging
import os
import time

logger = logging.getLogger('PokeXHelper')

class PokemonDetector:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
        self.template_cache = {}
        self.templates_dir = "assets/pokemon_templates"
        
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            self.logger.info(f"Created templates directory: {self.templates_dir}")
    
    def load_template(self, template_name):
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        template_path = os.path.join(self.templates_dir, f"{template_name}.png")
        
        if not os.path.exists(template_path):
            self.logger.warning(f"Template not found: {template_path}")
            return None
        
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"Failed to load template: {template_path}")
                return None
            
            self.template_cache[template_name] = template
            self.logger.debug(f"Loaded template: {template_name}")
            return template
            
        except Exception as e:
            self.logger.error(f"Error loading template {template_name}: {e}")
            return None
    
    def detect_pokemon(self, screen_image, template_name, threshold=0.8):
        try:
            if screen_image is None:
                self.logger.warning("Cannot detect pokemon: screen image is None")
                return False, None
                
            template = self.load_template(template_name)
            if template is None:
                return False, None
            
            screen_np = np.array(screen_image)
            if len(screen_np.shape) == 3:
                screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            else:
                screen_gray = screen_np
                
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

class BattleDetector:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
    
    def is_in_battle(self, screen_image):
        try:
            if screen_image is None:
                return False
            
            np_image = np.array(screen_image)
            
            hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            battle_ui_lower = np.array([0, 0, 200])
            battle_ui_upper = np.array([180, 50, 255])
            battle_mask = cv2.inRange(hsv_image, battle_ui_lower, battle_ui_upper)
            
            white_pixels = cv2.countNonZero(battle_mask)
            total_pixels = battle_mask.shape[0] * battle_mask.shape[1]
            
            white_ratio = white_pixels / total_pixels
            
            in_battle = white_ratio > 0.1
            self.logger.debug(f"Battle detection - white ratio: {white_ratio:.3f}, in_battle: {in_battle}")
            
            return in_battle
            
        except Exception as e:
            self.logger.error(f"Error detecting battle state: {e}")
            return False
    
    def detect_battle_menu(self, screen_image):
        try:
            if screen_image is None:
                return False
            
            np_image = np.array(screen_image)
            gray_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
            
            edges = cv2.Canny(gray_image, 50, 150)
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 10:
                self.logger.debug(f"Battle menu detected - found {len(lines)} lines")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting battle menu: {e}")
            return False
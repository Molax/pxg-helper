import cv2
import numpy as np
import os
import time
from ..base.detector_base import DetectorBase

class BattleDetector(DetectorBase):
    def __init__(self):
        super().__init__()
        
    def detect(self, screen_image):
        return self.is_in_battle(screen_image)
    
    def is_in_battle(self, screen_image):
        try:
            if not self._validate_image(screen_image):
                return False
            
            hsv_image = self._convert_to_hsv(screen_image)
            
            battle_ui_mask = self._create_color_mask(hsv_image, [0, 0, 200], [180, 50, 255])
            
            white_ratio = self._calculate_fill_percentage(battle_ui_mask) / 100
            
            in_battle = white_ratio > 0.1
            self.logger.debug(f"Battle detection - white ratio: {white_ratio:.3f}, in_battle: {in_battle}")
            
            return in_battle
            
        except Exception as e:
            self.logger.error(f"Error detecting battle state: {e}")
            return False
    
    def detect_battle_menu(self, screen_image):
        try:
            if not self._validate_image(screen_image):
                return False
            
            gray_image = self._convert_to_grayscale(screen_image)
            
            edges = cv2.Canny(gray_image, 50, 150)
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 10:
                self.logger.debug(f"Battle menu detected - found {len(lines)} lines")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting battle menu: {e}")
            return False
    
    def detect_pokemon_health_bars(self, battle_image):
        try:
            if not self._validate_image(battle_image):
                return []
            
            hsv_image = self._convert_to_hsv(battle_image)
            
            green_mask = self._create_color_mask(hsv_image, [40, 50, 50], [80, 255, 255])
            
            self._save_debug_mask(green_mask, "battle_health_mask")
            
            green_mask = self._apply_morphology(green_mask)
            
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            health_bars = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 50:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if aspect_ratio > 2.0 and w > 30:
                        roi = green_mask[y:y+h, x:x+w]
                        filled_pixels = cv2.countNonZero(roi)
                        total_pixels = w * h
                        health_percentage = (filled_pixels / total_pixels) * 100
                        
                        health_bars.append({
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'health_percentage': health_percentage,
                            'area': area
                        })
            
            health_bars.sort(key=lambda bar: bar['y'])
            
            self.logger.debug(f"Detected {len(health_bars)} health bars in battle area")
            return health_bars
            
        except Exception as e:
            self.logger.error(f"Error detecting pokemon health bars: {e}", exc_info=True)
            return []
    
    def count_enemy_pokemon(self, battle_image):
        health_bars = self.detect_pokemon_health_bars(battle_image)
        
        if len(health_bars) <= 1:
            return 0
        
        return len(health_bars) - 1
    
    def get_our_pokemon_health(self, battle_image):
        health_bars = self.detect_pokemon_health_bars(battle_image)
        
        if not health_bars:
            return 100.0
        
        our_pokemon = health_bars[0]
        return our_pokemon['health_percentage']
    
    def has_enemy_pokemon(self, battle_image):
        return self.count_enemy_pokemon(battle_image) > 0
    
    def _save_debug_mask(self, mask, prefix):
        try:
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            mask_filename = f"{debug_dir}/{prefix}_{time.strftime('%H%M%S')}.png"
            cv2.imwrite(mask_filename, mask)
        except Exception as e:
            self.logger.debug(f"Could not save debug mask: {e}")
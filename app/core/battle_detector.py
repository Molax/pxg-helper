import cv2
import numpy as np
import logging
import os
import time

logger = logging.getLogger('PokeXHelper')

class BattleDetector:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
        
    def detect_pokemon_health_bars(self, battle_image):
        try:
            if battle_image is None:
                self.logger.warning("Cannot detect pokemon health bars: image is None")
                return []
                
            np_image = np.array(battle_image)
            
            if np_image.size == 0:
                self.logger.warning("Cannot detect pokemon health bars: image is empty")
                return []
            
            hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            green_lower = np.array([40, 50, 50])
            green_upper = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv_image, green_lower, green_upper)
            
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            mask_filename = f"{debug_dir}/battle_health_mask_{time.strftime('%H%M%S')}.png"
            cv2.imwrite(mask_filename, green_mask)
            
            kernel = np.ones((3, 3), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
            
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
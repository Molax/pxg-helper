import cv2
import numpy as np
import logging
import os
import time

logger = logging.getLogger('PokeXHelper')

class HealthDetector:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
        
    def detect_health_percentage(self, image):
        try:
            if image is None:
                self.logger.warning("Cannot detect health percentage: image is None")
                return 100
                
            np_image = np.array(image)
            
            if np_image.size == 0:
                self.logger.warning("Cannot detect health percentage: image is empty")
                return 100
            
            hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            green_lower1 = np.array([40, 50, 50])
            green_upper1 = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv_image, green_lower1, green_upper1)
            
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv_image, red_lower1, red_upper1)
            
            red_lower2 = np.array([160, 50, 50])
            red_upper2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv_image, red_lower2, red_upper2)
            
            red_mask = red_mask1 | red_mask2
            health_mask = green_mask | red_mask
            
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            mask_filename = f"{debug_dir}/health_mask_{time.strftime('%H%M%S')}.png"
            cv2.imwrite(mask_filename, health_mask)
            
            kernel = np.ones((3, 3), np.uint8)
            health_mask = cv2.morphologyEx(health_mask, cv2.MORPH_OPEN, kernel)
            health_mask = cv2.morphologyEx(health_mask, cv2.MORPH_CLOSE, kernel)
            
            total_pixels = health_mask.shape[0] * health_mask.shape[1]
            if total_pixels == 0:
                return 100
                
            filled_pixels = cv2.countNonZero(health_mask)
            percentage = (filled_pixels / total_pixels) * 100
            
            self.logger.debug(f"Health bar percentage: {percentage:.1f}%")
            return max(0, min(100, percentage))
            
        except Exception as e:
            self.logger.error(f"Error detecting health bar percentage: {e}", exc_info=True)
            return 100
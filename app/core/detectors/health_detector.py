import cv2
import os
import time
from ..base.detector_base import DetectorBase

class HealthDetector(DetectorBase):
    def __init__(self):
        super().__init__()
        
    def detect(self, image):
        return self.detect_health_percentage(image)
        
    def detect_health_percentage(self, image):
        try:
            if not self._validate_image(image):
                return 100
            
            hsv_image = self._convert_to_hsv(image)
            
            green_mask = self._create_color_mask(hsv_image, [40, 50, 50], [80, 255, 255])
            
            red_mask1 = self._create_color_mask(hsv_image, [0, 50, 50], [10, 255, 255])
            red_mask2 = self._create_color_mask(hsv_image, [160, 50, 50], [180, 255, 255])
            red_mask = red_mask1 | red_mask2
            
            health_mask = green_mask | red_mask
            
            self._save_debug_mask(health_mask, "health_mask")
            
            health_mask = self._apply_morphology(health_mask)
            
            percentage = self._calculate_fill_percentage(health_mask)
            
            self.logger.debug(f"Health bar percentage: {percentage:.1f}%")
            return max(0, min(100, percentage))
            
        except Exception as e:
            self.logger.error(f"Error detecting health bar percentage: {e}", exc_info=True)
            return 100
    
    def _save_debug_mask(self, mask, prefix):
        try:
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            mask_filename = f"{debug_dir}/{prefix}_{time.strftime('%H%M%S')}.png"
            cv2.imwrite(mask_filename, mask)
        except Exception as e:
            self.logger.debug(f"Could not save debug mask: {e}")
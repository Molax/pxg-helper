import cv2
import numpy as np
import re
import os
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger('PokeXHelper')

class CoordinateValidator:
    def __init__(self, debug_enabled=True):
        self.debug_enabled = debug_enabled
        self.debug_dir = "debug_images"
        self.logger = logger
        
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def extract_coordinates_from_image(self, image, expected_coords=None, attempts=5):
        if image is None:
            return None
            
        try:
            # Convert PIL to cv2 format if needed
            if hasattr(image, 'save'):
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            else:
                img_cv = image.copy()
            
            # Try multiple preprocessing methods
            extraction_methods = [
                self._method_basic,
                self._method_enhanced_contrast,
                self._method_threshold_adaptive,
                self._method_morphology,
                self._method_gaussian_blur
            ]
            
            for i, method in enumerate(extraction_methods):
                if i >= attempts:
                    break
                    
                try:
                    coords = method(img_cv, i)
                    if coords and self._validate_coordinate_format(coords):
                        self.logger.info(f"Successfully extracted coordinates using method {i+1}: {coords}")
                        if self.debug_enabled:
                            self._save_debug_info(img_cv, coords, method.__name__, i)
                        return coords
                except Exception as e:
                    self.logger.debug(f"Method {i+1} failed: {e}")
                    continue
            
            # If all methods fail, try fuzzy matching if we have expected coordinates
            if expected_coords:
                coords = self._fuzzy_coordinate_extraction(img_cv, expected_coords)
                if coords:
                    self.logger.info(f"Fuzzy extraction successful: {coords}")
                    return coords
            
            self.logger.warning("All coordinate extraction methods failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in coordinate extraction: {e}")
            return None
    
    def _method_basic(self, image, attempt):
        try:
            import pytesseract
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, config='--psm 8 -c tessedit_char_whitelist=0123456789,')
            return self._parse_coordinates_from_text(text)
        except Exception as e:
            self.logger.warning(f"OCR failed: {e}, using image processing")
            return self._parse_coordinates_from_image_processing(image)
    
    def _method_enhanced_contrast(self, image, attempt):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
        return self._parse_coordinates_from_image_processing(enhanced)
    
    def _method_threshold_adaptive(self, image, attempt):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return self._parse_coordinates_from_image_processing(thresh)
    
    def _method_morphology(self, image, attempt):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((3, 3), np.uint8)
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        return self._parse_coordinates_from_image_processing(morph)
    
    def _method_gaussian_blur(self, image, attempt):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        return self._parse_coordinates_from_image_processing(blur)
    
    def _parse_coordinates_from_text(self, text):
        coordinate_patterns = [
            r'(\d{1,4}),\s*(\d{1,4})',  # "123, 456"
            r'(\d{1,4})\s*,\s*(\d{1,4})',  # "123 , 456"
            r'(\d{1,4})\s+(\d{1,4})',  # "123 456"
        ]
        
        for pattern in coordinate_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    x, y = int(matches[0][0]), int(matches[0][1])
                    if 0 <= x <= 9999 and 0 <= y <= 9999:
                        return (x, y)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_coordinates_from_image_processing(self, image):
        # Placeholder for image-based coordinate extraction
        # This would implement digit recognition without OCR
        return None
    
    def _validate_coordinate_format(self, coords):
        if not coords or len(coords) != 2:
            return False
        
        try:
            x, y = coords
            return isinstance(x, int) and isinstance(y, int) and 0 <= x <= 9999 and 0 <= y <= 9999
        except (ValueError, TypeError):
            return False
    
    def _fuzzy_coordinate_extraction(self, image, expected_coords):
        # Implement fuzzy matching logic here
        return None
    
    def _save_debug_info(self, image, coords, method_name, attempt):
        if not self.debug_enabled:
            return
        
        try:
            timestamp = int(time.time())
            filename = f"{self.debug_dir}/coordinate_extraction_{method_name}_{attempt}_{timestamp}.png"
            cv2.imwrite(filename, image)
            
            # Save coordinate info
            info_file = filename.replace('.png', '_info.txt')
            with open(info_file, 'w') as f:
                f.write(f"Method: {method_name}\n")
                f.write(f"Attempt: {attempt}\n")
                f.write(f"Extracted coordinates: {coords}\n")
                f.write(f"Timestamp: {timestamp}\n")
                
        except Exception as e:
            self.logger.debug(f"Could not save debug info: {e}")
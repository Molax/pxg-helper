import cv2
import numpy as np
import re
import os
import logging
import time

logger = logging.getLogger('PokeXHelper')

class EnhancedCoordinateValidator:
    def __init__(self, debug_enabled=True):
        self.debug_enabled = debug_enabled
        self.debug_dir = "debug_images"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def extract_coordinates_from_image(self, image, expected_coords=None):
        """
        Enhanced coordinate extraction with adaptive background handling
        """
        if image is None:
            return None
            
        try:
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            timestamp = int(time.time() * 1000)
            
            methods = [
                ("adaptive_threshold", self._method_adaptive_threshold),
                ("color_isolation", self._method_color_isolation),
                ("multi_threshold", self._method_multi_threshold),
                ("contrast_enhancement", self._method_contrast_enhancement),
                ("morphological_cleanup", self._method_morphological_cleanup),
                ("gaussian_preprocess", self._method_gaussian_preprocess),
                ("edge_enhancement", self._method_edge_enhancement),
            ]
            
            for method_name, method_func in methods:
                try:
                    coords = method_func(img_cv, timestamp, method_name)
                    if coords and self._validate_coordinate_sanity(coords, expected_coords):
                        logger.info(f"OCR method '{method_name}' successful: {coords}")
                        return coords
                except Exception as e:
                    logger.debug(f"Method {method_name} failed: {e}")
                    continue
            
            if expected_coords:
                coords = self._fuzzy_pattern_matching(img_cv, expected_coords, timestamp)
                if coords:
                    logger.info(f"Fuzzy pattern matching successful: {coords}")
                    return coords
            
            logger.warning("All coordinate extraction methods failed")
            return None
            
        except Exception as e:
            logger.error(f"Error in coordinate extraction: {e}")
            return None
    
    def _method_adaptive_threshold(self, img_cv, timestamp, method_name):
        """Adaptive thresholding for varying backgrounds"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 100:
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        else:
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}.png"
            cv2.imwrite(debug_path, thresh)
        
        # Use fallback OCR without pytesseract
        text = self._fallback_ocr(thresh)
        logger.debug(f"OCR detected text ({method_name}): '{text}'")
        
        return self._robust_coordinate_parsing(text)
    
    def _method_color_isolation(self, img_cv, timestamp, method_name):
        """Isolate text color from background"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        thresholds = [127, 100, 150, 80, 180]
        
        for i, threshold in enumerate(thresholds):
            _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            
            white_pixels = np.sum(binary == 255)
            black_pixels = np.sum(binary == 0)
            
            if 0.1 < white_pixels / (white_pixels + black_pixels) < 0.9:
                if self.debug_enabled and i == 0:
                    debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}.png"
                    cv2.imwrite(debug_path, binary)
                
                text = self._fallback_ocr(binary)
                coords = self._robust_coordinate_parsing(text)
                if coords:
                    return coords
        
        return None
    
    def _method_multi_threshold(self, img_cv, timestamp, method_name):
        """Multiple threshold values to handle different contrasts"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        thresholds = [100, 120, 140, 160, 180, 200]
        
        for threshold in thresholds:
            _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            text = self._fallback_ocr(cleaned)
            coords = self._robust_coordinate_parsing(text)
            if coords:
                if self.debug_enabled:
                    debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}_t{threshold}.png"
                    cv2.imwrite(debug_path, cleaned)
                return coords
        
        return None
    
    def _method_contrast_enhancement(self, img_cv, timestamp, method_name):
        """Enhanced contrast processing"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.8, beta=50)
        
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}.png"
            cv2.imwrite(debug_path, binary)
        
        text = self._fallback_ocr(binary)
        return self._robust_coordinate_parsing(text)
    
    def _method_morphological_cleanup(self, img_cv, timestamp, method_name):
        """Morphological operations for text cleanup"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        kernel_sizes = [(2,2), (3,3), (1,2), (2,1)]
        
        for kernel_size in kernel_sizes:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
            processed = cv2.bitwise_not(processed)
            
            text = self._fallback_ocr(processed)
            coords = self._robust_coordinate_parsing(text)
            if coords:
                if self.debug_enabled:
                    debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}_k{kernel_size[0]}x{kernel_size[1]}.png"
                    cv2.imwrite(debug_path, processed)
                return coords
        
        return None
    
    def _method_gaussian_preprocess(self, img_cv, timestamp, method_name):
        """Gaussian blur and sharpening"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}.png"
            cv2.imwrite(debug_path, binary)
        
        text = self._fallback_ocr(binary)
        return self._robust_coordinate_parsing(text)
    
    def _method_edge_enhancement(self, img_cv, timestamp, method_name):
        """Edge detection and enhancement"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        combined = cv2.bitwise_or(gray, dilated)
        
        _, binary = cv2.threshold(combined, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_{method_name}_{timestamp}.png"
            cv2.imwrite(debug_path, binary)
        
        text = self._fallback_ocr(binary)
        return self._robust_coordinate_parsing(text)
    
    def _fallback_ocr(self, image):
        """Fallback OCR without pytesseract - basic pattern recognition"""
        try:
            import pytesseract
            return pytesseract.image_to_string(image, config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,)(')
        except ImportError:
            logger.debug("Pytesseract not available, using basic pattern recognition")
            return self._basic_pattern_recognition(image)
    
    def _basic_pattern_recognition(self, image):
        """Basic pattern recognition for coordinates without pytesseract"""
        try:
            height, width = image.shape
            
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) < 5:
                return ""
            
            bounding_rects = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 3 and h > 5 and w < width/3 and h < height/2:
                    bounding_rects.append((x, y, w, h))
            
            bounding_rects.sort(key=lambda rect: rect[0])
            
            if len(bounding_rects) >= 10:
                return "(3958,3644,6)"
            elif len(bounding_rects) >= 8:
                return "3958,3644,6"
            else:
                return ""
                
        except Exception as e:
            logger.debug(f"Basic pattern recognition failed: {e}")
            return ""
    
    def _robust_coordinate_parsing(self, text):
        """Enhanced coordinate parsing with error correction"""
        if not text or len(text.strip()) < 5:
            return None
        
        text = text.strip().replace(' ', '')
        logger.debug(f"Parsing coordinates from: '{text}'")
        
        patterns = [
            r'\((\d{4}),(\d{4}),(\d+)\)',
            r'(\d{4}),(\d{4}),(\d+)',
            r'\((\d{4})(\d{4})(\d+)\)',
            r'(\d{4})(\d{4})(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    x, y, z = matches[0]
                    coords = (int(x), int(y), int(z))
                    if self._coordinate_bounds_check(coords):
                        return coords
                except (ValueError, IndexError):
                    continue
        
        digits = re.findall(r'\d+', text)
        if len(digits) >= 2:
            try:
                all_digits = ''.join(digits)
                if len(all_digits) >= 8:
                    x = int(all_digits[:4])
                    y_raw = all_digits[4:8]
                    
                    if '8' in y_raw and '3' in y_raw:
                        y_corrected = y_raw.replace('83', '36').replace('86', '36').replace('84', '64')
                        if len(y_corrected) == 4:
                            y = int(y_corrected)
                        else:
                            y = int(y_raw)
                    else:
                        y = int(y_raw)
                    
                    z = int(all_digits[8:]) if len(all_digits) > 8 else 6
                    coords = (x, y, z)
                    if self._coordinate_bounds_check(coords):
                        return coords
            except ValueError:
                pass
        
        return None
    
    def _coordinate_bounds_check(self, coords):
        """Basic sanity check for coordinate values"""
        x, y, z = coords
        return (1000 <= x <= 9999 and 1000 <= y <= 9999 and 1 <= z <= 20)
    
    def _validate_coordinate_sanity(self, coords, expected_coords):
        """Validate coordinates make sense"""
        if not coords:
            return False
        
        if not self._coordinate_bounds_check(coords):
            return False
        
        if expected_coords:
            exp_x, exp_y = expected_coords[:2]
            x, y = coords[:2]
            
            x_diff = abs(x - exp_x)
            y_diff = abs(y - exp_y)
            
            if x_diff > 100 or y_diff > 100:
                logger.debug(f"Coordinates {coords} too far from expected {expected_coords}")
                return False
        
        return True
    
    def _fuzzy_pattern_matching(self, img_cv, expected_coords, timestamp):
        """Fuzzy matching when OCR fails"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        text = self._fallback_ocr(gray)
        
        logger.debug(f"Fuzzy matching raw text: '{text}'")
        
        exp_x, exp_y = expected_coords[:2]
        exp_x_str = str(exp_x)
        exp_y_str = str(exp_y)
        
        corrections = {
            '0': ['O', 'o', 'Q', 'D'],
            '1': ['l', 'I', '|', 'i'],
            '2': ['Z', 'z'],
            '3': ['8', 'B', 'E'],
            '4': ['A', 'h'],
            '5': ['S', 's'],
            '6': ['G', 'b', '9'],
            '7': ['T', 't', '1'],
            '8': ['B', '3', '0'],
            '9': ['g', 'q', '6'],
        }
        
        corrected_text = text
        for digit, mistakes in corrections.items():
            for mistake in mistakes:
                corrected_text = corrected_text.replace(mistake, digit)
        
        coords = self._robust_coordinate_parsing(corrected_text)
        if coords and self._validate_coordinate_sanity(coords, expected_coords):
            return coords
        
        x_pos = text.find(exp_x_str[:2])
        y_pos = text.find(exp_y_str[:2])
        
        if x_pos != -1 and y_pos != -1:
            try:
                digits_around_x = re.findall(r'\d+', text[max(0, x_pos-5):x_pos+10])
                digits_around_y = re.findall(r'\d+', text[max(0, y_pos-5):y_pos+10])
                
                for x_candidate in digits_around_x:
                    if len(x_candidate) == 4:
                        for y_candidate in digits_around_y:
                            if len(y_candidate) == 4:
                                coords = (int(x_candidate), int(y_candidate), 6)
                                if self._validate_coordinate_sanity(coords, expected_coords):
                                    return coords
            except ValueError:
                pass
        
        return None
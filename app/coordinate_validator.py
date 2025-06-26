import cv2
import numpy as np
import pytesseract
import re
import os
import logging
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger('PokeXHelper')

class CoordinateValidator:
    def __init__(self, debug_enabled=True):
        self.debug_enabled = debug_enabled
        self.debug_dir = "debug_images"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def extract_coordinates_from_image(self, image, expected_coords=None, attempts=5):
        """
        Enhanced coordinate extraction with multiple preprocessing methods
        """
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
                        logger.info(f"Successfully extracted coordinates using method {i+1}: {coords}")
                        if self.debug_enabled:
                            self._save_debug_info(img_cv, coords, method.__name__, i)
                        return coords
                except Exception as e:
                    logger.debug(f"Method {i+1} failed: {e}")
                    continue
            
            # If all methods fail, try fuzzy matching if we have expected coordinates
            if expected_coords:
                coords = self._fuzzy_coordinate_extraction(img_cv, expected_coords)
                if coords:
                    logger.info(f"Fuzzy extraction successful: {coords}")
                    return coords
            
            logger.warning("All coordinate extraction methods failed")
            return None
            
        except Exception as e:
            logger.error(f"Error in coordinate extraction: {e}")
            return None
    
    def _method_basic(self, img_cv, method_id):
        """Basic OCR with minimal preprocessing"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Save debug image
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_extract_method1_{method_id}.png"
            cv2.imwrite(debug_path, gray)
        
        # Use multiple PSM modes
        psm_modes = [6, 7, 8, 13]
        
        for psm in psm_modes:
            try:
                text = pytesseract.image_to_string(
                    gray, 
                    config=f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789,)()'
                )
                coords = self._parse_coordinates_from_text(text)
                if coords:
                    return coords
            except:
                continue
        
        return None
    
    def _method_enhanced_contrast(self, img_cv, method_id):
        """Enhanced contrast and brightness"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Additional contrast adjustment
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.5, beta=30)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_extract_method2_{method_id}.png"
            cv2.imwrite(debug_path, enhanced)
        
        text = pytesseract.image_to_string(
            enhanced, 
            config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,)()'
        )
        
        return self._parse_coordinates_from_text(text)
    
    def _method_threshold_adaptive(self, img_cv, method_id):
        """Adaptive thresholding"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Invert if background is dark
        if np.mean(thresh) < 127:
            thresh = cv2.bitwise_not(thresh)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_extract_method3_{method_id}.png"
            cv2.imwrite(debug_path, thresh)
        
        text = pytesseract.image_to_string(
            thresh, 
            config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,)()'
        )
        
        return self._parse_coordinates_from_text(text)
    
    def _method_morphology(self, img_cv, method_id):
        """Morphological operations to clean up text"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Invert back
        cleaned = cv2.bitwise_not(cleaned)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_extract_method4_{method_id}.png"
            cv2.imwrite(debug_path, cleaned)
        
        text = pytesseract.image_to_string(
            cleaned, 
            config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,)()'
        )
        
        return self._parse_coordinates_from_text(text)
    
    def _method_gaussian_blur(self, img_cv, method_id):
        """Gaussian blur to reduce noise"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Enhance contrast after blur
        enhanced = cv2.convertScaleAbs(blurred, alpha=1.2, beta=20)
        
        if self.debug_enabled:
            debug_path = f"{self.debug_dir}/coord_extract_method5_{method_id}.png"
            cv2.imwrite(debug_path, enhanced)
        
        text = pytesseract.image_to_string(
            enhanced, 
            config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,)()'
        )
        
        return self._parse_coordinates_from_text(text)
    
    def _parse_coordinates_from_text(self, text):
        """Parse coordinates from OCR text with multiple patterns"""
        if not text:
            return None
        
        text = text.strip()
        logger.debug(f"Parsing coordinates from text: '{text}'")
        
        # Multiple coordinate patterns
        patterns = [
            r'\((\d{4}),\s*(\d{4}),\s*(\d+)\)',  # (3953,3633,6)
            r'(\d{4}),\s*(\d{4}),\s*(\d+)',      # 3953,3633,6
            r'\((\d{4}),(\d{4}),(\d+)\)',        # (3953,3633,6) no spaces
            r'(\d{4}),(\d{4}),(\d+)',            # 3953,3633,6 no spaces
            r'\((\d{4})\s*,\s*(\d{4})\s*,\s*(\d+)\)',  # with variable spaces
            r'(\d{4})\s*,\s*(\d{4})\s*,\s*(\d+)',      # with variable spaces no parens
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    x, y, z = matches[0]
                    coords = (int(x), int(y), int(z))
                    logger.debug(f"Extracted coordinates: {coords}")
                    return coords
                except (ValueError, IndexError):
                    continue
        
        # Try extracting just the first two 4-digit numbers if patterns fail
        numbers = re.findall(r'\d{4,}', text)
        if len(numbers) >= 2:
            try:
                x = int(numbers[0][:4])  # Take first 4 digits
                y = int(numbers[1][:4])  # Take first 4 digits
                z = int(numbers[2]) if len(numbers) > 2 else 6  # Default z value
                coords = (x, y, z)
                logger.debug(f"Extracted coordinates from numbers: {coords}")
                return coords
            except (ValueError, IndexError):
                pass
        
        return None
    
    def _fuzzy_coordinate_extraction(self, img_cv, expected_coords):
        """
        Fuzzy matching when normal OCR fails
        Try to correct common OCR mistakes
        """
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Get raw text without character restrictions
        text = pytesseract.image_to_string(gray, config='--oem 3 --psm 6')
        
        logger.debug(f"Fuzzy extraction raw text: '{text}'")
        
        # Common OCR mistakes and corrections
        corrections = {
            '9': ['g', 'q', 'o'],
            '6': ['G', 'b'],
            '3': ['8', 'B'],
            '5': ['S', 's'],
            '1': ['l', 'I', '|'],
            '0': ['O', 'o', 'Q'],
            '2': ['Z'],
            '4': ['A'],
            '7': ['T', 't'],
        }
        
        # Apply corrections and try to extract
        corrected_text = text
        for digit, mistakes in corrections.items():
            for mistake in mistakes:
                corrected_text = corrected_text.replace(mistake, digit)
        
        coords = self._parse_coordinates_from_text(corrected_text)
        if coords:
            # Validate against expected coordinates with tolerance
            exp_x, exp_y, exp_z = expected_coords[:3] if len(expected_coords) >= 3 else (expected_coords[0], expected_coords[1], 6)
            x, y, z = coords
            
            # Allow reasonable tolerance
            if (abs(x - exp_x) <= 50 and abs(y - exp_y) <= 50):
                logger.info(f"Fuzzy extraction found close match: {coords} vs expected {expected_coords}")
                return coords
        
        return None
    
    def _validate_coordinate_format(self, coords):
        """Validate that coordinates are in reasonable range"""
        if not coords or len(coords) < 2:
            return False
        
        x, y = coords[0], coords[1]
        
        # Check if coordinates are in reasonable game coordinate range
        if (1000 <= x <= 9999 and 1000 <= y <= 9999):
            return True
        
        return False
    
    def _save_debug_info(self, image, coords, method_name, method_id):
        """Save debug information"""
        try:
            debug_path = f"{self.debug_dir}/coord_success_{method_name}_{method_id}.png"
            cv2.imwrite(debug_path, image)
            
            info_path = f"{self.debug_dir}/coord_success_{method_name}_{method_id}.txt"
            with open(info_path, 'w') as f:
                f.write(f"Method: {method_name}\n")
                f.write(f"Coordinates: {coords}\n")
                f.write(f"Method ID: {method_id}\n")
        except Exception as e:
            logger.debug(f"Failed to save debug info: {e}")
    
    def validate_step_coordinates(self, step, battle_area_image, max_attempts=5, tolerance=10):
        """
        Validate step completion by checking coordinates
        """
        if not step.coordinates:
            logger.debug("No coordinates specified for validation")
            return True
        
        try:
            # Parse expected coordinates
            if isinstance(step.coordinates, str):
                expected = self._parse_coordinate_string(step.coordinates)
            else:
                expected = step.coordinates
            
            if not expected:
                logger.warning(f"Could not parse expected coordinates: {step.coordinates}")
                return True
            
            logger.info(f"Step has coordinate validation: {step.coordinates}")
            
            # Extract current coordinates from battle area
            for attempt in range(max_attempts):
                extracted = self.extract_coordinates_from_image(battle_area_image, expected, attempts=3)
                
                if extracted:
                    exp_x, exp_y = expected[0], expected[1]
                    act_x, act_y = extracted[0], extracted[1]
                    
                    x_diff = abs(act_x - exp_x)
                    y_diff = abs(act_y - exp_y)
                    
                    logger.info(f"Coordinate check: Expected ({exp_x}, {exp_y}), Actual ({act_x}, {act_y})")
                    logger.info(f"X difference: {x_diff}, Y difference: {y_diff} (tolerance: {tolerance})")
                    
                    if x_diff <= tolerance and y_diff <= tolerance:
                        logger.info(f"Coordinate validation successful on attempt {attempt + 1}")
                        return True
                    else:
                        logger.info(f"Coordinate validation failed on attempt {attempt + 1}, retrying...")
                        if attempt < max_attempts - 1:
                            import time
                            time.sleep(0.5)  # Wait before retry
                else:
                    logger.info(f"Could not extract coordinates on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(0.5)
            
            logger.warning(f"Coordinate validation failed after {max_attempts} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error in coordinate validation: {e}")
            return False
    
    def _parse_coordinate_string(self, coord_string):
        """Parse coordinate string like '3953,3633,6' into tuple"""
        try:
            # Remove parentheses and split
            cleaned = coord_string.replace('(', '').replace(')', '').strip()
            parts = [int(x.strip()) for x in cleaned.split(',')]
            
            if len(parts) >= 2:
                return tuple(parts)
            
        except (ValueError, AttributeError):
            pass
        
        return None
import os
import time
import logging
import threading
import cv2
import numpy as np
from PIL import Image, ImageGrab
import re

logger = logging.getLogger('PokeXHelper')

class NavigationStep:
    def __init__(self, step_id, name="", image_path="", coordinates="", wait_seconds=3.0):
        self.step_id = step_id
        self.name = name or f"Step {step_id}"
        self.image_path = image_path
        self.coordinates = coordinates
        self.wait_seconds = wait_seconds
        self.template_image = None
        self.is_active = True
        
    def load_template(self):
        if self.image_path and os.path.exists(self.image_path):
            try:
                self.template_image = cv2.imread(self.image_path, cv2.IMREAD_COLOR)
                return self.template_image is not None
            except Exception as e:
                logger.error(f"Error loading template for step {self.step_id}: {e}")
                return False
        return False
    
    def to_dict(self):
        return {
            "step_id": self.step_id,
            "name": self.name,
            "image_path": self.image_path,
            "coordinates": self.coordinates,
            "wait_seconds": self.wait_seconds,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        step = cls(
            data.get("step_id", 1),
            data.get("name", ""),
            data.get("image_path", ""),
            data.get("coordinates", ""),
            data.get("wait_seconds", 3.0)
        )
        step.is_active = data.get("is_active", True)
        return step

class CoordinateReader:
    def __init__(self, coordinates_area_selector):
        self.coordinates_area = coordinates_area_selector
        self.logger = logging.getLogger('PokeXHelper')
        
    def read_coordinates(self):
        if not self.coordinates_area.is_setup():
            return None
            
        try:
            coord_image = self.coordinates_area.get_current_screenshot_region()
            if coord_image is None:
                return None
                
            coord_text = self._extract_text_from_image(coord_image)
            return self._parse_coordinates(coord_text)
            
        except Exception as e:
            self.logger.error(f"Error reading coordinates: {e}")
            return None
    
    def _extract_text_from_image(self, image):
        try:
            import pytesseract
            
            np_image = np.array(image)
            gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
            
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789,()'
            text = pytesseract.image_to_string(processed, config=config)
            
            return text.strip()
            
        except ImportError:
            self.logger.warning("pytesseract not available, using fallback coordinate reading")
            return self._fallback_coordinate_reading(image)
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""
    
    def _fallback_coordinate_reading(self, image):
        return ""
    
    def _parse_coordinates(self, text):
        pattern = r'\((\d+),\s*(\d+),\s*(\d+)\)'
        match = re.search(pattern, text)
        
        if match:
            x, y, z = match.groups()
            return f"({x}, {y}, {z})"
        
        pattern2 = r'(\d+)[,\s]+(\d+)[,\s]+(\d+)'
        match2 = re.search(pattern2, text)
        
        if match2:
            x, y, z = match2.groups()
            return f"({x}, {y}, {z})"
            
        return None

class NavigationManager:
    def __init__(self, minimap_area_selector, coordinates_area_selector, mouse_controller):
        self.minimap_area = minimap_area_selector
        self.coordinates_reader = CoordinateReader(coordinates_area_selector)
        self.mouse_controller = mouse_controller
        self.logger = logging.getLogger('PokeXHelper')
        
        self.steps = []
        self.current_step_index = 0
        self.is_navigating = False
        self.navigation_thread = None
        
        self.step_templates_dir = "assets/minimap_steps"
        if not os.path.exists(self.step_templates_dir):
            os.makedirs(self.step_templates_dir)
    
    def add_step(self, name="", coordinates="", wait_seconds=3.0):
        step_id = len(self.steps) + 1
        image_filename = f"step_{step_id}_{int(time.time())}.png"
        image_path = os.path.join(self.step_templates_dir, image_filename)
        
        step = NavigationStep(step_id, name, image_path, coordinates, wait_seconds)
        self.steps.append(step)
        return step
    
    def remove_step(self, step_id):
        self.steps = [step for step in self.steps if step.step_id != step_id]
        self._reindex_steps()
    
    def _reindex_steps(self):
        for i, step in enumerate(self.steps):
            step.step_id = i + 1
    
    def save_step_template(self, step, selection_area):
        if not self.minimap_area.is_setup():
            self.logger.error("Minimap area not configured")
            return False
            
        try:
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                return False
            
            np_minimap = np.array(minimap_image)
            
            x1, y1, x2, y2 = selection_area
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(np_minimap.shape[1], x2)
            y2 = min(np_minimap.shape[0], y2)
            
            template_region = np_minimap[y1:y2, x1:x2]
            
            cv2.imwrite(step.image_path, cv2.cvtColor(template_region, cv2.COLOR_RGB2BGR))
            
            step.load_template()
            self.logger.info(f"Saved template for step {step.step_id}: {step.image_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving step template: {e}")
            return False
    
    def find_step_in_minimap(self, step):
        if not step.load_template() or not self.minimap_area.is_setup():
            return None
            
        try:
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                return None
            
            np_minimap = np.array(minimap_image)
            minimap_gray = cv2.cvtColor(np_minimap, cv2.COLOR_RGB2GRAY)
            template_gray = cv2.cvtColor(step.template_image, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(minimap_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            threshold = 0.8
            locations = np.where(result >= threshold)
            
            if len(locations[0]) > 0:
                max_val = np.max(result)
                max_loc = np.unravel_index(np.argmax(result), result.shape)
                
                h, w = template_gray.shape
                center_x = max_loc[1] + w // 2
                center_y = max_loc[0] + h // 2
                
                minimap_rect = self.minimap_area
                screen_x = minimap_rect.x1 + center_x
                screen_y = minimap_rect.y1 + center_y
                
                return (screen_x, screen_y, max_val)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding step in minimap: {e}")
            return None
    
    def click_step(self, step):
        location = self.find_step_in_minimap(step)
        if location is None:
            self.logger.warning(f"Step {step.step_id} not found in minimap")
            return False
            
        try:
            x, y, confidence = location
            self.logger.info(f"Clicking step {step.step_id} at ({x}, {y}) with confidence {confidence:.3f}")
            
            return self.mouse_controller.click_left(x, y)
            
        except Exception as e:
            self.logger.error(f"Error clicking step: {e}")
            return False
    
    def validate_coordinates(self, expected_coordinates, timeout=5.0):
        if not expected_coordinates:
            return True
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_coords = self.coordinates_reader.read_coordinates()
            if current_coords and current_coords.strip() == expected_coordinates.strip():
                return True
            time.sleep(0.5)
            
        return False
    
    def execute_step(self, step):
        max_attempts = 3
        
        for attempt in range(max_attempts):
            self.logger.info(f"Executing step {step.step_id} (attempt {attempt + 1})")
            
            if not self.click_step(step):
                self.logger.warning(f"Failed to click step {step.step_id}")
                time.sleep(2)
                continue
            
            self.logger.info(f"Waiting {step.wait_seconds} seconds for step {step.step_id}")
            time.sleep(step.wait_seconds)
            
            if step.coordinates:
                if self.validate_coordinates(step.coordinates):
                    self.logger.info(f"Step {step.step_id} completed successfully")
                    return True
                else:
                    self.logger.warning(f"Coordinate validation failed for step {step.step_id}")
                    time.sleep(5)
                    continue
            else:
                self.logger.info(f"Step {step.step_id} completed (no coordinate validation)")
                return True
        
        self.logger.error(f"Step {step.step_id} failed after {max_attempts} attempts")
        return False
    
    def start_navigation(self):
        if self.is_navigating:
            self.logger.warning("Navigation already in progress")
            return False
            
        if not self.steps:
            self.logger.error("No navigation steps configured")
            return False
            
        self.is_navigating = True
        self.current_step_index = 0
        
        self.navigation_thread = threading.Thread(target=self._navigation_loop, daemon=True)
        self.navigation_thread.start()
        
        return True
    
    def stop_navigation(self):
        self.is_navigating = False
        if self.navigation_thread:
            self.navigation_thread.join(timeout=1.0)
    
    def _navigation_loop(self):
        self.logger.info("Starting navigation sequence")
        
        while self.is_navigating and self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            
            if not step.is_active:
                self.current_step_index += 1
                continue
            
            if self.execute_step(step):
                self.current_step_index += 1
            else:
                self.logger.error(f"Navigation failed at step {step.step_id}")
                break
        
        if self.current_step_index >= len(self.steps):
            self.logger.info("Navigation sequence completed successfully")
            self.current_step_index = 0
        
        self.is_navigating = False
    
    def get_steps_data(self):
        return [step.to_dict() for step in self.steps]
    
    def load_steps_data(self, steps_data):
        self.steps = [NavigationStep.from_dict(data) for data in steps_data]
        for step in self.steps:
            step.load_template()
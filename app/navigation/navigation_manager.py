import time
import cv2
import numpy as np
import logging
import os
import re
import threading
from .enhanced_coordinate_validator import EnhancedCoordinateValidator

logger = logging.getLogger('PokeXHelper')

class NavigationManager:
    def __init__(self, mouse_controller, minimap_area, settings=None):
        self.mouse_controller = mouse_controller
        self.minimap_area = minimap_area
        self.steps = []
        self.current_step_index = 0
        self.is_navigating = False
        self.navigation_thread = None
        self.stop_navigation_flag = False
        self.logger = logger
        
        self.next_step_id = 1
        
        self.ui_log_callback = None
        
        self.settings = settings or {}
        self.coordinate_validation_enabled = self.settings.get("helper_settings", {}).get("coordinate_validation", True)
        self.coordinate_tolerance = 15
        
        self.coordinate_area = None
        
        self.coordinate_validator = EnhancedCoordinateValidator(debug_enabled=True)
    
    def set_ui_log_callback(self, callback):
        """Set callback function for UI logging"""
        self.ui_log_callback = callback
    
    def log(self, message):
        """Log message to UI if callback is set"""
        if self.ui_log_callback:
            self.ui_log_callback(message)
        self.logger.info(message)
    
    def set_coordinate_area(self, coordinate_area_selector):
        """Set the coordinate area selector"""
        self.coordinate_area = coordinate_area_selector
    
    def add_step(self, name, coordinates="", wait_seconds=3.0):
        from .navigation_step import NavigationStep
        
        step = NavigationStep(
            step_id=self.next_step_id,
            name=name,
            coordinates=coordinates,
            wait_seconds=wait_seconds
        )
        
        self.steps.append(step)
        self.next_step_id += 1
        
        self.logger.info(f"Added step {step.step_id}: '{step.name}' with icon path: {step.icon_image_path}")
        return step
    
    def remove_step(self, step_id):
        step = next((s for s in self.steps if s.step_id == step_id), None)
        if step:
            if step.icon_image_path and os.path.exists(step.icon_image_path):
                try:
                    os.remove(step.icon_image_path)
                    self.logger.info(f"Deleted icon file: {step.icon_image_path}")
                except Exception as e:
                    self.logger.error(f"Failed to delete icon file: {e}")
            
            self.steps.remove(step)
            self.logger.info(f"Removing step {step_id}: '{step.name}'")
            self.logger.info(f"Step {step_id} removed, remaining steps: {len(self.steps)}")
    
    def find_step_icon_in_minimap(self, step, threshold=0.8):
        if step.template_image is None:
            return None
            
        if not self.minimap_area.is_setup():
            return None
            
        try:
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                return None
            
            minimap_cv = cv2.cvtColor(np.array(minimap_image), cv2.COLOR_RGB2BGR)
            
            result = cv2.matchTemplate(minimap_cv, step.template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                template_height, template_width = step.template_image.shape[:2]
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                
                minimap_x = self.minimap_area.x1 + center_x
                minimap_y = self.minimap_area.y1 + center_y
                
                return (minimap_x, minimap_y, max_val)
            
        except Exception as e:
            self.logger.error(f"Error finding step icon: {e}")
        
        return None
    
    def extract_coordinates_from_coordinate_area(self):
        """Extract coordinates using enhanced validator"""
        if not self.coordinate_area or not self.coordinate_area.is_setup():
            return None
        
        try:
            coord_image = self.coordinate_area.get_current_screenshot_region()
            if coord_image is None:
                return None
            
            coordinates = self.coordinate_validator.extract_coordinates_from_image(coord_image)
            
            if coordinates:
                self.logger.info(f"Extracted coordinates from coordinate area: {coordinates}")
                return coordinates
            else:
                self.logger.warning("Failed to extract coordinates from coordinate area")
                return None
        
        except Exception as e:
            self.logger.error(f"Error extracting coordinates from coordinate area: {e}")
            return None
    
    def validate_step_completion(self, step):
        """Validate step completion using coordinate area if configured"""
        try:
            if not self.coordinate_validation_enabled:
                self.logger.debug("Coordinate validation disabled, skipping")
                return True
            
            if not step.coordinates:
                self.logger.debug("No coordinates specified for validation")
                return True
            
            self.logger.info(f" Validating completion of step {step.step_id}: '{step.name}'")
            self.logger.info(f" Step has coordinate validation: {step.coordinates}")
            
            expected = self._parse_expected_coordinates(step.coordinates)
            if not expected:
                self.logger.warning(f"Could not parse expected coordinates: {step.coordinates}")
                return True
            
            if self.coordinate_area and self.coordinate_area.is_setup():
                return self._validate_with_coordinate_area(step, expected)
            else:
                self.logger.warning("No coordinate validation area configured")
                return True
                
        except Exception as e:
            self.logger.error(f"Error validating step completion: {e}")
            return True
    
    def _validate_with_coordinate_area(self, step, expected):
        """Validate using coordinate area with enhanced OCR"""
        max_attempts = 4
        
        for attempt in range(max_attempts):
            try:
                coord_image = self.coordinate_area.get_current_screenshot_region()
                if coord_image is None:
                    self.logger.warning(f"Could not capture coordinate area on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                    continue
                
                coordinates = self.coordinate_validator.extract_coordinates_from_image(
                    coord_image, expected_coords=expected
                )
                
                if coordinates:
                    exp_x, exp_y = expected[0], expected[1]
                    act_x, act_y = coordinates[0], coordinates[1]
                    
                    x_diff = abs(act_x - exp_x)
                    y_diff = abs(act_y - exp_y)
                    
                    self.logger.info(f" Coordinate check: Expected ({exp_x}, {exp_y}), Actual ({act_x}, {act_y})")
                    self.logger.info(f" X difference: {x_diff}, Y difference: {y_diff} (margin: {self.coordinate_tolerance})")
                    
                    if x_diff <= self.coordinate_tolerance and y_diff <= self.coordinate_tolerance:
                        self.logger.info(f" Coordinate validation successful on attempt {attempt + 1}")
                        return True
                    else:
                        self.logger.info(f" Coordinate validation failed on attempt {attempt + 1}, retrying...")
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)
                else:
                    self.logger.info(f" Could not extract coordinates on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                        
            except Exception as e:
                self.logger.error(f"Error in coordinate validation attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
        
        self.logger.warning(f" Coordinate validation failed after {max_attempts} attempts")
        return False
    
    def _parse_expected_coordinates(self, coord_string):
        """Parse expected coordinate string"""
        try:
            patterns = [
                r'\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*',
                r'\((\d+),\s*(\d+),\s*(\d+)\)',
                r'(\d{4}),\s*(\d{4}),\s*(\d+)',
                r'\((\d{4}),(\d{4}),(\d+)\)',
                r'(\d{4}),(\d{4}),(\d+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, coord_string)
                if matches:
                    try:
                        x, y, z = matches[0]
                        return (int(x), int(y), int(z))
                    except (ValueError, IndexError):
                        continue
            
            numbers = re.findall(r'\d{4}', coord_string)
            if len(numbers) >= 2:
                try:
                    return (int(numbers[0]), int(numbers[1]), 6)
                except ValueError:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing coordinates: {e}")
            return None
    
    def execute_step(self, step):
        try:
            self.logger.info(f" Executing step {step.step_id}: '{step.name}'")
            
            location = self.find_step_icon_in_minimap(step, threshold=0.7)
            if not location:
                self.logger.warning(f" Step {step.step_id} icon not found in minimap")
                return False
                
            x, y, confidence = location
            self.logger.info(f" Found step {step.step_id} icon at ({x}, {y}) with {confidence:.1%} confidence")
            
            if self.mouse_controller.click_at(x, y):
                self.logger.info(f" Clicked at ({x}, {y}) for step {step.step_id}")
                
                screen_width = 3440
                screen_height = 1440
                center_x = screen_width // 2
                center_y = screen_height // 2
                self.mouse_controller.move_to(center_x, center_y)
                self.logger.info(f" Moved mouse to screen center ({center_x}, {center_y})")
                
                self.logger.info(f" Waiting {step.wait_seconds} seconds for step completion")
                time.sleep(step.wait_seconds)
                
                return self.validate_step_completion(step)
            else:
                self.logger.error(f" Failed to click at ({x}, {y}) for step {step.step_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            return False
    
    def start_navigation(self):
        if self.is_navigating:
            self.logger.warning("Navigation already in progress")
            return False
            
        if not self.steps:
            self.logger.error("No navigation steps configured")
            return False
        
        if not self.minimap_area.is_setup():
            self.logger.error("Minimap area not configured - cannot start navigation")
            return False
        
        valid_steps = [step for step in self.steps if step.is_active and step.template_image is not None]
        if not valid_steps:
            self.logger.error("No valid steps with icons configured")
            return False
            
        self.logger.info(f"Starting navigation with {len(valid_steps)} valid steps")
        self.is_navigating = True
        self.stop_navigation_flag = False
        self.current_step_index = 0
        
        self.navigation_thread = threading.Thread(target=self._navigation_loop, daemon=True)
        self.navigation_thread.start()
        
        return True
    
    def stop_navigation(self):
        self.logger.info("Stopping navigation...")
        self.stop_navigation_flag = True
        self.is_navigating = False
        
        if self.navigation_thread and self.navigation_thread.is_alive():
            self.navigation_thread.join(timeout=2.0)
        
        self.logger.info("Navigation stopped")
    
    def _navigation_loop(self):
        """Main navigation loop with enhanced coordinate validation"""
        self.logger.info(f" Starting navigation sequence with {len(self.steps)} steps")
        
        active_steps = [step for step in self.steps if step.is_active]
        ready_steps = [step for step in active_steps if step.template_image is not None]
        
        self.logger.info(f" Found {len(active_steps)} active steps, {len(ready_steps)} ready with icons")
        
        if not ready_steps:
            self.logger.error("No steps with valid icons found")
            self.is_navigating = False
            return
        
        try:
            while self.is_navigating and not self.stop_navigation_flag:
                
                for step_index, step in enumerate(ready_steps):
                    if self.stop_navigation_flag:
                        break
                    
                    self.logger.info(f" Processing step {step_index+1}/{len(ready_steps)}: '{step.name}'")
                    
                    if self.execute_step(step):
                        self.logger.info(f" Step {step.step_id} '{step.name}' completed successfully")
                    else:
                        self.logger.error(f" Navigation failed at step {step.step_id} '{step.name}'")
                
                if not self.stop_navigation_flag:
                    time.sleep(1)
                    self.logger.info(" Navigation sequence completed - restarting from beginning")
                    
        except Exception as e:
            self.logger.error(f"Error in navigation loop: {e}")
        finally:
            self.logger.info(" Navigation sequence ended")
            self.is_navigating = False
    
    def get_steps_data(self):
        try:
            steps_data = []
            for step in self.steps:
                try:
                    step_dict = step.to_dict()
                    steps_data.append(step_dict)
                except Exception as e:
                    self.logger.error(f"Error serializing step {step.step_id}: {e}")
                    
            self.logger.info(f"Serialized {len(steps_data)} steps for saving")
            return steps_data
        except Exception as e:
            self.logger.error(f"Error getting steps data: {e}")
            return []
    
    def load_steps_data(self, steps_data):
        from .navigation_step import NavigationStep
        
        self.steps = []
        max_step_id = 0
        
        for data in steps_data:
            step = NavigationStep.from_dict(data)
            if step.load_template():
                self.logger.debug(f"Loaded template for step {step.step_id}: {step.name}")
            else:
                self.logger.warning(f"Could not load template for step {step.step_id}: {step.name}")
            
            self.steps.append(step)
            max_step_id = max(max_step_id, step.step_id)
        
        self.next_step_id = max_step_id + 1
        self.logger.info(f"Loaded {len(self.steps)} navigation steps")
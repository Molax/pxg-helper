import time
import cv2
import numpy as np
import logging
import os
import re
import threading
import math
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
                self.logger.debug(f"Extracted coordinates: {coordinates}")
                return coordinates
            else:
                self.logger.debug("No valid coordinates found in coordinate area")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting coordinates from coordinate area: {e}")
            return None
    
    def parse_coordinates(self, coord_string):
        """Parse coordinate string and return (x, y, z) tuple"""
        if not coord_string or not isinstance(coord_string, str):
            return None
            
        try:
            coord_string = coord_string.strip()
            
            patterns = [
                r'(\d{4}),\s*(\d{4}),\s*(\d+)',
                r'(\d{4})\s+(\d{4})\s+(\d+)',
                r'(\d{4}):(\d{4}):(\d+)',
                r'X:\s*(\d{4})\s*Y:\s*(\d{4})\s*Z:\s*(\d+)',
                r'x:\s*(\d{4})\s*y:\s*(\d{4})\s*z:\s*(\d+)',
                r'\[(\d{4}),\s*(\d{4}),\s*(\d+)\]',
                r'\((\d{4}),\s*(\d{4}),\s*(\d+)\)'
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
    
    def calculate_distance(self, coord1, coord2):
        """Calculate distance between two coordinates"""
        if not coord1 or not coord2:
            return float('inf')
        
        x1, y1 = coord1[:2]
        x2, y2 = coord2[:2]
        
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance
    
    def execute_step(self, step, max_retries=2):
        """Execute a step with retry logic"""
        for attempt in range(max_retries):
            try:
                attempt_msg = f" (attempt {attempt + 1}/{max_retries})" if max_retries > 1 else ""
                self.logger.info(f" Executing step {step.step_id}: '{step.name}'{attempt_msg}")
                
                location = self.find_step_icon_in_minimap(step, threshold=0.7)
                if not location:
                    self.logger.warning(f" Step {step.step_id} icon not found in minimap{attempt_msg}")
                    if attempt < max_retries - 1:
                        self.logger.info(f" Retrying step {step.step_id} in 2 seconds...")
                        time.sleep(2)
                        continue
                    return False
                    
                x, y, confidence = location
                self.logger.info(f" Found step {step.step_id} icon at ({x}, {y}) with {confidence:.1%} confidence{attempt_msg}")
                
                if self.mouse_controller.click_at(x, y):
                    self.logger.info(f" Clicked at ({x}, {y}) for step {step.step_id}{attempt_msg}")
                    
                    screen_width = 3440
                    screen_height = 1440
                    center_x = screen_width // 2
                    center_y = screen_height // 2
                    self.mouse_controller.move_to(center_x, center_y)
                    self.logger.info(f" Moved mouse to screen center ({center_x}, {center_y})")
                    
                    self.logger.info(f" Waiting {step.wait_seconds} seconds for step completion")
                    time.sleep(step.wait_seconds)
                    
                    validation_result = self.validate_step_completion(step)
                    if validation_result:
                        return True
                    elif attempt < max_retries - 1:
                        self.logger.warning(f" Step {step.step_id} validation failed, retrying...")
                        time.sleep(1)
                        continue
                    else:
                        self.logger.error(f" Step {step.step_id} validation failed after {max_retries} attempts")
                        return False
                else:
                    self.logger.error(f" Failed to click at ({x}, {y}) for step {step.step_id}{attempt_msg}")
                    if attempt < max_retries - 1:
                        self.logger.info(f" Retrying click for step {step.step_id}...")
                        time.sleep(1)
                        continue
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error executing step {step.step_id}{attempt_msg}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f" Retrying step {step.step_id} due to error...")
                    time.sleep(2)
                    continue
                return False
        
        return False
    
    def validate_step_completion(self, step):
        """Validate if step was completed successfully"""
        try:
            if self.coordinate_validation_enabled and self.coordinate_area:
                time.sleep(0.5)
                
                current_coords = self.extract_coordinates_from_coordinate_area()
                if not current_coords:
                    self.logger.warning(f"Could not extract coordinates for validation")
                    return True
                
                target_coords = self.parse_coordinates(step.coordinates)
                if not target_coords:
                    self.logger.debug(f"No target coordinates configured for step {step.step_id}")
                    return True
                
                distance = self.calculate_distance(current_coords, target_coords)
                
                if distance <= self.coordinate_tolerance:
                    self.logger.info(f"[SUCCESS] Step {step.step_id} validated - reached target coordinates")
                    return True
                else:
                    self.logger.warning(f"[WARNING] Step {step.step_id} validation failed - distance: {distance}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating step completion: {e}")
            return True
    
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
        """Main navigation loop with enhanced coordinate validation and retry logic"""
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
                sequence_success = True
                
                for step_index, step in enumerate(ready_steps):
                    if self.stop_navigation_flag:
                        break
                    
                    self.logger.info(f" Processing step {step_index+1}/{len(ready_steps)}: '{step.name}'")
                    
                    step_success = self.execute_step(step, max_retries=2)
                    
                    if step_success:
                        self.logger.info(f" Step {step.step_id} '{step.name}' completed successfully")
                    else:
                        self.logger.error(f" Navigation failed at step {step.step_id} '{step.name}' after retries")
                        sequence_success = False
                        break
                
                if sequence_success and not self.stop_navigation_flag:
                    time.sleep(1)
                    self.logger.info(" Navigation sequence completed successfully - restarting from beginning")
                elif not self.stop_navigation_flag:
                    self.logger.warning(" Navigation sequence failed - retrying from beginning in 5 seconds")
                    time.sleep(5)
                    
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
    
    def preview_step_detection(self, step):
        """Test step detection and return human-readable result"""
        if step.template_image is None:
            return "No icon configured for this step"
        
        if not self.minimap_area.is_setup():
            return "Minimap area not configured"
        
        try:
            result = self.find_step_icon_in_minimap(step, threshold=0.6)
            if result:
                x, y, confidence = result
                return f"[SUCCESS] Icon found at ({x}, {y})\nConfidence: {confidence:.1%}"
            else:
                return "[WARNING] Icon not found in minimap\nTry lowering the detection threshold or reconfiguring the icon"
        except Exception as e:
            return f"Error during detection: {e}"

    def save_step_icon(self, step, icon_bounds):
        """Save step icon from selected area"""
        try:
            x1, y1, x2, y2 = icon_bounds
            
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                self.logger.error("Could not capture minimap image")
                return False
            
            rel_x1 = x1 - self.minimap_area.x1
            rel_y1 = y1 - self.minimap_area.y1
            rel_x2 = x2 - self.minimap_area.x1
            rel_y2 = y2 - self.minimap_area.y1
            
            rel_x1 = max(0, rel_x1)
            rel_y1 = max(0, rel_y1)
            rel_x2 = min(minimap_image.width, rel_x2)
            rel_y2 = min(minimap_image.height, rel_y2)
            
            if rel_x2 <= rel_x1 or rel_y2 <= rel_y1:
                self.logger.error("Invalid icon bounds")
                return False
            
            icon_image = minimap_image.crop((rel_x1, rel_y1, rel_x2, rel_y2))
            
            icons_dir = "assets/navigation_icons"
            if not os.path.exists(icons_dir):
                os.makedirs(icons_dir)
            
            timestamp = int(time.time() * 1000)
            filename = f"step_{step.step_id}_{timestamp}.png"
            icon_path = os.path.join(icons_dir, filename)
            
            if step.icon_image_path and os.path.exists(step.icon_image_path):
                try:
                    os.remove(step.icon_image_path)
                    self.logger.info(f"Removed old icon: {step.icon_image_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove old icon: {e}")
            
            icon_image.save(icon_path, "PNG")
            step.icon_image_path = icon_path
            step.icon_bounds = icon_bounds
            
            if step.load_template():
                self.logger.info(f"Saved and loaded icon for step {step.step_id}: {icon_path}")
                return True
            else:
                self.logger.error(f"Failed to load template after saving icon")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving step icon: {e}")
            return False

    def cleanup_unused_icons(self):
        """Clean up unused icon files"""
        try:
            icons_dir = "assets/navigation_icons"
            if not os.path.exists(icons_dir):
                self.logger.info("Icons directory does not exist")
                return
            
            used_files = set()
            for step in self.steps:
                if step.icon_image_path:
                    filename = os.path.basename(step.icon_image_path)
                    used_files.add(filename)
            
            self.logger.info(f"Found {len(used_files)} icon files in use: {used_files}")
            
            cleanup_count = 0
            for filename in os.listdir(icons_dir):
                if filename.endswith('.png') and filename not in used_files:
                    file_path = os.path.join(icons_dir, filename)
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up unused icon file: {filename}")
                        cleanup_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {filename}: {e}")
            
            if cleanup_count == 0:
                self.logger.info("No unused icon files to clean up")
            else:
                self.logger.info(f"Cleaned up {cleanup_count} unused icon files")
                
        except Exception as e:
            self.logger.error(f"Error during icon cleanup: {e}")
            raise
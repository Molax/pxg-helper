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
    def __init__(self, step_id, name="", icon_image_path="", coordinates="", wait_seconds=3.0):
        self.step_id = step_id
        self.name = name or f"Step {step_id}"
        self.icon_image_path = icon_image_path
        self.coordinates = coordinates
        self.wait_seconds = wait_seconds
        self.template_image = None
        self.is_active = True
        self.icon_bounds = None
        
    def load_template(self):
        if not self.icon_image_path:
            return False
            
        if not os.path.exists(self.icon_image_path):
            logger.debug(f"Template file does not exist for step {self.step_id}: {self.icon_image_path}")
            return False
            
        try:
            self.template_image = cv2.imread(self.icon_image_path, cv2.IMREAD_COLOR)
            if self.template_image is not None:
                logger.debug(f"Successfully loaded template for step {self.step_id}")
                return True
            else:
                logger.warning(f"Template image is None for step {self.step_id}: {self.icon_image_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading template for step {self.step_id}: {e}")
            return False
    
    def to_dict(self):
        return {
            "step_id": self.step_id,
            "name": self.name,
            "icon_image_path": self.icon_image_path,
            "coordinates": self.coordinates,
            "wait_seconds": self.wait_seconds,
            "is_active": self.is_active,
            "icon_bounds": self.icon_bounds
        }
    
    @classmethod
    def from_dict(cls, data):
        step = cls(
            data.get("step_id", 1),
            data.get("name", ""),
            data.get("icon_image_path", ""),
            data.get("coordinates", ""),
            data.get("wait_seconds", 3.0)
        )
        step.is_active = data.get("is_active", True)
        step.icon_bounds = data.get("icon_bounds")
        return step

class NavigationManager:
    def __init__(self, minimap_area_selector, battle_area_selector, mouse_controller):
        self.minimap_area = minimap_area_selector
        self.battle_area = battle_area_selector
        self.mouse_controller = mouse_controller
        self.steps = []
        self.is_navigating = False
        self.current_step_index = 0
        self.navigation_thread = None
        self.stop_navigation_flag = False
        self.logger = logger
        
        self.next_step_id = 1
    
    def add_step(self, name, coordinates="", wait_seconds=3.0):
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
    
    def execute_step(self, step):
        try:
            self.logger.info(f"Executing step {step.step_id}: '{step.name}'")
            
            location = self.find_step_icon_in_minimap(step, threshold=0.7)
            if not location:
                self.logger.warning(f"Step {step.step_id} icon not found in minimap")
                return False
                
            x, y, confidence = location
            self.logger.info(f"Found step {step.step_id} icon at ({x}, {y}) with {confidence:.1%} confidence")
            
            if self.mouse_controller.click_at(x, y):
                self.logger.info(f"Clicked at ({x}, {y}) for step {step.step_id}")
                time.sleep(step.wait_seconds)
                return self.validate_step_completion(step)
            else:
                self.logger.error(f"Failed to click at ({x}, {y}) for step {step.step_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            return False
    
    def validate_step_completion(self, step):
        try:
            time.sleep(0.5)
            
            if self.battle_area.is_setup():
                battle_image = self.battle_area.get_current_screenshot_region()
                if battle_image:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        battle_image.save(temp_file.name)
                        temp_path = temp_file.name
                    
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating step completion: {e}")
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
        self.logger.info(f"Starting navigation sequence with {len(self.steps)} steps")
        
        active_steps = [step for step in self.steps if step.is_active]
        ready_steps = [step for step in active_steps if step.template_image is not None]
        
        self.logger.info(f"Found {len(active_steps)} active steps, {len(ready_steps)} ready with icons")
        
        if not ready_steps:
            self.logger.error("No steps with valid icons found")
            self.is_navigating = False
            return
        
        try:
            while self.is_navigating and not self.stop_navigation_flag and self.current_step_index < len(self.steps):
                step = self.steps[self.current_step_index]
                
                self.logger.info(f"Processing step {self.current_step_index + 1}/{len(self.steps)}: '{step.name}'")
                
                if not step.is_active:
                    self.logger.info(f"Step {step.step_id} '{step.name}' is inactive, skipping")
                    self.current_step_index += 1
                    continue
                
                if not step.template_image:
                    self.logger.warning(f"Step {step.step_id} '{step.name}' has no icon, skipping")
                    self.current_step_index += 1
                    continue
                
                if self.execute_step(step):
                    self.logger.info(f"Step {step.step_id} '{step.name}' completed successfully")
                    self.current_step_index += 1
                else:
                    self.logger.error(f"Navigation failed at step {step.step_id} '{step.name}'")
                    break
                
                if self.is_navigating and not self.stop_navigation_flag:
                    time.sleep(1.0)
            
            if self.current_step_index >= len(self.steps) and not self.stop_navigation_flag:
                self.logger.info("Navigation sequence completed successfully")
                self.current_step_index = 0
            
        except Exception as e:
            self.logger.error(f"Error in navigation loop: {e}")
        finally:
            self.logger.info("Navigation sequence ended")
            self.is_navigating = False
            self.stop_navigation_flag = False
    
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
        if not self.minimap_area.is_setup():
            return "Minimap area not configured"
            
        location = self.find_step_icon_in_minimap(step, threshold=0.6)
        if location:
            x, y, confidence = location
            return f"Found at ({x}, {y}) - {confidence:.1%} match"
        else:
            return "Not found in minimap area"
    
    def cleanup_unused_icons(self):
        try:
            icons_dir = "assets/navigation_icons"
            if not os.path.exists(icons_dir):
                return
                
            used_files = {step.icon_image_path for step in self.steps if step.icon_image_path}
            
            for filename in os.listdir(icons_dir):
                file_path = os.path.join(icons_dir, filename)
                if file_path not in used_files and filename.startswith("step_"):
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up unused icon: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to cleanup icon {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during icon cleanup: {e}")
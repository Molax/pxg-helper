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
        self.logger = logging.getLogger('PokeXHelper')
        
        self.steps = []
        self.current_step_index = 0
        self.is_navigating = False
        self.navigation_thread = None
        
        self.step_icons_dir = "assets/navigation_icons"
        if not os.path.exists(self.step_icons_dir):
            os.makedirs(self.step_icons_dir)
    
    def cleanup_unused_icons(self):
        try:
            if not os.path.exists(self.step_icons_dir):
                self.logger.info("Icons directory does not exist, nothing to clean up")
                return
            
            used_files = set()
            for step in self.steps:
                if hasattr(step, 'icon_image_path') and step.icon_image_path:
                    filename = os.path.basename(step.icon_image_path)
                    if filename:
                        used_files.add(filename)
            
            self.logger.info(f"Found {len(used_files)} icon files in use: {used_files}")
            
            cleaned_count = 0
            for filename in os.listdir(self.step_icons_dir):
                if filename.endswith('.png') and filename not in used_files:
                    file_path = os.path.join(self.step_icons_dir, filename)
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up unused icon file: {filename}")
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.warning(f"Could not delete unused icon {filename}: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} unused icon files")
            else:
                self.logger.info("No unused icon files to clean up")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up unused icons: {e}", exc_info=True)
    
    def add_step(self, name="", coordinates="", wait_seconds=3.0):
        step_id = len(self.steps) + 1
        icon_filename = f"step_{step_id}_{int(time.time())}.png"
        icon_path = os.path.join(self.step_icons_dir, icon_filename)
        
        step = NavigationStep(step_id, name, icon_path, coordinates, wait_seconds)
        self.steps.append(step)
        
        self.logger.info(f"Added step {step_id}: '{name}' with icon path: {icon_path}")
        return step
    
    def remove_step(self, step_id):
        step_to_remove = None
        for step in self.steps:
            if step.step_id == step_id:
                step_to_remove = step
                break
        
        if step_to_remove:
            self.logger.info(f"Removing step {step_id}: '{step_to_remove.name}'")
            
            if hasattr(step_to_remove, 'icon_image_path') and step_to_remove.icon_image_path and os.path.exists(step_to_remove.icon_image_path):
                try:
                    os.remove(step_to_remove.icon_image_path)
                    self.logger.info(f"Deleted icon file: {step_to_remove.icon_image_path}")
                except Exception as e:
                    self.logger.warning(f"Could not delete icon file: {e}")
            
            self.steps = [step for step in self.steps if step.step_id != step_id]
            self._reindex_steps()
            self.logger.info(f"Step {step_id} removed, remaining steps: {len(self.steps)}")
        else:
            self.logger.warning(f"Step {step_id} not found for removal")
    
    def _reindex_steps(self):
        for i, step in enumerate(self.steps):
            step.step_id = i + 1
    
    def save_step_icon(self, step, icon_bounds):
        try:
            x1, y1, x2, y2 = icon_bounds
            
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
            
            os.makedirs(os.path.dirname(step.icon_image_path), exist_ok=True)
            screenshot.save(step.icon_image_path)
            step.icon_bounds = icon_bounds
            
            if step.load_template():
                self.logger.info(f"Saved and loaded icon for step {step.step_id}: {step.icon_image_path}")
                return True
            else:
                self.logger.error(f"Failed to load template after saving for step {step.step_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error saving step icon: {e}", exc_info=True)
            return False
    
    def find_step_icon_in_minimap(self, step, threshold=0.8):
        if not step.load_template():
            self.logger.warning(f"Could not load template for step {step.step_id}")
            return None
            
        if not self.minimap_area.is_setup():
            self.logger.error("Minimap area not configured")
            return None
            
        try:
            minimap_image = self.minimap_area.get_current_screenshot_region()
            if minimap_image is None:
                self.logger.error("Could not capture minimap area")
                return None
            
            minimap_np = np.array(minimap_image)
            minimap_gray = cv2.cvtColor(minimap_np, cv2.COLOR_RGB2GRAY)
            template_gray = cv2.cvtColor(step.template_image, cv2.COLOR_BGR2GRAY)
            
            self.logger.info(f"Searching for step {step.step_id} icon in minimap area")
            self.logger.debug(f"Minimap size: {minimap_gray.shape}, Template size: {template_gray.shape}")
            
            result = cv2.matchTemplate(minimap_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            locations = np.where(result >= threshold)
            
            if len(locations[0]) > 0:
                max_val = np.max(result)
                max_loc = np.unravel_index(np.argmax(result), result.shape)
                
                h, w = template_gray.shape
                minimap_center_x = max_loc[1] + w // 2
                minimap_center_y = max_loc[0] + h // 2
                
                screen_x = self.minimap_area.x1 + minimap_center_x
                screen_y = self.minimap_area.y1 + minimap_center_y
                
                self.logger.info(f"Found step {step.step_id} icon at minimap ({minimap_center_x}, {minimap_center_y}) -> screen ({screen_x}, {screen_y}) with confidence {max_val:.3f}")
                return (screen_x, screen_y, max_val)
            
            self.logger.warning(f"Step {step.step_id} icon not found in minimap (threshold: {threshold})")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding step icon in minimap: {e}", exc_info=True)
            return None
    
    def click_step_icon(self, step):
        location = self.find_step_icon_in_minimap(step)
        if location is None:
            self.logger.warning(f"Step {step.step_id} '{step.name}' icon not found in minimap")
            return False
            
        try:
            x, y, confidence = location
            self.logger.info(f"Clicking step {step.step_id} '{step.name}' icon at ({x}, {y}) with confidence {confidence:.3f}")
            
            success = self.mouse_controller.click_left(x, y)
            if success:
                self.logger.info(f"Successfully clicked step {step.step_id} icon")
            else:
                self.logger.error(f"Failed to click step {step.step_id} icon")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error clicking step icon: {e}", exc_info=True)
            return False
    
    def execute_step(self, step):
        max_attempts = 3
        
        for attempt in range(max_attempts):
            self.logger.info(f"Executing step {step.step_id}: '{step.name}' (attempt {attempt + 1})")
            
            if not self.click_step_icon(step):
                self.logger.warning(f"Failed to click step {step.step_id} icon")
                time.sleep(2)
                continue
            
            self.logger.info(f"Waiting {step.wait_seconds} seconds for step {step.step_id} to complete")
            time.sleep(step.wait_seconds)
            
            if step.coordinates:
                if self.validate_step_completion(step):
                    self.logger.info(f"Step {step.step_id} completed successfully")
                    return True
                else:
                    self.logger.warning(f"Step {step.step_id} validation failed")
                    time.sleep(2)
                    continue
            else:
                self.logger.info(f"Step {step.step_id} completed (no validation)")
                return True
        
        self.logger.error(f"Step {step.step_id} failed after {max_attempts} attempts")
        return False
    
    def validate_step_completion(self, step):
        if not step.coordinates:
            return True
            
        try:
            if self.battle_area.is_setup():
                battle_image = self.battle_area.get_current_screenshot_region()
                if battle_image:
                    return True
            
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
        self.current_step_index = 0
        
        self.navigation_thread = threading.Thread(target=self._navigation_loop, daemon=True)
        self.navigation_thread.start()
        
        return True
    
    def stop_navigation(self):
        self.is_navigating = False
        if self.navigation_thread:
            self.navigation_thread.join(timeout=1.0)
    
    def _navigation_loop(self):
        self.logger.info(f"Starting navigation sequence with {len(self.steps)} steps")
        
        active_steps = [step for step in self.steps if step.is_active]
        ready_steps = [step for step in active_steps if step.template_image is not None]
        
        self.logger.info(f"Found {len(active_steps)} active steps, {len(ready_steps)} ready with icons")
        
        if not ready_steps:
            self.logger.error("No steps with valid icons found")
            self.is_navigating = False
            return
        
        while self.is_navigating and self.current_step_index < len(self.steps):
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
            
            if self.is_navigating:
                time.sleep(1.0)
        
        if self.current_step_index >= len(self.steps):
            self.logger.info("Navigation sequence completed successfully")
            self.current_step_index = 0
        
        self.logger.info("Navigation sequence ended")
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
        self.steps = []
        for data in steps_data:
            step = NavigationStep.from_dict(data)
            if step.load_template():
                self.logger.debug(f"Loaded template for step {step.step_id}: {step.name}")
            else:
                self.logger.warning(f"Could not load template for step {step.step_id}: {step.name}")
            self.steps.append(step)
    
    def preview_step_detection(self, step):
        if not self.minimap_area.is_setup():
            return "Minimap area not configured"
            
        location = self.find_step_icon_in_minimap(step, threshold=0.6)
        if location:
            x, y, confidence = location
            return f"Found at ({x}, {y}) - {confidence:.1%} match"
        else:
            return "Not found in minimap area"
import os
import time
import logging
import threading
import cv2
import numpy as np
from PIL import Image, ImageGrab

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
        
        if not self.icon_image_path:
            self.icon_image_path = f"assets/navigation_icons/step_{step_id}_{int(time.time() * 1000)}.png"
        
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
        self.ui_log_callback = None
        
        self.next_step_id = 1
    
    def set_ui_log_callback(self, callback):
        self.ui_log_callback = callback
    
    def log_to_ui(self, message, level="INFO"):
        if self.ui_log_callback:
            self.ui_log_callback(message)
        
        clean_message = message.encode('ascii', 'ignore').decode('ascii')
        
        if level == "INFO":
            self.logger.info(clean_message)
        elif level == "WARNING":
            self.logger.warning(clean_message)
        elif level == "ERROR":
            self.logger.error(clean_message)
        elif level == "DEBUG":
            self.logger.debug(clean_message)
    
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
    
    def save_step_icon(self, step, icon_bounds):
        try:
            x1, y1, x2, y2 = icon_bounds
            
            os.makedirs("assets/navigation_icons", exist_ok=True)
            
            icon_image = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
            icon_image.save(step.icon_image_path)
            
            step.icon_bounds = icon_bounds
            
            if step.load_template():
                self.logger.info(f"Saved and loaded icon for step {step.step_id}: {step.icon_image_path}")
                return True
            else:
                self.logger.error(f"Failed to load template after saving for step {step.step_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving step icon: {e}")
            return False
    
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
            self.log_to_ui(f"🎯 Executing step {step.step_id}: '{step.name}'")
            
            location = self.find_step_icon_in_minimap(step, threshold=0.7)
            if not location:
                self.log_to_ui(f"❌ Step {step.step_id} icon not found in minimap", "WARNING")
                return False
                
            x, y, confidence = location
            self.log_to_ui(f"✅ Found step {step.step_id} icon at ({x}, {y}) with {confidence:.1%} confidence")
            
            if self.mouse_controller.click_left(x, y):
                self.log_to_ui(f"🖱️ Clicked at ({x}, {y}) for step {step.step_id}")
                
                import ctypes
                screen_width = ctypes.windll.user32.GetSystemMetrics(0)
                screen_height = ctypes.windll.user32.GetSystemMetrics(1)
                center_x = screen_width // 2
                center_y = screen_height // 2
                
                self.mouse_controller.move_to(center_x, center_y)
                self.log_to_ui(f"🖱️ Moved mouse to screen center ({center_x}, {center_y})")
                
                self.log_to_ui(f"⏱️ Waiting {step.wait_seconds} seconds for step completion")
                time.sleep(step.wait_seconds)
                return self.validate_step_completion(step)
            else:
                self.log_to_ui(f"❌ Failed to click at ({x}, {y}) for step {step.step_id}", "ERROR")
                return False
                
        except Exception as e:
            self.log_to_ui(f"❌ Error executing step {step.step_id}: {e}", "ERROR")
            return False
    
    def extract_coordinates_from_image(self, image):
        try:
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Use a lower threshold to capture more text but try different values
            thresholds = [180, 200, 160, 220]
            
            for threshold in thresholds:
                _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
                
                # Clean up the image
                kernel = np.ones((1,1), np.uint8)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                
                try:
                    import pytesseract
                    
                    tesseract_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                        r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.environ.get('USERNAME', '')),
                        'tesseract'
                    ]
                    
                    for path in tesseract_paths:
                        if os.path.exists(path) or path == 'tesseract':
                            pytesseract.pytesseract.tesseract_cmd = path
                            break
                    
                    # Try OCR on the cleaned image directly
                    configs = [
                        '--psm 8 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 7 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 6 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 13',
                        '--psm 8'
                    ]
                    
                    for config in configs:
                        try:
                            text = pytesseract.image_to_string(thresh, config=config).strip()
                            
                            if text:
                                self.log_to_ui(f"📄 OCR detected text (threshold {threshold}): '{text}'")
                            
                            import re
                            # Look for 3D coordinates with exactly 4 digits: (3959, 3632, 6)
                            coord_match = re.search(r'\((\d{4}),\s*(\d{4}),\s*\d+\)', text)
                            if coord_match:
                                coord_x = int(coord_match.group(1))
                                coord_y = int(coord_match.group(2))
                                self.log_to_ui(f"✅ Successfully extracted 3D coordinates: ({coord_x}, {coord_y})")
                                return (coord_x, coord_y)
                            
                            # Look for 2D coordinates with exactly 4 digits: (3959, 3632)
                            coord_match = re.search(r'\((\d{4}),\s*(\d{4})\)', text)
                            if coord_match:
                                coord_x = int(coord_match.group(1))
                                coord_y = int(coord_match.group(2))
                                self.log_to_ui(f"✅ Successfully extracted 2D coordinates: ({coord_x}, {coord_y})")
                                return (coord_x, coord_y)
                            
                            # Try to find consecutive 4-digit numbers in sequence
                            clean_text = re.sub(r'[^\d,()]', '', text)
                            four_digit_matches = re.findall(r'\d{4}', clean_text)
                            if len(four_digit_matches) >= 2:
                                coord_x = int(four_digit_matches[0])
                                coord_y = int(four_digit_matches[1])
                                # Validate coordinates are in reasonable range
                                if 1000 <= coord_x <= 9999 and 1000 <= coord_y <= 9999:
                                    self.log_to_ui(f"✅ Extracted coordinates from 4-digit numbers: ({coord_x}, {coord_y})")
                                    return (coord_x, coord_y)
                                
                        except Exception as config_error:
                            continue
                    
                    if text:
                        self.log_to_ui(f"⚠️ OCR found text: '{text}' but no valid coordinates (threshold {threshold})", "WARNING")
                    
                except Exception as ocr_error:
                    continue
            
            self.log_to_ui(f"⚠️ OCR processing failed on all thresholds", "WARNING")
            return None
            
        except Exception as e:
            self.log_to_ui(f"❌ Error extracting coordinates from image: {e}", "ERROR")
            return None
    
    def get_current_coordinates_simple(self):
        try:
            import ctypes
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            screen_height = ctypes.windll.user32.GetSystemMetrics(1)
            
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            self.mouse_controller.move_to(center_x, center_y)
            time.sleep(0.3)
            
            # Position coordinate area correctly - coordinates appear INSIDE the minimap area at the top
            coord_area_x1 = self.minimap_area.x1 - 50
            coord_area_y1 = self.minimap_area.y1 + 5
            coord_area_x2 = self.minimap_area.x1 + 150
            coord_area_y2 = self.minimap_area.y1 + 35
            
            from PIL import ImageGrab
            coord_screenshot = ImageGrab.grab(bbox=(coord_area_x1, coord_area_y1, coord_area_x2, coord_area_y2), all_screens=True)
            
            coordinates = self.extract_coordinates_from_image(coord_screenshot)
            if coordinates:
                self.log_to_ui(f"📍 Image processing detected coordinates: {coordinates}")
                return coordinates
            
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            debug_path = f"{debug_dir}/coordinate_area_{int(time.time())}.png"
            coord_screenshot.save(debug_path)
            self.log_to_ui(f"📸 Saved coordinate area screenshot: {debug_path}")
            self.log_to_ui(f"📍 Coordinate area bounds: ({coord_area_x1}, {coord_area_y1}) to ({coord_area_x2}, {coord_area_y2})")
            self.log_to_ui(f"📍 Minimap bounds: ({self.minimap_area.x1}, {self.minimap_area.y1}) to ({self.minimap_area.x2}, {self.minimap_area.y2})")
            
            return None
        except Exception as e:
            self.log_to_ui(f"❌ Error in simple coordinate detection: {e}", "ERROR")
            return None
    
    def get_current_coordinates(self):
        try:
            if not self.minimap_area.is_setup():
                return None
            
            import ctypes
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            screen_height = ctypes.windll.user32.GetSystemMetrics(1)
            
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            self.mouse_controller.move_to(center_x, center_y)
            time.sleep(0.5)
            
            # Coordinates appear in the TOP portion of the minimap area, not above it
            coord_area_x1 = self.minimap_area.x1 - 50
            coord_area_y1 = self.minimap_area.y1 + 5
            coord_area_x2 = self.minimap_area.x1 + 150
            coord_area_y2 = self.minimap_area.y1 + 35
            
            try:
                from PIL import ImageGrab
                coord_image = ImageGrab.grab(bbox=(coord_area_x1, coord_area_y1, coord_area_x2, coord_area_y2), all_screens=True)
                
                coordinates = self.extract_coordinates_from_image(coord_image)
                if coordinates:
                    return coordinates
                
                try:
                    import pytesseract
                    
                    # Try different OCR configurations for better coordinate detection
                    configs = [
                        '--psm 8 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 7 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 6 -c tessedit_char_whitelist=0123456789,() ',
                        '--psm 13',
                        '--psm 8'
                    ]
                    
                    for config in configs:
                        text = pytesseract.image_to_string(coord_image, config=config).strip()
                        
                        import re
                        # Look for coordinates with 3 numbers: (xxxx, yyyy, z)
                        coord_match = re.search(r'\((\d{4}),\s*(\d{4}),\s*\d+\)', text)
                        if coord_match:
                            x = int(coord_match.group(1))
                            y = int(coord_match.group(2))
                            self.log_to_ui(f"📍 OCR detected 3D coordinates: ({x}, {y})")
                            return (x, y)
                        
                        # Fallback: Look for coordinates with 2 numbers: (xxxx, yyyy)
                        coord_match = re.search(r'\((\d{4}),\s*(\d{4})\)', text)
                        if coord_match:
                            x = int(coord_match.group(1))
                            y = int(coord_match.group(2))
                            self.log_to_ui(f"📍 OCR detected 2D coordinates: ({x}, {y})")
                            return (x, y)
                    
                    self.log_to_ui(f"📍 OCR text found: '{text}' but no coordinates matched", "WARNING")
                    self.log_to_ui(f"📍 Capture area: ({coord_area_x1}, {coord_area_y1}) to ({coord_area_x2}, {coord_area_y2})", "WARNING")
                    self.log_to_ui(f"📍 Minimap area: ({self.minimap_area.x1}, {self.minimap_area.y1}) to ({self.minimap_area.x2}, {self.minimap_area.y2})", "WARNING")
                    return self.get_current_coordinates_simple()
                except ImportError:
                    self.log_to_ui("⚠️ pytesseract not available, using image processing", "WARNING")
                    return self.get_current_coordinates_simple()
                except Exception as e:
                    self.log_to_ui(f"⚠️ OCR failed: {e}, using image processing", "WARNING")
                    return self.get_current_coordinates_simple()
            
            except Exception as e:
                self.log_to_ui(f"⚠️ Could not capture coordinate area: {e}", "WARNING")
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting current coordinates: {e}")
            return None
    
    def parse_coordinates(self, coord_string):
        try:
            if not coord_string or coord_string.strip() == "":
                return None
            
            parts = coord_string.replace(",", " ").split()
            if len(parts) >= 2:
                x = int(parts[0])
                y = int(parts[1])
                return (x, y)
            return None
        except Exception as e:
            self.logger.error(f"Error parsing coordinates '{coord_string}': {e}")
            return None
    
    def check_coordinates_match(self, expected_coords, actual_coords, margin=2):
        try:
            if not expected_coords or not actual_coords:
                return False
            
            exp_x, exp_y = expected_coords
            act_x, act_y = actual_coords
            
            x_match = abs(exp_x - act_x) <= margin
            y_match = abs(exp_y - act_y) <= margin
            
            self.log_to_ui(f"📊 Coordinate check: Expected ({exp_x}, {exp_y}), Actual ({act_x}, {act_y})")
            self.log_to_ui(f"📏 X difference: {abs(exp_x - act_x)}, Y difference: {abs(exp_y - act_y)} (margin: ±{margin})")
            
            return x_match and y_match
        except Exception as e:
            self.log_to_ui(f"❌ Error checking coordinate match: {e}", "ERROR")
            return False
    
    def validate_step_completion(self, step):
        try:
            self.log_to_ui(f"🔍 Validating completion of step {step.step_id}: '{step.name}'")
            time.sleep(0.5)
            
            if step.coordinates and step.coordinates.strip():
                expected_coords = self.parse_coordinates(step.coordinates)
                if expected_coords:
                    self.log_to_ui(f"📍 Step has coordinate validation: {step.coordinates}")
                    
                    for attempt in range(5):
                        current_coords = self.get_current_coordinates()
                        if current_coords:
                            if self.check_coordinates_match(expected_coords, current_coords):
                                self.log_to_ui(f"✅ Coordinate validation passed on attempt {attempt + 1}")
                                return True
                            else:
                                self.log_to_ui(f"🔄 Coordinate validation failed on attempt {attempt + 1}, retrying...")
                                time.sleep(1.0)
                        else:
                            self.log_to_ui(f"⚠️ Could not get current coordinates on attempt {attempt + 1}", "WARNING")
                            time.sleep(1.0)
                    
                    self.log_to_ui(f"❌ Coordinate validation failed after 5 attempts", "WARNING")
                    return False
                else:
                    self.log_to_ui("⚠️ Step has coordinate string but could not parse, skipping validation", "WARNING")
            else:
                self.log_to_ui("ℹ️ Step has no coordinate validation, assuming success")
            
            if self.battle_area.is_setup():
                battle_image = self.battle_area.get_current_screenshot_region()
                if battle_image:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        battle_image.save(temp_file.name)
                        temp_path = temp_file.name
                    
                    self.logger.debug(f"Saved validation image for step {step.step_id}: {temp_path}")
                    
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
            return True
            
        except Exception as e:
            self.log_to_ui(f"❌ Error validating step completion: {e}", "ERROR")
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
        self.log_to_ui(f"🚀 Starting navigation sequence with {len(self.steps)} steps")
        
        active_steps = [step for step in self.steps if step.is_active]
        ready_steps = [step for step in active_steps if step.template_image is not None]
        
        self.log_to_ui(f"📋 Found {len(active_steps)} active steps, {len(ready_steps)} ready with icons")
        
        if not ready_steps:
            self.log_to_ui("❌ No steps with valid icons found", "ERROR")
            self.is_navigating = False
            return
        
        try:
            while self.is_navigating and not self.stop_navigation_flag:
                for step_index, step in enumerate(ready_steps):
                    if self.stop_navigation_flag or not self.is_navigating:
                        break
                    
                    self.log_to_ui(f"🎬 Processing step {step_index + 1}/{len(ready_steps)}: '{step.name}'")
                    
                    if self.execute_step(step):
                        self.log_to_ui(f"✅ Step {step.step_id} '{step.name}' completed successfully")
                    else:
                        self.log_to_ui(f"❌ Navigation failed at step {step.step_id} '{step.name}'", "ERROR")
                        break
                    
                    if self.is_navigating and not self.stop_navigation_flag and step_index < len(ready_steps) - 1:
                        self.log_to_ui("⏳ Waiting 1 second before next step")
                        time.sleep(1.0)
                
                if not self.stop_navigation_flag and self.is_navigating:
                    self.log_to_ui("🔄 Navigation sequence completed - restarting from beginning")
                    time.sleep(2.0)
            
        except Exception as e:
            self.log_to_ui(f"❌ Error in navigation loop: {e}", "ERROR")
        finally:
            self.log_to_ui("🏁 Navigation sequence ended")
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
            used_filenames = {os.path.basename(path) for path in used_files}
            
            self.logger.info(f"Found {len(used_filenames)} icon files in use: {used_filenames}")
            
            cleaned_count = 0
            for filename in os.listdir(icons_dir):
                if filename.startswith("step_") and filename not in used_filenames:
                    file_path = os.path.join(icons_dir, filename)
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up unused icon: {file_path}")
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to cleanup icon {file_path}: {e}")
            
            if cleaned_count == 0:
                self.logger.info("No unused icon files to clean up")
            else:
                self.logger.info(f"Cleaned up {cleaned_count} unused icon files")
                        
        except Exception as e:
            self.logger.error(f"Error during icon cleanup: {e}")
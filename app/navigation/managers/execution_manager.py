import time
import threading
import logging

logger = logging.getLogger('PokeXHelper')

class ExecutionManager:
    def __init__(self, step_manager, step_detector, step_validator):
        self.step_manager = step_manager
        self.step_detector = step_detector
        self.step_validator = step_validator
        self.logger = logger
        
        self.is_navigating = False
        self.navigation_thread = None
        self.stop_navigation_flag = False
        self.current_step_index = 0
        
        self.ui_log_callback = None
    
    def set_ui_log_callback(self, callback):
        self.ui_log_callback = callback
    
    def log(self, message):
        if self.ui_log_callback:
            self.ui_log_callback(message)
        self.logger.info(message)
    
    def start_navigation(self):
        if self.is_navigating:
            self.logger.warning("Navigation already in progress")
            return False
            
        if not self.step_manager.steps:
            self.logger.error("No navigation steps configured")
            return False
        
        valid_steps = self.step_manager.get_ready_steps()
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
        self.logger.info(f"Starting navigation sequence with {len(self.step_manager.steps)} steps")
        
        ready_steps = self.step_manager.get_ready_steps()
        
        self.logger.info(f"Found {len(ready_steps)} ready steps with icons")
        
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
                    
                    self.logger.info(f"Processing step {step_index+1}/{len(ready_steps)}: '{step.name}'")
                    
                    step_success = self.execute_step(step, max_retries=2)
                    
                    if step_success:
                        self.logger.info(f"Step {step.step_id} '{step.name}' completed successfully")
                    else:
                        self.logger.error(f"Navigation failed at step {step.step_id} '{step.name}' after retries")
                        sequence_success = False
                        break
                
                if sequence_success and not self.stop_navigation_flag:
                    time.sleep(1)
                    self.logger.info("Navigation sequence completed successfully - restarting from beginning")
                elif not self.stop_navigation_flag:
                    self.logger.warning("Navigation sequence failed - retrying from beginning in 5 seconds")
                    time.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error in navigation loop: {e}")
        finally:
            self.logger.info("Navigation sequence ended")
            self.is_navigating = False
    
    def execute_step(self, step, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"[ATTEMPT {attempt + 1}] Executing step {step.step_id}: {step.name}")
                
                # Find the step icon in minimap
                result = self.step_detector.find_step_icon_in_minimap(step)
                if not result:
                    self.logger.warning(f"Step {step.step_id} icon not found in minimap")
                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return False
                
                x, y, confidence = result
                self.logger.info(f"Found step {step.step_id} icon at ({x}, {y}) with confidence {confidence:.1%}")
                
                # Click on the detected location
                success = self.step_detector.click_step_location(x, y)
                if not success:
                    self.logger.warning(f"Failed to click on step {step.step_id} location")
                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return False
                
                # Wait for step completion
                self.logger.info(f"Waiting {step.wait_seconds}s for step {step.step_id} to complete")
                time.sleep(step.wait_seconds)
                
                # Validate step completion if enabled
                if self.step_validator.validate_step_completion(step):
                    self.logger.info(f"Step {step.step_id} validation successful")
                    return True
                else:
                    self.logger.warning(f"Step {step.step_id} validation failed")
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error executing step {step.step_id} (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return False
        
        return False
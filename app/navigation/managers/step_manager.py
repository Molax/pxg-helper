import os
import logging

logger = logging.getLogger('PokeXHelper')

class StepManager:
    def __init__(self):
        self.steps = []
        self.next_step_id = 1
        self.logger = logger
    
    def add_step(self, name, coordinates="", wait_seconds=3.0):
        from ..navigation_step import NavigationStep
        
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
            self.logger.info(f"Removed step {step_id}")
            return True
        return False
    
    def get_step_by_id(self, step_id):
        return next((s for s in self.steps if s.step_id == step_id), None)
    
    def get_active_steps(self):
        return [step for step in self.steps if step.is_active]
    
    def get_ready_steps(self):
        active_steps = self.get_active_steps()
        return [step for step in active_steps if step.template_image is not None]
    
    def clear_all_steps(self):
        for step in self.steps:
            if step.icon_image_path and os.path.exists(step.icon_image_path):
                try:
                    os.remove(step.icon_image_path)
                except Exception as e:
                    self.logger.error(f"Failed to delete icon file: {e}")
        
        self.steps.clear()
        self.next_step_id = 1
        self.logger.info("Cleared all navigation steps")
    
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
        from ..navigation_step import NavigationStep
        
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
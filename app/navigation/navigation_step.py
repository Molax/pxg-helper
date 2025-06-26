import os
import cv2
import logging

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
        self.active = True  # For backward compatibility
        self.icon_bounds = None
        
    @property
    def active(self):
        return self.is_active
    
    @active.setter
    def active(self, value):
        self.is_active = value
        
    def load_template(self):
        """Load the template image for this step"""
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
        """Convert step to dictionary for serialization"""
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
        """Create step from dictionary"""
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
    
    def __str__(self):
        return f"NavigationStep(id={self.step_id}, name='{self.name}', active={self.is_active})"
    
    def __repr__(self):
        return self.__str__()
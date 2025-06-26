import math
import logging
from PIL import ImageGrab

logger = logging.getLogger('PokeXHelper')

class StepValidator:
    def __init__(self, coordinate_validator, validation_enabled=True, tolerance=15):
        self.coordinate_validator = coordinate_validator
        self.validation_enabled = validation_enabled
        self.tolerance = tolerance
        self.coordinate_area = None
        self.logger = logger
    
    def set_coordinate_area(self, coordinate_area_selector):
        self.coordinate_area = coordinate_area_selector
    
    def validate_step_completion(self, step):
        if not self.validation_enabled:
            return True
        
        try:
            if not self.coordinate_area or not self.coordinate_area.is_setup():
                self.logger.debug(f"No coordinate area configured for validation")
                return True
            
            # Get current coordinates from the coordinate area
            current_coords = self._get_current_coordinates()
            if not current_coords:
                self.logger.debug(f"Could not get current coordinates for validation")
                return True
            
            # Parse target coordinates from step
            target_coords = self._parse_target_coordinates(step.coordinates)
            if not target_coords:
                self.logger.debug(f"No target coordinates configured for step {step.step_id}")
                return True
            
            distance = self._calculate_distance(current_coords, target_coords)
            
            if distance <= self.tolerance:
                self.logger.info(f"[SUCCESS] Step {step.step_id} validated - reached target coordinates")
                return True
            else:
                self.logger.warning(f"[WARNING] Step {step.step_id} validation failed - distance: {distance}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error validating step completion: {e}")
            return True
    
    def _get_current_coordinates(self, max_attempts=5):
        for attempt in range(1, max_attempts + 1):
            try:
                bbox = (self.coordinate_area.x1, self.coordinate_area.y1, 
                       self.coordinate_area.x2, self.coordinate_area.y2)
                
                try:
                    coordinate_image = ImageGrab.grab(bbox=bbox, all_screens=True)
                except TypeError:
                    coordinate_image = ImageGrab.grab(bbox=bbox)
                
                coords = self.coordinate_validator.extract_coordinates_from_image(coordinate_image)
                
                if coords:
                    self.logger.debug(f"Successfully extracted coordinates: {coords}")
                    return coords
                else:
                    self.logger.warning(f"Could not get current coordinates on attempt {attempt}")
                    
            except Exception as e:
                self.logger.error(f"Error getting coordinates (attempt {attempt}): {e}")
        
        if max_attempts > 1:
            self.logger.warning(f"Coordinate validation failed after {max_attempts} attempts")
        
        return None
    
    def _parse_target_coordinates(self, coordinates_str):
        if not coordinates_str:
            return None
        
        try:
            # Handle various coordinate formats
            coordinates_str = coordinates_str.strip()
            
            # Try comma-separated format: "123,456" or "123, 456"
            if ',' in coordinates_str:
                parts = coordinates_str.split(',')
                if len(parts) == 2:
                    x = int(parts[0].strip())
                    y = int(parts[1].strip())
                    return (x, y)
            
            # Try space-separated format: "123 456"
            parts = coordinates_str.split()
            if len(parts) == 2:
                x = int(parts[0])
                y = int(parts[1])
                return (x, y)
                
        except (ValueError, IndexError) as e:
            self.logger.debug(f"Could not parse coordinates '{coordinates_str}': {e}")
        
        return None
    
    def _calculate_distance(self, coord1, coord2):
        x1, y1 = coord1
        x2, y2 = coord2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
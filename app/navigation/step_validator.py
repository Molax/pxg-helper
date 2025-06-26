import time
import math
from .enhanced_coordinate_validator import EnhancedCoordinateValidator

class StepValidator:
    def __init__(self, coordinate_tolerance, logger):
        self.coordinate_tolerance = coordinate_tolerance
        self.logger = logger
        self.coordinate_area = None
        self.coordinate_validator = EnhancedCoordinateValidator(debug_enabled=True)
    
    def set_coordinate_area(self, coordinate_area_selector):
        """Set the coordinate area selector"""
        self.coordinate_area = coordinate_area_selector
    
    def extract_coordinates_from_area(self):
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
    
    def calculate_distance(self, coord1, coord2):
        """Calculate distance between two coordinates"""
        if not coord1 or not coord2:
            return float('inf')
        
        x1, y1 = coord1[:2]
        x2, y2 = coord2[:2]
        
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance
    
    def validate_completion(self, step, coordinate_validation_enabled, parse_coordinates_func):
        """Validate if step was completed successfully"""
        try:
            if coordinate_validation_enabled and self.coordinate_area:
                time.sleep(0.5)
                
                current_coords = self.extract_coordinates_from_area()
                if not current_coords:
                    self.logger.warning(f"Could not extract coordinates for validation")
                    return True
                
                target_coords = parse_coordinates_func(step.coordinates)
                if not target_coords:
                    self.logger.debug(f"No target coordinates configured for step {step.step_id}")
                    return True
                
                distance = self.calculate_distance(current_coords, target_coords)
                
                if distance <= self.coordinate_tolerance:
                    self.logger.info(f"✓ Step {step.step_id} validated - reached target coordinates")
                    return True
                else:
                    self.logger.warning(f"⚠ Step {step.step_id} validation failed - distance: {distance}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating step completion: {e}")
            return True
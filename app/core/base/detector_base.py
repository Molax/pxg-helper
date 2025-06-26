import cv2
import numpy as np
import logging
import abc

logger = logging.getLogger('PokeXHelper')

class DetectorBase(abc.ABC):
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
    
    def _validate_image(self, image):
        if image is None:
            self.logger.warning("Cannot process: image is None")
            return False
            
        np_image = np.array(image)
        if np_image.size == 0:
            self.logger.warning("Cannot process: image is empty")
            return False
            
        return True
    
    def _convert_to_grayscale(self, image):
        np_image = np.array(image)
        if len(np_image.shape) == 3:
            return cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
        return np_image
    
    def _convert_to_hsv(self, image):
        np_image = np.array(image)
        return cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
    
    def _apply_morphology(self, mask, kernel_size=(3, 3)):
        kernel = np.ones(kernel_size, np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask
    
    def _create_color_mask(self, hsv_image, lower_bound, upper_bound):
        return cv2.inRange(hsv_image, np.array(lower_bound), np.array(upper_bound))
    
    def _calculate_fill_percentage(self, mask):
        total_pixels = mask.shape[0] * mask.shape[1]
        if total_pixels == 0:
            return 0
        filled_pixels = cv2.countNonZero(mask)
        return (filled_pixels / total_pixels) * 100
    
    @abc.abstractmethod
    def detect(self, image, **kwargs):
        pass
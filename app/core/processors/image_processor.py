import cv2
import numpy as np
import logging

logger = logging.getLogger('PokeXHelper')

class ImageProcessor:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
    
    def enhance_contrast(self, image, alpha=1.5, beta=0):
        try:
            np_image = np.array(image)
            enhanced = cv2.convertScaleAbs(np_image, alpha=alpha, beta=beta)
            return enhanced
        except Exception as e:
            self.logger.error(f"Error enhancing contrast: {e}")
            return image
    
    def apply_gaussian_blur(self, image, kernel_size=(5, 5), sigma_x=0):
        try:
            np_image = np.array(image)
            blurred = cv2.GaussianBlur(np_image, kernel_size, sigma_x)
            return blurred
        except Exception as e:
            self.logger.error(f"Error applying gaussian blur: {e}")
            return image
    
    def resize_image(self, image, width=None, height=None, maintain_aspect=True):
        try:
            np_image = np.array(image)
            h, w = np_image.shape[:2]
            
            if width is None and height is None:
                return image
            
            if maintain_aspect:
                if width is not None:
                    height = int(h * width / w)
                elif height is not None:
                    width = int(w * height / h)
            
            resized = cv2.resize(np_image, (width, height), interpolation=cv2.INTER_AREA)
            return resized
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            return image
    
    def crop_image(self, image, x, y, width, height):
        try:
            np_image = np.array(image)
            cropped = np_image[y:y+height, x:x+width]
            return cropped
        except Exception as e:
            self.logger.error(f"Error cropping image: {e}")
            return image
    
    def threshold_image(self, image, threshold_value=127, max_value=255, threshold_type=cv2.THRESH_BINARY):
        try:
            if len(image.shape) == 3:
                gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray_image = image
            
            _, thresholded = cv2.threshold(gray_image, threshold_value, max_value, threshold_type)
            return thresholded
        except Exception as e:
            self.logger.error(f"Error applying threshold: {e}")
            return image
    
    def detect_edges(self, image, low_threshold=50, high_threshold=150):
        try:
            if len(image.shape) == 3:
                gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray_image = image
            
            edges = cv2.Canny(gray_image, low_threshold, high_threshold)
            return edges
        except Exception as e:
            self.logger.error(f"Error detecting edges: {e}")
            return image
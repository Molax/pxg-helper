import cv2
import numpy as np
import logging

logger = logging.getLogger('PokeXHelper')

class MatchProcessor:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
    
    def find_template_matches(self, screen_gray, template_gray, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
        try:
            result = cv2.matchTemplate(screen_gray, template_gray, method)
            locations = np.where(result >= threshold)
            
            matches = []
            if len(locations[0]) > 0:
                for y, x in zip(locations[0], locations[1]):
                    confidence = result[y, x]
                    h, w = template_gray.shape
                    match_box = (x, y, x + w, y + h)
                    
                    matches.append({
                        'box': match_box,
                        'confidence': confidence,
                        'center': (x + w // 2, y + h // 2)
                    })
                
                matches.sort(key=lambda m: m['confidence'], reverse=True)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error in template matching: {e}")
            return []
    
    def find_best_match(self, screen_gray, template_gray, threshold=0.8):
        matches = self.find_template_matches(screen_gray, template_gray, threshold)
        return matches[0] if matches else None
    
    def filter_overlapping_matches(self, matches, overlap_threshold=0.3):
        if not matches:
            return matches
        
        filtered_matches = []
        matches_sorted = sorted(matches, key=lambda m: m['confidence'], reverse=True)
        
        for match in matches_sorted:
            is_overlapping = False
            for existing_match in filtered_matches:
                if self._calculate_overlap(match['box'], existing_match['box']) > overlap_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered_matches.append(match)
        
        return filtered_matches
    
    def _calculate_overlap(self, box1, box2):
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        overlap_x = max(0, min(x2_1, x2_2) - max(x1_1, x1_2))
        overlap_y = max(0, min(y2_1, y2_2) - max(y1_1, y1_2))
        overlap_area = overlap_x * overlap_y
        
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - overlap_area
        
        if union_area == 0:
            return 0
        
        return overlap_area / union_area
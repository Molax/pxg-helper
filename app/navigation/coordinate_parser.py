import re

class CoordinateParser:
    def __init__(self, logger):
        self.logger = logger
    
    def parse(self, coord_string):
        """Parse coordinate string and return (x, y, z) tuple"""
        if not coord_string or not isinstance(coord_string, str):
            return None
            
        try:
            coord_string = coord_string.strip()
            
            patterns = [
                r'(\d{4}),\s*(\d{4}),\s*(\d+)',
                r'(\d{4})\s+(\d{4})\s+(\d+)',
                r'(\d{4}):(\d{4}):(\d+)',
                r'X:\s*(\d{4})\s*Y:\s*(\d{4})\s*Z:\s*(\d+)',
                r'x:\s*(\d{4})\s*y:\s*(\d{4})\s*z:\s*(\d+)',
                r'\[(\d{4}),\s*(\d{4}),\s*(\d+)\]',
                r'\((\d{4}),\s*(\d{4}),\s*(\d+)\)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, coord_string)
                if matches:
                    try:
                        x, y, z = matches[0]
                        return (int(x), int(y), int(z))
                    except (ValueError, IndexError):
                        continue
            
            numbers = re.findall(r'\d{4}', coord_string)
            if len(numbers) >= 2:
                try:
                    return (int(numbers[0]), int(numbers[1]), 6)
                except ValueError:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing coordinates: {e}")
            return None
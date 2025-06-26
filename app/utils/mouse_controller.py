import time
import logging
import ctypes
from ctypes import wintypes

logger = logging.getLogger('PokeXHelper')

class MouseController:
    def __init__(self):
        self.logger = logging.getLogger('PokeXHelper')
        
    def move_to(self, x, y):
        try:
            x, y = int(x), int(y)
            
            point = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            original_x, original_y = point.x, point.y
            
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.05)
            
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            if abs(point.x - x) > 5 or abs(point.y - y) > 5:
                screen_width = ctypes.windll.user32.GetSystemMetrics(0)
                screen_height = ctypes.windll.user32.GetSystemMetrics(1)
                
                norm_x = int(65535 * x / screen_width)
                norm_y = int(65535 * y / screen_height)
                
                MOUSEEVENTF_ABSOLUTE = 0x8000
                MOUSEEVENTF_MOVE = 0x0001
                ctypes.windll.user32.mouse_event(
                    MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 
                    norm_x, 
                    norm_y, 
                    0, 
                    0
                )
                time.sleep(0.1)
            
            return True
        except Exception as e:
            self.logger.error(f"Error moving mouse to ({x}, {y}): {e}")
            return False
    
    def click_left(self, x=None, y=None):
        try:
            if x is not None and y is not None:
                if not self.move_to(x, y):
                    return False
                time.sleep(0.1)
            
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.1)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            self.logger.debug(f"Left click at ({x}, {y})" if x and y else "Left click at current position")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking left mouse: {e}")
            return False
    
    def click_right(self, x=None, y=None):
        try:
            if x is not None and y is not None:
                if not self.move_to(x, y):
                    return False
                time.sleep(0.1)
            
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.1)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            
            self.logger.debug(f"Right click at ({x}, {y})" if x and y else "Right click at current position")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking right mouse: {e}")
            return False
    
    def double_click(self, x=None, y=None):
        try:
            if x is not None and y is not None:
                if not self.move_to(x, y):
                    return False
                time.sleep(0.1)
            
            self.click_left()
            time.sleep(0.05)
            self.click_left()
            
            self.logger.debug(f"Double click at ({x}, {y})" if x and y else "Double click at current position")
            return True
            
        except Exception as e:
            self.logger.error(f"Error double clicking: {e}")
            return False
import time
import logging
import ctypes

logger = logging.getLogger('PokeXHelper')

def get_virtual_key_code(key):
    key_map = {
        '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
        '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
        'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'esc': 0x1B,
        'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
        'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
        'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B
    }
    
    key = key.lower() if isinstance(key, str) else str(key)
    
    if key in key_map:
        return key_map[key]
    
    logger.warning(f"Key '{key}' not found in key map, using ASCII value")
    try:
        return ord(key.upper()[0])
    except:
        logger.error(f"Could not determine virtual key code for '{key}'")
        return 0

def press_key(key):
    try:
        vk_code = get_virtual_key_code(key)
        
        logger.debug(f"Pressing key '{key}' (VK: {vk_code})")
        
        KEYEVENTF_KEYUP = 0x0002
        
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        
        return True
    except Exception as e:
        logger.error(f"Error pressing key '{key}': {e}", exc_info=True)
        return False

def press_key_combination(key1, key2):
    try:
        vk_code1 = get_virtual_key_code(key1)
        vk_code2 = get_virtual_key_code(key2)
        
        logger.debug(f"Pressing key combination '{key1}+{key2}'")
        
        KEYEVENTF_KEYUP = 0x0002
        
        ctypes.windll.user32.keybd_event(vk_code1, 0, 0, 0)
        time.sleep(0.05)
        
        ctypes.windll.user32.keybd_event(vk_code2, 0, 0, 0)
        time.sleep(0.05)
        
        ctypes.windll.user32.keybd_event(vk_code2, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        
        ctypes.windll.user32.keybd_event(vk_code1, 0, KEYEVENTF_KEYUP, 0)
        
        return True
    except Exception as e:
        logger.error(f"Error pressing key combination {key1}+{key2}: {e}", exc_info=True)
        return False

def hold_key(key, duration):
    try:
        vk_code = get_virtual_key_code(key)
        
        logger.debug(f"Holding key '{key}' for {duration}s")
        
        KEYEVENTF_KEYUP = 0x0002
        
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(duration)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        
        return True
    except Exception as e:
        logger.error(f"Error holding key '{key}': {e}", exc_info=True)
        return False
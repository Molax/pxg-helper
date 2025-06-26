#!/usr/bin/env python3
import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox
import time

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('PokeXHelper')
    logger.setLevel(logging.INFO)
    
    from logging.handlers import RotatingFileHandler
    log_file = os.path.join('logs', f'pokexgames_helper_{time.strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    logger.info("PokeXGames Helper logging initialized")
    return logger

def check_dependencies():
    missing_libs = []
    dependencies = [
        ('win32gui', 'pywin32', 'Windows GUI functions'),
        ('cv2', 'opencv-python', 'Image processing'),
        ('numpy', 'numpy', 'Numerical operations'),
        ('PIL', 'pillow', 'Image handling')
    ]
    
    for module_name, package_name, purpose in dependencies:
        try:
            __import__(module_name)
        except ImportError:
            missing_libs.append((package_name, purpose))
    
    return missing_libs

def main():
    logger = setup_logging()
    
    missing_libs = check_dependencies()
    if missing_libs:
        error_message = "The following required libraries are missing:\n\n"
        for lib, purpose in missing_libs:
            error_message += f"• {lib} - {purpose}\n"
        error_message += "\nPlease install them using:\n"
        error_message += "pip install " + " ".join([lib for lib, _ in missing_libs])
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_message)
            root.destroy()
        except:
            print("ERROR: Missing dependencies")
            print(error_message)
        sys.exit(1)
    
    for directory in ["logs", "debug_images", "assets/pokemon_templates"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    try:
        from app.gui import PokeXGamesHelper
        
        root = tk.Tk()
        app = PokeXGamesHelper(root)
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error", f"Fatal error: {e}")
            root.destroy()
        except:
            print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
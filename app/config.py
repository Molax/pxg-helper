import os
import time
import logging
from logging.handlers import RotatingFileHandler
import json

DEFAULT_CONFIG = {
    "health_healing_key": "F1",
    "health_threshold": 60,
    "scan_interval": 0.5,
    "debug_enabled": True,
    "areas": {
        "health_bar": {
            "name": "Health Bar",
            "x1": None,
            "y1": None,
            "x2": None,
            "y2": None,
            "configured": False
        },
        "minimap": {
            "name": "Minimap",
            "x1": None,
            "y1": None,
            "x2": None,
            "y2": None,
            "configured": False
        },
        "battle_area": {
            "name": "Battle Area",
            "x1": None,
            "y1": None,
            "x2": None,
            "y2": None,
            "configured": False
        }
    },
    "helper_settings": {
        "auto_heal": True,
        "auto_navigation": False,
        "navigation_check_interval": 0.5,
        "step_timeout": 30,
        "coordinate_validation": True,
        "image_matching_threshold": 0.8,
        "battle_detection_enabled": True,
        "auto_battle": False
    },
    "navigation_steps": []
}

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('PokeXHelper')
    logger.setLevel(logging.INFO)
    
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    log_file = os.path.join('logs', f'pokexgames_helper_{time.strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    
    if DEFAULT_CONFIG["debug_enabled"]:
        debug_handler = logging.FileHandler(os.path.join('logs', f'debug_{time.strftime("%Y%m%d_%H%M%S")}.log'))
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        logger.addHandler(debug_handler)
        logger.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(console_handler)
    
    logger.info("PokeXGames Helper logging initialized")
    return logger

def load_config():
    config_path = 'pokexgames_config.json'
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logging.getLogger('PokeXHelper').info("Configuration loaded from file")
                
                if "areas" not in config:
                    config["areas"] = DEFAULT_CONFIG["areas"]
                    logging.getLogger('PokeXHelper').info("Added missing areas configuration")
                    save_config(config)
                
                if "battle_area" not in config["areas"]:
                    config["areas"]["battle_area"] = DEFAULT_CONFIG["areas"]["battle_area"]
                    logging.getLogger('PokeXHelper').info("Added battle area configuration")
                    save_config(config)
                
                if "coordinates" in config["areas"]:
                    del config["areas"]["coordinates"]
                    logging.getLogger('PokeXHelper').info("Removed deprecated coordinates area")
                    save_config(config)
                
                if "helper_settings" not in config:
                    config["helper_settings"] = DEFAULT_CONFIG["helper_settings"]
                    logging.getLogger('PokeXHelper').info("Added missing helper settings")
                    save_config(config)
                
                if "battle_detection_enabled" not in config["helper_settings"]:
                    config["helper_settings"]["battle_detection_enabled"] = True
                    config["helper_settings"]["auto_battle"] = False
                    logging.getLogger('PokeXHelper').info("Added battle detection settings")
                    save_config(config)
                
                if "navigation_steps" not in config:
                    config["navigation_steps"] = DEFAULT_CONFIG["navigation_steps"]
                    logging.getLogger('PokeXHelper').info("Added missing navigation steps")
                    save_config(config)
                
                return config
        except Exception as e:
            logging.getLogger('PokeXHelper').error(f"Error loading configuration: {e}")
            
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(config):
    config_path = 'pokexgames_config.json'
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logging.getLogger('PokeXHelper').info("Configuration saved to file")
    except Exception as e:
        logging.getLogger('PokeXHelper').error(f"Error saving configuration: {e}")
# app/__init__.py
"""
PokeXGames Helper
----------------------------------
Pokemon Battle Assistant
"""

__version__ = '1.0.0'

# app/core/__init__.py
"""Core detection and analysis modules"""

from app.core.pokemon_detector import  PokemonDetector, BattleDetector

from app.core.health_detector import  HealthDetector

# app/screen_capture/__init__.py
"""Screen capture and area selection modules"""

from app.screen_capture.area_selector import AreaSelector

# app/utils/__init__.py
"""Utility modules for keyboard input and system functions"""

from app.utils.keyboard_input import press_key, press_key_combination, hold_key

# app/ui/__init__.py
"""UI components and interface elements"""

pass
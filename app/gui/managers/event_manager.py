import logging
import threading
import time

logger = logging.getLogger('PokeXHelper')

class EventManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.helper_thread = None
        self.running = False
        self.start_time = None
        self.heals_used = 0
        self.steps_completed = 0
        self.battles_won = 0
    
    def start_helper(self):
        if self.running:
            logger.warning("Helper is already running")
            return
        
        try:
            health_configured = self.main_app.health_bar_selector.is_setup()
            if not health_configured:
                self.main_app.log("Cannot start: Health Bar area not configured")
                return
            
            self.running = True
            self.start_time = time.time()
            self.heals_used = 0
            self.steps_completed = 0
            self.battles_won = 0
            
            self.helper_thread = threading.Thread(target=self._helper_loop, daemon=True)
            self.helper_thread.start()
            
            self.main_app.update_status("Helper Running", "#28a745")
            self.main_app.log("Helper started successfully")
            
        except Exception as e:
            logger.error(f"Error starting helper: {e}")
            self.main_app.log(f"Error starting helper: {e}")
            self.running = False
    
    def stop_helper(self):
        if not self.running:
            logger.warning("Helper is not running")
            return
        
        try:
            self.running = False
            
            if self.helper_thread and self.helper_thread.is_alive():
                self.helper_thread.join(timeout=2.0)
            
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)
            
            self.main_app.update_status("Helper Stopped", "#6c757d")
            self.main_app.log(f"Helper stopped - Runtime: {elapsed_minutes}m {elapsed_seconds}s")
            self.main_app.log(f"Session stats - Heals: {self.heals_used}, Steps: {self.steps_completed}, Battles: {self.battles_won}")
            
        except Exception as e:
            logger.error(f"Error stopping helper: {e}")
            self.main_app.log(f"Error stopping helper: {e}")
        finally:
            self.running = False
    
    def _helper_loop(self):
        try:
            while self.running:
                self._check_health()
                self._check_navigation()
                self._check_battle_state()
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in helper loop: {e}")
            self.main_app.log(f"Helper error: {e}")
            self.running = False
            self.main_app.update_status("Helper Error", "#dc3545")
    
    def _check_health(self):
        try:
            if not self.main_app.health_bar_selector.is_setup():
                return
            
            from PIL import ImageGrab
            
            bbox = (
                self.main_app.health_bar_selector.x1,
                self.main_app.health_bar_selector.y1,
                self.main_app.health_bar_selector.x2,
                self.main_app.health_bar_selector.y2
            )
            
            health_image = ImageGrab.grab(bbox=bbox, all_screens=True)
            health_percentage = self.main_app.health_detector.detect_health_percentage(health_image)
            
            threshold = getattr(self.main_app, 'health_threshold', 60)
            auto_heal = getattr(self.main_app, 'auto_heal_enabled', True)
            
            if auto_heal and health_percentage < threshold:
                heal_key = getattr(self.main_app, 'heal_key', 'F1')
                from app.utils.keyboard_input import press_key
                press_key(heal_key)
                self.heals_used += 1
                self.main_app.log(f"Auto-heal triggered (Health: {health_percentage:.1f}%)")
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    def _check_navigation(self):
        try:
            if hasattr(self.main_app, 'navigation_manager'):
                if self.main_app.navigation_manager.is_navigating:
                    return
        except Exception as e:
            logger.debug(f"Navigation check error: {e}")
    
    def _check_battle_state(self):
        try:
            if not self.main_app.battle_area_selector.is_setup():
                return
            
            from PIL import ImageGrab
            
            bbox = (
                self.main_app.battle_area_selector.x1,
                self.main_app.battle_area_selector.y1,
                self.main_app.battle_area_selector.x2,
                self.main_app.battle_area_selector.y2
            )
            
            battle_image = ImageGrab.grab(bbox=bbox, all_screens=True)
            in_battle = self.main_app.battle_detector.is_in_battle(battle_image)
            
            if in_battle:
                enemy_count = self.main_app.battle_detector.count_enemy_pokemon(battle_image)
                if enemy_count == 0:
                    self.battles_won += 1
                    self.main_app.log(f"Battle won! Total battles won: {self.battles_won}")
                    
        except Exception as e:
            logger.debug(f"Battle state check error: {e}")
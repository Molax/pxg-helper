import time
import logging
import threading
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger('PokeXHelper')

class InterfaceManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.area_selector_window = None
        self._create_interface()
    
    def _create_interface(self):
        self.main_app.root.title("PokeXGames Helper v1.0")
        self.main_app.root.geometry("1400x900")
        self.main_app.root.configure(bg="#1a1a1a")
        self.main_app.root.protocol("WM_DELETE_WINDOW", self.main_app.on_closing)
        
        main_container = tk.Frame(self.main_app.root, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self._create_left_panel(main_container)
        self._create_right_panel(main_container)
        self._create_bottom_status(main_container)
        
        logger.info("PokeXGames Helper interface initialized")
    
    def _create_left_panel(self, parent):
        left_panel = tk.Frame(parent, bg="#2d2d2d", relief=tk.RIDGE, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        config_frame = tk.Frame(notebook, bg="#2d2d2d")
        nav_frame = tk.Frame(notebook, bg="#2d2d2d")
        
        notebook.add(config_frame, text="Configuration")
        notebook.add(nav_frame, text="Navigation")
        
        from app.ui.area_config_panel import AreaConfigPanel
        from app.ui.navigation_panel import NavigationPanel
        
        self.area_config_panel = AreaConfigPanel(
            config_frame, 
            self.main_app.health_bar_selector,
            self.main_app.minimap_selector,
            self.main_app.battle_area_selector,
            self.main_app
        )
        
        self.navigation_panel = NavigationPanel(
            nav_frame,
            self.main_app.navigation_manager,
            self.main_app
        )
        
        self.main_app.area_config_panel = self.area_config_panel
        self.main_app.navigation_panel = self.navigation_panel
    
    def _create_right_panel(self, parent):
        right_panel = tk.Frame(parent, bg="#2d2d2d", relief=tk.RIDGE, bd=1, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        right_panel.pack_propagate(False)
        
        controls_container = tk.Frame(right_panel, bg="#2d2d2d")
        controls_container.pack(fill=tk.X, padx=8, pady=8)
        
        log_container = tk.Frame(right_panel, bg="#2d2d2d")
        log_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        from app.ui.controls_panel import ControlsPanel
        from app.ui.log_panel import LogPanel
        
        self.controls_panel = ControlsPanel(
            controls_container,
            self.main_app.health_detector,
            self.main_app
        )
        
        self.log_panel = LogPanel(log_container)
        
        self.main_app.controls_panel = self.controls_panel
    
    def _create_bottom_status(self, parent):
        status_frame = tk.Frame(parent, bg="#1a1a1a", height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        status_frame.pack_propagate(False)
        
        self.status_indicator = tk.Label(status_frame, text="●", 
                                       font=("Segoe UI", 16), bg="#1a1a1a", fg="#ffc107")
        self.status_indicator.pack(side=tk.LEFT, padx=(8, 4))
        
        self.status_text = tk.Label(status_frame, text="Ready", 
                                  font=("Segoe UI", 10), bg="#1a1a1a", fg="#ffc107")
        self.status_text.pack(side=tk.LEFT)
    
    def start_area_selection(self, title, color, selector):
        self.log(f"Starting {title} selection...")
        
        def on_completion():
            self.log(f"{title} selection completed")
            self.area_config_panel.update_area_status(selector)
            self.check_configuration()
            
            try:
                self.main_app.config_manager.save_configuration()
                self.log(f"{title} configuration auto-saved")
            except Exception as e:
                self.log(f"Failed to auto-save {title} configuration: {e}")
        
        try:
            success = selector.start_selection(
                title=title,
                color=color,
                completion_callback=on_completion
            )
            
            if not success:
                self.log(f"Failed to start {title} selection")
                
        except Exception as e:
            logger.error(f"Error starting {title} selection: {e}")
            self.log(f"Error starting {title} selection: {e}")
    
    def check_configuration(self):
        health_configured = self.main_app.health_bar_selector.is_setup()
        minimap_configured = self.main_app.minimap_selector.is_setup()
        battle_configured = self.main_app.battle_area_selector.is_setup()
        
        if health_configured and minimap_configured and battle_configured:
            self.area_config_panel.set_config_status("All areas configured! Helper ready.", "#28a745")
            self.controls_panel.enable_start_button()
        else:
            missing = []
            if not health_configured:
                missing.append("Health Bar")
            if not minimap_configured:
                missing.append("Minimap")
            if not battle_configured:
                missing.append("Battle Area")
            
            self.area_config_panel.set_config_status(f"Configure: {', '.join(missing)}", "#ffc107")
            self.controls_panel.disable_start_button()
        
        if minimap_configured:
            self.navigation_panel.check_navigation_ready()
    
    def start_helper(self):
        self.log("Starting PokeXGames Helper...")
        self.main_app.running = True
        self.main_app.start_time = time.time()
        
        self.controls_panel.set_helper_running(True)
        self.navigation_panel.on_helper_state_changed(True)
        self.update_status("Running", "#28a745")
        
        self.main_app.helper_thread = threading.Thread(target=self.helper_loop, daemon=True)
        self.main_app.helper_thread.start()
        
        self.controls_panel.start_display_update()
    
    def stop_helper(self):
        self.log("Stopping PokeXGames Helper...")
        self.main_app.running = False
        
        self.controls_panel.set_helper_running(False)
        self.navigation_panel.on_helper_state_changed(False)
        self.update_status("Ready", "#28a745")
    
    def helper_loop(self):
        from app.utils.keyboard_input import press_key
        
        while self.main_app.running:
            try:
                if self.main_app.health_bar_selector.is_setup():
                    health_image = self.main_app.health_bar_selector.get_current_screenshot_region()
                    if health_image:
                        health_percent = self.main_app.health_detector.detect_health_percentage(health_image)
                        self.area_config_panel.update_health_percentage(health_percent)
                        
                        if self.controls_panel.should_auto_heal(health_percent):
                            heal_key = self.controls_panel.get_heal_key()
                            if press_key(heal_key):
                                self.main_app.heals_used += 1
                                self.controls_panel.update_heals_count(self.main_app.heals_used)
                                self.log(f"Health low ({health_percent:.1f}%), used heal ({heal_key})")
                
                if self.main_app.battle_area_selector.is_setup():
                    battle_image = self.main_app.battle_area_selector.get_current_screenshot_region()
                    if battle_image:
                        enemy_count = self.main_app.battle_detector.count_enemy_pokemon(battle_image)
                        in_battle = self.main_app.battle_detector.has_enemy_pokemon(battle_image)
                        
                        self.area_config_panel.update_battle_info(enemy_count, in_battle)
                        
                        if in_battle:
                            self.log(f"Battle detected! {enemy_count} enemy Pokemon found")
                
                if (self.controls_panel.should_auto_navigate() and 
                    not self.main_app.navigation_manager.is_navigating and
                    not self.navigation_panel.navigation_running):
                    if self.main_app.navigation_manager.steps:
                        self.navigation_panel.start_navigation()
                        self.log("Auto-navigation started by helper")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in helper loop: {e}")
                self.log(f"Helper error: {e}")
                time.sleep(1.0)
        
        self.log("Helper stopped")
    
    def update_status(self, text, color):
        self.status_indicator.config(fg=color)
        self.status_text.config(text=text, fg=color)
    
    def log(self, message):
        self.log_panel.add_log(message)
        logger.info(message)
import tkinter as tk
from tkinter import ttk
import time
import logging
import threading
from app.ui.area_config_panel import AreaConfigPanel
from app.ui.navigation_panel import NavigationPanel
from app.ui.controls_panel import ControlsPanel
from app.ui.log_panel import LogPanel

logger = logging.getLogger('PokeXHelper')

class InterfaceManager:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self._setup_scrollable_canvas()
    
    def _setup_scrollable_canvas(self):
        self.main_canvas = tk.Canvas(self.root, bg="#1a1a1a", highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_main = tk.Frame(self.main_canvas, bg="#1a1a1a")
        
        self.scrollable_main.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_main, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_interface(self):
        self.main_app.component_manager.set_root_window(self.root)
        
        main_container = tk.Frame(self.scrollable_main, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        self._create_header(main_container)
        self._create_content_area(main_container)
        
        self.main_app.log("PokeXGames Helper interface initialized")
    
    def _create_header(self, parent):
        header_frame = tk.Frame(parent, bg="#1a1a1a", height=70)
        header_frame.pack(fill=tk.X, pady=12)
        header_frame.pack_propagate(False)
        
        title_section = tk.Frame(header_frame, bg="#1a1a1a")
        title_section.pack(side=tk.LEFT, fill=tk.Y, pady=8)
        
        title_label = tk.Label(title_section, text="PokeXGames Helper", 
                              font=("Segoe UI", 20, "bold"), bg="#1a1a1a", fg="#ffffff")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(title_section, text="Battle Automation & Navigation Helper", 
                                 font=("Segoe UI", 12), bg="#1a1a1a", fg="#ff6b35")
        subtitle_label.pack(anchor=tk.W)
        
        status_section = tk.Frame(header_frame, bg="#1a1a1a")
        status_section.pack(side=tk.RIGHT, fill=tk.Y, pady=8)
        
        status_frame = tk.Frame(status_section, bg="#1a1a1a")
        status_frame.pack(side=tk.RIGHT, padx=20)
        
        status_label = tk.Label(status_frame, text="Status:", 
                               font=("Segoe UI", 10), bg="#1a1a1a", fg="#b3b3b3")
        status_label.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Label(status_frame, text="●", 
                                       font=("Segoe UI", 16), bg="#1a1a1a", fg="#28a745")
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        
        self.status_text = tk.Label(status_frame, text="Ready", 
                                   font=("Segoe UI", 10, "bold"), bg="#1a1a1a", fg="#28a745")
        self.status_text.pack(side=tk.LEFT, padx=5)
    
    def _create_content_area(self, parent):
        content_frame = tk.Frame(parent, bg="#1a1a1a")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        left_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=3)
        
        middle_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        middle_panel.grid(row=0, column=1, sticky="nsew", padx=3)
        
        right_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=3)
        
        self.area_config_panel = AreaConfigPanel(
            left_panel, 
            self.main_app.health_bar_selector,
            self.main_app.minimap_selector,
            self.main_app.battle_area_selector,
            self.main_app
        )
        
        self.navigation_panel = NavigationPanel(
            middle_panel,
            self.main_app.navigation_manager,
            self.main_app
        )
        
        self.main_app.navigation_panel = self.navigation_panel
        
        self.log_panel = LogPanel(right_panel)
        
        self.controls_panel = ControlsPanel(
            right_panel,
            self.main_app.health_detector,
            self.main_app
        )
        
        self.main_app.controls_panel = self.controls_panel
    
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
    
    def start_helper(self):
        self.log("Starting PokeXGames Helper...")
        self.main_app.running = True
        self.main_app.start_time = time.time()
        
        self.controls_panel.set_helper_running(True)
        self.update_status("Running", "#28a745")
        
        self.main_app.helper_thread = threading.Thread(target=self.helper_loop, daemon=True)
        self.main_app.helper_thread.start()
        
        self.controls_panel.start_display_update()
    
    def stop_helper(self):
        self.log("Stopping PokeXGames Helper...")
        self.main_app.running = False
        
        if self.main_app.navigation_manager.is_navigating:
            self.main_app.navigation_manager.stop_navigation()
        
        self.controls_panel.set_helper_running(False)
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
                
                if self.controls_panel.should_auto_navigate() and not self.main_app.navigation_manager.is_navigating:
                    if self.main_app.navigation_manager.steps:
                        self.main_app.navigation_manager.start_navigation()
                        self.log("Auto-navigation started")
                
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
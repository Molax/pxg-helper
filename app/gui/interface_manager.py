import time
import logging
import threading
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger('PokeXHelper')

class InterfaceManager:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.area_selector_window = None
    
    def create_interface(self):
        self.main_app.root.title("PokeXGames Helper v1.0")
        self.main_app.root.geometry("1400x900")
        self.main_app.root.configure(bg="#1a1a1a")
        self.main_app.root.protocol("WM_DELETE_WINDOW", self.main_app.on_closing)
        
        main_container = tk.Frame(self.main_app.root, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self._create_left_panel(main_container)
        self._create_right_panel(main_container)
        self._create_bottom_status(main_container)
        
        self.main_app.navigation_manager.set_ui_log_callback(self.log)
        
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
        
        self.navigation_panel = NavigationPanel(nav_frame, self.main_app.navigation_manager, self.main_app)
    
    def _create_right_panel(self, parent):
        right_panel = tk.Frame(parent, bg="#2d2d2d", relief=tk.RIDGE, bd=1, width=500)
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
    
    def check_configuration(self):
        health_configured = self.main_app.health_bar_selector.is_setup()
        minimap_configured = self.main_app.minimap_selector.is_setup()
        battle_configured = self.main_app.battle_area_selector.is_setup()
        
        if health_configured and minimap_configured and battle_configured:
            self.update_status("Configuration complete - Ready to start", "#4CAF50")
            if hasattr(self, 'controls_panel'):
                self.controls_panel.enable_start_button()
        else:
            missing = []
            if not health_configured:
                missing.append("Health Bar")
            if not minimap_configured:
                missing.append("Minimap")
            if not battle_configured:
                missing.append("Battle Area")
            
            self.update_status(f"Configure: {', '.join(missing)}", "#ff9800")
            if hasattr(self, 'controls_panel'):
                self.controls_panel.disable_start_button()
    
    def start_area_selection(self, title, color, selector):
        if self.area_selector_window:
            self.area_selector_window.destroy()
        
        self.log(f"Starting area selection for {title}")
        selector.title = title
        selector.color = color
        
        def on_selection_complete():
            self.area_selector_window = None
            self.check_configuration()
        
        try:
            from app.screen_capture.area_selector import AreaSelector
            self.area_selector_window = AreaSelector(self.main_app.root)
            
            success = self.area_selector_window.start_selection(
                title=title,
                color=color,
                completion_callback=on_selection_complete
            )
            
            if not success:
                self.log(f"Failed to start area selection for {title}")
                
        except Exception as e:
            self.log(f"Error starting area selection: {e}")
    
    def log(self, message):
        if hasattr(self, 'log_panel'):
            self.log_panel.add_log(message)
        else:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def update_status(self, text, color):
        self.status_label.config(text=text, fg=color)
    def _create_bottom_status(self, parent):
        status_frame = tk.Frame(parent, bg="#333333", height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready - Configure areas to begin",
            bg="#333333",
            fg="#cccccc",
            font=("Arial", 9),
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
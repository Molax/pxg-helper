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
        """Check configuration status and update UI"""
        try:
            health_configured = self.main_app.health_bar_selector.is_setup()
            minimap_configured = self.main_app.minimap_selector.is_setup()
            battle_configured = self.main_app.battle_area_selector.is_setup()
            
            # Update area previews
            if hasattr(self, 'area_config_panel'):
                self.area_config_panel.refresh_all_previews()
            
            if health_configured and minimap_configured and battle_configured:
                self.update_status("Configuration complete - Ready to start", "#4CAF50")
                if hasattr(self, 'area_config_panel'):
                    self.area_config_panel.set_config_status("All areas configured - Ready to start!", "#28a745")
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
                if hasattr(self, 'area_config_panel'):
                    self.area_config_panel.set_config_status(f"Configure: {', '.join(missing)}", "#ffc107")
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.disable_start_button()
                    
        except Exception as e:
            logger.error(f"Error checking configuration: {e}")
    
    def start_area_selection(self, title, color, selector):
        """Start area selection process"""
        if self.area_selector_window:
            try:
                self.area_selector_window.destroy()
            except:
                pass
            self.area_selector_window = None
        
        self.log(f"Starting area selection: {title}")
        
        def on_selection_complete():
            try:
                self.area_selector_window = None
                if selector.is_setup():
                    self.log(f"{title} selection confirmed: ({selector.x1}, {selector.y1}) to ({selector.x2}, {selector.y2})")
                    # Force create preview image
                    self._create_preview_for_selector(selector)
                    # Update the specific area display
                    if hasattr(self, 'area_config_panel'):
                        self.area_config_panel.update_area_status(selector)
                    # Check overall configuration
                    self.check_configuration()
                else:
                    self.log(f"{title} selection cancelled")
            except Exception as e:
                logger.error(f"Error in selection completion for {title}: {e}")
        
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
            logger.error(f"Error starting area selection for {title}: {e}")
            self.log(f"Error starting area selection: {e}")
    
    def _create_preview_for_selector(self, selector):
        """Create preview image for a selector"""
        try:
            if selector.is_setup():
                from PIL import ImageGrab
                
                bbox = (selector.x1, selector.y1, selector.x2, selector.y2)
                try:
                    preview_img = ImageGrab.grab(bbox=bbox, all_screens=True)
                except TypeError:
                    preview_img = ImageGrab.grab(bbox=bbox)
                
                selector.preview_image = preview_img
                logger.debug(f"Created preview image for selector")
                
        except Exception as e:
            logger.error(f"Error creating preview for selector: {e}")
    
    def start_helper(self):
        """Start the helper"""
        try:
            if not self.main_app.running:
                if self.main_app.health_bar_selector.is_setup():
                    self.main_app.running = True
                    self.main_app.start_time = time.time()
                    self.main_app.helper_thread = threading.Thread(target=self.main_app.helper_loop, daemon=True)
                    self.main_app.helper_thread.start()
                    
                    self.log("Helper started successfully")
                    self.update_status("Helper running", "#4CAF50")
                    
                    if hasattr(self, 'controls_panel'):
                        self.controls_panel.update_helper_status(True)
                else:
                    self.log("Configure health bar area before starting")
                    self.update_status("Health bar not configured", "#f44336")
        except Exception as e:
            logger.error(f"Error starting helper: {e}")
            self.log(f"Error starting helper: {e}")
    
    def stop_helper(self):
        """Stop the helper"""
        try:
            if self.main_app.running:
                self.main_app.running = False
                if self.main_app.helper_thread and self.main_app.helper_thread.is_alive():
                    self.main_app.helper_thread.join(timeout=2)
                
                self.log("Helper stopped")
                self.update_status("Helper stopped", "#ff9800")
                
                if hasattr(self, 'controls_panel'):
                    self.controls_panel.update_helper_status(False)
        except Exception as e:
            logger.error(f"Error stopping helper: {e}")
            self.log(f"Error stopping helper: {e}")
    
    def helper_loop(self):
        """Main helper loop"""
        while self.main_app.running:
            try:
                # Health detection logic would go here
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in helper loop: {e}")
                break
        
        self.main_app.running = False
    
    def log(self, message):
        """Log message to the log panel"""
        try:
            if hasattr(self, 'log_panel') and hasattr(self.log_panel, 'add_log'):
                self.log_panel.add_log(message)
            else:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] {message}")
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def update_status(self, text, color):
        """Update status bar"""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.config(text=text, fg=color)
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def _create_bottom_status(self, parent):
        """Create bottom status bar"""
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
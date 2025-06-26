import tkinter as tk
from tkinter import ttk, messagebox
import time
import logging
import threading
from PIL import Image, ImageTk

from app.ui.area_config_panel import AreaConfigPanel
from app.ui.navigation_panel import NavigationPanel
from app.ui.controls_panel import ControlsPanel
from app.ui.log_panel import LogPanel
from app.ui.dialogs import StepConfigDialog

logger = logging.getLogger('PokeXHelper')

class PokeXGamesHelper:
    def __init__(self, root):
        logger.info("Initializing PokeXGames Helper")
        self.root = root
        
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
        
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.title("PokeXGames Helper - Navigation & Automation")
        self.root.configure(bg="#1a1a1a")
        
        self._initialize_components()
        self._create_interface()
        
        self.log("PokeXGames Helper interface initialized")
        self._load_configuration()
        self.check_configuration()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        logger.info("PokeXGames Helper GUI initialized successfully")
    
    def _initialize_components(self):
        try:
            from app.screen_capture.area_selector import AreaSelector
            from app.core.health_detector import HealthDetector
            from app.navigation.navigation_manager import NavigationManager
            from app.utils.mouse_controller import MouseController
            
            self.health_bar_selector = AreaSelector(self.root)
            self.minimap_selector = AreaSelector(self.root)
            self.coordinates_selector = AreaSelector(self.root)
            
            self.health_detector = HealthDetector()
            self.mouse_controller = MouseController()
            self.navigation_manager = NavigationManager(
                self.minimap_selector, 
                self.coordinates_selector, 
                self.mouse_controller
            )
            
            logger.info("Components initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import components: {e}")
            raise
        
        self.running = False
        self.start_time = None
        self.heals_used = 0
        self.steps_completed = 0
        
        self.helper_thread = None
    
    def _create_interface(self):
        main_canvas = tk.Canvas(self.root, bg="#1a1a1a", highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_main = tk.Frame(main_canvas, bg="#1a1a1a")
        
        scrollable_main.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_main, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_container = tk.Frame(scrollable_main, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        self._create_header(main_container)
        self._create_content_area(main_container)
    
    def _create_header(self, parent):
        header_frame = tk.Frame(parent, bg="#1a1a1a", height=70)
        header_frame.pack(fill=tk.X, pady=12)
        header_frame.pack_propagate(False)
        
        title_section = tk.Frame(header_frame, bg="#1a1a1a")
        title_section.pack(side=tk.LEFT, fill=tk.Y, pady=8)
        
        title_label = tk.Label(title_section, text="PokeXGames Helper", 
                              font=("Segoe UI", 20, "bold"), bg="#1a1a1a", fg="#ffffff")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(title_section, text="Navigation & Automation Helper", 
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
            self.health_bar_selector,
            self.minimap_selector,
            self.coordinates_selector,
            self
        )
        
        self.navigation_panel = NavigationPanel(
            middle_panel,
            self.navigation_manager,
            self
        )
        
        self.log_panel = LogPanel(right_panel)
        
        self.controls_panel = ControlsPanel(
            right_panel,
            self.health_detector,
            self
        )
    
    def start_area_selection(self, title, color, selector):
        self.log(f"Starting {title} selection...")
        
        def on_completion():
            self.log(f"{title} selection completed")
            self.area_config_panel.update_area_status(selector)
            self.check_configuration()
        
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
        health_configured = self.health_bar_selector.is_setup()
        minimap_configured = self.minimap_selector.is_setup()
        coords_configured = self.coordinates_selector.is_setup()
        
        if health_configured and minimap_configured and coords_configured:
            self.area_config_panel.set_config_status("All areas configured! Helper ready.", "#28a745")
            self.controls_panel.enable_start_button()
        else:
            missing = []
            if not health_configured:
                missing.append("Health Bar")
            if not minimap_configured:
                missing.append("Minimap")
            if not coords_configured:
                missing.append("Coordinates")
            
            self.area_config_panel.set_config_status(f"Configure: {', '.join(missing)}", "#ffc107")
            self.controls_panel.disable_start_button()
    
    def start_helper(self):
        self.log("Starting PokeXGames Helper...")
        self.running = True
        self.start_time = time.time()
        
        self.controls_panel.set_helper_running(True)
        self.update_status("Running", "#28a745")
        
        self.helper_thread = threading.Thread(target=self.helper_loop, daemon=True)
        self.helper_thread.start()
        
        self.controls_panel.start_display_update()
    
    def stop_helper(self):
        self.log("Stopping PokeXGames Helper...")
        self.running = False
        
        if self.navigation_manager.is_navigating:
            self.navigation_manager.stop_navigation()
        
        self.controls_panel.set_helper_running(False)
        self.update_status("Ready", "#28a745")
    
    def helper_loop(self):
        from app.utils.keyboard_input import press_key
        
        while self.running:
            try:
                if self.health_bar_selector.is_setup():
                    health_image = self.health_bar_selector.get_current_screenshot_region()
                    if health_image:
                        health_percent = self.health_detector.detect_health_percentage(health_image)
                        self.area_config_panel.update_health_percentage(health_percent)
                        
                        if self.controls_panel.should_auto_heal(health_percent):
                            heal_key = self.controls_panel.get_heal_key()
                            if press_key(heal_key):
                                self.heals_used += 1
                                self.controls_panel.update_heals_count(self.heals_used)
                                self.log(f"Health low ({health_percent:.1f}%), used heal ({heal_key})")
                
                if self.coordinates_selector.is_setup():
                    current_coords = self.navigation_manager.coordinates_reader.read_coordinates()
                    if current_coords:
                        self.area_config_panel.update_coordinates(current_coords)
                    else:
                        self.area_config_panel.update_coordinates("Not detected")
                
                if self.controls_panel.should_auto_navigate() and not self.navigation_manager.is_navigating:
                    if self.navigation_manager.steps:
                        self.navigation_manager.start_navigation()
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
    
    def save_settings(self):
        try:
            self._save_configuration()
            self.log("Settings saved successfully")
        except Exception as e:
            self.log(f"Error saving settings: {e}")
    
    def _load_configuration(self):
        try:
            from app.config import load_config
            config = load_config()
            
            areas_config = config.get("areas", {})
            
            for area_name, selector in [
                ("health_bar", self.health_bar_selector),
                ("minimap", self.minimap_selector),
                ("coordinates", self.coordinates_selector)
            ]:
                area_config = areas_config.get(area_name, {})
                if area_config.get("configured", False):
                    x1 = area_config.get("x1")
                    y1 = area_config.get("y1")
                    x2 = area_config.get("x2")
                    y2 = area_config.get("y2")
                    
                    if all([x1 is not None, y1 is not None, x2 is not None, y2 is not None]):
                        selector.configure_from_saved(x1, y1, x2, y2)
                        selector.title = area_config.get("name", area_name.replace("_", " ").title())
            
            navigation_steps = config.get("navigation_steps", [])
            if navigation_steps:
                self.navigation_manager.load_steps_data(navigation_steps)
                self.navigation_panel.refresh_steps_display()
            
            self.controls_panel.load_settings_from_config(config)
            self.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.log("Using default configuration")
    
    def _save_configuration(self):
        try:
            from app.config import load_config, save_config
            config = load_config()
            
            for area_name, selector in [
                ("health_bar", self.health_bar_selector),
                ("minimap", self.minimap_selector),
                ("coordinates", self.coordinates_selector)
            ]:
                if selector.is_setup():
                    config["areas"][area_name] = {
                        "name": getattr(selector, 'title', area_name.replace("_", " ").title()),
                        "x1": selector.x1,
                        "y1": selector.y1,
                        "x2": selector.x2,
                        "y2": selector.y2,
                        "configured": True
                    }
            
            self.controls_panel.save_settings_to_config(config)
            config["navigation_steps"] = self.navigation_manager.get_steps_data()
            
            save_config(config)
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def on_closing(self):
        try:
            if self.running:
                self.stop_helper()
            
            if self.navigation_manager.is_navigating:
                self.navigation_manager.stop_navigation()
            
            self._save_configuration()
            logger.info("Application closing gracefully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        finally:
            self.root.destroy()

if __name__ == "__main__":
    import logging
    from app.config import setup_logging
    
    setup_logging()
    
    root = tk.Tk()
    app = PokeXGamesHelper(root)
    root.mainloop()
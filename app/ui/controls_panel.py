import tkinter as tk
from tkinter import ttk
import time

class ControlsPanel:
    def __init__(self, parent, health_detector, main_app):
        self.parent = parent
        self.health_detector = health_detector
        self.main_app = main_app
        
        self._create_ui()
        self._initialize_variables()
        self.display_update_active = False
    
    def _create_ui(self):
        settings_frame = tk.Frame(self.parent, bg="#2d2d2d")
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=12)
        
        self._create_helper_settings(settings_frame)
        
        controls_frame = tk.Frame(self.parent, bg="#2d2d2d")
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
        
        self._create_main_controls(controls_frame)
    
    def _create_helper_settings(self, parent):
        title_label = tk.Label(parent, text="Helper Settings", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=12)
        
        health_frame = tk.LabelFrame(parent, text="Health Management", bg="#2d2d2d", fg="#ffffff", 
                                   font=("Segoe UI", 10, "bold"))
        health_frame.pack(fill=tk.X, pady=8)
        
        heal_controls = tk.Frame(health_frame, bg="#2d2d2d")
        heal_controls.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(heal_controls, text="Heal Key:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.heal_key_var = tk.StringVar(value="F1")
        heal_combo = ttk.Combobox(heal_controls, textvariable=self.heal_key_var,
                                values=["F1", "F2", "F3", "F4", "F5", "1", "2", "3"], 
                                state="readonly", width=6)
        heal_combo.pack(side=tk.LEFT, padx=12)
        
        tk.Label(heal_controls, text="Threshold:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.health_threshold = tk.Scale(heal_controls, from_=0, to=100, orient=tk.HORIZONTAL,
                                       bg="#2d2d2d", fg="#ffffff", troughcolor="#1a1a1a",
                                       highlightthickness=0, activebackground="#dc3545", length=100)
        self.health_threshold.set(60)
        self.health_threshold.pack(side=tk.LEFT, padx=4)
        
        auto_heal_frame = tk.Frame(health_frame, bg="#2d2d2d")
        auto_heal_frame.pack(fill=tk.X, padx=8, pady=8)
        
        self.auto_heal_var = tk.BooleanVar(value=True)
        auto_heal_check = tk.Checkbutton(auto_heal_frame, text="Enable auto healing",
                                       variable=self.auto_heal_var, bg="#2d2d2d", fg="#ffffff",
                                       selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                       activeforeground="#ffffff", font=("Segoe UI", 9))
        auto_heal_check.pack(side=tk.LEFT)
        
        battle_frame = tk.LabelFrame(parent, text="Battle Settings", bg="#2d2d2d", fg="#ffffff", 
                                   font=("Segoe UI", 10, "bold"))
        battle_frame.pack(fill=tk.X, pady=8)
        
        battle_controls = tk.Frame(battle_frame, bg="#2d2d2d")
        battle_controls.pack(fill=tk.X, padx=8, pady=8)
        
        self.battle_detection_var = tk.BooleanVar(value=True)
        battle_detection_check = tk.Checkbutton(battle_controls, text="Enable battle detection",
                                              variable=self.battle_detection_var, bg="#2d2d2d", fg="#ffffff",
                                              selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                              activeforeground="#ffffff", font=("Segoe UI", 9))
        battle_detection_check.pack(side=tk.LEFT)
        
        nav_frame = tk.LabelFrame(parent, text="Navigation", bg="#2d2d2d", fg="#ffffff", 
                                font=("Segoe UI", 10, "bold"))
        nav_frame.pack(fill=tk.X, pady=8)
        
        nav_controls = tk.Frame(nav_frame, bg="#2d2d2d")
        nav_controls.pack(fill=tk.X, padx=8, pady=8)
        
        self.auto_nav_var = tk.BooleanVar(value=False)
        auto_nav_check = tk.Checkbutton(nav_controls, text="Auto navigation",
                                      variable=self.auto_nav_var, bg="#2d2d2d", fg="#ffffff",
                                      selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                      activeforeground="#ffffff", font=("Segoe UI", 9))
        auto_nav_check.pack(side=tk.LEFT)
    
    def _create_main_controls(self, parent):
        stats_frame = tk.Frame(parent, bg="#2d2d2d")
        stats_frame.pack(fill=tk.X, pady=12)
        
        stats_labels = [
            ("Heals Used:", "#dc3545", "heals_var"),
            ("Steps Completed:", "#17a2b8", "steps_var"),
            ("Battles Won:", "#9c27b0", "battles_var"),
            ("Uptime:", "#ffffff", "uptime_var")
        ]
        
        for text, color, var_name in stats_labels:
            frame = tk.Frame(stats_frame, bg="#2d2d2d")
            frame.pack(fill=tk.X, pady=1)
            
            tk.Label(frame, text=text, bg="#2d2d2d", fg=color,
                    font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            
            if var_name == "uptime_var":
                var = tk.StringVar(value="00:00:00")
            else:
                var = tk.StringVar(value="0")
            
            tk.Label(frame, textvariable=var, bg="#2d2d2d", fg="#ffffff",
                    font=("Segoe UI", 9)).pack(side=tk.RIGHT)
            
            setattr(self, var_name, var)
        
        buttons_frame = tk.Frame(parent, bg="#2d2d2d")
        buttons_frame.pack(fill=tk.X)
        
        self.start_btn = tk.Button(buttons_frame, text="START HELPER",
                                 bg="#28a745", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                 font=("Segoe UI", 12, "bold"), height=2, state=tk.DISABLED,
                                 activebackground="#218838", command=self._start_helper_clicked)
        self.start_btn.pack(fill=tk.X, pady=4)
        
        self.stop_btn = tk.Button(buttons_frame, text="STOP HELPER",
                                bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                font=("Segoe UI", 12, "bold"), height=2, state=tk.DISABLED,
                                activebackground="#c82333", command=self._stop_helper_clicked)
        self.stop_btn.pack(fill=tk.X, pady=4)
        
        save_btn = tk.Button(buttons_frame, text="Save Settings",
                           bg="#6c757d", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 10), height=1, activebackground="#5a6268",
                           command=self._save_settings_clicked)
        save_btn.pack(fill=tk.X)
    
    def _initialize_variables(self):
        self.heals_used = 0
        self.steps_completed = 0
        self.battles_won = 0
        self.start_time = None
    
    def _start_helper_clicked(self):
        self.main_app.log("Start Helper button clicked")
        self.main_app.start_helper()
    
    def _stop_helper_clicked(self):
        self.main_app.log("Stop Helper button clicked")
        self.main_app.stop_helper()
    
    def _save_settings_clicked(self):
        self.main_app.log("Save Settings button clicked")
        self.main_app.save_settings()
    
    def enable_start_button(self):
        self.start_btn.config(state=tk.NORMAL)
    
    def disable_start_button(self):
        self.start_btn.config(state=tk.DISABLED)
    
    def set_helper_running(self, running):
        if running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.start_time = time.time()
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def should_auto_heal(self, health_percent):
        return self.auto_heal_var.get() and health_percent < self.health_threshold.get()
    
    def should_auto_navigate(self):
        return self.auto_nav_var.get()
    
    def get_heal_key(self):
        return self.heal_key_var.get()
    
    def update_heals_count(self, count):
        self.heals_used = count
        self.heals_var.set(str(count))
    
    def update_battles_count(self, count):
        self.battles_won = count
        self.battles_var.set(str(count))
    
    def start_display_update(self):
        if not self.display_update_active:
            self.display_update_active = True
            self._update_display()
    
    def _update_display(self):
        if not self.main_app.running:
            self.display_update_active = False
            return
        
        try:
            if self.start_time:
                uptime = time.time() - self.start_time
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            if hasattr(self.main_app, 'navigation_manager'):
                self.steps_var.set(str(self.main_app.navigation_manager.current_step_index))
            
        except Exception:
            pass
        
        if self.display_update_active:
            self.main_app.root.after(1000, self._update_display)
    
    def load_settings_from_config(self, config):
        try:
            self.heal_key_var.set(config.get("health_healing_key", "F1"))
            self.health_threshold.set(config.get("health_threshold", 60))
            
            helper_settings = config.get("helper_settings", {})
            self.auto_heal_var.set(helper_settings.get("auto_heal", True))
            self.auto_nav_var.set(helper_settings.get("auto_navigation", False))
            self.battle_detection_var.set(helper_settings.get("battle_detection_enabled", True))
            
        except Exception as e:
            import logging
            logging.getLogger('PokeXHelper').error(f"Error loading settings: {e}")
    
    def save_settings_to_config(self, config):
        config["health_healing_key"] = self.heal_key_var.get()
        config["health_threshold"] = self.health_threshold.get()
        
        config["helper_settings"] = {
            "auto_heal": self.auto_heal_var.get(),
            "auto_navigation": self.auto_nav_var.get(),
            "battle_detection_enabled": self.battle_detection_var.get(),
            "navigation_check_interval": 0.5,
            "step_timeout": 30,
            "coordinate_validation": True,
            "image_matching_threshold": 0.8
        }
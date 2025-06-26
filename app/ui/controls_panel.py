import time
import tkinter as tk
from tkinter import ttk

class ControlsPanel:
    def __init__(self, parent, health_detector, main_app):
        self.parent = parent
        self.health_detector = health_detector
        self.main_app = main_app
        
        self.display_update_active = False
        
        self._create_ui()
        self._initialize_variables()
    
    def _create_ui(self):
        controls_frame = tk.Frame(self.parent, bg="#2d2d2d")
        controls_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(controls_frame, text="Helper Controls", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(pady=12)
        
        self._create_auto_controls(controls_frame)
        self._create_main_controls(controls_frame)
    
    def _create_auto_controls(self, parent):
        auto_frame = tk.LabelFrame(parent, text="Auto Settings", 
                                  font=("Segoe UI", 10, "bold"), bg="#2d2d2d", 
                                  fg="#ffffff", bd=1, relief=tk.RIDGE)
        auto_frame.pack(fill=tk.X, padx=12, pady=12)
        
        heal_frame = tk.Frame(auto_frame, bg="#2d2d2d")
        heal_frame.pack(fill=tk.X, padx=8, pady=8)
        
        self.auto_heal_var = tk.BooleanVar(value=True)
        auto_heal_check = tk.Checkbutton(heal_frame, text="Auto Heal", 
                                       variable=self.auto_heal_var, bg="#2d2d2d", fg="#ffffff",
                                       selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                       activeforeground="#ffffff", font=("Segoe UI", 9))
        auto_heal_check.pack(side=tk.LEFT)
        
        threshold_frame = tk.Frame(heal_frame, bg="#2d2d2d")
        threshold_frame.pack(side=tk.RIGHT)
        
        tk.Label(threshold_frame, text="Health %:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 4))
        
        self.health_threshold = tk.IntVar(value=30)
        threshold_spin = tk.Spinbox(threshold_frame, from_=10, to=90, width=5,
                                  textvariable=self.health_threshold, font=("Segoe UI", 8))
        threshold_spin.pack(side=tk.LEFT)
        
        key_frame = tk.Frame(auto_frame, bg="#2d2d2d")
        key_frame.pack(fill=tk.X, padx=8, pady=4)
        
        tk.Label(key_frame, text="Heal Key:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.heal_key_var = tk.StringVar(value="F1")
        heal_key_combo = ttk.Combobox(key_frame, textvariable=self.heal_key_var,
                                    values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"],
                                    width=8, font=("Segoe UI", 9), state="readonly")
        heal_key_combo.pack(side=tk.RIGHT)
        
        nav_frame = tk.Frame(auto_frame, bg="#2d2d2d")
        nav_frame.pack(fill=tk.X, padx=8, pady=4)
        
        self.auto_nav_var = tk.BooleanVar(value=False)
        auto_nav_check = tk.Checkbutton(nav_frame, text="Auto Navigate", 
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
    
    def stop_display_update(self):
        self.display_update_active = False
    
    def _update_display(self):
        if self.display_update_active and self.main_app.running:
            if self.start_time:
                elapsed = time.time() - self.start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.main_app.root.after(1000, self._update_display)
        else:
            self.display_update_active = False
    
    def save_settings_to_config(self, config):
        if "helper_settings" not in config:
            config["helper_settings"] = {}
        
        config["helper_settings"].update({
            "auto_heal": self.auto_heal_var.get(),
            "health_threshold": self.health_threshold.get(),
            "heal_key": self.heal_key_var.get(),
            "auto_navigate": self.auto_nav_var.get()
        })
    
    def load_settings_from_config(self, config):
        settings = config.get("helper_settings", {})
        
        self.auto_heal_var.set(settings.get("auto_heal", True))
        self.health_threshold.set(settings.get("health_threshold", 30))
        self.heal_key_var.set(settings.get("heal_key", "F1"))
        self.auto_nav_var.set(settings.get("auto_navigate", False))
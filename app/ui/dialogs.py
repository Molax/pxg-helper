import time
import tkinter as tk
from tkinter import ttk, messagebox

class StepConfigDialog:
    def __init__(self, parent, step=None):
        self.parent = parent
        self.step = step
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configure Navigation Step")
        self.dialog.geometry("450x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        if step:
            self.name_var.set(step.name)
            self.coordinates_var.set(step.coordinates)
            self.wait_seconds_var.set(step.wait_seconds)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="Step Name:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=35, font=("Segoe UI", 10))
        name_entry.grid(row=0, column=1, pady=5, sticky="ew")
        name_entry.focus()
        
        ttk.Label(main_frame, text="Target Coordinates:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.coordinates_var = tk.StringVar()
        coords_entry = ttk.Entry(main_frame, textvariable=self.coordinates_var, width=35, font=("Segoe UI", 10))
        coords_entry.grid(row=1, column=1, pady=5, sticky="ew")
        
        coords_help = ttk.Label(main_frame, text="Optional - e.g., (3947, 3633, 6)", 
                               font=("Segoe UI", 8), foreground="gray")
        coords_help.grid(row=2, column=1, sticky="w", pady=(0, 10))
        
        ttk.Label(main_frame, text="Wait Time (seconds):", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.wait_seconds_var = tk.DoubleVar(value=3.0)
        wait_spinbox = ttk.Spinbox(main_frame, from_=0.5, to=60.0, increment=0.5, 
                                  textvariable=self.wait_seconds_var, width=33, font=("Segoe UI", 10))
        wait_spinbox.grid(row=3, column=1, pady=5, sticky="ew")
        
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)
        
        instructions_label = ttk.Label(main_frame, text="How it works:", 
                                      font=("Segoe UI", 11, "bold"), foreground="#0066cc")
        instructions_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        instructions_frame = tk.Frame(main_frame, bg="#f8f9fa", relief=tk.FLAT, bd=1)
        instructions_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)
        
        instructions_text = tk.Text(instructions_frame, height=8, width=55, wrap=tk.WORD, 
                                   bg="#f8f9fa", font=("Segoe UI", 9), relief=tk.FLAT,
                                   padx=10, pady=10)
        instructions_text.pack(fill="both", expand=True)
        
        instructions_content = """1. After clicking OK, you'll be prompted to select the step icon

2. Use the area selector to capture any icon/button on your screen:
   • Quest markers, NPCs, buildings, UI buttons, etc.
   • Can be anywhere on any monitor
   • Draw a small rectangle around the target

3. During navigation, the helper will:
   • Search for the icon across all monitors
   • Click on it when found
   • Wait for the specified time
   • Continue to the next step

4. Target coordinates are optional for validation"""
        
        instructions_text.insert("1.0", instructions_content)
        instructions_text.config(state=tk.DISABLED)
        
        main_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ok_btn = ttk.Button(button_frame, text="Create Step", command=self._on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a step name.")
            return
            
        self.result = {
            'name': name,
            'coordinates': self.coordinates_var.get().strip(),
            'wait_seconds': self.wait_seconds_var.get()
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()

class SettingsDialog:
    def __init__(self, parent, current_settings):
        self.parent = parent
        self.current_settings = current_settings
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Helper Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_current_settings()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        health_frame = ttk.Frame(notebook)
        notebook.add(health_frame, text="Health")
        
        battle_frame = ttk.Frame(notebook)
        notebook.add(battle_frame, text="Battle")
        
        nav_frame = ttk.Frame(notebook)
        notebook.add(nav_frame, text="Navigation")
        
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        self._create_health_settings(health_frame)
        self._create_battle_settings(battle_frame)
        self._create_navigation_settings(nav_frame)
        self._create_advanced_settings(advanced_frame)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_defaults).pack(side=tk.LEFT)
    
    def _create_health_settings(self, parent):
        ttk.Label(parent, text="Health Management", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        key_frame = ttk.Frame(parent)
        key_frame.pack(fill=tk.X, pady=5)
        ttk.Label(key_frame, text="Healing Key:").pack(side=tk.LEFT)
        self.heal_key_var = tk.StringVar()
        ttk.Combobox(key_frame, textvariable=self.heal_key_var, 
                    values=["F1", "F2", "F3", "F4", "F5", "1", "2", "3"],
                    state="readonly").pack(side=tk.RIGHT)
        
        threshold_frame = ttk.Frame(parent)
        threshold_frame.pack(fill=tk.X, pady=5)
        ttk.Label(threshold_frame, text="Health Threshold:").pack(side=tk.LEFT)
        self.health_threshold_var = tk.IntVar()
        ttk.Scale(threshold_frame, from_=0, to=100, variable=self.health_threshold_var,
                 orient=tk.HORIZONTAL).pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.auto_heal_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable automatic healing", 
                       variable=self.auto_heal_var).pack(anchor=tk.W, pady=5)
    
    def _create_battle_settings(self, parent):
        ttk.Label(parent, text="Battle Detection", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        self.battle_detection_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable battle detection", 
                       variable=self.battle_detection_var).pack(anchor=tk.W, pady=5)
        
        self.auto_battle_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable auto battle (future feature)", 
                       variable=self.auto_battle_var, state=tk.DISABLED).pack(anchor=tk.W, pady=5)
    
    def _create_navigation_settings(self, parent):
        ttk.Label(parent, text="Navigation Settings", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        self.auto_nav_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable automatic navigation", 
                       variable=self.auto_nav_var).pack(anchor=tk.W, pady=5)
        
        timeout_frame = ttk.Frame(parent)
        timeout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(timeout_frame, text="Step Timeout (seconds):").pack(side=tk.LEFT)
        self.step_timeout_var = tk.IntVar()
        ttk.Spinbox(timeout_frame, from_=5, to=120, textvariable=self.step_timeout_var).pack(side=tk.RIGHT)
        
        self.coordinate_validation_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable coordinate validation", 
                       variable=self.coordinate_validation_var).pack(anchor=tk.W, pady=5)
    
    def _create_advanced_settings(self, parent):
        ttk.Label(parent, text="Advanced Settings", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        threshold_frame = ttk.Frame(parent)
        threshold_frame.pack(fill=tk.X, pady=5)
        ttk.Label(threshold_frame, text="Image Matching Threshold:").pack(side=tk.LEFT)
        self.match_threshold_var = tk.DoubleVar()
        ttk.Scale(threshold_frame, from_=0.5, to=1.0, variable=self.match_threshold_var,
                 orient=tk.HORIZONTAL).pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        interval_frame = ttk.Frame(parent)
        interval_frame.pack(fill=tk.X, pady=5)
        ttk.Label(interval_frame, text="Check Interval (seconds):").pack(side=tk.LEFT)
        self.check_interval_var = tk.DoubleVar()
        ttk.Spinbox(interval_frame, from_=0.1, to=5.0, increment=0.1,
                   textvariable=self.check_interval_var).pack(side=tk.RIGHT)
        
        self.debug_mode_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable debug mode", 
                       variable=self.debug_mode_var).pack(anchor=tk.W, pady=5)
    
    def _load_current_settings(self):
        self.heal_key_var.set(self.current_settings.get("health_healing_key", "F1"))
        self.health_threshold_var.set(self.current_settings.get("health_threshold", 60))
        
        helper_settings = self.current_settings.get("helper_settings", {})
        self.auto_heal_var.set(helper_settings.get("auto_heal", True))
        self.auto_nav_var.set(helper_settings.get("auto_navigation", False))
        self.battle_detection_var.set(helper_settings.get("battle_detection_enabled", True))
        self.auto_battle_var.set(helper_settings.get("auto_battle", False))
        self.step_timeout_var.set(helper_settings.get("step_timeout", 30))
        self.coordinate_validation_var.set(helper_settings.get("coordinate_validation", True))
        self.match_threshold_var.set(helper_settings.get("image_matching_threshold", 0.8))
        self.check_interval_var.set(helper_settings.get("navigation_check_interval", 0.5))
        self.debug_mode_var.set(self.current_settings.get("debug_enabled", True))
    
    def _reset_defaults(self):
        self.heal_key_var.set("F1")
        self.health_threshold_var.set(60)
        self.auto_heal_var.set(True)
        self.auto_nav_var.set(False)
        self.battle_detection_var.set(True)
        self.auto_battle_var.set(False)
        self.step_timeout_var.set(30)
        self.coordinate_validation_var.set(True)
        self.match_threshold_var.set(0.8)
        self.check_interval_var.set(0.5)
        self.debug_mode_var.set(True)
    
    def _on_ok(self):
        self.result = {
            "health_healing_key": self.heal_key_var.get(),
            "health_threshold": self.health_threshold_var.get(),
            "debug_enabled": self.debug_mode_var.get(),
            "helper_settings": {
                "auto_heal": self.auto_heal_var.get(),
                "auto_navigation": self.auto_nav_var.get(),
                "battle_detection_enabled": self.battle_detection_var.get(),
                "auto_battle": self.auto_battle_var.get(),
                "step_timeout": self.step_timeout_var.get(),
                "coordinate_validation": self.coordinate_validation_var.get(),
                "image_matching_threshold": self.match_threshold_var.get(),
                "navigation_check_interval": self.check_interval_var.get()
            }
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()
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
        self.dialog.geometry("400x300")
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
        
        ttk.Label(main_frame, text="Step Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(main_frame, text="Coordinates:").grid(row=1, column=0, sticky="w", pady=5)
        self.coordinates_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.coordinates_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(main_frame, text="Wait Seconds:").grid(row=2, column=0, sticky="w", pady=5)
        self.wait_seconds_var = tk.DoubleVar(value=3.0)
        ttk.Spinbox(main_frame, from_=0.5, to=60.0, increment=0.5, 
                   textvariable=self.wait_seconds_var, width=28).grid(row=2, column=1, pady=5)
        
        ttk.Label(main_frame, text="Instructions:", font=("Arial", 9, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=15)
        
        instructions = tk.Text(main_frame, height=6, width=50, wrap=tk.WORD, state=tk.DISABLED,
                              bg="#f0f0f0", font=("Arial", 8))
        instructions.grid(row=4, column=0, columnspan=2, pady=5)
        
        instructions.config(state=tk.NORMAL)
        instructions.insert(tk.END, 
            "1. Click 'Select Step Icon' to capture the icon area in the minimap\n"
            "2. Enter coordinates in format: (x, y, z) - e.g., (3947, 3633, 6)\n"
            "3. Set wait time - how long to wait after clicking before validation\n"
            "4. The helper will click the icon and wait for the character to reach the coordinates")
        instructions.config(state=tk.DISABLED)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Select Step Icon", 
                  command=self._select_icon).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="OK", 
                  command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_cancel).pack(side=tk.LEFT, padx=5)
    
    def _select_icon(self):
        messagebox.showinfo("Select Icon", 
            "The minimap area selection will open next.\n"
            "Draw a small rectangle around the step icon in the minimap.")
    
    def _on_ok(self):
        self.result = {
            'name': self.name_var.get() or f"Step {int(time.time())}",
            'coordinates': self.coordinates_var.get(),
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
        
        nav_frame = ttk.Frame(notebook)
        notebook.add(nav_frame, text="Navigation")
        
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        self._create_health_settings(health_frame)
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
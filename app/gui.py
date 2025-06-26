import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import time
import logging
import threading
from PIL import Image, ImageTk

logger = logging.getLogger('PokeXHelper')

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
        
        ttk.Label(main_frame, text="Instructions:", font=("Arial", 9, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(15, 5))
        
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
        header_frame.pack(fill=tk.X, pady=(0, 12))
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
        status_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        status_label = tk.Label(status_frame, text="Status:", 
                               font=("Segoe UI", 10), bg="#1a1a1a", fg="#b3b3b3")
        status_label.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Label(status_frame, text="●", 
                                       font=("Segoe UI", 16), bg="#1a1a1a", fg="#28a745")
        self.status_indicator.pack(side=tk.LEFT, padx=(5, 0))
        
        self.status_text = tk.Label(status_frame, text="Ready", 
                                   font=("Segoe UI", 10, "bold"), bg="#1a1a1a", fg="#28a745")
        self.status_text.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_content_area(self, parent):
        content_frame = tk.Frame(parent, bg="#1a1a1a")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        left_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        
        middle_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        middle_panel.grid(row=0, column=1, sticky="nsew", padx=(3, 3))
        
        right_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(3, 0))
        
        self._create_area_config_panel(left_panel)
        self._create_navigation_panel(middle_panel)
        self._create_controls_and_log_panel(right_panel)
    
    def _create_area_config_panel(self, parent):
        areas_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        areas_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(areas_frame, text="Area Configuration", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=(0, 12))
        
        for name, color, selector in [
            ("Health Bar", "#dc3545", self.health_bar_selector),
            ("Minimap Area", "#17a2b8", self.minimap_selector),
            ("Coordinates Area", "#ffc107", self.coordinates_selector)
        ]:
            self._create_area_card(areas_frame, name, color, selector)
        
        self.config_status_label = tk.Label(areas_frame, text="Configure areas to continue",
                                           font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffc107")
        self.config_status_label.pack(pady=(12, 0))
        
        health_info_frame = tk.Frame(areas_frame, bg="#2d2d2d")
        health_info_frame.pack(fill=tk.X, pady=(12, 0))
        
        tk.Label(health_info_frame, text="Current Health:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.health_percentage_var = tk.StringVar(value="100.0%")
        tk.Label(health_info_frame, textvariable=self.health_percentage_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        
        coords_info_frame = tk.Frame(areas_frame, bg="#2d2d2d")
        coords_info_frame.pack(fill=tk.X, pady=(8, 0))
        
        tk.Label(coords_info_frame, text="Current Position:", bg="#2d2d2d", fg="#ffc107",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.coordinates_var = tk.StringVar(value="Not detected")
        tk.Label(coords_info_frame, textvariable=self.coordinates_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
    
    def _create_area_card(self, parent, title, color, selector):
        card = tk.Frame(parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, padx=4, pady=4)
        
        header = tk.Frame(card, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        title_label = tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), 
                              bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                             bg="#3d3d3d", fg="#dc3545")
        status_dot.pack(side=tk.RIGHT)
        setattr(selector, 'status_dot', status_dot)
        
        preview_frame = tk.Frame(card, bg="#1a1a1a", height=40)
        preview_frame.pack(fill=tk.X, padx=8, pady=4)
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Not Configured",
                               bg="#1a1a1a", fg="#666666", font=("Segoe UI", 9))
        preview_label.pack(expand=True)
        setattr(selector, 'preview_label', preview_label)
        
        btn_frame = tk.Frame(card, bg="#3d3d3d")
        btn_frame.pack(fill=tk.X, padx=8, pady=(4, 8))
        
        select_btn = tk.Button(btn_frame, text=f"Select {title}",
                             bg=color, fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 9), activebackground=color,
                             command=lambda: self.start_area_selection(title, color, selector))
        select_btn.pack(fill=tk.X)
    
    def _create_navigation_panel(self, parent):
        nav_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        nav_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = tk.Frame(nav_frame, bg="#2d2d2d")
        header_frame.pack(fill=tk.X, pady=(0, 12))
        
        title_label = tk.Label(header_frame, text="Navigation Steps", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        add_btn = tk.Button(header_frame, text="+ Add Step",
                           bg="#28a745", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 10, "bold"), command=self.add_navigation_step)
        add_btn.pack(side=tk.RIGHT)
        
        steps_container = tk.Frame(nav_frame, bg="#2d2d2d")
        steps_container.pack(fill=tk.BOTH, expand=True)
        
        self.steps_canvas = tk.Canvas(steps_container, bg="#2d2d2d", highlightthickness=0, height=400)
        steps_scrollbar = ttk.Scrollbar(steps_container, orient="vertical", command=self.steps_canvas.yview)
        self.steps_frame = tk.Frame(self.steps_canvas, bg="#2d2d2d")
        
        self.steps_frame.bind(
            "<Configure>",
            lambda e: self.steps_canvas.configure(scrollregion=self.steps_canvas.bbox("all"))
        )
        
        self.steps_canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        self.steps_canvas.configure(yscrollcommand=steps_scrollbar.set)
        
        self.steps_canvas.pack(side="left", fill="both", expand=True)
        steps_scrollbar.pack(side="right", fill="y")
        
        nav_controls_frame = tk.Frame(nav_frame, bg="#2d2d2d")
        nav_controls_frame.pack(fill=tk.X, pady=(12, 0))
        
        self.start_nav_btn = tk.Button(nav_controls_frame, text="Start Navigation",
                                     bg="#007acc", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                     font=("Segoe UI", 11, "bold"), state=tk.DISABLED,
                                     command=self.start_navigation)
        self.start_nav_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        self.stop_nav_btn = tk.Button(nav_controls_frame, text="Stop Navigation",
                                    bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                    font=("Segoe UI", 11, "bold"), state=tk.DISABLED,
                                    command=self.stop_navigation)
        self.stop_nav_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
    
    def _create_controls_and_log_panel(self, parent):
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=0)
        
        settings_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        settings_frame.grid(row=0, column=0, sticky="ew")
        
        self._create_helper_settings(settings_frame)
        
        log_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=(0, 12))
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        
        title_label = tk.Label(log_frame, text="Activity Log", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff",
            selectbackground="#ff6b35", selectforeground="#ffffff",
            relief=tk.FLAT, borderwidth=0, font=("Consolas", 9), wrap=tk.WORD
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")
        
        controls_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        controls_frame.grid(row=2, column=0, sticky="ew")
        
        self._create_main_controls(controls_frame)
    
    def _create_helper_settings(self, parent):
        title_label = tk.Label(parent, text="Helper Settings", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=(0, 12))
        
        health_frame = tk.LabelFrame(parent, text="Health Management", bg="#2d2d2d", fg="#ffffff", 
                                   font=("Segoe UI", 10, "bold"))
        health_frame.pack(fill=tk.X, pady=(0, 8))
        
        heal_controls = tk.Frame(health_frame, bg="#2d2d2d")
        heal_controls.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(heal_controls, text="Heal Key:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.heal_key_var = tk.StringVar(value="F1")
        heal_combo = ttk.Combobox(heal_controls, textvariable=self.heal_key_var,
                                values=["F1", "F2", "F3", "F4", "F5", "1", "2", "3"], 
                                state="readonly", width=6)
        heal_combo.pack(side=tk.LEFT, padx=(4, 12))
        
        tk.Label(heal_controls, text="Threshold:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.health_threshold = tk.Scale(heal_controls, from_=0, to=100, orient=tk.HORIZONTAL,
                                       bg="#2d2d2d", fg="#ffffff", troughcolor="#1a1a1a",
                                       highlightthickness=0, activebackground="#dc3545", length=100)
        self.health_threshold.set(60)
        self.health_threshold.pack(side=tk.LEFT, padx=(4, 4))
        
        auto_heal_frame = tk.Frame(health_frame, bg="#2d2d2d")
        auto_heal_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.auto_heal_var = tk.BooleanVar(value=True)
        auto_heal_check = tk.Checkbutton(auto_heal_frame, text="Enable auto healing",
                                       variable=self.auto_heal_var, bg="#2d2d2d", fg="#ffffff",
                                       selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                       activeforeground="#ffffff", font=("Segoe UI", 9))
        auto_heal_check.pack(side=tk.LEFT)
        
        nav_frame = tk.LabelFrame(parent, text="Navigation", bg="#2d2d2d", fg="#ffffff", 
                                font=("Segoe UI", 10, "bold"))
        nav_frame.pack(fill=tk.X, pady=(0, 8))
        
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
        stats_frame.pack(fill=tk.X, pady=(0, 12))
        
        stats_labels = [
            ("Heals Used:", "#dc3545", "heals_var"),
            ("Steps Completed:", "#17a2b8", "steps_var"),
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
                                 activebackground="#218838", command=self.start_helper)
        self.start_btn.pack(fill=tk.X, pady=(0, 4))
        
        self.stop_btn = tk.Button(buttons_frame, text="STOP HELPER",
                                bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                font=("Segoe UI", 12, "bold"), height=2, state=tk.DISABLED,
                                activebackground="#c82333", command=self.stop_helper)
        self.stop_btn.pack(fill=tk.X, pady=(0, 4))
        
        save_btn = tk.Button(buttons_frame, text="Save Settings",
                           bg="#6c757d", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 10), height=1, activebackground="#5a6268",
                           command=self.save_settings)
        save_btn.pack(fill=tk.X)
    
    def add_navigation_step(self):
        if len(self.navigation_manager.steps) >= 20:
            messagebox.showwarning("Maximum Steps", "Maximum 20 navigation steps allowed.")
            return
            
        dialog = StepConfigDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            step = self.navigation_manager.add_step(
                dialog.result['name'],
                dialog.result['coordinates'],
                dialog.result['wait_seconds']
            )
            
            if messagebox.askyesno("Select Step Icon", 
                "Would you like to select the step icon in the minimap now?"):
                self.select_step_icon(step)
            
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def select_step_icon(self, step):
        def on_completion():
            self.log(f"Step icon selected for {step.name}")
        
        try:
            self.minimap_selector.start_selection(
                title=f"Select Icon for {step.name}",
                color="#00ff00",
                completion_callback=on_completion
            )
        except Exception as e:
            self.log(f"Error selecting step icon: {e}")
    
    def refresh_steps_display(self):
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        for i, step in enumerate(self.navigation_manager.steps):
            self.create_step_widget(step, i)
    
    def create_step_widget(self, step, index):
        step_frame = tk.Frame(self.steps_frame, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        step_frame.pack(fill=tk.X, padx=4, pady=2)
        
        header = tk.Frame(step_frame, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        step_label = tk.Label(header, text=f"{step.step_id}. {step.name}", 
                             font=("Segoe UI", 10, "bold"), bg="#3d3d3d", fg="#ffffff")
        step_label.pack(side=tk.LEFT)
        
        delete_btn = tk.Button(header, text="×", font=("Arial", 12, "bold"),
                              bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                              width=3, command=lambda: self.delete_step(step.step_id))
        delete_btn.pack(side=tk.RIGHT)
        
        info_frame = tk.Frame(step_frame, bg="#3d3d3d")
        info_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        if step.coordinates:
            coords_label = tk.Label(info_frame, text=f"Target: {step.coordinates}",
                                   font=("Segoe UI", 8), bg="#3d3d3d", fg="#17a2b8")
            coords_label.pack(anchor=tk.W)
        
        wait_label = tk.Label(info_frame, text=f"Wait: {step.wait_seconds}s",
                             font=("Segoe UI", 8), bg="#3d3d3d", fg="#ffc107")
        wait_label.pack(anchor=tk.W)
        
        status_label = tk.Label(info_frame, text="✓ Ready" if step.template_image else "⚠ No Icon",
                               font=("Segoe UI", 8), bg="#3d3d3d", 
                               fg="#28a745" if step.template_image else "#dc3545")
        status_label.pack(anchor=tk.W)
    
    def delete_step(self, step_id):
        if messagebox.askyesno("Delete Step", f"Delete step {step_id}?"):
            self.navigation_manager.remove_step(step_id)
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def start_area_selection(self, title, color, selector):
        self.log(f"Starting {title} selection...")
        
        def on_completion():
            self.log(f"{title} selection completed")
            self.update_area_status(selector)
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
    
    def update_area_status(self, selector):
        if hasattr(selector, 'status_dot') and hasattr(selector, 'preview_label'):
            if selector.is_setup():
                selector.status_dot.config(fg="#28a745")
                selector.preview_label.config(text="Configured", fg="#28a745")
            else:
                selector.status_dot.config(fg="#dc3545")
                selector.preview_label.config(text="Not Configured", fg="#666666")
    
    def check_configuration(self):
        health_configured = self.health_bar_selector.is_setup()
        minimap_configured = self.minimap_selector.is_setup()
        coords_configured = self.coordinates_selector.is_setup()
        
        if health_configured and minimap_configured and coords_configured:
            self.config_status_label.config(text="All areas configured! Helper ready.", fg="#28a745")
            self.start_btn.config(state=tk.NORMAL)
        else:
            missing = []
            if not health_configured:
                missing.append("Health Bar")
            if not minimap_configured:
                missing.append("Minimap")
            if not coords_configured:
                missing.append("Coordinates")
            
            self.config_status_label.config(text=f"Configure: {', '.join(missing)}", fg="#ffc107")
            self.start_btn.config(state=tk.DISABLED)
        
        for selector in [self.health_bar_selector, self.minimap_selector, self.coordinates_selector]:
            self.update_area_status(selector)
    
    def check_navigation_ready(self):
        if self.navigation_manager.steps and self.minimap_selector.is_setup():
            self.start_nav_btn.config(state=tk.NORMAL)
        else:
            self.start_nav_btn.config(state=tk.DISABLED)
    
    def start_navigation(self):
        if self.navigation_manager.start_navigation():
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
            self.log("Navigation started")
        else:
            self.log("Failed to start navigation")
    
    def stop_navigation(self):
        self.navigation_manager.stop_navigation()
        self.start_nav_btn.config(state=tk.NORMAL)
        self.stop_nav_btn.config(state=tk.DISABLED)
        self.log("Navigation stopped")
    
    def start_helper(self):
        self.log("Starting PokeXGames Helper...")
        self.running = True
        self.start_time = time.time()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.update_status("Running", "#28a745")
        
        self.helper_thread = threading.Thread(target=self.helper_loop, daemon=True)
        self.helper_thread.start()
        
        self._update_display()
    
    def stop_helper(self):
        self.log("Stopping PokeXGames Helper...")
        self.running = False
        
        if self.navigation_manager.is_navigating:
            self.navigation_manager.stop_navigation()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.update_status("Ready", "#28a745")
    
    def helper_loop(self):
        from app.utils.keyboard_input import press_key
        
        while self.running:
            try:
                if self.health_bar_selector.is_setup():
                    health_image = self.health_bar_selector.get_current_screenshot_region()
                    if health_image:
                        health_percent = self.health_detector.detect_health_percentage(health_image)
                        self.health_percentage_var.set(f"{health_percent:.1f}%")
                        
                        if self.auto_heal_var.get() and health_percent < self.health_threshold.get():
                            heal_key = self.heal_key_var.get()
                            if press_key(heal_key):
                                self.heals_used += 1
                                self.heals_var.set(str(self.heals_used))
                                self.log(f"Health low ({health_percent:.1f}%), used heal ({heal_key})")
                
                if self.coordinates_selector.is_setup():
                    current_coords = self.navigation_manager.coordinates_reader.read_coordinates()
                    if current_coords:
                        self.coordinates_var.set(current_coords)
                    else:
                        self.coordinates_var.set("Not detected")
                
                if self.auto_nav_var.get() and not self.navigation_manager.is_navigating:
                    if self.navigation_manager.steps:
                        self.navigation_manager.start_navigation()
                        self.log("Auto-navigation started")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in helper loop: {e}")
                self.log(f"Helper error: {e}")
                time.sleep(1.0)
        
        self.log("Helper stopped")
    
    def _update_display(self):
        if not self.running:
            return
        
        try:
            if self.start_time:
                uptime = time.time() - self.start_time
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.steps_var.set(str(self.navigation_manager.current_step_index))
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
        
        if self.running:
            self.root.after(1000, self._update_display)
    
    def update_status(self, text, color):
        self.status_indicator.config(fg=color)
        self.status_text.config(text=text, fg=color)
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
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
                self.refresh_steps_display()
            
            self._load_settings_from_config(config)
            self.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.log("Using default configuration")
    
    def _load_settings_from_config(self, config):
        try:
            self.heal_key_var.set(config.get("health_healing_key", "F1"))
            self.health_threshold.set(config.get("health_threshold", 60))
            
            helper_settings = config.get("helper_settings", {})
            self.auto_heal_var.set(helper_settings.get("auto_heal", True))
            self.auto_nav_var.set(helper_settings.get("auto_navigation", False))
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
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
            
            config["health_healing_key"] = self.heal_key_var.get()
            config["health_threshold"] = self.health_threshold.get()
            
            config["helper_settings"] = {
                "auto_heal": self.auto_heal_var.get(),
                "auto_navigation": self.auto_nav_var.get(),
                "navigation_check_interval": 0.5,
                "step_timeout": 30,
                "coordinate_validation": True,
                "image_matching_threshold": 0.8
            }
            
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
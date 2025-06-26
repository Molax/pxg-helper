import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
import logging
import threading
from PIL import Image, ImageTk

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
        
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.title("PokeXGames Helper")
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
            from app.core.pokemon_detector import HealthDetector, PokemonDetector, BattleDetector
            
            self.area_1_selector = AreaSelector(self.root)
            self.area_2_selector = AreaSelector(self.root)
            self.area_3_selector = AreaSelector(self.root)
            self.health_bar_selector = AreaSelector(self.root)
            
            self.health_detector = HealthDetector()
            self.pokemon_detector = PokemonDetector()
            self.battle_detector = BattleDetector()
            
            logger.info("Components initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import components: {e}")
            raise
        
        self.running = False
        self.start_time = None
        self.heals_used = 0
        
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
        
        subtitle_label = tk.Label(title_section, text="Pokemon Battle Assistant", 
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
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        
        left_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left_panel.grid_rowconfigure(1, weight=1)
        
        right_panel = tk.Frame(content_frame, bg="#2d2d2d", relief=tk.FLAT, bd=1)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=2)
        right_panel.grid_rowconfigure(1, weight=1)
        
        self._create_area_selection_panel(left_panel)
        self._create_log_panel(left_panel)
        self._create_settings_panel(right_panel)
        self._create_controls_panel(right_panel)
    
    def _create_area_selection_panel(self, parent):
        areas_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        areas_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        title_label = tk.Label(areas_frame, text="Area Configuration", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=(0, 12))
        
        areas_grid = tk.Frame(areas_frame, bg="#2d2d2d")
        areas_grid.pack(fill=tk.X)
        
        main_areas = tk.Frame(areas_grid, bg="#2d2d2d")
        main_areas.pack(fill=tk.X, pady=(0, 8))
        
        for i, (name, color, selector) in enumerate([
            ("Area 1", "#ff6b35", self.area_1_selector),
            ("Area 2", "#4ecdc4", self.area_2_selector),
            ("Area 3", "#45b7d1", self.area_3_selector)
        ]):
            main_areas.grid_columnconfigure(i, weight=1, uniform="area")
            self._create_area_card(main_areas, name, color, selector, 0, i)
        
        health_frame = tk.Frame(areas_grid, bg="#2d2d2d")
        health_frame.pack(fill=tk.X)
        
        self._create_health_card(health_frame)
        
        self.config_status_label = tk.Label(areas_frame, text="Configure areas to continue",
                                           font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffc107")
        self.config_status_label.pack(pady=(12, 0))
    
    def _create_area_card(self, parent, title, color, selector, row, col):
        card = tk.Frame(parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        
        header = tk.Frame(card, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        title_label = tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), 
                              bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                             bg="#3d3d3d", fg="#dc3545")
        status_dot.pack(side=tk.RIGHT)
        setattr(selector, 'status_dot', status_dot)
        
        preview_frame = tk.Frame(card, bg="#1a1a1a", height=50)
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
    
    def _create_health_card(self, parent):
        card = tk.Frame(parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, padx=4, pady=4)
        
        header = tk.Frame(card, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=12, pady=(12, 8))
        
        title_label = tk.Label(header, text="Health Bar", 
                              font=("Segoe UI", 11, "bold"), bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                             bg="#3d3d3d", fg="#dc3545")
        status_dot.pack(side=tk.RIGHT)
        setattr(self.health_bar_selector, 'status_dot', status_dot)
        
        content = tk.Frame(card, bg="#3d3d3d")
        content.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        preview_frame = tk.Frame(content, bg="#1a1a1a", width=100, height=40)
        preview_frame.pack(side=tk.LEFT, padx=(0, 12))
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Not Configured",
                               bg="#1a1a1a", fg="#666666", font=("Segoe UI", 9))
        preview_label.pack(expand=True)
        setattr(self.health_bar_selector, 'preview_label', preview_label)
        
        controls_frame = tk.Frame(content, bg="#3d3d3d")
        controls_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        select_btn = tk.Button(controls_frame, text="Select Health Bar",
                             bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 10), activebackground="#c82333",
                             command=lambda: self.start_area_selection("Health Bar", "#dc3545", self.health_bar_selector))
        select_btn.pack(fill=tk.X, pady=(0, 4))
        
        health_info_frame = tk.Frame(controls_frame, bg="#3d3d3d")
        health_info_frame.pack(fill=tk.X)
        
        tk.Label(health_info_frame, text="Health:", bg="#3d3d3d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.health_percentage_var = tk.StringVar(value="100.0%")
        tk.Label(health_info_frame, textvariable=self.health_percentage_var, 
                bg="#3d3d3d", fg="#ffffff", font=("Segoe UI", 9)).pack(side=tk.RIGHT)
    
    def _create_log_panel(self, parent):
        log_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        
        title_label = tk.Label(log_frame, text="Activity Log", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff",
            selectbackground="#ff6b35", selectforeground="#ffffff",
            relief=tk.FLAT, borderwidth=0, font=("Consolas", 10), wrap=tk.WORD
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")
    
    def _create_settings_panel(self, parent):
        settings_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        settings_frame.grid(row=0, column=0, sticky="nsew")
        settings_frame.grid_rowconfigure(1, weight=1)
        
        title_label = tk.Label(settings_frame, text="Helper Settings", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        settings_content = tk.Frame(settings_frame, bg="#2d2d2d")
        settings_content.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        
        self._create_health_settings(settings_content)
        self._create_behavior_settings(settings_content)
        self._create_detection_settings(settings_content)
    
    def _create_health_settings(self, parent):
        frame = tk.LabelFrame(parent, text="Health Management", bg="#2d2d2d", fg="#ffffff", 
                             font=("Segoe UI", 10, "bold"))
        frame.pack(fill=tk.X, padx=4, pady=(0, 8))
        
        heal_frame = tk.Frame(frame, bg="#2d2d2d")
        heal_frame.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(heal_frame, text="Heal Key:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.heal_key_var = tk.StringVar(value="F1")
        heal_combo = ttk.Combobox(heal_frame, textvariable=self.heal_key_var,
                                values=["F1", "F2", "F3", "F4", "F5", "1", "2", "3"], 
                                state="readonly", width=6)
        heal_combo.pack(side=tk.LEFT, padx=(4, 12))
        
        threshold_frame = tk.Frame(frame, bg="#2d2d2d")
        threshold_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        tk.Label(threshold_frame, text="Health Threshold:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.health_threshold = tk.Scale(threshold_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                       bg="#2d2d2d", fg="#ffffff", troughcolor="#1a1a1a",
                                       highlightthickness=0, activebackground="#dc3545")
        self.health_threshold.set(60)
        self.health_threshold.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))
        
        self.threshold_label = tk.Label(threshold_frame, text="60%", bg="#2d2d2d", fg="#dc3545",
                                       font=("Segoe UI", 9, "bold"), width=5)
        self.threshold_label.pack(side=tk.RIGHT)
        
        self.health_threshold.bind("<Motion>", lambda e: self.threshold_label.config(text=f"{self.health_threshold.get()}%"))
        
        auto_heal_frame = tk.Frame(frame, bg="#2d2d2d")
        auto_heal_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.auto_heal_var = tk.BooleanVar(value=True)
        auto_heal_check = tk.Checkbutton(auto_heal_frame, text="Enable auto healing",
                                       variable=self.auto_heal_var, bg="#2d2d2d", fg="#ffffff",
                                       selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                       activeforeground="#ffffff", font=("Segoe UI", 9))
        auto_heal_check.pack(side=tk.LEFT)
    
    def _create_behavior_settings(self, parent):
        frame = tk.LabelFrame(parent, text="Helper Behavior", bg="#2d2d2d", fg="#ffffff", 
                             font=("Segoe UI", 10, "bold"))
        frame.pack(fill=tk.X, padx=4, pady=(0, 8))
        
        scan_frame = tk.Frame(frame, bg="#2d2d2d")
        scan_frame.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(scan_frame, text="Scan Interval:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.scan_interval = tk.Scale(scan_frame, from_=0.1, to=2.0, resolution=0.1,
                                    orient=tk.HORIZONTAL, bg="#2d2d2d", fg="#ffffff",
                                    troughcolor="#1a1a1a", highlightthickness=0)
        self.scan_interval.set(0.5)
        self.scan_interval.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))
        
        self.scan_label = tk.Label(scan_frame, text="0.5s", bg="#2d2d2d", fg="#ffffff",
                                 font=("Segoe UI", 9), width=5)
        self.scan_label.pack(side=tk.RIGHT)
        
        self.scan_interval.bind("<Motion>", lambda e: self.scan_label.config(text=f"{self.scan_interval.get()}s"))
        
        debug_frame = tk.Frame(frame, bg="#2d2d2d")
        debug_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.debug_var = tk.BooleanVar()
        debug_check = tk.Checkbutton(debug_frame, text="Enable debug mode",
                                   variable=self.debug_var, bg="#2d2d2d", fg="#ffffff",
                                   selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                   activeforeground="#ffffff", font=("Segoe UI", 9))
        debug_check.pack(side=tk.LEFT)
    
    def _create_detection_settings(self, parent):
        frame = tk.LabelFrame(parent, text="Detection Settings", bg="#2d2d2d", fg="#ffffff", 
                             font=("Segoe UI", 10, "bold"))
        frame.pack(fill=tk.X, padx=4, pady=(0, 8))
        
        threshold_frame = tk.Frame(frame, bg="#2d2d2d")
        threshold_frame.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(threshold_frame, text="Match Threshold:", bg="#2d2d2d", fg="#ffffff",
                font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.match_threshold = tk.Scale(threshold_frame, from_=0.5, to=1.0, resolution=0.05,
                                      orient=tk.HORIZONTAL, bg="#2d2d2d", fg="#ffffff",
                                      troughcolor="#1a1a1a", highlightthickness=0)
        self.match_threshold.set(0.8)
        self.match_threshold.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))
        
        self.match_label = tk.Label(threshold_frame, text="0.8", bg="#2d2d2d", fg="#ffffff",
                                   font=("Segoe UI", 9), width=5)
        self.match_label.pack(side=tk.RIGHT)
        
        self.match_threshold.bind("<Motion>", lambda e: self.match_label.config(text=f"{self.match_threshold.get():.2f}"))
        
        pokemon_frame = tk.Frame(frame, bg="#2d2d2d")
        pokemon_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        
        self.pokemon_detection_var = tk.BooleanVar(value=True)
        pokemon_check = tk.Checkbutton(pokemon_frame, text="Pokemon detection",
                                     variable=self.pokemon_detection_var, bg="#2d2d2d", fg="#ffffff",
                                     selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                     activeforeground="#ffffff", font=("Segoe UI", 9))
        pokemon_check.pack(side=tk.LEFT)
        
        battle_frame = tk.Frame(frame, bg="#2d2d2d")
        battle_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.battle_detection_var = tk.BooleanVar(value=True)
        battle_check = tk.Checkbutton(battle_frame, text="Battle detection",
                                    variable=self.battle_detection_var, bg="#2d2d2d", fg="#ffffff",
                                    selectcolor="#1a1a1a", activebackground="#2d2d2d",
                                    activeforeground="#ffffff", font=("Segoe UI", 9))
        battle_check.pack(side=tk.LEFT)
    
    def _create_controls_panel(self, parent):
        controls_frame = tk.Frame(parent, bg="#2d2d2d", padx=12, pady=12)
        controls_frame.grid(row=1, column=0, sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        
        helper_frame = tk.Frame(controls_frame, bg="#2d2d2d")
        helper_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        helper_frame.grid_columnconfigure(0, weight=1)
        helper_frame.grid_columnconfigure(1, weight=1)
        
        self.start_btn = tk.Button(helper_frame, text="START HELPER",
                                 bg="#28a745", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                 font=("Segoe UI", 12, "bold"), height=2, state=tk.DISABLED,
                                 activebackground="#218838", command=self.start_helper)
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        self.stop_btn = tk.Button(helper_frame, text="STOP HELPER",
                                bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                font=("Segoe UI", 12, "bold"), height=2, state=tk.DISABLED,
                                activebackground="#c82333", command=self.stop_helper)
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        
        stats_frame = tk.Frame(controls_frame, bg="#2d2d2d")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        
        self._create_stats_display(stats_frame)
        
        actions_frame = tk.Frame(controls_frame, bg="#2d2d2d")
        actions_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        
        reset_btn = tk.Button(actions_frame, text="Reset Stats",
                             bg="#6c757d", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 10), height=1, activebackground="#5a6268",
                             command=self.reset_stats)
        reset_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        save_btn = tk.Button(actions_frame, text="Save Settings",
                           bg="#17a2b8", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 10), height=1, activebackground="#138496",
                           command=self.save_settings)
        save_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))
    
    def _create_stats_display(self, parent):
        stats_grid = tk.Frame(parent, bg="#2d2d2d")
        stats_grid.pack(fill=tk.X)
        
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)
        
        labels = [
            ("Heals Used:", "#dc3545", "heals_var"),
            ("Pokemon Found:", "#4ecdc4", "pokemon_var"),
            ("Battles:", "#45b7d1", "battles_var"),
            ("Uptime:", "#ffffff", "uptime_var"),
            ("Health:", "#dc3545", "health_var"),
            ("Status:", "#28a745", "status_var")
        ]
        
        for i, (text, color, var_name) in enumerate(labels):
            row, col = divmod(i, 3)
            
            frame = tk.Frame(stats_grid, bg="#2d2d2d")
            frame.grid(row=row, column=col, sticky="ew", padx=1, pady=1)
            
            tk.Label(frame, text=text, bg="#2d2d2d", fg=color,
                    font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            
            if var_name == "uptime_var":
                var = tk.StringVar(value="00:00:00")
            elif var_name == "health_var":
                var = tk.StringVar(value="100%")
            elif var_name == "status_var":
                var = tk.StringVar(value="Ready")
            else:
                var = tk.StringVar(value="0")
            
            label = tk.Label(frame, textvariable=var, bg="#2d2d2d", fg="#ffffff",
                           font=("Segoe UI", 9))
            label.pack(side=tk.RIGHT)
            
            setattr(self, var_name, var)
    
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
                
                if hasattr(selector, 'preview_image') and selector.preview_image:
                    try:
                        img = selector.preview_image.resize((80, 40), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        selector.preview_label.config(image=photo, text="")
                        selector.preview_label.image = photo
                    except Exception as e:
                        logger.debug(f"Could not update preview image: {e}")
            else:
                selector.status_dot.config(fg="#dc3545")
                selector.preview_label.config(text="Not Configured", fg="#666666")
    
    def check_configuration(self):
        health_configured = self.health_bar_selector.is_setup()
        areas_configured = sum([
            self.area_1_selector.is_setup(),
            self.area_2_selector.is_setup(),
            self.area_3_selector.is_setup()
        ])
        
        if health_configured:
            self.config_status_label.config(text="Health bar configured! Helper ready to start.", fg="#28a745")
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.config_status_label.config(text="Configure health bar to continue", fg="#ffc107")
            self.start_btn.config(state=tk.DISABLED)
        
        for selector in [self.area_1_selector, self.area_2_selector, self.area_3_selector, self.health_bar_selector]:
            self.update_area_status(selector)
    
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
                        self.health_var.set(f"{health_percent:.0f}%")
                        
                        if self.auto_heal_var.get() and health_percent < self.health_threshold.get():
                            heal_key = self.heal_key_var.get()
                            if press_key(heal_key):
                                self.heals_used += 1
                                self.heals_var.set(str(self.heals_used))
                                self.log(f"Health low ({health_percent:.1f}%), used heal ({heal_key})")
                
                time.sleep(self.scan_interval.get())
                
            except Exception as e:
                logger.error(f"Error in helper loop: {e}")
                self.log(f"Helper error: {e}")
                time.sleep(1.0)
        
        self.log("Helper stopped")
    
    def reset_stats(self):
        self.heals_used = 0
        self.start_time = None
        
        self.heals_var.set("0")
        self.pokemon_var.set("0")
        self.battles_var.set("0")
        self.uptime_var.set("00:00:00")
        self.health_var.set("100%")
        
        self.log("Statistics reset")
    
    def save_settings(self):
        try:
            self._save_configuration()
            self.log("Settings saved successfully")
        except Exception as e:
            self.log(f"Error saving settings: {e}")
    
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
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
        
        if self.running:
            self.root.after(1000, self._update_display)
    
    def update_status(self, text, color):
        self.status_indicator.config(fg=color)
        self.status_text.config(text=text, fg=color)
        self.status_var.set(text)
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        logger.info(message)
    
    def _load_configuration(self):
        try:
            from app.config import load_config
            config = load_config()
            
            areas_config = config.get("areas", {})
            
            for area_name, selector in [
                ("area_1", self.area_1_selector),
                ("area_2", self.area_2_selector),
                ("area_3", self.area_3_selector),
                ("health_bar", self.health_bar_selector)
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
            
            self._load_settings_from_config(config)
            self.log("Configuration loaded from file")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.log("Using default configuration")
    
    def _load_settings_from_config(self, config):
        try:
            self.heal_key_var.set(config.get("health_healing_key", "F1"))
            self.health_threshold.set(config.get("health_threshold", 60))
            self.scan_interval.set(config.get("scan_interval", 0.5))
            self.debug_var.set(config.get("debug_enabled", False))
            
            helper_settings = config.get("helper_settings", {})
            self.auto_heal_var.set(helper_settings.get("auto_heal", True))
            self.match_threshold.set(helper_settings.get("image_matching_threshold", 0.8))
            self.pokemon_detection_var.set(helper_settings.get("pokemon_detection_enabled", True))
            self.battle_detection_var.set(helper_settings.get("battle_detection_enabled", True))
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def _save_configuration(self):
        try:
            from app.config import load_config, save_config
            config = load_config()
            
            for area_name, selector in [
                ("area_1", self.area_1_selector),
                ("area_2", self.area_2_selector),
                ("area_3", self.area_3_selector),
                ("health_bar", self.health_bar_selector)
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
            config["scan_interval"] = self.scan_interval.get()
            config["debug_enabled"] = self.debug_var.get()
            
            config["helper_settings"] = {
                "auto_heal": self.auto_heal_var.get(),
                "image_matching_threshold": self.match_threshold.get(),
                "pokemon_detection_enabled": self.pokemon_detection_var.get(),
                "battle_detection_enabled": self.battle_detection_var.get()
            }
            
            save_config(config)
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def on_closing(self):
        try:
            if self.running:
                self.stop_helper()
            
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
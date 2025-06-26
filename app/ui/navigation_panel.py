import tkinter as tk
from tkinter import ttk, messagebox
from app.ui.dialogs import StepConfigDialog

class NavigationPanel:
    def __init__(self, parent, navigation_manager, main_app):
        self.parent = parent
        self.navigation_manager = navigation_manager
        self.main_app = main_app
        
        self._create_ui()
    
    def _create_ui(self):
        nav_frame = tk.Frame(self.parent, bg="#2d2d2d")
        nav_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        self._create_header(nav_frame)
        self._create_steps_area(nav_frame)
        self._create_controls(nav_frame)
    
    def _create_header(self, parent):
        header_frame = tk.Frame(parent, bg="#2d2d2d")
        header_frame.pack(fill=tk.X, pady=12)
        
        title_label = tk.Label(header_frame, text="Navigation Steps", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        add_btn = tk.Button(header_frame, text="+ Add Step",
                           bg="#28a745", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 10, "bold"), command=self.add_navigation_step)
        add_btn.pack(side=tk.RIGHT)
    
    def _create_steps_area(self, parent):
        steps_container = tk.Frame(parent, bg="#2d2d2d")
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
    
    def _create_controls(self, parent):
        nav_controls_frame = tk.Frame(parent, bg="#2d2d2d")
        nav_controls_frame.pack(fill=tk.X, pady=12)
        
        self.start_nav_btn = tk.Button(nav_controls_frame, text="Start Navigation",
                                     bg="#007acc", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                     font=("Segoe UI", 11, "bold"), state=tk.DISABLED,
                                     command=self.start_navigation)
        self.start_nav_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        
        self.stop_nav_btn = tk.Button(nav_controls_frame, text="Stop Navigation",
                                    bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                                    font=("Segoe UI", 11, "bold"), state=tk.DISABLED,
                                    command=self.stop_navigation)
        self.stop_nav_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
    
    def add_navigation_step(self):
        if len(self.navigation_manager.steps) >= 20:
            messagebox.showwarning("Maximum Steps", "Maximum 20 navigation steps allowed.")
            return
            
        dialog = StepConfigDialog(self.main_app.root)
        self.main_app.root.wait_window(dialog.dialog)
        
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
            self.main_app.log(f"Step icon selected for {step.name}")
        
        try:
            self.main_app.minimap_selector.start_selection(
                title=f"Select Icon for {step.name}",
                color="#00ff00",
                completion_callback=on_completion
            )
        except Exception as e:
            self.main_app.log(f"Error selecting step icon: {e}")
    
    def refresh_steps_display(self):
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        for i, step in enumerate(self.navigation_manager.steps):
            self.create_step_widget(step, i)
    
    def create_step_widget(self, step, index):
        step_frame = tk.Frame(self.steps_frame, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        step_frame.pack(fill=tk.X, padx=4, pady=2)
        
        header = tk.Frame(step_frame, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=8)
        
        step_label = tk.Label(header, text=f"{step.step_id}. {step.name}", 
                             font=("Segoe UI", 10, "bold"), bg="#3d3d3d", fg="#ffffff")
        step_label.pack(side=tk.LEFT)
        
        delete_btn = tk.Button(header, text="×", font=("Arial", 12, "bold"),
                              bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                              width=3, command=lambda: self.delete_step(step.step_id))
        delete_btn.pack(side=tk.RIGHT)
        
        info_frame = tk.Frame(step_frame, bg="#3d3d3d")
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        
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
    
    def check_navigation_ready(self):
        if self.navigation_manager.steps and self.main_app.minimap_selector.is_setup():
            self.start_nav_btn.config(state=tk.NORMAL)
        else:
            self.start_nav_btn.config(state=tk.DISABLED)
    
    def start_navigation(self):
        if self.navigation_manager.start_navigation():
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
            self.main_app.log("Navigation started")
        else:
            self.main_app.log("Failed to start navigation")
    
    def stop_navigation(self):
        self.navigation_manager.stop_navigation()
        self.start_nav_btn.config(state=tk.NORMAL)
        self.stop_nav_btn.config(state=tk.DISABLED)
        self.main_app.log("Navigation stopped")
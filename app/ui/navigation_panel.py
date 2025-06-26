import os
import tkinter as tk
from tkinter import ttk, messagebox
from app.ui.dialogs import StepConfigDialog

class NavigationPanel:
    def __init__(self, parent, navigation_manager, main_app):
        self.parent = parent
        self.navigation_manager = navigation_manager
        self.main_app = main_app
        self.navigation_running = False
        
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
            
            self.main_app.log(f"Created step {step.step_id}: '{step.name}'")
            
            if messagebox.askyesno("Select Step Icon", 
                f"Would you like to select the icon for '{step.name}' now?\n\n"
                "You can select any area on your screen containing the icon\n"
                "that represents this navigation step."):
                self.select_step_icon(step)
            else:
                self.refresh_steps_display()
                self.check_navigation_ready()
    
    def select_step_icon(self, step):
        if not self.main_app.minimap_selector.is_setup():
            messagebox.showerror("Minimap Not Configured", 
                "Please configure the minimap area first before selecting step icons.")
            return
        
        self.main_app.log(f"Select an icon for '{step.name}' within the minimap area")
        
        def on_selection_complete():
            self.main_app.log(f"Icon selection completed for '{step.name}'")
            self.refresh_steps_display()
            self.check_navigation_ready()
        
        try:
            from app.screen_capture.area_selector import AreaSelector
            
            icon_selector = AreaSelector(self.main_app.root)
            
            def on_icon_completion():
                if icon_selector.is_setup():
                    icon_bounds = (icon_selector.x1, icon_selector.y1, icon_selector.x2, icon_selector.y2)
                    if self.navigation_manager.save_step_icon(step, icon_bounds):
                        self.main_app.log(f"Icon saved for step '{step.name}'")
                        self.refresh_steps_display()
                        self.check_navigation_ready()
                    else:
                        self.main_app.log(f"Failed to save icon for step '{step.name}'")
                else:
                    self.main_app.log(f"Icon selection cancelled for step '{step.name}'")
            
            success = icon_selector.start_selection(
                title=f"Select Icon for '{step.name}' (in minimap area)",
                color="#00ff00",
                completion_callback=on_icon_completion
            )
            
            if not success:
                self.main_app.log(f"Failed to start icon selection for step '{step.name}'")
                
        except Exception as e:
            self.main_app.log(f"Error selecting step icon: {e}")
    
    def refresh_steps_display(self):
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        self.main_app.log(f"Refreshing steps display - {len(self.navigation_manager.steps)} steps")
        
        for i, step in enumerate(self.navigation_manager.steps):
            self.create_step_widget(step, i)
    
    def create_step_widget(self, step, index):
        step_frame = tk.Frame(self.steps_frame, bg="#1a1a1a", relief=tk.RIDGE, bd=1)
        step_frame.pack(fill=tk.X, pady=4, padx=8)
        
        main_frame = tk.Frame(step_frame, bg="#1a1a1a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        header_frame = tk.Frame(main_frame, bg="#1a1a1a")
        header_frame.pack(fill=tk.X)
        
        step_label = tk.Label(header_frame, text=f"Step {step.step_id}: {step.name}",
                             font=("Segoe UI", 12, "bold"), bg="#1a1a1a", fg="#ffffff")
        step_label.pack(side=tk.LEFT)
        
        if step.is_active:
            status_text = "Active"
            status_color = "#28a745"
        else:
            status_text = "Inactive"
            status_color = "#6c757d"
        
        status_label = tk.Label(header_frame, text=status_text,
                               font=("Segoe UI", 9, "bold"), bg="#1a1a1a", fg=status_color)
        status_label.pack(side=tk.RIGHT)
        
        details_frame = tk.Frame(main_frame, bg="#1a1a1a")
        details_frame.pack(fill=tk.X, pady=4)
        
        if step.coordinates:
            coord_label = tk.Label(details_frame, text=f"Target: {step.coordinates}",
                                  font=("Segoe UI", 9), bg="#1a1a1a", fg="#cccccc")
            coord_label.pack(side=tk.LEFT)
        
        wait_label = tk.Label(details_frame, text=f"Wait: {step.wait_seconds}s",
                             font=("Segoe UI", 9), bg="#1a1a1a", fg="#cccccc")
        wait_label.pack(side=tk.RIGHT)
        
        icon_frame = tk.Frame(main_frame, bg="#1a1a1a")
        icon_frame.pack(fill=tk.X, pady=4)
        
        has_icon = (step.icon_image_path and os.path.exists(step.icon_image_path))
        icon_status_text = "Icon: Configured" if has_icon else "Icon: Not Set"
        icon_status_color = "#28a745" if has_icon else "#ffc107"
        
        icon_status_label = tk.Label(icon_frame, text=icon_status_text,
                                   font=("Segoe UI", 9), bg="#1a1a1a", fg=icon_status_color)
        icon_status_label.pack(side=tk.LEFT)
        
        controls_frame = tk.Frame(main_frame, bg="#1a1a1a")
        controls_frame.pack(fill=tk.X, pady=4)
        
        icon_btn = tk.Button(controls_frame, text="Set Icon",
                           bg="#007acc", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 8), command=lambda: self.select_step_icon(step))
        icon_btn.pack(side=tk.LEFT, padx=2)
        
        edit_btn = tk.Button(controls_frame, text="Edit",
                           bg="#6c757d", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 8), command=lambda: self.edit_step(step))
        edit_btn.pack(side=tk.LEFT, padx=2)
        
        test_btn = tk.Button(controls_frame, text="Test",
                           bg="#17a2b8", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                           font=("Segoe UI", 8), command=lambda: self.test_step(step))
        test_btn.pack(side=tk.LEFT, padx=2)
        
        toggle_text = "Deactivate" if step.is_active else "Activate"
        toggle_color = "#ffc107" if step.is_active else "#28a745"
        toggle_btn = tk.Button(controls_frame, text=toggle_text,
                             bg=toggle_color, fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 8), command=lambda: self.toggle_step(step.step_id))
        toggle_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = tk.Button(controls_frame, text="Delete",
                             bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 8), command=lambda: self.delete_step(step.step_id))
        delete_btn.pack(side=tk.RIGHT, padx=2)
    
    def edit_step(self, step):
        dialog = StepConfigDialog(self.main_app.root, step)
        self.main_app.root.wait_window(dialog.dialog)
        
        if dialog.result:
            step.name = dialog.result['name']
            step.coordinates = dialog.result['coordinates']
            step.wait_seconds = dialog.result['wait_seconds']
            
            self.main_app.log(f"Updated step {step.step_id}: '{step.name}'")
            self.refresh_steps_display()
    
    def toggle_step(self, step_id):
        step = next((s for s in self.navigation_manager.steps if s.step_id == step_id), None)
        if step:
            step.is_active = not step.is_active
            status = "activated" if step.is_active else "deactivated"
            self.main_app.log(f"Step {step_id} '{step.name}' {status}")
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def test_step(self, step):
        if not self.main_app.minimap_selector.is_setup():
            messagebox.showerror("Minimap Not Configured", 
                "Please configure the minimap area first before testing steps.")
            return
        
        result = self.navigation_manager.preview_step_detection(step)
        messagebox.showinfo("Detection Test", f"Step '{step.name}':\n{result}")
    
    def delete_step(self, step_id):
        step_name = next((step.name for step in self.navigation_manager.steps if step.step_id == step_id), f"Step {step_id}")
        if messagebox.askyesno("Delete Step", f"Delete '{step_name}'?\n\nThis will also delete the icon file."):
            self.navigation_manager.remove_step(step_id)
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def check_navigation_ready(self):
        if not self.main_app.minimap_selector.is_setup():
            self.start_nav_btn.config(state=tk.DISABLED)
            return
            
        ready_steps = []
        for step in self.navigation_manager.steps:
            if step.is_active:
                if step.template_image is None and step.icon_image_path:
                    step.load_template()
                if step.template_image is not None:
                    ready_steps.append(step)
        
        if ready_steps and not self.navigation_running:
            self.start_nav_btn.config(state=tk.NORMAL)
            self.main_app.log(f"Navigation ready with {len(ready_steps)} configured steps")
        else:
            self.start_nav_btn.config(state=tk.DISABLED)
    
    def start_navigation(self):
        self.main_app.log("Starting navigation sequence")
        if self.navigation_manager.start_navigation():
            self.navigation_running = True
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
            self.main_app.log("Navigation started successfully")
            self._monitor_navigation_status()
        else:
            self.main_app.log("Failed to start navigation - check that steps have icons configured")
    
    def stop_navigation(self):
        self.main_app.log("Stopping navigation sequence") 
        self.navigation_manager.stop_navigation()
        self.navigation_running = False
        self._update_navigation_buttons()
        self.main_app.log("Navigation stopped")
    
    def _monitor_navigation_status(self):
        if self.navigation_running and not self.navigation_manager.is_navigating:
            self.navigation_running = False
            self._update_navigation_buttons()
            self.main_app.log("Navigation sequence completed")
        
        if self.navigation_running:
            self.main_app.root.after(1000, self._monitor_navigation_status)
    
    def _update_navigation_buttons(self):
        if self.navigation_running:
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
        else:
            self.check_navigation_ready()
            self.stop_nav_btn.config(state=tk.DISABLED)
    
    def on_helper_state_changed(self, helper_running):
        pass
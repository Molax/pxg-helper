import tkinter as tk
from tkinter import ttk, messagebox
import time

class NavigationPanel:
    def __init__(self, parent, navigation_manager, main_app):
        self.parent = parent
        self.navigation_manager = navigation_manager
        self.main_app = main_app
        self.navigation_running = False
        
        # Initialize coordinate area selector
        self._setup_coordinate_area()
        
        self._create_widgets()
        
    def _setup_coordinate_area(self):
        """Initialize coordinate area selector"""
        try:
            from app.screen_capture.area_selector import AreaSelector
            self.coordinate_area = AreaSelector(self.main_app.root)
            self.coordinate_area.title = "Coordinate Display Area"
            
            # Set it in navigation manager
            self.navigation_manager.set_coordinate_area(self.coordinate_area)
            
        except Exception as e:
            self.main_app.log(f"Failed to setup coordinate area: {e}")
            self.coordinate_area = None
        
    def _create_widgets(self):
        # Main container
        main_container = tk.Frame(self.parent, bg="#2d2d2d")
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Title
        title_frame = tk.Frame(main_container, bg="#2d2d2d")
        title_frame.pack(fill=tk.X, pady=(0, 8))
        
        title_label = tk.Label(title_frame, text="Navigation Helper", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        # Configuration section
        config_frame = tk.LabelFrame(main_container, text="Configuration", 
                                   font=("Segoe UI", 10, "bold"), bg="#2d2d2d", fg="#ffffff",
                                   relief=tk.RIDGE, bd=1)
        config_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Coordinate area configuration
        coord_config_frame = tk.Frame(config_frame, bg="#2d2d2d")
        coord_config_frame.pack(fill=tk.X, padx=8, pady=8)
        
        coord_label = tk.Label(coord_config_frame, text="Coordinate Display Area:", 
                              font=("Segoe UI", 10), bg="#2d2d2d", fg="#cccccc")
        coord_label.pack(side=tk.LEFT)
        
        self.coord_status_label = tk.Label(coord_config_frame, text="Not configured", 
                                          font=("Segoe UI", 9), bg="#2d2d2d", fg="#ffc107")
        self.coord_status_label.pack(side=tk.LEFT, padx=(8, 0))
        
        coord_btn = tk.Button(coord_config_frame, text="Select Coordinate Area", 
                             command=self.select_coordinate_area,
                             font=("Segoe UI", 9), bg="#007acc", fg="white",
                             relief=tk.FLAT, padx=12, pady=4)
        coord_btn.pack(side=tk.RIGHT)
        
        # Info text for coordinate area
        coord_info = tk.Label(config_frame, 
                             text="Select the area where coordinates are displayed (e.g., (3953,3633,6))",
                             font=("Segoe UI", 8), bg="#2d2d2d", fg="#888888")
        coord_info.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        # Control buttons
        controls_frame = tk.Frame(main_container, bg="#2d2d2d")
        controls_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.start_nav_btn = tk.Button(controls_frame, text="Start Navigation", 
                                      command=self.start_navigation,
                                      font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white",
                                      relief=tk.FLAT, padx=15, pady=6, state=tk.DISABLED)
        self.start_nav_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_nav_btn = tk.Button(controls_frame, text="Stop Navigation", 
                                     command=self.stop_navigation,
                                     font=("Segoe UI", 10, "bold"), bg="#dc3545", fg="white",
                                     relief=tk.FLAT, padx=15, pady=6, state=tk.DISABLED)
        self.stop_nav_btn.pack(side=tk.LEFT, padx=5)
        
        add_step_btn = tk.Button(controls_frame, text="Add Step", 
                                command=self.add_navigation_step,
                                font=("Segoe UI", 10), bg="#007acc", fg="white",
                                relief=tk.FLAT, padx=12, pady=6)
        add_step_btn.pack(side=tk.RIGHT)
        
        # Steps container
        steps_container = tk.LabelFrame(main_container, text="Navigation Steps", 
                                       font=("Segoe UI", 10, "bold"), bg="#2d2d2d", fg="#ffffff",
                                       relief=tk.RIDGE, bd=1)
        steps_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for steps
        canvas = tk.Canvas(steps_container, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(steps_container, orient="vertical", command=canvas.yview)
        self.steps_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Update coordinate area status
        self.update_coordinate_area_status()
    
    def select_coordinate_area(self):
        """Start coordinate area selection"""
        if not self.coordinate_area:
            messagebox.showerror("Error", "Coordinate area selector not initialized")
            return
        
        self.main_app.log("Select the coordinate display area...")
        
        def on_completion():
            self.main_app.log("Coordinate area selection completed")
            self.update_coordinate_area_status()
            self.save_coordinate_area_config()
        
        try:
            success = self.coordinate_area.start_selection(
                title="Coordinate Display Area",
                color="#00ff00",
                completion_callback=on_completion
            )
            
            if not success:
                self.main_app.log("Failed to start coordinate area selection")
                
        except Exception as e:
            self.main_app.log(f"Error selecting coordinate area: {e}")
    
    def save_coordinate_area_config(self):
        """Save coordinate area configuration"""
        try:
            if self.coordinate_area and self.coordinate_area.is_setup():
                from app.config import load_config, save_config
                config = load_config()
                
                # Add coordinate area to config
                if "coordinate_area" not in config:
                    config["coordinate_area"] = {}
                
                config["coordinate_area"] = {
                    "name": "Coordinate Display Area",
                    "x1": self.coordinate_area.x1,
                    "y1": self.coordinate_area.y1,
                    "x2": self.coordinate_area.x2,
                    "y2": self.coordinate_area.y2,
                    "configured": True
                }
                
                save_config(config)
                self.main_app.log("Coordinate area configuration auto-saved")
                
        except Exception as e:
            self.main_app.log(f"Failed to save coordinate area: {e}")
    
    def load_coordinate_area_config(self):
        """Load coordinate area configuration"""
        try:
            from app.config import load_config
            config = load_config()
            
            coord_config = config.get("coordinate_area", {})
            if coord_config.get("configured", False):
                x1 = coord_config.get("x1")
                y1 = coord_config.get("y1")
                x2 = coord_config.get("x2")
                y2 = coord_config.get("y2")
                
                if all([x1 is not None, y1 is not None, x2 is not None, y2 is not None]):
                    if self.coordinate_area and self.coordinate_area.configure_from_saved(x1, y1, x2, y2):
                        self.main_app.log(f"Loaded coordinate area: ({x1},{y1}) to ({x2},{y2})")
                        self.update_coordinate_area_status()
                        return True
                        
        except Exception as e:
            self.main_app.log(f"Error loading coordinate area config: {e}")
        
        return False
    
    def update_coordinate_area_status(self):
        """Update coordinate area status display"""
        if self.coordinate_area and self.coordinate_area.is_setup():
            self.coord_status_label.config(text="Configured", fg="#28a745")
        else:
            self.coord_status_label.config(text="Not configured", fg="#ffc107")
    
    def add_navigation_step(self):
        """Add a new navigation step"""
        from app.ui.dialogs import StepConfigDialog
        
        try:
            dialog = StepConfigDialog(self.main_app.root)
            self.main_app.root.wait_window(dialog.dialog)
            
            if dialog.result:
                name = dialog.result.get("name", "")
                coordinates = dialog.result.get("coordinates", "")
                wait_seconds = dialog.result.get("wait_seconds", 3.0)
                
                if name:
                    step = self.navigation_manager.add_step(name, coordinates, wait_seconds)
                    self.main_app.log(f"Created step {step.step_id}: '{step.name}'")
                    self.select_step_icon(step)
                else:
                    self.refresh_steps_display()
                    self.check_navigation_ready()
                    
        except Exception as e:
            self.main_app.log(f"Error adding navigation step: {e}")
    
    def select_step_icon(self, step):
        """Select icon for a navigation step"""
        if not self.main_app.minimap_selector.is_setup():
            messagebox.showerror("Minimap Not Configured", 
                "Please configure the minimap area first before selecting step icons.")
            return
        
        self.main_app.log(f"Select an icon for '{step.name}' within the minimap area")
        
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
        """Refresh the display of navigation steps"""
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        self.main_app.log(f"Refreshing steps display - {len(self.navigation_manager.steps)} steps")
        
        for i, step in enumerate(self.navigation_manager.steps):
            self.create_step_widget(step, i)
    
    def create_step_widget(self, step, index):
        """Create widget for a navigation step"""
        step_frame = tk.Frame(self.steps_frame, bg="#1a1a1a", relief=tk.RIDGE, bd=1)
        step_frame.pack(fill=tk.X, pady=4, padx=8)
        
        main_frame = tk.Frame(step_frame, bg="#1a1a1a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Header with step info
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
        
        # Details
        details_frame = tk.Frame(main_frame, bg="#1a1a1a")
        details_frame.pack(fill=tk.X, pady=4)
        
        if step.coordinates:
            coord_label = tk.Label(details_frame, text=f"Target: {step.coordinates}",
                                  font=("Segoe UI", 9), bg="#1a1a1a", fg="#cccccc")
            coord_label.pack(side=tk.LEFT)
        
        wait_label = tk.Label(details_frame, text=f"Wait: {step.wait_seconds}s",
                             font=("Segoe UI", 9), bg="#1a1a1a", fg="#cccccc")
        wait_label.pack(side=tk.RIGHT)
        
        # Icon status
        icon_frame = tk.Frame(main_frame, bg="#1a1a1a")
        icon_frame.pack(fill=tk.X, pady=2)
        
        import os
        if step.icon_image_path and os.path.exists(step.icon_image_path):
            icon_text = "✓ Icon configured"
            icon_color = "#28a745"
        else:
            icon_text = "⚠ No icon"
            icon_color = "#ffc107"
        
        icon_label = tk.Label(icon_frame, text=icon_text,
                             font=("Segoe UI", 9), bg="#1a1a1a", fg=icon_color)
        icon_label.pack(side=tk.LEFT)
        
        # Action buttons
        buttons_frame = tk.Frame(main_frame, bg="#1a1a1a")
        buttons_frame.pack(fill=tk.X, pady=(8, 0))
        
        # Edit button
        edit_btn = tk.Button(buttons_frame, text="Edit", 
                            command=lambda: self.edit_step(step.step_id),
                            font=("Segoe UI", 8), bg="#6c757d", fg="white",
                            relief=tk.FLAT, padx=8, pady=2)
        edit_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Test button
        test_btn = tk.Button(buttons_frame, text="Test", 
                            command=lambda: self.test_step_detection(step),
                            font=("Segoe UI", 8), bg="#17a2b8", fg="white",
                            relief=tk.FLAT, padx=8, pady=2)
        test_btn.pack(side=tk.LEFT, padx=4)
        
        # Set Icon button
        icon_btn = tk.Button(buttons_frame, text="Set Icon", 
                            command=lambda: self.select_step_icon(step),
                            font=("Segoe UI", 8), bg="#007acc", fg="white",
                            relief=tk.FLAT, padx=8, pady=2)
        icon_btn.pack(side=tk.LEFT, padx=4)
        
        # Delete button
        delete_btn = tk.Button(buttons_frame, text="Delete", 
                              command=lambda: self.delete_step(step.step_id),
                              font=("Segoe UI", 8), bg="#dc3545", fg="white",
                              relief=tk.FLAT, padx=8, pady=2)
        delete_btn.pack(side=tk.RIGHT)
        
        # Toggle active button
        toggle_text = "Deactivate" if step.is_active else "Activate"
        toggle_btn = tk.Button(buttons_frame, text=toggle_text, 
                              command=lambda: self.toggle_step_active(step.step_id),
                              font=("Segoe UI", 8), bg="#ffc107", fg="black",
                              relief=tk.FLAT, padx=8, pady=2)
        toggle_btn.pack(side=tk.RIGHT, padx=(0, 4))
    
    def edit_step(self, step_id):
        """Edit a navigation step"""
        step = next((s for s in self.navigation_manager.steps if s.step_id == step_id), None)
        if not step:
            return
        
        from app.ui.dialogs import StepConfigDialog
        
        try:
            dialog = StepConfigDialog(self.main_app.root, step)
            self.main_app.root.wait_window(dialog.dialog)
            
            if dialog.result:
                step.name = dialog.result.get("name", step.name)
                step.coordinates = dialog.result.get("coordinates", step.coordinates)
                step.wait_seconds = dialog.result.get("wait_seconds", step.wait_seconds)
                
                self.main_app.log(f"Updated step {step.step_id}: '{step.name}'")
                self.refresh_steps_display()
                
        except Exception as e:
            self.main_app.log(f"Error editing step: {e}")
    
    def toggle_step_active(self, step_id):
        """Toggle step active status"""
        step = next((s for s in self.navigation_manager.steps if s.step_id == step_id), None)
        if step:
            step.is_active = not step.is_active
            status = "activated" if step.is_active else "deactivated"
            self.main_app.log(f"Step {step.step_id} '{step.name}' {status}")
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def test_step_detection(self, step):
        """Test step detection in minimap"""
        if not self.main_app.minimap_selector.is_setup():
            messagebox.showerror("Error", "Minimap area not configured")
            return
        
        result = self.navigation_manager.preview_step_detection(step)
        messagebox.showinfo("Detection Test", f"Step '{step.name}':\n{result}")
    
    def delete_step(self, step_id):
        """Delete a navigation step"""
        step_name = next((step.name for step in self.navigation_manager.steps if step.step_id == step_id), f"Step {step_id}")
        if messagebox.askyesno("Delete Step", f"Delete '{step_name}'?\n\nThis will also delete the icon file."):
            self.navigation_manager.remove_step(step_id)
            self.refresh_steps_display()
            self.check_navigation_ready()
    
    def check_navigation_ready(self):
        """Check if navigation is ready to start"""
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
        """Start navigation sequence"""
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
        """Stop navigation sequence"""
        self.main_app.log("Stopping navigation sequence") 
        self.navigation_manager.stop_navigation()
        self.navigation_running = False
        self._update_navigation_buttons()
        self.main_app.log("Navigation stopped")
    
    def _monitor_navigation_status(self):
        """Monitor navigation status and update UI"""
        if self.navigation_running and not self.navigation_manager.is_navigating:
            self.navigation_running = False
            self._update_navigation_buttons()
            self.main_app.log("Navigation sequence completed")
        
        if self.navigation_running:
            self.main_app.root.after(1000, self._monitor_navigation_status)
    
    def _update_navigation_buttons(self):
        """Update navigation button states"""
        if self.navigation_running:
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
        else:
            self.check_navigation_ready()
            self.stop_nav_btn.config(state=tk.DISABLED)
    
    def on_helper_state_changed(self, helper_running):
        """Handle helper state changes"""
        pass
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

class NavigationPanel:
    def __init__(self, parent, navigation_manager, main_app):
        self.parent = parent
        self.main_app = main_app
        self.navigation_manager = navigation_manager
        self.coordinate_area = None
        self.navigation_running = False
        
        self._setup_coordinate_area()
        self.create_panel()
    def _setup_coordinate_area(self):
        """Initialize coordinate area selector"""
        try:
            from app.screen_capture.area_selector import AreaSelector
            self.coordinate_area = AreaSelector(self.main_app.root)
            self.navigation_manager.set_coordinate_area(self.coordinate_area)
        except Exception as e:
            self.main_app.log(f"Error setting up coordinate area: {e}")
            self.coordinate_area = None
    
    def create_panel(self):
        main_frame = tk.Frame(self.parent, bg="#2d2d2d")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        title_label = tk.Label(main_frame, text="Navigation System", 
                              font=("Segoe UI", 14, "bold"), 
                              bg="#2d2d2d", fg="#ffffff")
        title_label.pack(pady=(0, 10))
        
        self._create_coordinate_area_section(main_frame)
        self._create_steps_section(main_frame)
        self._create_navigation_controls(main_frame)
    
    def _create_coordinate_area_section(self, parent):
        coord_frame = tk.LabelFrame(parent, text="Coordinate Display Area", 
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#2d2d2d", fg="#ffffff", bd=2, relief=tk.RIDGE)
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        
        coord_inner = tk.Frame(coord_frame, bg="#2d2d2d")
        coord_inner.pack(fill=tk.X, padx=8, pady=8)
        
        self.coord_status_label = tk.Label(coord_inner, text="Not configured", 
                                          font=("Segoe UI", 10), 
                                          bg="#2d2d2d", fg="#ffc107")
        self.coord_status_label.pack(side=tk.LEFT)
        
        coord_btn = tk.Button(coord_inner, text="Configure Coordinate Area",
                             command=self.configure_coordinate_area,
                             font=("Segoe UI", 9), bg="#007acc", fg="white",
                             relief=tk.FLAT, padx=12, pady=4)
        coord_btn.pack(side=tk.RIGHT)
    
    def _create_steps_section(self, parent):
        steps_frame = tk.LabelFrame(parent, text="Navigation Steps", 
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#2d2d2d", fg="#ffffff", bd=2, relief=tk.RIDGE)
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        steps_inner = tk.Frame(steps_frame, bg="#2d2d2d")
        steps_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        add_btn = tk.Button(steps_inner, text="+ Add Navigation Step",
                           command=self.add_navigation_step,
                           font=("Segoe UI", 10, "bold"), bg="#28a745", fg="white",
                           relief=tk.FLAT, padx=15, pady=8)
        add_btn.pack(pady=(0, 10))
        
        canvas = tk.Canvas(steps_inner, bg="#2d2d2d", highlightthickness=0)
        scrollbar = tk.Scrollbar(steps_inner, orient="vertical", command=canvas.yview)
        self.steps_frame = tk.Frame(canvas, bg="#2d2d2d")
        
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_navigation_controls(self, parent):
        controls_frame = tk.Frame(parent, bg="#2d2d2d")
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_nav_btn = tk.Button(controls_frame, text="START NAVIGATION",
                                      command=self.start_navigation,
                                      font=("Segoe UI", 12, "bold"), 
                                      bg="#28a745", fg="white",
                                      relief=tk.FLAT, padx=20, pady=10,
                                      state=tk.DISABLED)
        self.start_nav_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_nav_btn = tk.Button(controls_frame, text="STOP NAVIGATION",
                                     command=self.stop_navigation,
                                     font=("Segoe UI", 12, "bold"), 
                                     bg="#dc3545", fg="white",
                                     relief=tk.FLAT, padx=20, pady=10,
                                     state=tk.DISABLED)
        self.stop_nav_btn.pack(side=tk.LEFT)
    
    def configure_coordinate_area(self):
        """Configure the coordinate display area"""
        try:
            def on_completion():
                if self.coordinate_area.is_setup():
                    self.main_app.log(f"Coordinate area configured: ({self.coordinate_area.x1},{self.coordinate_area.y1}) to ({self.coordinate_area.x2},{self.coordinate_area.y2})")
                    self.update_coordinate_area_status()
                else:
                    self.main_app.log("Coordinate area configuration cancelled")
            
            success = self.coordinate_area.start_selection(
                title="Select Coordinate Display Area",
                color="#ff00ff",
                completion_callback=on_completion
            )
            
            if not success:
                self.main_app.log("Failed to start coordinate area selection")
                
        except Exception as e:
            self.main_app.log(f"Error configuring coordinate area: {e}")
    
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
                
                if all(coord is not None for coord in [x1, y1, x2, y2]):
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
                    self.refresh_steps_display()
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
                try:
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
                except Exception as e:
                    self.main_app.log(f"Error in icon completion callback: {e}")
            
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
        """Create widget for a navigation step with icon preview"""
        step_frame = tk.Frame(self.steps_frame, bg="#2d2d2d", relief=tk.RIDGE, bd=1)
        step_frame.pack(fill=tk.X, pady=4, padx=8)
        
        main_frame = tk.Frame(step_frame, bg="#2d2d2d")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Header with step info
        header_frame = tk.Frame(main_frame, bg="#2d2d2d")
        header_frame.pack(fill=tk.X)
        
        step_label = tk.Label(header_frame, text=f"Step {step.step_id}: {step.name}",
                             font=("Segoe UI", 12, "bold"), bg="#2d2d2d", fg="#ffffff")
        step_label.pack(side=tk.LEFT)
        
        if step.is_active:
            status_text = "Active"
            status_color = "#28a745"
        else:
            status_text = "Inactive"
            status_color = "#6c757d"
        
        status_label = tk.Label(header_frame, text=status_text,
                               font=("Segoe UI", 9, "bold"), bg="#2d2d2d", fg=status_color)
        status_label.pack(side=tk.RIGHT)
        
        # Details and Icon Preview Row
        content_frame = tk.Frame(main_frame, bg="#2d2d2d")
        content_frame.pack(fill=tk.X, pady=4)
        
        # Left side - Details
        details_frame = tk.Frame(content_frame, bg="#2d2d2d")
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        if step.coordinates:
            coord_label = tk.Label(details_frame, text=f"Target: {step.coordinates}",
                                  font=("Segoe UI", 9), bg="#2d2d2d", fg="#cccccc")
            coord_label.pack(anchor=tk.W)
        
        wait_label = tk.Label(details_frame, text=f"Wait: {step.wait_seconds}s",
                             font=("Segoe UI", 9), bg="#2d2d2d", fg="#cccccc")
        wait_label.pack(anchor=tk.W)
        
        # Icon status
        if step.icon_image_path and os.path.exists(step.icon_image_path):
            icon_text = "✓ Icon configured"
            icon_color = "#28a745"
        else:
            icon_text = "⚠ No icon"
            icon_color = "#ffc107"
        
        icon_label = tk.Label(details_frame, text=icon_text,
                             font=("Segoe UI", 9), bg="#2d2d2d", fg=icon_color)
        icon_label.pack(anchor=tk.W)
        
        # Right side - Icon Preview
        if step.icon_image_path and os.path.exists(step.icon_image_path):
            try:
                preview_frame = tk.Frame(content_frame, bg="#3d3d3d", relief=tk.SUNKEN, bd=1)
                preview_frame.pack(side=tk.RIGHT, padx=(10, 0))
                
                pil_image = Image.open(step.icon_image_path)
                
                # Scale image to fit preview (max 60x60)
                max_size = 60
                pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                preview_label = tk.Label(preview_frame, image=photo, bg="#3d3d3d")
                preview_label.image = photo  # Keep a reference
                preview_label.pack(padx=4, pady=4)
                
                # Add size info
                size_text = f"{pil_image.width}x{pil_image.height}"
                size_label = tk.Label(preview_frame, text=size_text,
                                     font=("Segoe UI", 7), bg="#3d3d3d", fg="#cccccc")
                size_label.pack()
                
            except Exception as e:
                self.main_app.log(f"Error loading icon preview for step {step.step_id}: {e}")
        
        # Action buttons
        buttons_frame = tk.Frame(main_frame, bg="#2d2d2d")
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
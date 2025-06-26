import os
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
        
        try:
            self.main_app.log(f"Select an icon for '{step.name}' within the minimap area")
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
            
        self.steps_canvas.update_idletasks()
    
    def create_step_widget(self, step, index):
        step_frame = tk.Frame(self.steps_frame, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        step_frame.pack(fill=tk.X, padx=4, pady=2)
        
        header = tk.Frame(step_frame, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=8)
        
        step_label = tk.Label(header, text=f"{step.step_id}. {step.name}", 
                             font=("Segoe UI", 10, "bold"), bg="#3d3d3d", fg="#ffffff")
        step_label.pack(side=tk.LEFT)
        
        buttons_frame = tk.Frame(header, bg="#3d3d3d")
        buttons_frame.pack(side=tk.RIGHT)
        
        edit_btn = tk.Button(buttons_frame, text="📝", font=("Arial", 10),
                            bg="#17a2b8", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                            width=3, command=lambda: self.edit_step_icon(step))
        edit_btn.pack(side=tk.LEFT, padx=2)
        
        test_btn = tk.Button(buttons_frame, text="🔍", font=("Arial", 10),
                            bg="#ffc107", fg="#000000", relief=tk.FLAT, borderwidth=0,
                            width=3, command=lambda: self.test_step_detection(step))
        test_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = tk.Button(buttons_frame, text="×", font=("Arial", 12, "bold"),
                              bg="#dc3545", fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                              width=3, command=lambda: self.delete_step(step.step_id))
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        info_frame = tk.Frame(step_frame, bg="#3d3d3d")
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        
        if step.coordinates:
            coords_label = tk.Label(info_frame, text=f"Target: {step.coordinates}",
                                   font=("Segoe UI", 8), bg="#3d3d3d", fg="#17a2b8")
            coords_label.pack(anchor=tk.W)
        
        wait_label = tk.Label(info_frame, text=f"Wait: {step.wait_seconds}s",
                             font=("Segoe UI", 8), bg="#3d3d3d", fg="#ffc107")
        wait_label.pack(anchor=tk.W)
        
        has_icon = (step.template_image is not None and 
                   hasattr(step, 'icon_image_path') and 
                   step.icon_image_path and 
                   os.path.exists(step.icon_image_path))
        status_text = "✓ Icon Ready" if has_icon else "⚠ No Icon"
        status_color = "#28a745" if has_icon else "#dc3545"
        
        status_label = tk.Label(info_frame, text=status_text,
                               font=("Segoe UI", 8), bg="#3d3d3d", fg=status_color)
        status_label.pack(anchor=tk.W)
        
        if has_icon:
            try:
                from PIL import Image, ImageTk
                
                if os.path.exists(step.icon_image_path):
                    icon_img = Image.open(step.icon_image_path)
                    icon_img.thumbnail((60, 30), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    
                    icon_label = tk.Label(info_frame, image=icon_photo, bg="#3d3d3d")
                    icon_label.image = icon_photo
                    icon_label.pack(anchor=tk.W, pady=2)
            except Exception as e:
                self.main_app.log(f"Error loading icon preview: {e}")
    
    def edit_step_icon(self, step):
        if messagebox.askyesno("Edit Icon", f"Select a new icon for '{step.name}'?"):
            self.select_step_icon(step)
    
    def test_step_detection(self, step):
        if not step.template_image:
            messagebox.showwarning("No Icon", f"Step '{step.name}' has no icon to test.")
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
        
        if ready_steps:
            self.start_nav_btn.config(state=tk.NORMAL)
            self.main_app.log(f"Navigation ready with {len(ready_steps)} configured steps")
        else:
            self.start_nav_btn.config(state=tk.DISABLED)
    
    def start_navigation(self):
        self.main_app.log("Starting navigation sequence")
        if self.navigation_manager.start_navigation():
            self.start_nav_btn.config(state=tk.DISABLED)
            self.stop_nav_btn.config(state=tk.NORMAL)
            self.main_app.log("Navigation started")
        else:
            self.main_app.log("Failed to start navigation - check that steps have icons configured")
    
    def stop_navigation(self):
        self.main_app.log("Stopping navigation sequence") 
        self.navigation_manager.stop_navigation()
        self.start_nav_btn.config(state=tk.NORMAL)
        self.stop_nav_btn.config(state=tk.DISABLED)
        self.main_app.log("Navigation stopped")
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import logging

logger = logging.getLogger('PokeXHelper')

class AreaConfigPanel:
    def __init__(self, parent, health_selector, minimap_selector, battle_area_selector, main_app):
        self.parent = parent
        self.health_selector = health_selector
        self.minimap_selector = minimap_selector
        self.battle_area_selector = battle_area_selector
        self.main_app = main_app
        
        # Store references for dynamic updates
        self.area_widgets = {}
        
        self._create_ui()
        self._update_all_areas()
    
    def _create_ui(self):
        areas_frame = tk.Frame(self.parent, bg="#2d2d2d")
        areas_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        title_label = tk.Label(areas_frame, text="Area Configuration", 
                              font=("Segoe UI", 14, "bold"), bg="#2d2d2d", fg="#ffffff")
        title_label.pack(anchor=tk.W, pady=12)
        
        for name, color, selector in [
            ("Health Bar", "#dc3545", self.health_selector),
            ("Minimap Area", "#17a2b8", self.minimap_selector),
            ("Battle Area", "#9c27b0", self.battle_area_selector)
        ]:
            self._create_area_card(areas_frame, name, color, selector)
        
        self.config_status_label = tk.Label(areas_frame, text="Configure areas to continue",
                                           font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffc107")
        self.config_status_label.pack(pady=12)
        
        self._create_info_displays(areas_frame)
    
    def _create_area_card(self, parent, title, color, selector):
        card = tk.Frame(parent, bg="#3d3d3d", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, padx=4, pady=4)
        
        header = tk.Frame(card, bg="#3d3d3d")
        header.pack(fill=tk.X, padx=8, pady=8)
        
        title_label = tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), 
                              bg="#3d3d3d", fg="#ffffff")
        title_label.pack(side=tk.LEFT)
        
        status_dot = tk.Label(header, text="●", font=("Segoe UI", 12), 
                             bg="#3d3d3d", fg="#dc3545")
        status_dot.pack(side=tk.RIGHT)
        
        # Preview frame with fixed height
        preview_frame = tk.Frame(card, bg="#1a1a1a", height=50)
        preview_frame.pack(fill=tk.X, padx=8, pady=4)
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Not Configured",
                               bg="#1a1a1a", fg="#666666", font=("Segoe UI", 9))
        preview_label.pack(expand=True)
        
        # Coordinates label
        coords_label = tk.Label(card, text="", bg="#3d3d3d", fg="#888888", 
                               font=("Segoe UI", 8))
        coords_label.pack(padx=8, pady=2)
        
        btn_frame = tk.Frame(card, bg="#3d3d3d")
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        
        select_btn = tk.Button(btn_frame, text=f"Select {title}",
                             bg=color, fg="#ffffff", relief=tk.FLAT, borderwidth=0,
                             font=("Segoe UI", 9), activebackground=color,
                             command=lambda: self._start_area_selection(title, color, selector))
        select_btn.pack(fill=tk.X)
        
        # Store widget references for updates
        self.area_widgets[selector] = {
            'status_dot': status_dot,
            'preview_label': preview_label,
            'coords_label': coords_label,
            'card': card,
            'title': title
        }
    
    def _start_area_selection(self, title, color, selector):
        """Start area selection with proper completion handling"""
        self.main_app.log(f"Starting {title} selection...")
        
        def on_completion():
            try:
                if selector.is_setup():
                    self.main_app.log(f"{title} configured: ({selector.x1},{selector.y1}) to ({selector.x2},{selector.y2})")
                    # Force update the preview
                    self._create_preview_image(selector)
                    self.update_area_status(selector)
                    self.main_app.interface_manager.check_configuration()
                    # Auto-save configuration
                    self.main_app.save_settings()
                else:
                    self.main_app.log(f"{title} selection cancelled")
            except Exception as e:
                logger.error(f"Error in completion callback for {title}: {e}")
                self.main_app.log(f"Error updating {title}: {e}")
        
        try:
            success = selector.start_selection(
                title=title,
                color=color,
                completion_callback=on_completion
            )
            
            if not success:
                self.main_app.log(f"Failed to start {title} selection")
                
        except Exception as e:
            logger.error(f"Error starting {title} selection: {e}")
            self.main_app.log(f"Error starting {title} selection: {e}")
    
    def _create_preview_image(self, selector):
        """Create preview image for area selector"""
        try:
            if selector.is_setup():
                from PIL import ImageGrab
                
                # Capture the area
                bbox = (selector.x1, selector.y1, selector.x2, selector.y2)
                try:
                    preview_img = ImageGrab.grab(bbox=bbox, all_screens=True)
                except TypeError:
                    # Fallback for older PIL versions
                    preview_img = ImageGrab.grab(bbox=bbox)
                
                # Store the preview image in the selector
                selector.preview_image = preview_img
                logger.debug(f"Created preview image for {selector.title if hasattr(selector, 'title') else 'area'}")
                
        except Exception as e:
            logger.error(f"Error creating preview image: {e}")
    
    def update_area_status(self, selector):
        """Update area status display with preview image"""
        if selector not in self.area_widgets:
            return
            
        widgets = self.area_widgets[selector]
        status_dot = widgets['status_dot']
        preview_label = widgets['preview_label']
        coords_label = widgets['coords_label']
        
        try:
            if selector.is_setup():
                # Update status indicator
                status_dot.config(fg="#28a745")
                
                # Update coordinates display
                coords_text = f"({selector.x1}, {selector.y1}) to ({selector.x2}, {selector.y2})"
                coords_label.config(text=coords_text, fg="#28a745")
                
                # Update preview image
                if hasattr(selector, 'preview_image') and selector.preview_image:
                    try:
                        # Resize image to fit preview area
                        img = selector.preview_image.resize((120, 40), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Update preview label with image
                        preview_label.config(image=photo, text="", bg="#1a1a1a")
                        preview_label.image = photo  # Keep reference to prevent garbage collection
                        
                        logger.debug(f"Updated preview image for {widgets['title']}")
                        
                    except Exception as e:
                        logger.error(f"Error updating preview image for {widgets['title']}: {e}")
                        preview_label.config(text="Configured", fg="#28a745", image="")
                        if hasattr(preview_label, 'image'):
                            delattr(preview_label, 'image')
                else:
                    preview_label.config(text="Configured", fg="#28a745", image="")
                    if hasattr(preview_label, 'image'):
                        delattr(preview_label, 'image')
            else:
                # Area not configured
                status_dot.config(fg="#dc3545")
                preview_label.config(text="Not Configured", fg="#666666", image="")
                coords_label.config(text="", fg="#888888")
                if hasattr(preview_label, 'image'):
                    delattr(preview_label, 'image')
                    
        except Exception as e:
            logger.error(f"Error updating area status for {widgets['title']}: {e}")
    
    def _update_all_areas(self):
        """Update all area displays"""
        try:
            for selector in [self.health_selector, self.minimap_selector, self.battle_area_selector]:
                if selector.is_setup():
                    self._create_preview_image(selector)
                self.update_area_status(selector)
        except Exception as e:
            logger.error(f"Error updating all areas: {e}")
    
    def _create_info_displays(self, parent):
        info_frame = tk.LabelFrame(parent, text="Live Information", 
                                  font=("Segoe UI", 10, "bold"), bg="#2d2d2d", fg="#ffffff",
                                  relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, pady=12)
        
        health_info_frame = tk.Frame(info_frame, bg="#2d2d2d")
        health_info_frame.pack(fill=tk.X, pady=12)
        
        tk.Label(health_info_frame, text="Current Health:", bg="#2d2d2d", fg="#dc3545",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.health_percentage_var = tk.StringVar(value="100.0%")
        tk.Label(health_info_frame, textvariable=self.health_percentage_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        
        battle_info_frame = tk.Frame(info_frame, bg="#2d2d2d")
        battle_info_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(battle_info_frame, text="Enemy Pokemon:", bg="#2d2d2d", fg="#9c27b0",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.enemy_count_var = tk.StringVar(value="0")
        tk.Label(battle_info_frame, textvariable=self.enemy_count_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        
        battle_status_frame = tk.Frame(info_frame, bg="#2d2d2d")
        battle_status_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(battle_status_frame, text="Battle Status:", bg="#2d2d2d", fg="#ffc107",
                font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.battle_status_var = tk.StringVar(value="No Battle")
        tk.Label(battle_status_frame, textvariable=self.battle_status_var, 
                bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 10)).pack(side=tk.RIGHT)
    
    def set_config_status(self, text, color):
        """Update configuration status"""
        self.config_status_label.config(text=text, fg=color)
    
    def update_health_percentage(self, percentage):
        """Update health percentage display"""
        self.health_percentage_var.set(f"{percentage:.1f}%")
    
    def update_battle_info(self, enemy_count, in_battle):
        """Update battle information display"""
        self.enemy_count_var.set(str(enemy_count))
        if in_battle:
            self.battle_status_var.set("In Battle")
        else:
            self.battle_status_var.set("No Battle")
    
    def refresh_all_previews(self):
        """Refresh all area previews - call this after loading configuration"""
        self._update_all_areas()
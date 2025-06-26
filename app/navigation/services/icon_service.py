import os
import time
import logging
from PIL import ImageGrab

logger = logging.getLogger('PokeXHelper')

class IconService:
    def __init__(self, icons_dir="assets/navigation_icons"):
        self.icons_dir = icons_dir
        self.logger = logger
        
        if not os.path.exists(self.icons_dir):
            os.makedirs(self.icons_dir)
    
    def save_step_icon(self, step, icon_bounds, minimap_area):
        try:
            x1, y1, x2, y2 = icon_bounds
            
            # Capture minimap area
            bbox = (minimap_area.x1, minimap_area.y1, minimap_area.x2, minimap_area.y2)
            try:
                minimap_image = ImageGrab.grab(bbox=bbox, all_screens=True)
            except TypeError:
                minimap_image = ImageGrab.grab(bbox=bbox)
            
            if minimap_image is None:
                self.logger.error("Could not capture minimap image")
                return False
            
            # Calculate relative coordinates within minimap
            rel_x1 = x1 - minimap_area.x1
            rel_y1 = y1 - minimap_area.y1
            rel_x2 = x2 - minimap_area.x1
            rel_y2 = y2 - minimap_area.y1
            
            # Ensure coordinates are within bounds
            rel_x1 = max(0, rel_x1)
            rel_y1 = max(0, rel_y1)
            rel_x2 = min(minimap_image.width, rel_x2)
            rel_y2 = min(minimap_image.height, rel_y2)
            
            if rel_x2 <= rel_x1 or rel_y2 <= rel_y1:
                self.logger.error("Invalid icon bounds")
                return False
            
            # Crop the icon from minimap
            icon_image = minimap_image.crop((rel_x1, rel_y1, rel_x2, rel_y2))
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"step_{step.step_id}_{timestamp}.png"
            filepath = os.path.join(self.icons_dir, filename)
            
            # Delete old icon file if it exists
            if step.icon_image_path and os.path.exists(step.icon_image_path):
                try:
                    os.remove(step.icon_image_path)
                    self.logger.debug(f"Deleted old icon file: {step.icon_image_path}")
                except Exception as e:
                    self.logger.warning(f"Could not delete old icon file: {e}")
            
            # Save new icon
            icon_image.save(filepath)
            step.icon_image_path = filepath
            
            # Load template for immediate use
            step.load_template()
            
            self.logger.info(f"Saved icon for step {step.step_id}: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving step icon: {e}")
            return False
    
    def delete_step_icon(self, step):
        try:
            if step.icon_image_path and os.path.exists(step.icon_image_path):
                os.remove(step.icon_image_path)
                self.logger.info(f"Deleted icon file: {step.icon_image_path}")
                step.icon_image_path = None
                step.template_image = None
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting step icon: {e}")
            return False
    
    def cleanup_unused_icons(self, active_steps):
        try:
            if not os.path.exists(self.icons_dir):
                return
            
            # Get all icon files currently in use
            used_files = set()
            for step in active_steps:
                if step.icon_image_path:
                    used_files.add(os.path.basename(step.icon_image_path))
            
            # Remove unused files
            removed_count = 0
            for filename in os.listdir(self.icons_dir):
                if filename.endswith('.png') and filename not in used_files:
                    filepath = os.path.join(self.icons_dir, filename)
                    try:
                        os.remove(filepath)
                        removed_count += 1
                        self.logger.debug(f"Removed unused icon: {filepath}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove unused icon {filepath}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} unused icon files")
                
        except Exception as e:
            self.logger.error(f"Error during icon cleanup: {e}")
    
    def get_icon_info(self, step):
        if not step.icon_image_path or not os.path.exists(step.icon_image_path):
            return None
        
        try:
            stat = os.stat(step.icon_image_path)
            return {
                'path': step.icon_image_path,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            self.logger.error(f"Error getting icon info: {e}")
            return None
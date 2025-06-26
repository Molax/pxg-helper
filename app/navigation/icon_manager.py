import os

class IconManager:
    def __init__(self, logger):
        self.logger = logger
        self.icons_dir = "assets/navigation_icons"
    
    def delete_step_icon(self, step):
        """Delete icon file for a step"""
        if step.icon_image_path and os.path.exists(step.icon_image_path):
            try:
                os.remove(step.icon_image_path)
                self.logger.info(f"Deleted icon file: {step.icon_image_path}")
            except Exception as e:
                self.logger.error(f"Failed to delete icon file: {e}")
    
    def cleanup_unused_icons(self, steps):
        """Clean up unused icon files"""
        try:
            if not os.path.exists(self.icons_dir):
                self.logger.info("Icons directory does not exist")
                return
            
            used_files = set()
            for step in steps:
                if step.icon_image_path:
                    filename = os.path.basename(step.icon_image_path)
                    used_files.add(filename)
            
            self.logger.info(f"Found {len(used_files)} icon files in use: {used_files}")
            
            cleanup_count = 0
            for filename in os.listdir(self.icons_dir):
                if filename.endswith('.png') and filename not in used_files:
                    file_path = os.path.join(self.icons_dir, filename)
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up unused icon file: {filename}")
                        cleanup_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {filename}: {e}")
            
            if cleanup_count == 0:
                self.logger.info("No unused icon files to clean up")
            else:
                self.logger.info(f"Cleaned up {cleanup_count} unused icon files")
                
        except Exception as e:
            self.logger.error(f"Error during icon cleanup: {e}")
            raise
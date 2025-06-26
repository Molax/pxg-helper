import cv2
import os
import logging

logger = logging.getLogger('PokeXHelper')

class TemplateManager:
    def __init__(self, templates_dir="assets/pokemon_templates"):
        self.logger = logging.getLogger('PokeXHelper')
        self.template_cache = {}
        self.templates_dir = templates_dir
        
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            self.logger.info(f"Created templates directory: {self.templates_dir}")
    
    def load_template(self, template_name):
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        template_path = os.path.join(self.templates_dir, f"{template_name}.png")
        
        if not os.path.exists(template_path):
            self.logger.warning(f"Template not found: {template_path}")
            return None
        
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"Failed to load template: {template_path}")
                return None
            
            self.template_cache[template_name] = template
            self.logger.debug(f"Loaded template: {template_name}")
            return template
            
        except Exception as e:
            self.logger.error(f"Error loading template {template_name}: {e}")
            return None
    
    def get_template_grayscale(self, template_name):
        template = self.load_template(template_name)
        if template is None:
            return None
        
        cache_key = f"{template_name}_gray"
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        self.template_cache[cache_key] = template_gray
        return template_gray
    
    def clear_cache(self):
        self.template_cache.clear()
        self.logger.debug("Template cache cleared")
    
    def get_available_templates(self):
        if not os.path.exists(self.templates_dir):
            return []
        
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.png'):
                templates.append(filename[:-4])
        return templates
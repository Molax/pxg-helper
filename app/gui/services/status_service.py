import logging

logger = logging.getLogger('PokeXHelper')

class StatusService:
    def __init__(self):
        self.status_layout = None
        self.current_status = "Ready"
        self.current_color = "#28a745"
        self.status_callbacks = []
    
    def set_status_layout(self, status_layout):
        self.status_layout = status_layout
    
    def add_status_callback(self, callback):
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback):
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def update_status(self, text, color="#28a745"):
        self.current_status = text
        self.current_color = color
        
        if self.status_layout:
            try:
                self.status_layout.update_status(text, color)
            except Exception as e:
                logger.error(f"Error updating status in layout: {e}")
        
        for callback in self.status_callbacks:
            try:
                callback(text, color)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def get_current_status(self):
        return self.current_status, self.current_color
    
    def set_ready(self):
        self.update_status("Ready", "#28a745")
    
    def set_running(self):
        self.update_status("Helper Running", "#28a745")
    
    def set_stopped(self):
        self.update_status("Helper Stopped", "#6c757d")
    
    def set_error(self, error_message="Error"):
        self.update_status(error_message, "#dc3545")
    
    def set_warning(self, warning_message="Warning"):
        self.update_status(warning_message, "#ff9800")
    
    def set_configuring(self, area_name):
        self.update_status(f"Configure: {area_name}", "#ff9800")
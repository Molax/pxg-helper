import logging
import time
from datetime import datetime

logger = logging.getLogger('PokeXHelper')

class UILogger:
    def __init__(self):
        self.log_panel = None
        self.max_log_entries = 1000
    
    def set_log_panel(self, log_panel):
        self.log_panel = log_panel
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        logger.info(message)
        
        if self.log_panel:
            try:
                # Use add_log method which exists in LogPanel
                self.log_panel.add_log(message)
            except Exception as e:
                logger.error(f"Error adding log entry to UI: {e}")
    
    def add_log_entry(self, message, level="INFO"):
        """Compatibility method for LogPanel interface"""
        if self.log_panel:
            try:
                self.log_panel.add_log(message)
            except Exception as e:
                logger.error(f"Error adding log entry to UI: {e}")
    
    def log_info(self, message):
        self.log(message, "INFO")
    
    def log_warning(self, message):
        self.log(message, "WARNING")
    
    def log_error(self, message):
        self.log(message, "ERROR")
    
    def log_success(self, message):
        self.log(message, "SUCCESS")
    
    def clear_logs(self):
        if self.log_panel:
            try:
                self.log_panel.clear_log()
            except Exception as e:
                logger.error(f"Error clearing logs: {e}")
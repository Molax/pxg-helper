from typing import List, Dict, Any, Tuple
import logging
from .schemas import ConfigSchema, AreaConfig, HelperSettings, AdvancedSettings, UISettings

logger = logging.getLogger('PokeXHelper')

class ValidationError:
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity
    
    def __str__(self):
        return f"{self.severity.upper()}: {self.field} - {self.message}"

class ConfigValidator:
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_area(self, area_name: str, area: AreaConfig) -> List[ValidationError]:
        errors = []
        
        if area.configured:
            if not area.is_valid():
                if any([area.x1 is None, area.y1 is None, area.x2 is None, area.y2 is None]):
                    errors.append(ValidationError(
                        f"areas.{area_name}",
                        "Missing coordinate values",
                        "error"
                    ))
                elif area.x1 >= area.x2 or area.y1 >= area.y2:
                    errors.append(ValidationError(
                        f"areas.{area_name}",
                        "Invalid coordinate bounds (x1 >= x2 or y1 >= y2)",
                        "error"
                    ))
                elif area.x1 < 0 or area.y1 < 0:
                    errors.append(ValidationError(
                        f"areas.{area_name}",
                        "Negative coordinates not allowed",
                        "error"
                    ))
            
            area_width = area.x2 - area.x1 if area.x2 and area.x1 else 0
            area_height = area.y2 - area.y1 if area.y2 and area.y1 else 0
            
            if area_width < 10 or area_height < 10:
                errors.append(ValidationError(
                    f"areas.{area_name}",
                    f"Area too small ({area_width}x{area_height}), minimum 10x10 pixels",
                    "warning"
                ))
            
            if area_width > 2000 or area_height > 2000:
                errors.append(ValidationError(
                    f"areas.{area_name}",
                    f"Area very large ({area_width}x{area_height}), may impact performance",
                    "warning"
                ))
        
        return errors
    
    def validate_helper_settings(self, settings: HelperSettings) -> List[ValidationError]:
        errors = []
        
        if not 0.1 <= settings.step_timeout <= 300:
            errors.append(ValidationError(
                "helper_settings.step_timeout",
                f"Step timeout {settings.step_timeout} must be between 0.1 and 300 seconds",
                "error"
            ))
        
        if not 0.5 <= settings.image_matching_threshold <= 1.0:
            errors.append(ValidationError(
                "helper_settings.image_matching_threshold",
                f"Image matching threshold {settings.image_matching_threshold} must be between 0.5 and 1.0",
                "error"
            ))
        
        if not 0.1 <= settings.navigation_check_interval <= 10.0:
            errors.append(ValidationError(
                "helper_settings.navigation_check_interval",
                f"Navigation check interval {settings.navigation_check_interval} must be between 0.1 and 10.0 seconds",
                "error"
            ))
        
        if settings.step_timeout < 5:
            errors.append(ValidationError(
                "helper_settings.step_timeout",
                f"Step timeout {settings.step_timeout} is very low, may cause false timeouts",
                "warning"
            ))
        
        return errors
    
    def validate_advanced_settings(self, settings: AdvancedSettings) -> List[ValidationError]:
        errors = []
        
        if not 10 <= settings.health_threshold <= 99:
            errors.append(ValidationError(
                "advanced_settings.health_threshold",
                f"Health threshold {settings.health_threshold} must be between 10 and 99",
                "error"
            ))
        
        if not 0.1 <= settings.scan_interval <= 5.0:
            errors.append(ValidationError(
                "advanced_settings.scan_interval",
                f"Scan interval {settings.scan_interval} must be between 0.1 and 5.0 seconds",
                "error"
            ))
        
        if not 100 <= settings.max_log_lines <= 10000:
            errors.append(ValidationError(
                "advanced_settings.max_log_lines",
                f"Max log lines {settings.max_log_lines} must be between 100 and 10000",
                "error"
            ))
        
        if settings.max_backups < 1:
            errors.append(ValidationError(
                "advanced_settings.max_backups",
                f"Max backups {settings.max_backups} must be at least 1",
                "error"
            ))
        
        if not 0.5 <= settings.detection_sensitivity <= 1.0:
            errors.append(ValidationError(
                "advanced_settings.detection_sensitivity",
                f"Detection sensitivity {settings.detection_sensitivity} must be between 0.5 and 1.0",
                "error"
            ))
        
        if settings.health_threshold > 80:
            errors.append(ValidationError(
                "advanced_settings.health_threshold",
                f"Health threshold {settings.health_threshold} is very high, may cause frequent healing",
                "warning"
            ))
        
        if settings.auto_save_interval < 10:
            errors.append(ValidationError(
                "advanced_settings.auto_save_interval",
                f"Auto-save interval {settings.auto_save_interval} is very frequent, may impact performance",
                "warning"
            ))
        
        return errors
    
    def validate_ui_settings(self, settings: UISettings) -> List[ValidationError]:
        errors = []
        
        valid_themes = ["dark", "light"]
        if settings.theme not in valid_themes:
            errors.append(ValidationError(
                "ui_settings.theme",
                f"Theme '{settings.theme}' not valid, must be one of: {valid_themes}",
                "error"
            ))
        
        if not 6 <= settings.font_size <= 16:
            errors.append(ValidationError(
                "ui_settings.font_size",
                f"Font size {settings.font_size} must be between 6 and 16",
                "error"
            ))
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if settings.log_level not in valid_log_levels:
            errors.append(ValidationError(
                "ui_settings.log_level",
                f"Log level '{settings.log_level}' not valid, must be one of: {valid_log_levels}",
                "error"
            ))
        
        return errors
    
    def validate_navigation_steps(self, steps: List) -> List[ValidationError]:
        errors = []
        
        if len(steps) > 50:
            errors.append(ValidationError(
                "navigation_steps",
                f"Too many navigation steps ({len(steps)}), maximum recommended is 50",
                "warning"
            ))
        
        step_ids = set()
        for i, step in enumerate(steps):
            step_id = step.get('id') if isinstance(step, dict) else getattr(step, 'id', None)
            if step_id in step_ids:
                errors.append(ValidationError(
                    f"navigation_steps[{i}].id",
                    f"Duplicate step ID: {step_id}",
                    "error"
                ))
            step_ids.add(step_id)
            
            x = step.get('x') if isinstance(step, dict) else getattr(step, 'x', None)
            y = step.get('y') if isinstance(step, dict) else getattr(step, 'y', None)
            
            if x is not None and (x < 0 or x > 5000):
                errors.append(ValidationError(
                    f"navigation_steps[{i}].x",
                    f"X coordinate {x} is out of reasonable range (0-5000)",
                    "warning"
                ))
            
            if y is not None and (y < 0 or y > 5000):
                errors.append(ValidationError(
                    f"navigation_steps[{i}].y",
                    f"Y coordinate {y} is out of reasonable range (0-5000)",
                    "warning"
                ))
        
        return errors
    
    def validate_schema(self, schema: ConfigSchema) -> Tuple[List[ValidationError], List[ValidationError]]:
        errors = []
        warnings = []
        
        for area_name, area in schema.areas_schema.items():
            area_errors = self.validate_area(area_name, area)
            for error in area_errors:
                if error.severity == "error":
                    errors.append(error)
                else:
                    warnings.append(error)
        
        helper_errors = self.validate_helper_settings(schema.helper_settings)
        for error in helper_errors:
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        advanced_errors = self.validate_advanced_settings(schema.advanced_settings)
        for error in advanced_errors:
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        ui_errors = self.validate_ui_settings(schema.ui_settings)
        for error in ui_errors:
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        nav_errors = self.validate_navigation_steps(schema.navigation_steps)
        for error in nav_errors:
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        coordinate_errors = self.validate_area("coordinate_area", schema.coordinate_area)
        for error in coordinate_errors:
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        return errors, warnings
    
    def log_validation_results(self, errors: List[ValidationError], warnings: List[ValidationError]):
        if errors:
            logger.error(f"Configuration validation found {len(errors)} errors:")
            for error in errors:
                logger.error(f"  {error}")
        
        if warnings:
            logger.warning(f"Configuration validation found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")
        
        if not errors and not warnings:
            logger.info("Configuration validation passed successfully")
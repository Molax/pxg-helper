import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageGrab
import logging
import ctypes
import os
from ctypes import wintypes, Structure, c_wchar, sizeof, byref

logger = logging.getLogger('PokeXHelper')

class MONITORINFOEX(Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint32),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", ctypes.c_uint32),
        ("szDevice", c_wchar * 32)
    ]

class AreaSelector:
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger('PokeXHelper')
        
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None
        self.is_configured = False
        
        self.selection_window = None
        self.canvas = None
        self.selection_rect = None
        self.start_x = None
        self.start_y = None
        self.preview_image = None
        self.title = "Selection"
        self.color = "yellow"
        
        self.completion_callback = None
        self.desktop_bounds = None
        
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
        
    def is_setup(self):
        return self.is_configured and all([
            self.x1 is not None,
            self.y1 is not None,
            self.x2 is not None,
            self.y2 is not None
        ])
    
    def configure_from_saved(self, x1, y1, x2, y2):
        if all([x1 is not None, y1 is not None, x2 is not None, y2 is not None]):
            self.x1 = int(x1)
            self.y1 = int(y1)
            self.x2 = int(x2)
            self.y2 = int(y2)
            self.is_configured = True
            
            title = getattr(self, 'title', 'Selection')
            self.logger.info(f"{title} configured from saved coordinates: ({self.x1},{self.y1}) to ({self.x2},{self.y2})")
            
            try:
                self.preview_image = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2), all_screens=True)
            except TypeError:
                try:
                    self.preview_image = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
                except Exception as e:
                    self.logger.warning(f"Could not create preview image: {e}")
            except Exception as e:
                self.logger.warning(f"Could not create preview image: {e}")
                
            return True
        return False
    
    def _get_desktop_bounds(self):
        monitors = []
        
        def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            info = MONITORINFOEX()
            info.cbSize = sizeof(MONITORINFOEX)
            
            if ctypes.windll.user32.GetMonitorInfoW(hMonitor, byref(info)):
                rect = info.rcMonitor
                monitors.append({
                    'x': rect.left,
                    'y': rect.top,
                    'width': rect.right - rect.left,
                    'height': rect.bottom - rect.top
                })
            return True
        
        try:
            MonitorEnumProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(wintypes.RECT),
                ctypes.c_ulong
            )
            
            callback = MonitorEnumProc(monitor_enum_proc)
            ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
        except Exception as e:
            self.logger.error(f"Error enumerating monitors: {e}")
        
        if not monitors:
            try:
                width = ctypes.windll.user32.GetSystemMetrics(0)
                height = ctypes.windll.user32.GetSystemMetrics(1)
                monitors = [{'x': 0, 'y': 0, 'width': width, 'height': height}]
                self.logger.info(f"Fallback to primary monitor: {width}x{height}")
            except Exception as e:
                self.logger.error(f"Error getting system metrics: {e}")
                monitors = [{'x': 0, 'y': 0, 'width': 1920, 'height': 1080}]
        
        if not monitors:
            return 0, 0, 1920, 1080
            
        min_x = min(m['x'] for m in monitors)
        min_y = min(m['y'] for m in monitors)
        max_x = max(m['x'] + m['width'] for m in monitors)
        max_y = max(m['y'] + m['height'] for m in monitors)
        
        width = max_x - min_x
        height = max_y - min_y
        
        self.logger.info(f"Desktop bounds: ({min_x}, {min_y}) to ({max_x}, {max_y}) = {width}x{height}")
        return min_x, min_y, width, height
    
    def start_selection(self, title="Select Area", color="yellow", completion_callback=None):
        self.logger.info(f"Starting area selection: {title}")
        self.title = title
        self.color = color
        self.completion_callback = completion_callback
        
        try:
            self.desktop_bounds = self._get_desktop_bounds()
            return self._create_selection_window()
            
        except Exception as e:
            self.logger.error(f"Error starting selection: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start selection: {e}")
            return False
    
    def _create_selection_window(self):
        try:
            if self.selection_window:
                self.selection_window.destroy()
                
            self.selection_window = tk.Toplevel(self.root)
            self.selection_window.withdraw()
            
            desktop_x, desktop_y, desktop_width, desktop_height = self.desktop_bounds
            
            self.logger.info(f"Creating selection window with desktop bounds: {self.desktop_bounds}")
            
            try:
                screenshot = ImageGrab.grab(all_screens=True)
                self.logger.info(f"Screenshot captured with size: {screenshot.size}")
            except Exception as e:
                self.logger.error(f"Failed to capture screenshot: {e}")
                return False
            
            if screenshot.size != (desktop_width, desktop_height):
                self.logger.info(f"Screenshot size {screenshot.size} != expected {desktop_width}x{desktop_height}, adjusting")
                try:
                    if screenshot.size[0] >= desktop_width and screenshot.size[1] >= desktop_height:
                        screenshot = screenshot.crop((0, 0, desktop_width, desktop_height))
                    else:
                        screenshot = screenshot.resize((desktop_width, desktop_height), Image.Resampling.LANCZOS)
                except Exception as resize_error:
                    self.logger.warning(f"Failed to resize screenshot: {resize_error}")
            
            self.screenshot_tk = ImageTk.PhotoImage(screenshot)
            
            self.selection_window.overrideredirect(True)
            self.selection_window.attributes('-alpha', 0.8)
            self.selection_window.attributes('-topmost', True)
            self.selection_window.configure(bg='black')
            self.selection_window.geometry(f"{desktop_width}x{desktop_height}+{desktop_x}+{desktop_y}")
            
            self.canvas = tk.Canvas(
                self.selection_window, 
                cursor="crosshair",
                highlightthickness=0,
                bg='black',
                width=desktop_width,
                height=desktop_height
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            self.canvas.create_image(0, 0, image=self.screenshot_tk, anchor=tk.NW)
            
            text_x = desktop_width // 2
            text_y = 50
            
            self.canvas.create_text(
                text_x, text_y,
                text=f"Select {self.title}",
                fill="white",
                font=("Arial", 24, "bold")
            )
            
            self.canvas.create_text(
                text_x, text_y + 40,
                text="Click and drag to select the area",
                fill="yellow",
                font=("Arial", 18)
            )
            
            self.canvas.create_text(
                text_x, text_y + 80,
                text="ESC to cancel",
                fill="white",
                font=("Arial", 16)
            )
            
            self.canvas.bind("<Button-1>", self._on_click)
            self.canvas.bind("<B1-Motion>", self._on_drag)
            self.canvas.bind("<ButtonRelease-1>", self._on_release)
            
            self.selection_window.bind("<Escape>", self._on_escape)
            self.selection_window.bind("<Key>", self._on_key)
            
            self.selection_window.deiconify()
            self.selection_window.focus_force()
            self.selection_window.grab_set()
            
            self.start_x = None
            self.start_y = None
            
            self.logger.info("Area selection window created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating selection window: {e}", exc_info=True)
            return False
    
    def _on_click(self, event):
        desktop_x, desktop_y, desktop_width, desktop_height = self.desktop_bounds
        self.start_x = event.x + desktop_x
        self.start_y = event.y + desktop_y
        
        self.logger.debug(f"Click registered: canvas ({event.x}, {event.y}) -> global ({self.start_x}, {self.start_y})")
        
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.canvas.delete("size_info")
            
    def _on_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
            
        desktop_x, desktop_y, desktop_width, desktop_height = self.desktop_bounds
        current_x = event.x + desktop_x
        current_y = event.y + desktop_y
        
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.canvas.delete("size_info")
        
        canvas_x1 = self.start_x - desktop_x
        canvas_y1 = self.start_y - desktop_y
        canvas_x2 = event.x
        canvas_y2 = event.y
        
        self.selection_rect = self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline=self.color,
            width=4,
            fill="",
            dash=(10, 5)
        )
        
        width = abs(current_x - self.start_x)
        height = abs(current_y - self.start_y)
        
        if width > 10 and height > 10:
            self.canvas.create_text(
                (canvas_x1 + canvas_x2) / 2,
                (canvas_y1 + canvas_y2) / 2,
                text=f"{int(width)} × {int(height)}",
                fill="white",
                font=("Arial", 16, "bold"),
                tags="size_info"
            )
    
    def _on_release(self, event):
        if self.start_x is None or self.start_y is None:
            self.logger.warning("Mouse release without valid start coordinates")
            return
            
        desktop_x, desktop_y, desktop_width, desktop_height = self.desktop_bounds
        end_x = event.x + desktop_x
        end_y = event.y + desktop_y
        
        self.x1 = min(self.start_x, end_x)
        self.y1 = min(self.start_y, end_y)
        self.x2 = max(self.start_x, end_x)
        self.y2 = max(self.start_y, end_y)
        
        width = abs(self.x2 - self.x1)
        height = abs(self.y2 - self.y1)
        
        self.logger.info(f"Selection complete: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2}), size: {width}x{height}")
        
        if width < 5 or height < 5:
            self.logger.warning("Selection too small, ignoring")
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            self.canvas.delete("size_info")
            self.start_x = None
            self.start_y = None
            return
        
        self.logger.info(f"Selection made: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})")
        self._show_confirm_dialog()
    
    def _on_escape(self, event):
        self.logger.info("Selection cancelled by user (ESC key)")
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
    
    def _on_key(self, event):
        if event.keysym == 'Escape':
            self._on_escape(event)
    
    def _show_confirm_dialog(self):
        if not all([self.x1, self.y1, self.x2, self.y2]):
            self.logger.error("Cannot show confirm dialog: coordinates not set")
            return
        
        width = abs(self.x2 - self.x1)
        height = abs(self.y2 - self.y1)
        
        try:
            try:
                self.preview_image = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2), all_screens=True)
            except TypeError:
                self.preview_image = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
            
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            preview_path = f"{debug_dir}/{self.title.replace(' ', '_').lower()}_preview.png"
            self.preview_image.save(preview_path)
            self.logger.debug(f"Saved preview to {preview_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating preview: {e}")
        
        self.selection_window.withdraw()
        
        confirm = messagebox.askyesno(
            f"Confirm {self.title} Selection",
            f"Is this the correct area for {self.title}?\n\n"
            f"Coordinates: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})\n"
            f"Size: {width}×{height} pixels",
            parent=self.root
        )
        
        if confirm:
            self.is_configured = True
            self.logger.info(f"{self.title} selection confirmed: ({self.x1}, {self.y1}) to ({self.x2}, {self.y2})")
            
            if self.selection_window:
                self.selection_window.destroy()
                self.selection_window = None
            
            if self.completion_callback:
                try:
                    self.completion_callback()
                except Exception as e:
                    self.logger.error(f"Error in completion callback: {e}")
        else:
            self.selection_window.deiconify()
            self.logger.info(f"{self.title} selection canceled, retrying")
            if self.canvas and self.selection_rect:
                self.canvas.delete(self.selection_rect)
            self.canvas.delete("size_info")
            self.selection_rect = None
            self.preview_image = None
            self.start_x = None
            self.start_y = None
    
    def get_current_screenshot_region(self):
        if not self.is_configured:
            self.logger.warning("Cannot capture region: not configured yet")
            return None
            
        if not all([self.x1, self.y1, self.x2, self.y2]):
            self.logger.warning("Cannot capture region: coordinates not set")
            return None
            
        try:
            if any(coord < -10000 or coord > 10000 for coord in [self.x1, self.y1, self.x2, self.y2]):
                self.logger.error(f"Coordinates out of range: ({self.x1},{self.y1}) to ({self.x2},{self.y2})")
                return None
                
            if self.x2 <= self.x1 or self.y2 <= self.y1:
                self.logger.error(f"Invalid coordinate order: ({self.x1},{self.y1}) to ({self.x2},{self.y2})")
                return None
            
            try:
                screenshot = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2), all_screens=True)
            except TypeError:
                screenshot = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
            
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.logger.error(f"Screenshot has zero dimensions: {screenshot.size}")
                return None
                
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Error capturing region: {e}", exc_info=True)
            return None
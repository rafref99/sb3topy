"""
monitors.py

Contains classes for variable and list monitors.
"""

import pygame as pg
from . import config

class Monitor(pg.sprite.DirtySprite):
    """
    A simple variable monitor.
    """
    def __init__(self, name, target, varname, x, y, visible, mode, slider_min=0, slider_max=100):
        super().__init__()
        self.name = name
        self.target = target
        self.varname = varname
        self.visible = visible
        self.mode = mode # 'default', 'large', 'slider'
        
        self.font = pg.font.SysFont("Arial", 12, bold=True)
        self.value_font = pg.font.SysFont("Arial", 12, bold=True)
        
        self.x = x
        self.y = y
        self.rect = pg.Rect(x, y, 0, 0)
        self.image = None
        
        self.last_value = None
        self.dirty = 2 # Always dirty at start

    def update(self, display):
        if not self.visible:
            return

        # Get current value from target
        try:
            value = getattr(self.target, self.varname)
        except AttributeError:
            value = ""

        if value != self.last_value or self.dirty:
            self.last_value = value
            self.render_monitor(display)
            self.dirty = 1

    def render_monitor(self, display):
        # Simple rendering for now
        val_str = str(self.last_value)
        
        if self.mode == 'large':
            val_surf = self.value_font.render(val_str, True, (255, 255, 255))
            width = max(val_surf.get_width() + 10, 40)
            height = val_surf.get_height() + 5
            self.image = pg.Surface((width, height), pg.SRCALPHA)
            self.image.fill((255, 140, 26)) # Orange
            self.image.blit(val_surf, ((width - val_surf.get_width())//2, (height - val_surf.get_height())//2))
        else:
            name_surf = self.font.render(self.name, True, (0, 0, 0))
            val_surf = self.value_font.render(val_str, True, (255, 255, 255))
            
            val_width = max(val_surf.get_width() + 10, 30)
            width = name_surf.get_width() + val_width + 15
            height = 20
            
            self.image = pg.Surface((width, height), pg.SRCALPHA)
            self.image.fill((230, 230, 230)) # Light gray background
            pg.draw.rect(self.image, (150, 150, 150), self.image.get_rect(), 1) # Border
            
            self.image.blit(name_surf, (5, (height - name_surf.get_height())//2))
            
            val_rect = pg.Rect(name_surf.get_width() + 10, 2, val_width, height - 4)
            pg.draw.rect(self.image, (255, 140, 26), val_rect) # Orange box
            self.image.blit(val_surf, (val_rect.centerx - val_surf.get_width()//2, val_rect.centery - val_surf.get_height()//2))

        # Scale and position
        self.image = pg.transform.scale(self.image, (int(self.image.get_width() * display.scale), int(self.image.get_height() * display.scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (display.rect.x + self.x * display.scale, display.rect.y + self.y * display.scale)

    def set_position(self, x, y, scale, display_rect):
        self.rect.x = display_rect.x + x * scale
        self.rect.y = display_rect.y + y * scale

class ListMonitor(pg.sprite.DirtySprite):
    """
    A list monitor.
    """
    def __init__(self, name, target, listname, x, y, width, height, visible):
        super().__init__()
        self.name = name
        self.target = target
        self.listname = listname
        self.visible = visible
        
        self.font = pg.font.SysFont("Arial", 12, bold=True)
        self.item_font = pg.font.SysFont("Arial", 12)
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pg.Rect(x, y, width, height)
        self.image = None
        self.last_value = None
        self.dirty = 2

    def update(self, display):
        if not self.visible:
            return

        try:
            scratch_list = getattr(self.target, self.listname)
            value = list(getattr(scratch_list, "list", scratch_list))
        except AttributeError:
            value = []

        if value != self.last_value or self.dirty:
            self.last_value = value
            self.render_monitor(display)
            self.dirty = 1

    def render_monitor(self, display):
        width = max(1, self.width)
        height = max(1, self.height)
        self.image = pg.Surface((width, height), pg.SRCALPHA)
        self.image.fill((230, 230, 230))
        pg.draw.rect(self.image, (150, 150, 150), self.image.get_rect(), 1)
        
        # Title
        name_surf = self.font.render(self.name, True, (0, 0, 0))
        self.image.blit(name_surf, ((width - name_surf.get_width())//2, 2))
        
        # Items (basic display)
        y_offset = 20
        for i, item in enumerate(self.last_value[:10]): # Only show first 10 for now
            item_str = f"{i+1} {item}"
            item_surf = self.item_font.render(item_str, True, (0, 0, 0))
            self.image.blit(item_surf, (5, y_offset))
            y_offset += 15
            if y_offset > height - 15:
                break
        
        # Length
        len_str = f"length {len(self.last_value)}"
        len_surf = self.font.render(len_str, True, (0, 0, 0))
        self.image.blit(len_surf, ((width - len_surf.get_width())//2, height - 15))

        # Scale
        self.image = pg.transform.scale(self.image, (int(width * display.scale), int(height * display.scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (display.rect.x + self.x * display.scale, display.rect.y + self.y * display.scale)

    def set_position(self, x, y, scale, display_rect):
        self.rect.x = display_rect.x + x * scale
        self.rect.y = display_rect.y + y * scale

"""Debugging module."""
import pygame
import logging

from .display import DisplayManager, DisplayLayer
from .events import TickEvent, EventManager
from .modules import Module
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class DebugModule(Module):

    """Debugging module."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.debug = self.container.get(DebugFlag)

        self.events = self.container.get(EventManager)

        self.clock = self.container.get(DisplayClock)
        self.display = self.container.get(DisplayManager)
        self.font = pygame.font.SysFont('monospace', 14)

        self.layer = DisplayLayer(size=[300, 190], position=[5, 5], flags=pygame.SRCALPHA, z_index=250)

    def start(self):
        """Start the module."""
        self.display.add_layer(self.layer)
        self.events.register(TickEvent, self.on_tick)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def on_tick(self, event):
        """Handle a tick."""
        if not self.debug.value:
            return

        self.layer.surface.fill([10, 10, 10, 200])

        info = pygame.display.Info()

        text = [
            "Akurra DEV",
            "FPS: %d" % self.clock.get_fps(),
            "Driver: %s" % pygame.display.get_driver(),
            "HW accel: %s" % info.hw,
            "Windowed support: %s" % info.wm,
            "Video mem: %s mb" % info.video_mem,
            "HW surface blit accel: %s" % info.blit_hw,
            "HW surface colorkey blit accel: %s" % info.blit_hw_CC,
            "HW surface pixel alpha blit accel: %s" % info.blit_hw_A,
            "SW surface blit accel: %s" % info.blit_sw,
            "SW surface colorkey blit accel: %s" % info.blit_sw_CC,
            "SW surface pixel alpha blit accel: %s" % info.blit_sw_A
        ]

        offset_x = 5
        offset_y = 5
        line_height = 15

        for t in text:
            self.layer.surface.blit(self.font.render(t, 1, (255, 255, 0)), [offset_x, offset_y])
            offset_y += line_height

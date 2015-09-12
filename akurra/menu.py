"""Menu module."""

import logging
import pygame
from .states import GameState

logger = logging.getLogger(__name__)


class MenuButton:
    """A button on a menu screen."""

    def __init__(self, name, callback):
        """Init function."""
        from .input import InputModule
        self.name = name
        self.callback = callback
        self.input = self.container.get(InputModule)


class MenuScreen(GameState):
    """Base class for menu screen."""

    def __init__(self, name, background_color=(0, 0, 0, 255)):
        """Initialize the menu screen."""
        from .events import EventManager
        from .display import DisplayLayer, DisplayModule
        super().__init__()
        self.name = name
        self.background_color = background_color
        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.layer = DisplayLayer(flags=pygame.SRCALPHA)
        self.big_font = pygame.font.SysFont('monospace', 50)

        # store a few values ahead of time  so we don't have to
        # calculate them during ticks
        self.title = self.big_font.render(self.name, False, (255, 0, 0))
        self.screen_size = self.display.screen.get_size()
        self.title_position = (int((self.screen_size[0] - self.title.get_width()) / 2), 0)

    def enable(self):
        """Enable the menu screen."""
        from .events import TickEvent
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)
        self.display.add_layer(self.layer)

    def disable(self):
        """Disable the menu screen."""
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def on_video_resize(self, event):
        """Adjust resolution when resize event occurs."""
        self.screen_size = event.size
        self.title_position = (int((self.screen_size[0] - self.title.get_width()) / 2), 0)

    def on_tick(self, event):
        """Respond to tick events"""
        surface = self.layer.surface
        surface.fill(self.background_color)
        surface.blit(self.title, self.title_position)



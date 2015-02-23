"""Debug module."""
import logging
import pygame
from injector import inject
from akurra.logging import configure_logging
from akurra.events import EventManager
from akurra.display import FrameRenderCompletedEvent
from akurra.keyboard import KeyboardManager
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class DebugManager:

    """Debug manager."""

    def on_frame_render_completed(self, event):
        """Handle a frame render completion."""
        if self.debug.value:
            pygame.display.set_caption('%s (FPS: %d)' % (self.display_caption, self.clock.get_fps()))

    def on_toggle(self, event):
        """Handle a debug toggle."""
        logger.debug('Toggling debug state')
        self.disable() if self.debug.value else self.enable()

    def enable(self):
        """Enable debugging."""
        self.debug.value = True
        configure_logging(debug=self.debug.value)

        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)

    def disable(self):
        """Disable debugging."""
        self.debug.value = False
        configure_logging(debug=self.debug.value)

        self.events.unregister(self.on_frame_render_completed)
        pygame.display.set_caption(self.display_caption)

    @inject(keyboard=KeyboardManager, events=EventManager, screen=DisplayScreen, display_caption=DisplayCaption,
            clock=DisplayClock, debug=DebugFlag)
    def __init__(self, keyboard, events, screen, display_caption, clock, debug):
        """Constructor."""
        logger.debug('Initializing DebugManager')

        self.keyboard = keyboard
        self.keyboard.register(pygame.K_F11, self.on_toggle, mods=pygame.KMOD_LCTRL)

        self.debug = debug
        self.display_caption = display_caption
        self.events = events
        self.clock = clock
        self.screen = screen

        if self.debug.value:
            self.enable()

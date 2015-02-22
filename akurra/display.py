"""Screen module."""
import logging
import pygame
from injector import inject, singleton, Module
from akurra.locals import Display, DisplayResolution, DisplayFlags
from akurra.events import Event, EventManager


logger = logging.getLogger(__name__)


class DisplayModule(Module):

    """Display module."""

    def configure(self, binder):
        """Configure a dependency injector."""
        binder.bind(DisplayManager, scope=singleton)
        binder.bind(Display, create_display)


@singleton
@inject(resolution=DisplayResolution, flags=DisplayFlags)
def create_display(resolution=[0, 0], flags=0):
    """Create and return a display with a few options."""
    display = pygame.display.set_mode(resolution, flags)
    logger.debug('Display created [resolution=%s, flags=%s]', resolution, flags)

    return display


class FrameRenderEvent(Event):

    """Frame render event."""


class FrameRenderCompletedEvent(Event):

    """Frame render completion event."""


class DisplayManager:

    """Display controller."""

    @inject(display=Display)
    def on_frame_render(self, event, display):
        """
        Perform a frame render, updating the contents of the entire display.

        Internally, this will perform a screen flip.
        See also http://www.pygame.org/docs/ref/display.html#pygame.display.flip

        :param event: FrameRenderEvent

        """
        pygame.display.flip()
        self.events.dispatch(FrameRenderCompletedEvent())

    @inject(events=EventManager)
    def __init__(self, events):
        """Constructor."""
        logger.debug('Initializing DisplayManager')

        self.events = events
        self.events.register(FrameRenderEvent, self.on_frame_render)

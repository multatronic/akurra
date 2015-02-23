"""Screen module."""
import logging
import pygame
from injector import inject, singleton, Module
from akurra.locals import *  # noqa
from akurra.events import Event, EventManager


logger = logging.getLogger(__name__)


class DisplayModule(Module):

    """Display module."""

    def configure(self, binder):
        """Configure a dependency injector."""
        binder.bind(DisplayManager, scope=singleton)
        binder.bind(DisplayScreen, create_screen)


@singleton
@inject(resolution=DisplayResolution, flags=DisplayFlags, caption=DisplayCaption)
def create_screen(resolution=[0, 0], flags=0, caption='akurra'):
    """Create and return a screen with a few options."""
    screen = pygame.display.set_mode(resolution, flags)
    pygame.display.set_caption(caption)
    logger.debug('Display created [resolution=%s, flags=%s]', resolution, flags)

    return screen


class FrameRenderEvent(Event):

    """Frame render event."""


class FrameRenderCompletedEvent(Event):

    """Frame render completion event."""


class DisplayManager:

    """Display controller."""

    def on_frame_render(self, event):
        """
        Perform a frame render, updating the contents of the entire display.

        Internally, this will perform a screen flip.
        See also http://www.pygame.org/docs/ref/display.html#pygame.display.flip

        :param event: FrameRenderEvent

        """
        pygame.display.flip()
        self.clock.tick(self.max_fps)

        self.events.dispatch(FrameRenderCompletedEvent())

    @inject(events=EventManager, screen=DisplayScreen, clock=DisplayClock, max_fps=DisplayMaxFPS)
    def __init__(self, events, screen, clock, max_fps=250):
        """Constructor."""
        logger.debug('Initializing DisplayManager')

        self.events = events
        self.events.register(FrameRenderEvent, self.on_frame_render)

        self.screen = screen
        self.clock = clock
        self.max_fps = max_fps

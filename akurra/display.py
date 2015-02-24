"""Screen module."""
import logging
import pygame
from injector import inject
from akurra.locals import *  # noqa
from akurra.events import Event, EventManager


logger = logging.getLogger(__name__)


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


class DisplayObject:

    """Display object."""

    def __init__(self, **kwargs):
        """Constructor."""
        for key in kwargs:
            setattr(self, key, kwargs[key])


class DisplayManager:

    """Display controller."""

    def add(self, object):
        """Add an object to the display."""
        self.objects[id(object)] = object

    def remove(self, object):
        """Remove an object from the display."""
        self.objects.pop(id(object), None)

    def on_frame_render(self, event):
        """
        Perform a frame render, updating the contents of the entire display.

        Internally, this will perform a screen flip.
        See also http://www.pygame.org/docs/ref/display.html#pygame.display.flip

        :param event: FrameRenderEvent

        """
        # @TODO Load background from map
        # @TODO Z-index support for all objects
        self.screen.fill([25, 25, 25])

        for o_id in self.objects:
            self.screen.blit(self.objects[o_id].surface, self.objects[o_id].position)

        pygame.display.update()
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
        self.objects = {}

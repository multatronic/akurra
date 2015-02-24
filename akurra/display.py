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

    @property
    def display(self):
        """Return display."""
        return self._display

    @display.setter
    def display(self, value):
        """Set display."""
        self._display = value

    @property
    def z_index(self):
        """Return zIndex."""
        return self._z_index

    @z_index.setter
    def z_index(self, value):
        """Set zIndex."""
        # If we're attached to the displaymanager, unbind from the old layer and bind to the new one
        display = self.display if self.display else None

        if display:
            display.remove(self)

        self._z_index = value

        if display:
            display.add(self)

        self._z_index = value

    def __init__(self, **kwargs):
        """Constructor."""
        self._z_index = 1000
        self._display = None

        for key in kwargs:
            setattr(self, key, kwargs[key])


class DisplayManager:

    """Display controller."""

    def add(self, object):
        """Add an object to the display."""
        if object.z_index not in self.objects:
            self.objects[object.z_index] = {}
            self.object_keys = sorted(self.objects.keys(), key=int)

        self.objects[object.z_index][id(object)] = object

        # Set display within object
        object.display = self

    def remove(self, object):
        """Remove an object from the display."""
        to_remove = None

        # If we're able to remov an object and there are no other objects for this z_index,
        # queue the layer for removal
        if self.objects[object.z_index].pop(id(object), None) and not self.objects[object.z_index]:
            to_remove = object.z_index

        if to_remove:
            self.objects.pop(to_remove, None)
            self.object_keys.remove(to_remove)

        # Remove display from object
        object.display = None

    def on_frame_render(self, event):
        """
        Perform a frame render, updating the contents of the entire display.

        Internally, this will perform a screen flip.
        See also http://www.pygame.org/docs/ref/display.html#pygame.display.flip

        :param event: FrameRenderEvent

        """
        # @TODO Load background from map
        self.screen.fill([25, 25, 25])

        for z_index in self.object_keys:
            for o_id in self.objects[z_index]:
                self.screen.blit(self.objects[z_index][o_id].surface, self.objects[z_index][o_id].position)

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
        self.object_keys = []

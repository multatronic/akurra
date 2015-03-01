"""Screen module."""
import logging
import pygame
from injector import inject
import pyscroll
from pyscroll.util import PyscrollGroup
from akurra.locals import *  # noqa
from akurra.events import Event, TickEvent, EventManager


logger = logging.getLogger(__name__)


@inject(resolution=DisplayResolution, flags=DisplayFlags, caption=DisplayCaption)
def create_screen(resolution=[0, 0], flags=0, caption='akurra'):
    """Create and return a screen with a few options."""
    screen = pygame.display.set_mode(resolution, flags)
    pygame.display.set_caption(caption)
    logger.debug('Display created [resolution=%s, flags=%s]', resolution, flags)

    return screen


class FrameRenderCompletedEvent(Event):

    """Frame render completion event."""


class DisplayLayer:

    """Display layer."""

    def __init__(self, size=None, position=[0, 0], z_index=None, display=None):
        """Constructor."""
        if not z_index:
            z_index = 100

        if display and not size:
            size = display.screen.get_size()

        self._z_index = z_index
        self._display = display
        self.size = size
        self.position = position

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
        # If we're attached to the displaymanager, make sure our z_index
        # binding is correct
        display = self.display if self.display else None

        if display:
            display.remove(self)

        self._z_index = value

        if display:
            display.add(self)

        self._z_index = value

    def update(self, delta_time):
        """
        Compute an update to the layer's state.

        Generally, this will update the state of all objects inside of the layer.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        # Do stuff here

    def draw(self):
        """Draw the layer onto the display."""
        # Do stuff here

    def resize(self, size):
        """
        Resize the layer.

        :param list size: New layer size, in pixels.

        """
        self.size = size


class SurfaceDisplayLayer(DisplayLayer):

    """
    Surface display layer.

    A display layer for rendering a surface.

    """

    def __init__(self, size=None, position=[0, 0], flags=0, z_index=None, display=None):
        """Constructor."""
        super().__init__(size=size, position=position, z_index=z_index, display=display)

        self.surface = pygame.Surface(self.size, flags=flags)

    def draw(self):
        """Draw the layer onto the display."""
        super().draw()

        self.display.screen.blit(self.surface, self.position)

    def resize(self, size):
        """Resize the layer."""
        self.surface = pygame.transform.scale(self.surface, size)

        super().resize(size)


class ObjectsSurfaceDisplayLayer(SurfaceDisplayLayer):

    """
    Objects surface display layer.

    A display layer for rendering display objects with surfaces onto a root surface.

    """

    def __init__(self, size=None, position=[0, 0], flags=0, z_index=None, display=None):
        """Constructor."""
        super().__init__(size=size, position=position, flags=flags, z_index=z_index, display=display)

        self.objects = {}
        self.object_z_indexes = []

    def add_object(self, object):
        """Add an object to the layer."""
        if object.z_index not in self.objects:
            self.objects[object.z_index] = {}
            self.object_z_indexes = sorted(self.objects.keys(), key=int)

        self.objects[object.z_index][object] = 1

        # Set layer within object
        object.layer = self

    def remove_object(self, object):
        """Remove an object from the layer."""
        to_remove = None

        # If we're able to remov an object and there are no other objects for this z_index,
        # queue the key for removal
        if self.objects[object.z_index].pop(object, None) and not self.objects[object.z_index]:
            to_remove = object.z_index

        if to_remove:
            self.objects.pop(to_remove, None)
            self.object_z_indexes.remove(to_remove)

        # Remove layer from object
        object.layer = None

    def update(self, delta_time):
        """Compute an update to the layer's state."""
        super().update(delta_time)

        for z_index in self.object_z_indexes:
            for object in self.objects[z_index]:
                object.update(delta_time)

    def draw(self):
        """Draw the layer onto the display."""
        for z_index in self.object_z_indexes:
            for object in self.objects[z_index]:
                self.surface.blit(object.surface, object.position)

        super().draw()


class ScrollingMapDisplayLayer(DisplayLayer):

    """
    Scrollable map display layer.

    A display layer for rendering a scrollable map.

    """

    def __init__(self, tmx_data, default_layer=0, size=None, z_index=None, display=None):
        """Constructor."""
        super().__init__(size=size, z_index=z_index, display=display)

        # Create data source
        self.map_data = pyscroll.data.TiledMapData(tmx_data)
        # Auto-generate collision map
        self.collision_map = [pygame.Rect(x.x, x.y, x.width, x.height) for x in tmx_data.objects]

        self.map_layer = pyscroll.BufferedRenderer(self.map_data, self.size, clamp_camera=True)
        self.surface = self.map_layer.buffer
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=default_layer)

        self.center = None

    def update(self, delta_time):
        """Compute an update to the layer's state."""
        self.group.update(delta_time)

        # Check if entity bases are colliding with the collision map
        # Entities must have a rect called core, and a revert_move method,
        # otherwise this will fail
        for entity in self.group.sprites():
            if entity.core.collidelist(self.collision_map) > -1:
                entity.revert_move()

    def draw(self):
        """Draw the layer onto the display."""
        # Center the map/screen if needed
        if self.center:
            self.group.center(self.center.rect.center)

        # Draw the map and all sprites
        self.group.draw(self.display.screen)

    def resize(self, size):
        """Handle a resize."""
        self.map_layer.set_size(size)
        self.surface = self.map_layer.buffer

        super().resize(size)


class DisplayManager:

    """Display controller."""

    def add_layer(self, layer):
        """Add a layer to the display."""
        if layer.z_index not in self.layers:
            self.layers[layer.z_index] = {}
            self.layer_z_indexes = sorted(self.layers.keys(), key=int)

        self.layers[layer.z_index][layer] = 1

        # Set display within layer
        layer.display = self

    def remove_layer(self, layer):
        """Remove a layer from the display."""
        to_remove = None

        # If we're able to remove a layer and there are no other layers for this z_index,
        # queue the key for removal
        if self.layers[layer.z_index].pop(layer, None) and not self.layers[layer.z_index]:
            to_remove = layer.z_index

        if to_remove:
            self.layers.pop(to_remove, None)
            self.layer_z_indexes.remove(to_remove)

        # Remove display from layer
        layer.display = None

    def on_tick(self, event):
        """
        Perform a frame render, updating the contents of the entire display.

        Internally, this will render all layers and perform a screen update.
        See also http://www.pygame.org/docs/ref/display.html#pygame.display.flip

        :param event: TickEvent

        """
        for z_index in self.layer_z_indexes:
            for layer in self.layers[z_index]:
                layer.update(event.delta_time)
                layer.draw()

        pygame.display.flip()
        self.events.dispatch(FrameRenderCompletedEvent())

    def on_video_resize(self, event):
        """Handle resizing of the display."""
        old_size = pygame.display.get_surface().get_size()
        create_screen(event.size)

        for z_index in self.layers:
            for layer in self.layers[z_index]:
                if layer.size == old_size:
                    layer.resize(event.size)

    @inject(events=EventManager, screen=DisplayScreen, clock=DisplayClock, max_fps=DisplayMaxFPS)
    def __init__(self, events, screen, clock, max_fps=240):
        """Constructor."""
        logger.debug('Initializing DisplayManager')

        self.events = events
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)

        self.screen = screen

        self.layers = {}
        self.layer_z_indexes = []

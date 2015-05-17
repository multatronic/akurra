"""Screen module."""
import logging
import pygame
import random
from injector import inject
import pyscroll
from pyscroll.util import PyscrollGroup

from .locals import *  # noqa
from .events import Event, TickEvent, EventManager
from .entities import MapLayerComponent, EntityManager
from .utils import ContainerAware


logger = logging.getLogger(__name__)


class FrameRenderCompletedEvent(Event):

    """Frame render completion event."""


class DisplayLayer(ContainerAware):

    """Display layer."""

    def __init__(self, size=None, flags=0, position=[0, 0], z_index=None):
        """Constructor."""
        if not z_index:
            z_index = 100

        if not size:
            info = pygame.display.Info()
            size = info.current_w, info.current_h

        self._z_index = z_index
        self.display = None

        self.size = size
        self.position = position
        self.flags = flags

        self.surface = pygame.Surface(self.size, flags=self.flags)

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

    def update(self, delta_time):
        """
        Compute an update to the layer's state.

        Generally, this will update the state of all objects inside of the layer.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        pass

    def draw(self, surface):
        """Draw the layer onto a surface."""
        surface.blit(self.surface, self.position)

    def resize(self, size):
        """
        Resize the layer.

        :param list size: New layer size, in pixels.

        """
        self.size = size
        self.surface = pygame.transform.scale(self.surface, self.size)


class ObjectsDisplayLayer(DisplayLayer):

    """
    Objects display layer.

    A display layer for rendering display objects with surfaces onto a root surface.

    """

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

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

    def draw(self, surface):
        """Draw the layer onto a surface."""
        for z_index in self.object_z_indexes:
            for object in self.objects[z_index]:
                object.draw(self.surface)

        super().draw(surface)


class EntityDisplayLayer(DisplayLayer):

    """
    Entity display layer.

    A layer for rendering and displaying entities.

    """

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.entities = {}

    def add_entity(self, entity):
        """Add an entity to the layer."""
        entity.add_component(MapLayerComponent(layer=self))
        self.entities[entity.id] = entity

    def remove_entity(self, entity):
        """Remove an entity from the layer."""
        entity.components.pop(MapLayerComponent, None)
        self.entities.pop(entity.id, None)

    def draw(self, surface):
        """Draw the layer onto a surface."""
        for entity_id in self.entities:
            self.surface.blit(self.entities[entity_id].components['sprite'].image, self.entities[entity_id].components['position'].position)

        super().draw(surface)


class ScrollingMapEntityDisplayLayer(EntityDisplayLayer):

    """
    Scrollable map display layer.

    A display layer for rendering entities on a scrollable map.

    """

    def __init__(self, tmx_data, default_layer=0, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.em = self.container.get(EntityManager)

        # Create data source
        self.map_data = pyscroll.data.TiledMapData(tmx_data)
        self.map_layer = pyscroll.BufferedRenderer(self.map_data, self.size, clamp_camera=True)

        self.surface = self.map_layer.buffer
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=default_layer)

        self.build_collision_map()
        self.spawn_entities()

        self.center = None

    def build_collision_map(self):
        """Build a collision map based on map data."""
        self.collision_map = []

        for o in self.map_data.tmx.objects:
            if o.properties.get('collision', False):
                self.collision_map.append(pygame.Rect(o.x, o.y, o.width, o.height))

    def spawn_entities(self):
        """Spawn entities on the map based on map data."""
        for o in self.map_data.tmx.objects:
            if o.properties.get('spawn', False):
                templates = o.properties['spawn_templates'].split(';')

                for i in range(0, o.properties.get('spawn_count', 1)):
                    template = random.choice(templates)
                    entity = self.em.create_entity_from_template(template)

                    if 'position' in entity.components:
                        entity.components['position'].position = pygame.Rect(o.x, o.y, o.width, o.height).center

                    self.add_entity(entity)

    def update(self, delta_time):
        """Compute an update to the layer's state."""
        super().update(delta_time)
        self.group.update(delta_time)

    def add_entity(self, entity):
        """Add an entity to the layer."""
        super().add_entity(entity)
        self.group.add(entity)

        # If this entity supports collision detection, add its collision core to our collision map
        if 'physics' in entity.components:
            self.collision_map.append(entity.components['physics'].collision_core)

    def remove_entity(self, entity):
        """Remove an entity from the layer."""
        super().remove_entity(entity)
        self.group.remove(entity)

        # If this entity supports collision detection, remove its collision core from our collision map
        if 'physics' in entity.components:
            self.collision_map.remove(entity.components['physics'].collision_core)

    def draw(self, surface):
        """Draw the layer onto a surface."""
        # Center the map/screen if needed
        if self.center:
            self.group.center(self.center.rect.center)

        # Draw the map and all sprites
        self.group.draw(surface)

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

        logger.debug('Added layer "%s" to display [z-index=%s]', layer, layer.z_index)

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

        logger.debug('Removed layer "%s" to display [z-index=%s]', layer, layer.z_index)

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
                layer.draw(self.screen)

        pygame.display.flip()
        self.events.dispatch(FrameRenderCompletedEvent())

    def on_video_resize(self, event):
        """Handle resizing of the display."""
        old_size = self.screen.get_size()
        self.resolution = event.size
        self.screen = self.create_screen()

        for z_index in self.layers:
            for layer in self.layers[z_index]:
                if layer.size == old_size:
                    layer.resize(event.size)

    def create_screen(self):
        """Create and return a screen with a few options."""
        screen = pygame.display.set_mode(self.resolution, self.flags)
        pygame.display.set_caption(self.caption)
        logger.debug('Display created [resolution=%s, flags=%s]', self.resolution, self.flags)

        return screen

    @inject(events=EventManager, resolution=DisplayResolution, flags=DisplayFlags, caption=DisplayCaption)
    def __init__(self, events, resolution=[0, 0], flags=0, caption='akurra'):
        """Constructor."""
        logger.debug('Initializing DisplayManager')

        self.events = events
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)

        self.resolution = resolution
        self.flags = flags
        self.caption = caption
        self.screen = self.create_screen()

        self.layers = {}
        self.layer_z_indexes = []

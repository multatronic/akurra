"""Screen module."""
import logging
import pygame
import random
import math
from injector import inject
import pyscroll
from pyscroll.util import PyscrollGroup

from .locals import *  # noqa
from .events import Event, TickEvent, EventManager
from .assets import AssetManager
from .entities import LayerComponent, EntityManager, MapLayerComponent
from .utils import ContainerAware, hr_event_type, map_point_to_screen, layer_point_to_map


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


class EntityDisplayLayer(DisplayLayer):

    """
    Entity display layer.

    A layer for rendering and displaying entities.

    """

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.em = self.container.get(EntityManager)
        self.entities = {}

    def add_entity(self, entity):
        """Add an entity to the layer."""
        entity.add_component(LayerComponent(layer=self))

        self.entities[entity.id] = entity

    def remove_entity(self, entity):
        """Remove an entity from the layer."""
        entity.components.pop(LayerComponent, None)
        self.entities.pop(entity.id, None)

    def draw(self, surface):
        """Draw the layer onto a surface."""
        self.surface.fill([0, 0, 0, 0])

        for entity_id in self.entities:
            self.surface.blit(self.entities[entity_id].components['sprite'].image,
                              self.entities[entity_id].components['position'].primary_position)

        super().draw(surface)

    def find_closest_entity(self, entity_id=None, criteria=None):
        """Find the closest entity (with position component) relative to a target entity."""

        if entity_id is not None and criteria is not None:
            target_entity = self.em.find_entity_by_id(entity_id)
            if target_entity is not None and 'position' in target_entity.components:
                eligible_entities = self.em.find_entities_by_components(criteria)
                entity_position = target_entity.components['position'].position

                try:
                    # sort by distance to player to find the closest entity with dialogue component
                    if len(eligible_entities) > 1:
                        eligible_entities.sort(key=lambda entity:
                                               math.sqrt(
                                                (entity.components['position'].position[0] - entity_position[0]) ** 2
                                                +
                                                (entity.components['position'].position[1] - entity_position[1]) ** 2
                                                ))
                    return eligible_entities[0]
                except KeyError:
                    return None
        return None

    def find_entities_at(self, position, ignore_ids=[], position_type='primary', radius=None, limit=None):
        """
        Find and return a list of entities in a given radius around the given position.

        :param position: Coordinate where entity lookup should start.
        :param radius: Radius of the search.
        :param ignore_ids: List of entity IDs to ignore when searching.
        :param limit: Maximum amount of results to return.
        :param position_type: Position type to perform comparisons with.

        """
        for entity_id in self.entities:
            if entity_id in ignore_ids:
                continue

            entity = self.entities[entity_id]
            target = getattr(entity.components['position'], position_type + '_position')

            target_rect = entity.components['sprite'].rect.copy()
            # target_rect = entity.components['physics'].collision_core.copy()
            target_rect.center = target

            if ((not radius) and (target_rect.collidepoint(position))) or \
                    ((radius) and distance_between(position, target) <= radius):
                yield entity

                if limit:
                    limit -= 1

                    if not limit:
                        break

    def on_entity_mouse(self, entity, event):
        """
        Handle a mouse event as the cursor is focused on a certain entity.

        :param entity: Entity that is currently focused by the cursor.
        :param event: Mouse event to handle.

        """
        logger.warning('Dected event "%s" on "%s".', hr_event_type(event.type), entity.components['character'].name)


class ScrollingMapEntityDisplayLayer(EntityDisplayLayer):

    """
    Scrollable map display layer.

    A display layer for rendering entities on a scrollable map.

    """

    def __init__(self, tmx_data, default_layer=0, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.em = self.container.get(EntityManager)
        self.events = self.container.get(EventManager)
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
        assets = self.container.get(AssetManager)
        for o in self.map_data.tmx.objects:
            if o.properties.get('spawn', False):
                templates = o.properties['spawn_templates'].split(';')
                dialogue_tree = o.properties.get('dialogue_tree', None)
                for i in range(0, o.properties.get('spawn_count', 1)):
                    template = random.choice(templates)
                    entity = self.em.create_entity_from_template(template)

                    if 'dialogue' in entity.components:
                        entity.components['dialogue'].tree = assets.get_dialogue_tree(dialogue_tree)

                    if 'position' in entity.components:
                        target = pygame.Rect(o.x, o.y, o.width, o.height).center

                        entity.components['position'].layer_position = target
                        # entity.components['position'].map_position = layer_point_to_map(self.map_layer, target)
                        # entity.components['position'].screen_position = \
                        #     map_point_to_screen(self.map_layer, entity.components['position'].map_position)

                    self.add_entity(entity)

    def update(self, delta_time):
        """Compute an update to the layer's state."""
        super().update(delta_time)
        self.group.update(delta_time)

    def add_entity(self, entity):
        """Add an entity to the layer."""
        super().add_entity(entity)
        entity.add_component(MapLayerComponent())
        self.group.add(entity)

        # If this entity supports collision detection, add its collision core to our collision map
        if 'physics' in entity.components:
            self.collision_map.append(entity.components['physics'].collision_core)

    def remove_entity(self, entity):
        """Remove an entity from the layer."""
        super().remove_entity(entity)
        entity.remove_component(MapLayerComponent)
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

    def add_layer(self, layer):
        """Add a layer to the display."""
        if layer.z_index not in self.layers:
            self.layers[layer.z_index] = {}
            self.layer_z_indexes = sorted(self.layers.keys(), key=int)

        self.layers[layer.z_index][layer] = 1

        # Set display within layer
        layer.display = self

        logger.debug('Added layer "%s" to display [z_index=%s]', id(layer), layer.z_index)

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

        logger.debug('Removed layer "%s" from display [z_index=%s]', id(layer), layer.z_index)

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

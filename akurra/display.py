"""Screen module."""
import logging
import pygame
import random
import functools
import pyscroll
from pyscroll.util import PyscrollGroup

from .locals import *  # noqa
from .keyboard import KeyboardModule
from .events import Event, TickEvent, EventManager
from .entities import LayerComponent, EntityManager, MapLayerComponent
from .modules import Module
from .utils import ContainerAware, hr_event_type, distance_between


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
        self.entities = {}

    def add_entity(self, entity):
        """Add an entity to the layer."""
        entity.add_component(LayerComponent(layer=self))
        self.entities[entity.id] = entity

    def remove_entity(self, entity):
        """Remove an entity from the layer."""
        entity.remove_component(LayerComponent)
        self.entities.pop(entity.id, None)

    def draw(self, surface):
        """Draw the layer onto a surface."""
        self.surface.fill([0, 0, 0, 0])

        for entity_id in self.entities:
            self.surface.blit(self.entities[entity_id].components['sprite'].image,
                              self.entities[entity_id].components['position'].primary_position)

        super().draw(surface)

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
        logger.warning('Detected event "%s" on "%s".', hr_event_type(event.type), entity.components['character'].name)


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
        self.build_mana_map()
        self.spawn_entities()

        self.center = None

    def build_collision_map(self):
        """Build a collision map based on map data."""
        logger.debug('Building collision map [map=%s]', self.map_data.tmx.filename)
        self.collision_map = []

        for o in self.map_data.tmx.objects:
            if o.properties.get('collision', 'false') == 'true':
                self.collision_map.append(pygame.Rect(o.x, o.y, o.width, o.height))

    def build_mana_map(self):
        """Build a mana map based on map data."""
        logger.debug('Building mana map [map=%s]', self.map_data.tmx.filename)
        self.mana_map = {}
        self.mana_replenishment_map = {}

        # Loop through all vibible layers
        for i, l in enumerate(self.map_data.tmx.visible_layers):
            # Only continue for terrain layers
            if l.properties.get('terrain', 'false') == 'true':
                # Iterate over all tiles
                for x in range(0, l.width):
                    for y in range(0, l.height):
                        tile = self.map_data.tmx.get_tile_properties(x, y, i)

                        # Only continue if the current tile has mana types
                        if tile and tile.get('mana_types'):
                            # Initialize dicts if needed
                            if not self.mana_map.get(i):
                                self.mana_map[i] = {}

                            if not self.mana_map[i].get(x):
                                self.mana_map[i][x] = {}

                            if not self.mana_map[i][x].get(y):
                                self.mana_map[i][x][y] = {}

                            # Parse mana type data
                            mana_types = tile['mana_types'].split(';')
                            mana_types = [x.split(':') for x in mana_types]

                            # Index mana types by type, and use defaults
                            for mana in mana_types:
                                # .. = [<current_stores>, <max_stores>]
                                self.mana_map[i][x][y][mana[0]] = [
                                    float(mana[1]) if len(mana) > 1 else 1,
                                    float(mana[2]) if len(mana) > 2 else (float(mana[1] if len(mana) > 1 else 1))
                                ]

    def spawn_entities(self):
        """Spawn entities on the map based on map data."""
        logger.debug('Spawning entities [map=%s]', self.map_data.tmx.filename)

        for o in self.map_data.tmx.objects:
            if o.properties.get('spawn', 'false') == 'true':
                templates = o.properties['spawn_templates'].split(';')

                for i in range(0, o.properties.get('spawn_count', 1)):
                    template = random.choice(templates)
                    entity = self.em.create_entity_from_template(template)

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


class DisplayModule(Module):

    """Display module."""

    dependencies = [
        'keyboard'
    ]

    def __init__(self):
        """Constructor."""
        self.configuration = self.container.get(Configuration)
        self.events = self.container.get(EventManager)
        self.keyboard = self.container.get(KeyboardModule)

        self.resolution = self.configuration.get('akurra.display.resolution', [0, 0])
        self.caption = self.configuration.get('akurra.display.caption', 'Akurra DEV')

        self.flags = self.configuration.get('akurra.display.flags', ['DOUBLEBUF', 'HWSURFACE', 'RESIZABLE'])
        self.flags = functools.reduce(lambda x, y: x | y, [getattr(pygame, x) for x in self.flags])

        self.screen = self.create_screen()

        self.layers = {}
        self.layer_z_indexes = []

    def start(self):
        """Start the module."""
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)

        self.keyboard.add_action_listener('fullscreen_toggle', self.toggle_fullscreen)

    def stop(self):
        """Stop the module."""
        self.keyboard.remove_action_listener(self.toggle_fullscreen)

        self.events.unregister(self.on_video_resize)
        self.events.unregister(self.on_tick)

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

    def toggle_fullscreen(self, event):
        """Toggle fullscreen mode."""
        if event.original_event['type'] is not pygame.KEYDOWN:
            return

        if self.flags & pygame.FULLSCREEN:
            self.flags ^= pygame.FULLSCREEN
        else:
            self.flags |= pygame.FULLSCREEN

"""Entities module."""
import logging
import pygame
from uuid import uuid4
from enum import Enum

from .locals import *  # noqa
from .assets import SpriteAnimation
from .events import Event, TickEvent, EventManager
from .audio import AudioModule
from .modules import ModuleLoader
from .utils import ContainerAware, map_point_to_screen, screen_point_to_layer, snake_case, memoize
from .assets import AssetManager

logger = logging.getLogger(__name__)


class EntityRect(pygame.Rect):

    """Pygame rect subclass which can contain a reference to an entity."""


class EntityDirection(Enum):

    """EntityDirection enum."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    NORTH_EAST = NORTH | EAST
    SOUTH_EAST = SOUTH | EAST
    NORTH_WEST = NORTH | WEST
    SOUTH_WEST = SOUTH | WEST


class EntityState(Enum):

    """Entity state enum."""

    DEAD = 0
    STATIONARY = 1

    CAN_MOVE = 2
    CAN_USE_SKILLS = 4
    CAN_CHANGE_INPUT = 8
    CAN_REPLENISH_HEALTH = 16
    CAN_BE_DAMAGED = 32

    NORMAL = CAN_MOVE | CAN_USE_SKILLS | CAN_CHANGE_INPUT | CAN_REPLENISH_HEALTH | CAN_BE_DAMAGED


class EntityInput(Enum):

    """Entity input enum."""

    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3

    MANA_GATHER = 4
    SKILL_USAGE = 5

    TARGET_ENTITY = 6
    TARGET_POINT = 7

    SELECTED_SKILL = 8


class SystemStatus(Enum):

    """System status enum."""

    STOPPED = 0
    STARTED = 1


class EntityEvent(Event):

    """Base entity event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__()

        self.entity_id = entity_id


class EntityMoveEvent(EntityEvent):

    """Entity movement event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


class EntityCollisionEvent(EntityEvent):

    """Entity collision event."""

    def __init__(self, entity_id, collided_rect, collided_entity_id=None):
        """Constructor."""
        super().__init__(entity_id)

        self.collided_rect = collided_rect
        self.collided_entity_id = collided_entity_id


class EntityHealthChangeEvent(EntityEvent):

    """Entity health change event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


class EntityDeathEvent(EntityEvent):

    """Entity death event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


class EntityInputChangeEvent(EntityEvent):

    """Entity input change event."""

    def __init__(self, entity_id, input, input_state):
        """Constructor."""
        super().__init__(entity_id)

        self.input = input
        self.input_state = input_state


class EntityStateChangeEvent(EntityEvent):

    """Entity state change event."""

    def __init__(self, entity_id, entity_state):
        """Constructor."""
        super().__init__(entity_id)

        self.entity_state = entity_state


class Entity(pygame.sprite.Sprite):

    """
    Base entity.

    In order to be able to show stuff on the screen, we need to subclass pygame.sprite.Sprite.
    Because of this, Entity needs to have an "image" and a "rect". Not very ECS-y, but still.

    """

    def __init__(self, id=None, components={}):
        """Constructor."""
        super().__init__()

        self.id = id if id else uuid4()
        self.components = {}

        from . import container
        self.entities = container.get(EntityManager)

        for key in components:
            self.add_component(components[key])

    def add_component(self, component):
        """Add a component to the entity."""
        self.components[component.type] = component
        component.entity = self

        # Register entity component in entitymanager
        self.entities.add_entity_component(self, component)

    def remove_component(self, component):
        """Remove a component from the entity."""
        self.components.pop(component.type, None)
        component.entity = None

        # Unregister entity component in entitymanager
        self.entities.remove_entity_component(self, component)


class EntityManager(ContainerAware):

    """Entity manager."""

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing EntityManager')

        self.configuration = self.container.get(Configuration)

        self.components_group = self.configuration.get('akurra.entities.components.entry_point_group',
                                                       'akurra.entities.components')
        self.systems_group = self.configuration.get('akurra.entities.systems.entry_point_group',
                                                    'akurra.entities.systems')
        self.entity_templates = self.configuration.get('akurra.entities.templates', {})

        self.entities = {}
        self.entities_components = {}

        self.components = {}
        self.systems = {}

        self.component_loader = ModuleLoader(group=self.components_group, instantiate=False)
        self.system_loader = ModuleLoader(group=self.systems_group)

        self.load_components()

    def start(self):
        """Start."""
        self.system_loader.load()
        self.system_loader.start()

    def stop(self):
        """Stop."""
        self.system_loader.stop()
        self.system_loader.unload()

    def load_components(self):
        """Load components."""
        logger.debug('Loading all entity components')

        self.component_loader.load()
        self.components = self.component_loader.modules.copy()

        for name in self.component_loader.modules:
            if name not in self.entities_components:
                self.entities_components[name] = {}

    def clear_cache(self):
        """Clear various caches."""
        self.__class__.find_entities_by_components.cache.clear()
        self.__class__.find_entity_by_id_and_components.cache.clear()

    def add_entity(self, entity):
        """Add an entity to the manager."""
        self.entities[entity.id] = entity
        [self.add_entity_component(entity, entity.components[x]) for x in entity.components]

    def remove_entity(self, entity):
        """Remove an entity from the manager."""
        [self.remove_entity_component(entity, entity.components[x]) for x in entity.components]
        self.entities.pop(entity.id, None)

    def add_entity_component(self, entity, component):
        """Add a component to an entity, adding it to the manager."""
        self.entities_components[component.type][entity.id] = entity
        self.clear_cache()

    def remove_entity_component(self, entity, component):
        """Remove a component from an entity, removing it from the manager."""
        self.entities_components[component.type].pop(entity.id, None)
        self.clear_cache()

    def find_entity_by_id(self, entity_id):
        """Find an entity by its ID."""
        return self.entities.get(entity_id, None)

    @memoize
    def find_entities_by_components(self, components):
        """Find entities which are made up of specific components."""
        keys = [list(self.entities_components[x].keys()) for x in components]
        intersection = set(keys[0]).intersection(*keys)

        return [self.entities[x] for x in intersection]

    @memoize
    def find_entity_by_id_and_components(self, entity_id, components):
        """Find an entity by its ID if it is made up of specific components."""
        entity = self.find_entity_by_id(entity_id)

        if (not components) or (not entity):
            return None

        return entity if False not in [x in entity.components for x in components] else None

    def create_entity_from_template(self, template_name):
        """Create an entity from a template."""
        template = self.entity_templates[template_name].copy()

        # If the template has a parent, merge this data into a copy of the parent
        # Before we do this, unset the parent of the current template
        # This also means that if our parent has its own parent, we will
        # continue to merge our ancestors in until we run out
        while template.get('parent', None):
            # Copy the template's parent and remove the template's parent reference
            parent = self.entity_templates[template['parent']].copy()
            template.pop('parent', None)

            # Update the parent's components with the child template's components
            parent['components'].update(template['components'])
            template = parent

        entity = Entity()

        for component_name, component_args in template['components'].items():
            component_args = component_args if component_args else {}
            entity.components[component_name] = self.components[component_name](entity=entity, **component_args)

        self.add_entity(entity)

        return entity


class Component(ContainerAware):

    """Base component."""

    @property
    def type(self):
        """Return type."""
        # Replace this property on a class level with the correct, generated type code
        self.__class__.type = snake_case(self.__class__.__name__.replace('Component', ''))

        return self.__class__.type

    def __init__(self, entity=None):
        """Constructor."""
        if entity:
            self.entity = entity


class HealthComponent(Component):

    """Health component."""

    def __init__(self, min=0, max=100, health=1, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.min = min
        self.max = max
        self.health = health


class ManaComponent(Component):

    """Mana component."""

    def __init__(self, mana={}, max=100, **kwargs):
        """
        Constructor.

        :param mana: Dictionary representing current mana stores, indexed by type.
                     The value for a type should never exceed the value for the same
                     type in `max` if max is a dict, or simply `max` if max is an
                     integer.
        :param max: Maximum mana that can be gathered, either passed as a Dictionary
                    with values indexed by mana type, or as an integer value.
        """
        super().__init__(**kwargs)

        self.mana = mana
        self.max = max


class PositionComponent(Component):

    """Position component."""

    @property
    def primary_position(self):
        """Return primary position."""
        return getattr(self, self.primary + '_position')

    @primary_position.setter
    def primary_position(self, value):
        """Set primary position."""
        setattr(self, self.primary + '_position', value)

    @property
    def screen_position(self):
        """Return screen position."""
        return self._screen_position

    @screen_position.setter
    def screen_position(self, value):
        """Set screen position."""
        self._screen_position = list(value)

    @property
    def layer_position(self):
        """Return layer position."""
        return self._layer_position

    @layer_position.setter
    def layer_position(self, value):
        """Set layer position."""
        self._layer_position = list(value)

    @property
    def map_position(self):
        """Return map position."""
        return self._map_position

    @map_position.setter
    def map_position(self, value):
        """Set map position."""
        self._map_position = list(value)

    def __init__(self, screen_position=[0, 0], layer_position=[0, 0], map_position=[0, 0], primary='layer', **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.screen_position = screen_position
        self.layer_position = layer_position
        self.map_position = map_position

        self.primary = primary
        self.old = None


class VelocityComponent(Component):

    """Velocity component."""

    def __init__(self, direction=[0, 0], speed=200, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.direction = direction
        self.speed = speed


class CharacterComponent(Component):

    """Character component."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.name = name


class SpriteComponent(Component):

    """Sprite component."""

    @property
    def entity(self):
        """Return entity."""
        return self._entity

    @entity.setter
    def entity(self, value):
        """Set entity."""
        self._entity = value

        # pygame.sprite.Sprite-specific stuff
        self._entity.rect = self.rect
        self._entity.image = self.image

    def __init__(self, image=None, sprite_size=[0, 0], animations={}, direction=EntityDirection.SOUTH,
                 state='stationary', **kwargs):
        """Constructor."""
        self.direction = direction
        self.state = state
        self.sprite_size = sprite_size

        if image:
            self.image = self.container.get(AssetManager).get_image(image, alpha=True)
        else:
            self.image = pygame.Surface(self.sprite_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)

        self.default_image = self.image.copy()
        self.animations = {}

        for state in animations:
            animations[state] = animations[state] if type(animations[state]) is list else [animations[state]]
            self.animations[state] = []

            for value in animations[state]:
                value['frame_size'] = value.get('frame_size', self.sprite_size)
                value['render_offset'] = value.get('render_offset', [(self.sprite_size[y] - value['frame_size'][y]) / 2
                                                   for y in [0, 1]])
                value['direction'] = value.get('direction', self.direction.name)

                animation = SpriteAnimation(**value)
                self.animations[state].append(animation)

        self.rect = self.image.get_rect()

        super().__init__(**kwargs)


class InputComponent(Component):

    """Input component."""

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.input = {
            EntityInput.MOVE_UP: False,
            EntityInput.MOVE_DOWN: False,
            EntityInput.MOVE_LEFT: False,
            EntityInput.MOVE_RIGHT: False,
            EntityInput.MANA_GATHER: False,
            EntityInput.SKILL_USAGE: False,
            EntityInput.SELECTED_SKILL: None,
            EntityInput.TARGET_POINT: None,
            EntityInput.TARGET_ENTITY: None,
        }


class PhysicsComponent(Component):

    """Physics component."""

    @property
    def entity(self):
        """Return entity."""
        return self._entity

    @entity.setter
    def entity(self, value):
        """Set entity."""
        self._entity = value

        # Set reference to entity in collision rectangle, in order to be able to find
        # collided entities again
        self.collision_core.entity = self._entity

    def __init__(self, core_size=[0, 0], core_offset=[0, 0], **kwargs):
        """Constructor."""
        self.collision_core = EntityRect([0, 0], core_size)
        self.collision_core_offset = core_offset

        super().__init__(**kwargs)


class PlayerComponent(Component):

    """Player component."""


class LayerComponent(Component):

    """Map layer component."""

    def __init__(self, layer=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.layer = layer


class MapLayerComponent(Component):

    """Map layer component."""

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)


class StateComponent(Component):

    """State component."""

    def __init__(self, state=EntityState.NORMAL, **kwargs):
        """Constructor."""
        self.state = state


class System(ContainerAware):

    """Base system."""

    requirements = []
    event_handlers = {}

    def __init__(self):
        """Constructor."""
        self.events = self.container.get(EventManager)
        self.entities = self.container.get(EntityManager)

        # Order requirements, this makes result caching more efficient
        self.requirements.sort()

    def start(self):
        """Start the system."""
        for event, handler in self.event_handlers.items():
            self.events.register(event, getattr(self, handler[0]), handler[1])

    def stop(self):
        """Stop the system."""
        for handler in self.event_handlers.values():
            self.events.unregister(getattr(self, handler[0]))

    def on_event(self, event):
        """Handle an event."""
        for entity in self.entities.find_entities_by_components(self.requirements):
            self.update(entity, event)

    def on_entity_event(self, event):
        """Handle an event which contains a reference to an entity."""
        entity = self.entities.find_entity_by_id_and_components(event.entity_id, self.requirements)

        if entity:
            self.update(entity, event)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        raise NotImplementedError()


class SpriteRectPositionCorrectionSystem(System):

    """Sprite rect position correction system."""

    requirements = [
        'sprite',
        'position'
    ]

    event_handlers = {
        TickEvent:  ['on_event', 13]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if not entity.components['position'].old:
            entity.components['position'].old = list(entity.components['position'].primary_position)
            self.events.dispatch(EntityMoveEvent(entity.id))

        # pygame.sprite.Sprite logic
        entity.components['sprite'].rect.topleft = list(entity.components['position'].primary_position)


class PlayerInputSystem(System):

    """Input system."""

    requirements = [
        'input',
        'player',
        'layer',
        'map_layer',
        'state'
    ]

    action_inputs = {
        'move_up': EntityInput.MOVE_UP,
        'move_down': EntityInput.MOVE_DOWN,
        'move_left': EntityInput.MOVE_LEFT,
        'move_right': EntityInput.MOVE_RIGHT,
        'mana_gather': EntityInput.MANA_GATHER,
        'skill_usage': EntityInput.SKILL_USAGE,
    }

    def __init__(self):
        """Constructor."""
        super().__init__()

        from .input import InputModule
        self.input = self.container.get(InputModule)

    def start(self):
        """Start the system."""
        [self.input.add_action_listener(x, self.on_event) for x in self.action_inputs.keys()]

    def stop(self):
        """Stop the system."""
        self.input.remove_action_listener(self.on_event)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if not entity.components['state'].state.value & EntityState.CAN_CHANGE_INPUT.value:
            return

        input = self.action_inputs[event.action]
        entity.components['input'].input[input] = event.state

        if event.source == 'mouse':
            entity.components['input'].input[EntityInput.TARGET_POINT] = \
                screen_point_to_layer(entity.components['layer'].layer.map_layer, event.original_event['pos'])

        # Trigger an input change event
        self.events.dispatch(EntityInputChangeEvent(entity.id, input, event.state))


class VelocitySystem(System):

    """Velocity system."""

    requirements = [
        'input',
        'velocity',
    ]

    input_velocities = {
        EntityInput.MOVE_UP: [0, -1],
        EntityInput.MOVE_DOWN: [0, 1],
        EntityInput.MOVE_LEFT: [-1, 0],
        EntityInput.MOVE_RIGHT: [1, 0]
    }

    event_handlers = {
        EntityInputChangeEvent: ['on_entity_event', 10]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        for x in self.input_velocities.keys():
            if entity.components['input'].input[x]:
                entity.components['velocity'].direction = self.input_velocities[x]
                return

        entity.components['velocity'].direction = [0, 0]


class MovementSystem(System):

    """Movement system."""

    requirements = [
        'position',
        'velocity',
        'sprite'
    ]

    event_handlers = {
        TickEvent: ['on_event', 11]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        entity.components['sprite'].state = 'moving' if \
            list(filter(None, entity.components['velocity'].direction)) else 'stationary'

        # Do nothing if there is no velocity
        if not entity.components['velocity'].direction[0] and not entity.components['velocity'].direction[1]:
            return

        entity.components['position'].old = list(entity.components['position'].primary_position)

        entity.components['position'].primary_position[0] += entity.components['velocity'].direction[0] * \
            entity.components['velocity'].speed * event.delta_time
        entity.components['position'].primary_position[1] += entity.components['velocity'].direction[1] * \
            entity.components['velocity'].speed * event.delta_time

        # Calculate and set direction
        direction = EntityDirection.NORTH.value if entity.components['velocity'].direction[1] < 0 \
            else EntityDirection.SOUTH.value if entity.components['velocity'].direction[1] else 0
        direction |= EntityDirection.EAST.value if entity.components['velocity'].direction[0] > 0 \
            else EntityDirection.WEST.value if entity.components['velocity'].direction[0] else 0

        entity.components['sprite'].direction = EntityDirection(direction)

        for state in entity.components['sprite'].animations:
            for animation in entity.components['sprite'].animations[state]:
                animation.direction = entity.components['sprite'].direction.name

        # Trigger a move event
        self.events.dispatch(EntityMoveEvent(entity.id))


class PositioningSystem(System):

    """Positioning system."""

    requirements = [
        'position',
        'layer',
        'map_layer',
        'physics'
    ]

    event_handlers = {
        EntityMoveEvent: ['on_entity_event', 15]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        position = entity.components['position']
        map = entity.components['layer'].layer.map_layer
        core_center = entity.components['physics'].collision_core.center

        if position.primary != 'map':
            position.map_position[0] = core_center[0] / map.data.tilewidth
            position.map_position[1] = core_center[1] / map.data.tileheight

        if position.primary != 'screen':
            position.screen_position = map_point_to_screen(map, core_center)


class RenderingSystem(System):

    """Rendering system."""

    requirements = [
        'sprite'
    ]

    event_handlers = {
        TickEvent: ['on_event', 13]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        try:
            entity.components['sprite'].image.fill([0, 0, 0, 0])

            for x in entity.components['sprite'].animations[entity.components['sprite'].state]:
                entity.components['sprite'].image.blit(x.get_frame(), x.render_offset)
        except KeyError:
            entity.components['sprite'].image.blit(entity.components['sprite'].default_image, [0, 0])


class SpriteRenderOrderingSystem(System):

    """Sprite render ordering system."""

    requirements = [
        'position',
        'sprite',
        'layer',
        'map_layer'
    ]

    event_handlers = {
        EntityMoveEvent: ['on_entity_event', 10]
    }

    def on_event(self, event):
        """Handle an event."""

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        entity.components['layer'].layer.group._spritelist = sorted(
            entity.components['layer'].layer.group._spritelist,
            key=lambda x: x.components['position'].layer_position[1])


class CollisionSystem(System):

    """Collision system."""

    requirements = [
        'position',
        'map_layer',
        'layer',
        'physics',
        'sprite'
    ]

    event_handlers = {
        EntityMoveEvent: ['on_entity_event', 12]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # We can't do much without a location history
        if not entity.components['position'].old:
            return

        entity.components['physics'].collision_core.center = entity.components['sprite'].rect.center

        entity.components['physics'].collision_core.centerx += \
            entity.components['physics'].collision_core_offset[0]
        entity.components['physics'].collision_core.centery += \
            entity.components['physics'].collision_core_offset[1]

        collision_rects = entity.components['layer'].layer.collision_map[:]
        collision_rects.remove(entity.components['physics'].collision_core)

        collisions = entity.components['physics'].collision_core.collidelist(collision_rects)

        if collisions > -1:
            entity.components['position'].primary_position = entity.components['position'].old
            entity.components['sprite'].rect.topleft = list(entity.components['position'].primary_position)
            entity.components['physics'].collision_core.center = entity.components['sprite'].rect.center

            entity.components['physics'].collision_core.centerx += \
                entity.components['physics'].collision_core_offset[0]
            entity.components['physics'].collision_core.centery += \
                entity.components['physics'].collision_core_offset[1]

            # Trigger a collision event
            collided_rect = collision_rects[collisions]
            collided_entity_id = collided_rect.entity.id if hasattr(collided_rect, 'entity') else None
            self.events.dispatch(EntityCollisionEvent(entity.id, collided_rect, collided_entity_id))


class PlayerTerrainSoundSystem(System):

    """System for triggering sound effects when the player walks over terrain."""

    requirements = [
        'player',
        'position',
        'map_layer',
        'layer'
    ]

    event_handlers = {
        EntityMoveEvent: ['on_entity_event', 13]
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.audio = self.container.get(AudioModule)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # Fetch the current tile the player is walking on, based on the current map location
        coords = [int(x) for x in entity.components['position'].map_position]

        for i, l in enumerate(entity.components['layer'].layer.map_data.tmx.visible_layers):
            if l.properties.get('terrain', 'false') == 'true':
                try:
                    tile = entity.components['layer'].layer.map_data.tmx.get_tile_properties(coords[0], coords[1], i)

                    if tile and tile.get('terrain_type'):
                        self.audio.play_sound('terrain_%s' % tile.get('terrain_type'), channel='terrain', queue=False)
                except KeyError:
                    # If no tile was found on this layer, that's too bad but we can continue regardless
                    pass


class ManaGatheringSystem(System):

    """Mana gathering system."""

    requirements = [
        'input',
        'mana',
        'position',
        'layer',
        'map_layer'
    ]

    event_handlers = {
        TickEvent: ['on_event', 10]
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.cfg = self.container.get(Configuration)

        self.default_gather_radius = self.cfg.get('akurra.entities.systems.mana_gathering.default_gather_radius', 1)
        self.default_gather_amount = self.cfg.get('akurra.entities.systems.mana_gathering.default_gather_amount', 1)
        self.minimum_gather_amount = self.cfg.get('akurra.entities.systems.mana_gathering.minimum_gather_amount', 1)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if entity.components['input'].input[EntityInput.MANA_GATHER]:
            # Fetch the current tile the player is walking on, based on the current map location
            coords = [int(x) for x in entity.components['position'].map_position]

            layer = entity.components['layer'].layer
            mana = entity.components['mana'].mana

            gather_radius = self.default_gather_radius
            gather_amount = self.default_gather_amount * event.delta_time
            gather_amount_min = self.minimum_gather_amount
            amount_max = entity.components['mana'].max

            tile_matrix = [
                list(range(coords[0] - gather_radius, coords[0] + gather_radius + 1)),
                list(range(coords[1] - gather_radius, coords[1] + gather_radius + 1))
            ]

            for i, l in enumerate(layer.map_data.tmx.visible_layers):
                # Only continue for terrain layers
                if l.properties.get('terrain', 'false') == 'true':
                    for x in tile_matrix[0]:
                        for y in tile_matrix[1]:
                            try:
                                # Attempt to lower amount of mana for tile in tile map  by mana_gather_amount,
                                # and add it to the entity's reserves
                                for type, mana_data in layer.mana_map[i][x][y].items():
                                    # If we have at least the required amount of mana
                                    if mana_data[0] >= gather_amount_min:
                                        # Remove the mana from the terrain
                                        mana_data[0] -= gather_amount

                                        # If removing would result in negatives, only give the entity as much as we can
                                        if mana_data[0] < 0:
                                            mana[type] = mana.get(type, 0) + (gather_amount + mana_data[0])
                                            mana_data[0] = 0
                                        # If we have an excess of nothing left, just give the entire amount
                                        else:
                                            mana[type] = mana.get(type, 0) + gather_amount

                                        # If we were to exceed the maximum amount of this type we can carry, subtract
                                        # the difference
                                        if mana[type] > amount_max:
                                            mana_data[0] += amount_max - mana[type]
                                            mana[type] = amount_max

                                        # Add this tile to the mana replenishment map just in case
                                        layer.mana_replenishment_map['%s-%s-%s-%s' % (i, x, y, type)] = [i, x, y, type]
                            except KeyError:
                                pass
                            except ValueError:
                                pass


class ManaReplenishmentSystem(System):

    """Mana replenishment system."""

    requirements = [
        'layer',
        'map_layer',
        'player'
    ]

    event_handlers = {
        TickEvent: ['on_event', 10]
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.cfg = self.container.get(Configuration)
        self.default_replenishment_amount = \
            self.cfg.get('akurra.entities.systems.mana_replenishment.default_replenishment_amount', 1)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        layer = entity.components['layer'].layer
        replenishment_amount = self.default_replenishment_amount * event.delta_time

        # Loop over all tiles which require replenishment, and replenish them
        for key, tile_mana in layer.mana_replenishment_map.copy().items():
            mana_data = layer.mana_map[tile_mana[0]][tile_mana[1]][tile_mana[2]][tile_mana[3]]
            mana_data[0] += replenishment_amount

            # If adding would result in exceeding the max amount, only give the tile as much as we can
            if mana_data[0] >= mana_data[1]:
                mana_data[0] = mana_data[1]

                # Remove this tile from the replenishment map since we've replenished it
                layer.mana_replenishment_map.pop(key, None)


class HealthRegenerationSystem(System):

    """Health replenishment system."""

    requirements = [
        'layer',
        'map_layer',
        'health',
        'state'
    ]

    event_handlers = {
        TickEvent: ['on_event', 10]
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.cfg = self.container.get(Configuration)
        self.default_regeneration_amount = \
            self.cfg.get('akurra.entities.systems.health_regeneration.default_regeneration_amount', 1)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if not entity.components['state'].state.value & EntityState.CAN_REPLENISH_HEALTH.value:
            return

        health_component = entity.components['health']

        # Skip this entity if we're at full health
        if health_component.health == health_component.max:
            return

        regeneration_amount = self.default_regeneration_amount * event.delta_time
        health_component.health += regeneration_amount

        # If adding would result in exceeding the max amount, only give the entity as much as we can
        if health_component.health >= health_component.max:
            health_component.health = health_component.max


class DeathSystem(System):

    """Death system."""

    requirements = [
        'state',
        'sprite',
    ]

    event_handlers = {
        EntityStateChangeEvent: ['on_entity_event', 10],
    }

    def update(self, entity, event=None):
        """Have an entity handled by the system."""
        if entity.components['state'].state is EntityState.DEAD:
            entity.components['sprite'].state = 'death'
            self.events.dispatch(EntityDeathEvent(entity.id))

            # If this entity has an input component, set all inputs to false
            try:
                for key in entity.components['input'].input:
                    entity.components['input'].input[key] = False
            except KeyError:
                pass

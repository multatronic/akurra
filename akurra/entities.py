"""Entities module."""
import logging
import pygame
from uuid import uuid4
from enum import Enum
from pkg_resources import iter_entry_points
from injector import inject

from .locals import *  # noqa
from .assets import SpriteAnimation
from .events import TickEvent, EntityMoveEvent, EventManager
from .keyboard import KeyboardManager
from .audio import AudioManager
from .utils import ContainerAware


logger = logging.getLogger(__name__)


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

    STATIONARY = 0
    MOVING = 1


class EntityInput(Enum):

    """Entity input enum."""

    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3


# class EquipmentSlot(Enum):

#     """Equipment slot enum."""

#     HEAD = 0
#     SHOULDERS = 1
#     CHEST = 2
#     WAIST = 3
#     LEGS = 4
#     FEET = 5
#     ARMS = 6
#     LEFT_HAND = 7
#     RIGHT_HAND = 8
#     NECK = 9
#     CLOAK = 10
#     FINGER_1 = 11
#     FINGER_2 = 12
#     FINGER_3 = 13
#     FINGER_4 = 14
#     FINGER_5 = 15
#     FINGER_6 = 16
#     FINGER_7 = 17
#     FINGER_8 = 18
#     FINGER_9 = 19
#     FINGER_10 = 20


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

        # @DO Have the EntityManager inject the container to avoid overhead?
        # @DO Maybe use a ContainerComponent with a static container inside?
        from . import container
        self.entities = container.get(EntityManager)

        for key in components:
            self.add_component(components[key])

    def add_component(self, component):
        """Add a component to the entity."""
        self.components[component.type] = component
        component.entity = self

        # Add entity to component dict in entitymanager
        self.entities.entities_components[component.type][self.id] = self

    def remove_component(self, component):
        """Remove a component from the entity."""
        self.components.pop(component.type, None)
        component.entity = None

        # Remove entity from component dict in entitymanager
        self.entities_components[component.type].pop(self.id, None)


class EntityManager:

    """Entity manager."""

    @inject(components_entry_point_group=EntityComponentEntryPointGroup,
            systems_entry_point_group=EntitySystemEntryPointGroup,
            entity_templates=EntityTemplates)
    def __init__(self, components_entry_point_group='akurra.entities.components',
                 systems_entry_point_group='akurra.entities.systems',
                 entity_templates={}):
        """Constructor."""
        logger.debug('Initializing EntityManager [components_group=%s, systems_group=%s]',
                     components_entry_point_group, systems_entry_point_group)
        self.components_entry_point_group = components_entry_point_group
        self.systems_entry_point_group = systems_entry_point_group

        self.entities = {}
        self.entities_components = {}
        self.entity_templates = entity_templates

        self.components = {}
        self.systems = {}

    def start(self):
        """Start."""
        self.load_components()
        self.load_systems()
        self.start_systems()

    def stop(self):
        """Stop."""
        self.stop_systems()
        self.unload_systems()

    def load_components(self):
        """Load components."""
        logger.debug('Loading all entity components')
        [self.load_component(x.name) for x in iter_entry_points(group=self.components_entry_point_group)]

    def load_component(self, name):
        """Load a component by name."""
        logger.debug('Loading entity component "%s"', name)

        for entry_point in iter_entry_points(group=self.components_entry_point_group, name=name):
            self.components[name] = entry_point.load()

            if name not in self.entities_components:
                self.entities_components[name] = {}

        logger.debug('Entity component "%s" loaded', name)

    def load_systems(self):
        """Load systems."""
        logger.debug('Loading all entity systems')
        [self.load_system(x.name) for x in iter_entry_points(group=self.systems_entry_point_group)]

    def load_system(self, name):
        """Load a system by name."""
        logger.debug('Loading entity system "%s"', name)

        for entry_point in iter_entry_points(group=self.systems_entry_point_group, name=name):
            self.systems[name] = entry_point.load()()

        logger.debug('Entity system "%s" loaded', name)

    def start_systems(self):
        """Start systems."""
        logger.debug('Starting all entity systems')
        [self.start_system(x) for x in self.systems]

    def start_system(self, name):
        """Start a system by name."""
        logger.debug('Starting entity system "%s"', name)
        self.systems[name].start()
        logger.debug('Entity system "%s" started', name)

    def stop_systems(self):
        """Stop systems."""
        logger.debug('Stopping all entity systems')
        [self.stop_system(x) for x in self.systems]

    def stop_system(self, name):
        """Stop a system by name."""
        logger.debug('Stopping entity system "%s"', name)
        self.systems[name].stop()
        logger.debug('Entity system "%s" stopped', name)

    def unload_system(self, name):
        """
        Unload a system by name..

        :param name: A string identifier for a system.

        """
        logger.debug('Unloading entity system "%s"', name)

        del self.systems[name]
        self.systems.pop("", None)
        self.systems.pop(None, None)

        logger.debug('Unloaded entity system "%s"', name)

    def unload_systems(self):
        """Unload all systems."""
        logger.debug('Unloading all entity systems')

        # We need to copy the list of names, because unloading a system
        # removes it from the systems dict
        [self.unload_system(x) for x in list(self.systems.keys())]

    def add_entity(self, entity):
        """Add an entity to the manager."""
        self.entities[entity.id] = entity

        for key in entity.components:
            self.entities_components[key][entity.id] = entity

    def remove_entity(self, entity):
        """Remove an entity from the manager."""
        self.entities.pop(entity.id, None)
        [self.entities_components[x].pop(entity.id, None) for x in self.entities_components]

    def find_entity_by_id(self, entity_id):
        """Find an entity by its ID."""
        return self.entities.get(entity_id, None)

    def find_entities_by_components(self, components):
        """Find entities which are made up of specific components."""
        keys = [list(self.entities_components[x].keys()) for x in components]
        intersection = set(keys[0]).intersection(*keys)

        return [self.entities[x] for x in intersection]

    def create_entity_from_template(self, template_name):
        """Create an entity from a template."""
        template = self.entity_templates[template_name]
        entity = Entity()

        for component in template['components']:
            component_name = component[0] if type(component) is list else component
            component_args = component[1] if type(component) is list else {}

            entity.components[component_name] = self.components[component_name](entity=entity, **component_args)

        self.add_entity(entity)

        return entity


class Component:

    """Base component."""

    def __init__(self, entity=None):
        """Constructor."""
        self.entity = entity


class HealthComponent(Component):

    """Health component."""

    type = 'health'

    def __init__(self, min=0, max=100, hp=1, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.min = min
        self.max = max
        self.hp = hp


class PositionComponent(Component):

    """Position component."""

    type = 'position'

    @property
    def position(self):
        """Set position."""
        return self._position

    @position.setter
    def position(self, value):
        """Return position."""
        self._position = list(value)

    def __init__(self, position=[0, 0], **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.position = position
        self.old = None


class VelocityComponent(Component):

    """Velocity component."""

    type = 'velocity'

    def __init__(self, velocity=[0, 0], max=300, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.velocity = velocity
        self.max = 300


class CharacterComponent(Component):

    """Character component."""

    type = 'character'

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.name = name


class SpriteComponent(Component):

    """Sprite component."""

    type = 'sprite'

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
                 state=EntityState.STATIONARY, **kwargs):
        """Constructor."""
        self.direction = direction
        self.state = state

        self.image = image if image else pygame.Surface(sprite_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)
        self.default_image = self.image.copy()
        self.animations = {}

        for state in animations:
            self.animations[state] = SpriteAnimation(**animations[state])
            self.animations[state].direction = self.direction.name

        self.rect = self.image.get_rect()

        super().__init__(**kwargs)


class InputComponent(Component):

    """Input component."""

    type = 'input'

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.input = {
            EntityInput.MOVE_UP: False,
            EntityInput.MOVE_DOWN: False,
            EntityInput.MOVE_LEFT: False,
            EntityInput.MOVE_RIGHT: False
        }


class PhysicsComponent(Component):

    """Physics component."""

    type = 'physics'

    def __init__(self, core_size=[0, 0], core_offset=[0, 0], **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.collision_core = pygame.Rect([0, 0], core_size)
        self.collision_core_offset = core_offset


class PlayerComponent(Component):

    """Player component."""

    type = 'player'


class MapLayerComponent(Component):

    """Map layer component."""

    type = 'map_layer'

    def __init__(self, layer=None, location=[0, 0], **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.layer = layer
        self.location = location


class System(ContainerAware):

    """Base system."""

    requirements = []
    event_handlers = {}

    def __init__(self):
        """Constructor."""
        self.events = self.container.get(EventManager)
        self.entities = self.container.get(EntityManager)

    def start(self):
        """Start the system."""
        for event, handler in self.event_handlers.items():
            self.events.register(event, getattr(self, handler))

    def stop(self):
        """Stop the system."""
        for handler in self.event_handlers.values():
            self.events.unregister(getattr(self, handler))

    def on_event(self, event):
        """Handle an event."""
        for entity in self.entities.find_entities_by_components(self.requirements):
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
        TickEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # pygame.sprite.Sprite logic
        entity.components['sprite'].rect.topleft = list(entity.components['position'].position)


class PlayerInputSystem(System):

    """Input system."""

    requirements = [
        'input',
        'player'
    ]

    key_inputs = {
        pygame.K_UP: EntityInput.MOVE_UP,
        pygame.K_DOWN: EntityInput.MOVE_DOWN,
        pygame.K_LEFT: EntityInput.MOVE_LEFT,
        pygame.K_RIGHT: EntityInput.MOVE_RIGHT
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.keyboard = self.container.get(KeyboardManager)

    def start(self):
        """Start the system."""
        for key in pygame.KEYDOWN, pygame.KEYUP:
            [self.keyboard.register(x, self.on_event, event_type=key) for x in self.key_inputs.keys()]

    def stop(self):
        """Stop the system."""
        self.keyboard.unregister(self.on_event)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if event.key in self.key_inputs:
            entity.components['input'].input[self.key_inputs[event.key]] = event.type == pygame.KEYDOWN


class VelocitySystem(System):

    """Velocity system."""

    requirements = [
        'input',
        'velocity'
    ]

    input_velocities = {
        EntityInput.MOVE_UP: [0, -1],
        EntityInput.MOVE_DOWN: [0, 1],
        EntityInput.MOVE_LEFT: [-1, 0],
        EntityInput.MOVE_RIGHT: [1, 0]
    }

    event_handlers = {
        TickEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        for x in self.input_velocities.keys():
            if entity.components['input'].input[x]:
                entity.components['velocity'].velocity =  \
                    [y * entity.components['velocity'].max for y in self.input_velocities[x]]

                return

        entity.components['velocity'].velocity = [0, 0]


class MovementSystem(System):

    """Movement system."""

    requirements = [
        'position',
        'velocity',
        'sprite'
    ]

    event_handlers = {
        TickEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # If we have no old position, assume we have to initialize
        if not entity.components['position'].old:
            entity.components['position'].old = list(entity.components['position'].position)
            entity.components['sprite'].rect.topleft = list(entity.components['position'].position)
            return

        entity.components['sprite'].state = EntityState.MOVING if \
            list(filter(None, entity.components['velocity'].velocity)) else EntityState.STATIONARY

        # Do nothing if there is no velocity
        if not entity.components['velocity'].velocity[0] and not entity.components['velocity'].velocity[1]:
            return

        entity.components['position'].old = list(entity.components['position'].position)

        entity.components['position'].position[0] += entity.components['velocity'].velocity[0] * event.delta_time
        entity.components['position'].position[1] += entity.components['velocity'].velocity[1] * event.delta_time

        # Calculate and set direction
        direction = EntityDirection.NORTH.value if entity.components['velocity'].velocity[1] < 0 \
            else EntityDirection.SOUTH.value if entity.components['velocity'].velocity[1] else 0
        direction |= EntityDirection.EAST.value if entity.components['velocity'].velocity[0] > 0 \
            else EntityDirection.WEST.value if entity.components['velocity'].velocity[0] else 0

        entity.components['sprite'].direction = EntityDirection(direction)

        for state in entity.components['sprite'].animations:
            entity.components['sprite'].animations[state].direction = entity.components['sprite'].direction.name

        # Trigger a move event
        self.events.dispatch(EntityMoveEvent(entity.id))


class MapLocationSystem(System):

    """Map location system."""

    requirements = [
        'map_layer',
        'physics',
        'velocity',
        'position'
    ]

    event_handlers = {
        EntityMoveEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        entity.components['map_layer'].location[0] = entity.components['physics'].collision_core.center[0] / \
            entity.components['map_layer'].layer.map_data.tilewidth
        entity.components['map_layer'].location[1] = entity.components['physics'].collision_core.center[1] / \
            entity.components['map_layer'].layer.map_data.tileheight


class RenderingSystem(System):

    """Rendering system."""

    requirements = [
        'sprite'
    ]

    event_handlers = {
        TickEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        try:
            frame = entity.components['sprite'].animations[entity.components['sprite'].state.name].get_frame()
            entity.components['sprite'].image.fill([0, 0, 0, 0])
            entity.components['sprite'].image.blit(frame, [0, 0])
        except KeyError:
            entity.components['sprite'].image.blit(entity.components['sprite'].default_image, [0, 0])


class CollisionSystem(System):

    """Collision system."""

    requirements = [
        'position',
        'map_layer',
        'physics',
        'sprite'
    ]

    event_handlers = {
        EntityMoveEvent: 'on_event'
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # We can't do much without a location history
        if not entity.components['position'].old:
            return

        entity.components['physics'].collision_core.center = entity.components['sprite'].rect.center
        entity.components['physics'].collision_core.centery += entity.components['sprite'].rect.height * \
            entity.components['physics'].collision_core_offset[1]

        if entity.components['physics'].collision_core.collidelist(
                entity.components['map_layer'].layer.collision_map) > -1:
            entity.components['position'].position = entity.components['position'].old
            entity.components['sprite'].rect.topleft = list(entity.components['position'].position)
            entity.components['physics'].collision_core.center = entity.components['sprite'].rect.center


class PlayerTerrainSoundSystem(System):

    """System for triggering sound effects when the player walks over terrain."""

    requirements = [
        'player',
        'map_layer'
    ]

    event_handlers = {
        EntityMoveEvent: 'on_event'
    }

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.audio = self.container.get(AudioManager)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # Fetch the current tile the player is walking on, based on the current map location
        coords = [int(x) for x in entity.components['map_layer'].location]

        for l in range(0, len(list(entity.components['map_layer'].layer.map_data.tmx.visible_layers))):
            try:
                tile = entity.components['map_layer'].layer.map_data.tmx.get_tile_properties(coords[0], coords[1], l)

                if tile and tile.get('terrain_type'):
                    self.audio.play_sound('terrain_%s' % tile.get('terrain_type'), channel='terrain', queue=False)
            except KeyError:
                # If no tile was found on this layer, that's too bad but we can continue regardless
                pass

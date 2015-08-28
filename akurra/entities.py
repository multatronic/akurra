"""Entities module."""
import logging
import pygame
from uuid import uuid4
from enum import Enum
from pkg_resources import iter_entry_points

from .locals import *  # noqa
from .assets import SpriteAnimation
from .events import Event, TickEvent, EventManager
from .audio import AudioModule
from .utils import ContainerAware, map_point_to_screen, screen_point_to_layer, unit_vector_between, memoize
from .assets import AssetManager

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

    MANA_GATHER = 4
    SKILL_USAGE = 5

    TARGET_ENTITY = 6
    TARGET_POINT = 7


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

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


class EntitySkillUsageEvent(EntityEvent):

    """Entity skill usage event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


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

        self.components_entry_point_group = self.configuration.get('akurra.entities.components.entry_point_group',
                                                                   'akurra.entities.components')
        self.systems_entry_point_group = self.configuration.get('akurra.entities.systems.entry_point_group',
                                                                'akurra.entities.systems')
        self.entity_templates = self.configuration.get('akurra.entities.templates', {})

        self.entities = {}
        self.entities_components = {}

        self.components = {}
        self.systems = {}
        self.systems_statuses = {}

        self.load_components()

    def start(self):
        """Start."""
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
        """
        Load a system by name.

        :param name: A string identifier for a system.

        """
        logger.debug('Loading entity system "%s"', name)

        for entry_point in iter_entry_points(group=self.systems_entry_point_group, name=name):
            self.systems[name] = entry_point.load()()
            self.systems_statuses[name] = SystemStatus.STOPPED

        logger.debug('Entity system "%s" loaded', name)

    def start_systems(self):
        """Start systems."""
        logger.debug('Starting all entity systems')
        [self.start_system(x) for x in self.systems]

    def start_system(self, name):
        """
        Start a system by name.

        :param name: A string identifier for a system.

        """
        logger.debug('Starting entity system "%s"', name)

        self.systems[name].start()
        self.systems_statuses[name] = SystemStatus.STARTED

        logger.debug('Entity system "%s" started', name)

    def stop_systems(self):
        """Stop systems."""
        logger.debug('Stopping all entity systems')
        [self.stop_system(x) for x in self.systems]

    def stop_system(self, name):
        """
        Stop a system by name.

        :param name: A string identifier for a system.

        """
        logger.debug('Stopping entity system "%s"', name)

        self.systems[name].stop()
        self.systems_statuses[name] = SystemStatus.STOPPED

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

    def toggle_system(self, name):
        """
        Toggle a system by name.

        :param name: A string identifier for a system.

        """
        if self.systems_statuses[name] is SystemStatus.STOPPED:
            self.start_system(name)
        else:
            self.stop_system(name)

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
        self.__class__.find_entities_by_components.cache.clear()

    def remove_entity_component(self, entity, component):
        """Remove a component from an entity, removing it from the manager."""
        self.entities_components[component.type].pop(entity.id, None)
        self.__class__.find_entities_by_components.cache.clear()

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
        template = self.entity_templates[template_name]

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

    def __init__(self, entity=None):
        """Constructor."""
        if entity:
            self.entity = entity


class HealthComponent(Component):

    """Health component."""

    type = 'health'

    def __init__(self, min=0, max=100, health=1, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.min = min
        self.max = max
        self.health = health


class ManaComponent(Component):

    """Mana component."""

    type = 'mana'

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

    type = 'position'

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

    type = 'velocity'

    def __init__(self, direction=[0, 0], speed=200, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.direction = direction
        self.speed = speed


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

    type = 'input'

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.input = {
            EntityInput.MOVE_UP: False,
            EntityInput.MOVE_DOWN: False,
            EntityInput.MOVE_LEFT: False,
            EntityInput.MOVE_RIGHT: False,
            EntityInput.MANA_GATHER: False
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


class LayerComponent(Component):

    """Map layer component."""

    type = 'layer'

    def __init__(self, layer=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.layer = layer


class MapLayerComponent(Component):

    """Map layer component."""

    type = 'map_layer'

    def __init__(self, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)


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
        'player'
    ]

    action_inputs = {
        'keyboard': {
            'move_up': EntityInput.MOVE_UP,
            'move_down': EntityInput.MOVE_DOWN,
            'move_left': EntityInput.MOVE_LEFT,
            'move_right': EntityInput.MOVE_RIGHT,
            'mana_gather': EntityInput.MANA_GATHER
        },
        'mouse': {
            'skill_usage': EntityInput.SKILL_USAGE
        }
    }

    def __init__(self):
        """Constructor."""
        super().__init__()

        from .mouse import MouseModule
        from .keyboard import KeyboardModule

        self.keyboard = self.container.get(KeyboardModule)
        self.mouse = self.container.get(MouseModule)

    def start(self):
        """Start the system."""
        [self.keyboard.add_action_listener(x, self.on_event) for x in self.action_inputs['keyboard'].keys()]
        [self.mouse.add_action_listener(x, self.on_event) for x in self.action_inputs['mouse'].keys()]

    def stop(self):
        """Stop the system."""
        self.mouse.remove_action_listener(self.on_event)
        self.keyboard.remove_action_listener(self.on_event)

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        if event.type == 'akurra.keyboard.KeyboardActionEvent':
            entity.components['input'].input[self.action_inputs['keyboard'][event.action]] = \
                event.original_event['type'] == pygame.KEYDOWN
        else:
            entity.components['input'].input[self.action_inputs['mouse'][event.action]] = \
                event.original_event['type'] == pygame.MOUSEBUTTONDOWN

            # If we're handling a mouse event, also update the current target of our entity
            # @TODO Find a better way to handle this?
            entity.components['input'].input[EntityInput.TARGET_POINT] = event.original_event['pos']


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
        TickEvent: ['on_event', 10]
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
        entity.components['sprite'].state = EntityState.MOVING if \
            list(filter(None, entity.components['velocity'].direction)) else EntityState.STATIONARY

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
        EntityMoveEvent: ['on_entity_event', 10]
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

            for x in entity.components['sprite'].animations[entity.components['sprite'].state.name]:
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
        EntityMoveEvent: ['on_event', 10]
    }

    def on_event(self, event):
        """Handle an event."""
        for entity in self.entities.find_entities_by_components(self.requirements):
            # Since only one map layer should be active at a time, it should be safe to only order the sprites once
            # self.update(entity, event)
            entity.components['layer'].layer.group._spritelist = sorted(
                entity.components['layer'].layer.group._spritelist,
                key=lambda x: x.components['position'].layer_position[1])
            break


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
            self.events.dispatch(EntityCollisionEvent(entity.id))


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


class SkillUsageSystem(System):

    """System for handling skill usage."""

    requirements = [
        'input',
        'position',
        'map_layer',
        'layer',
        'physics'  # @TODO This needs to go
    ]

    event_handlers = {
        TickEvent: ['on_event', 10]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # Only proceed if the entity skill usage input is active
        if entity.components['input'].input[EntityInput.SKILL_USAGE]:
            fireball = self.entities.create_entity_from_template('projectile')

            layer = entity.components['layer'].layer

            source = entity.components['physics'].collision_core.center
            target = screen_point_to_layer(layer.map_layer, entity.components['input'].input[EntityInput.TARGET_POINT])
            direction = unit_vector_between(source, target)

            fireball.components['position'].primary_position = source
            fireball.components['velocity'].direction = direction
            fireball.components['velocity'].speed = 150

            layer.add_entity(fireball)

            # Set the input to false so we don't accidentally use a skill twice
            # @TODO Remove this, because it sucks
            entity.components['input'].input[EntityInput.SKILL_USAGE] = False

            # Trigger a skill usage event
            self.events.dispatch(EntitySkillUsageEvent(entity.id))


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
        'health'
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
        health_component = entity.components['health']

        # Skip this entity if we're at full health
        if health_component.health == health_component.max:
            return

        regeneration_amount = self.default_regeneration_amount * event.delta_time
        health_component.health += regeneration_amount

        # If adding would result in exceeding the max amount, only give the entity as much as we can
        if health_component.health >= health_component.max:
            health_component.health = health_component.max

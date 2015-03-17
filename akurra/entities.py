"""Entities module."""
import pygame
from enum import Enum
from .assets import AssetManager, SpriteAnimation


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


class ItemState(Enum):

    """Item state enum."""

    DROPPED = 1
    HELD = 2
    EQUIPPED = 3


class ItemFlags(Enum):

    """Item flags enum."""

    CONSUMABLE = 1
    EQUIPPABLE = 2
    SELLABLE = 3


class EquipmentSlot(Enum):

    """Equipment slot enum."""

    HEAD = 0
    SHOULDERS = 1
    CHEST = 2
    WAIST = 3
    LEGS = 4
    FEET = 5
    ARMS = 6
    LEFT_HAND = 7
    RIGHT_HAND = 8
    NECK = 9
    CLOAK = 10
    FINGER_1 = 11
    FINGER_2 = 12
    FINGER_3 = 13
    FINGER_4 = 14
    FINGER_5 = 15
    FINGER_6 = 16
    FINGER_7 = 17
    FINGER_8 = 18
    FINGER_9 = 19
    FINGER_10 = 20
    FINGER_11 = 21


class Entity(pygame.sprite.Sprite):

    """
    Generic game entity.

    The generic game entity is based off of pyscroll's "Hero" example.

    There are two collision rects: one for the whole sprite ("rect") and
    another to check collisions with walls ("core").

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down' to
    as integers, the sprite would move faster moving left or up.

    Core is half as wide as the normal rect, and not very tall. This size
    allows the top of the sprite to overlap walls.

    There is also an old position ("position_old") that can used to reposition
    the sprite if it collides with level walls.

    A dict consisting of animations can be passed to the constructor. This
    allows for easy sprite animations.

    """

    def __init__(self, image, position=[0, 0], core=None, state=EntityState.STATIONARY, animations={}):
        """Constructor."""
        super().__init__()

        self.position = position
        self.position_old = list(self.position)

        self.default = image.copy()
        self.image = image
        self.rect = self.image.get_rect()

        if not core:
            core = pygame.Rect(position[0], position[1], self.rect.width * 0.25, self.rect.height * 0.25)

        self.core = core

        self.animations = animations
        self.state = state

    @property
    def position(self):
        """Set position."""
        return self._position

    @position.setter
    def position(self, value):
        """Return position."""
        self._position = list(value)

    def update(self, delta_time):
        """Compute an update to the entity's state."""
        try:
            frame = self.animations[self.state].get_frame()
            self.image.fill([0, 0, 0, 0])
            self.image.blit(frame, [0, 0])
        except KeyError:
            self.image.blit(self.default, [0, 0])


class Actor(Entity):

    """Generic game actor."""

    def __init__(self, velocity=[0, 0], direction=EntityDirection.NORTH, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.velocity = velocity
        self.direction = direction

    def update(self, delta_time):
        """
        Compute an update to the actor's state.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        self.position_old = list(self.position)
        self.position[0] += self.velocity[0] * delta_time
        self.position[1] += self.velocity[1] * delta_time

        self.rect.topleft = list(self.position)

        self.core.center = self.rect.center
        self.core.centery += (self.rect.height / 4)

        direction = EntityDirection.NORTH.value if self.velocity[1] < 0 \
            else EntityDirection.SOUTH.value if self.velocity[1] else 0
        direction |= EntityDirection.EAST.value if self.velocity[0] > 0 \
            else EntityDirection.WEST.value if self.velocity[0] else 0

        self.state = EntityState.MOVING if direction else EntityState.STATIONARY

        if direction:
            self.direction = EntityDirection(direction)

            for key in self.animations:
                self.animations[key].direction = self.direction

        super().update(delta_time)

    def revert_move(self):
        """Revert movement of an entity."""
        self.position = self.position_old
        self.rect.topleft = list(self.position)
        self.core.midbottom = self.rect.midbottom


class Player(Actor):

    """Player actor."""

    sprite_size = (64, 64)

    def __init__(self, inventory=[(False, 0) for x in range(32)], equipment={x: False for x in EquipmentSlot},
                 **kwargs):
        """Constructor."""
        image = pygame.Surface(self.sprite_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)
        core = pygame.Rect(0, 0, self.sprite_size[0] / 3, self.sprite_size[1] / 4)

        super().__init__(image=image, core=core, **kwargs)

        self.equipment = equipment
        self.inventory = inventory

        self.load_animations()

    def load_animations(self):
        """Load animations."""
        from . import container

        base = 'sprites/lpc_medieval_fantasy_character_sprites'
        assets = container.get(AssetManager)

        walking = assets.get_image(base + '/walkcycle/BODY_male.png', alpha=True)

        for slot, item in self.equipment.items():
            if item:
                sheet = item.images[ItemState.EQUIPPED][Player]
                walking.blit(sheet, [0, 0])

        self.animations = {
            EntityState.MOVING: SpriteAnimation(
                sheet=walking,
                directions=[EntityDirection.NORTH, EntityDirection.WEST, EntityDirection.SOUTH, EntityDirection.EAST],
                frames=9,
                frame_interval=20,
                loop=True,
            ),
            EntityState.STATIONARY: SpriteAnimation(
                sheet=walking,
                frame_size=self.sprite_size,
                directions=[EntityDirection.NORTH, EntityDirection.WEST, EntityDirection.SOUTH, EntityDirection.EAST],
                frames=1,
            )
        }

    def update(self, delta_time):
        """
        Compute an update to the actor's state.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        super().update(delta_time)

    def on_equip(self, event):
        """Handle equipment."""
        self.equipment[event.slot] = event.item
        self.load_animations()

    def on_unequip(self, event):
        """Handle unequipment."""
        self.equipment.pop(event.slot, None)
        self.load_animations()


class Item:

    """Base item."""

    def __init__(self, state=ItemState.DROPPED, flags=0, stackable=1, images={}, **kwargs):
        """Constructor."""
        self.images = images

        self.state = state
        self.flags = flags
        self.stackable = stackable

        for k, v in kwargs.items():
            setattr(self, k, v)

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
        self.core.midbottom = self.rect.midbottom

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

    sprite_size = (128, 128)

    def __init__(self, **kwargs):
        """Constructor."""
        image = pygame.Surface(self.sprite_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)
        core = pygame.Rect(0, 0, self.sprite_size[0] / 4, self.sprite_size[1] / 8)

        super().__init__(image=image, core=core, **kwargs)

        from . import container

        base_path = 'sprites/isometric_hero_and_heroine/hero'
        armor = container.get(AssetManager).get_image(base_path + '/steel_armor.png', alpha=True)
        head = container.get(AssetManager).get_image(base_path + '/male_head2.png', alpha=True)
        shield = container.get(AssetManager).get_image(base_path + '/shield.png', alpha=True)
        sword = container.get(AssetManager).get_image(base_path + '/longsword.png', alpha=True)

        sheet = armor
        sheet.blit(head, [0, 0])
        sheet.blit(shield, [0, 0])
        sheet.blit(sword, [0, 0])

        self.animations = {
            EntityState.MOVING: SpriteAnimation(
                sheet=sheet,
                frame_size=self.sprite_size,
                directions=[EntityDirection.WEST, EntityDirection.NORTH_WEST,
                            EntityDirection.NORTH, EntityDirection.NORTH_EAST,
                            EntityDirection.EAST, EntityDirection.SOUTH_EAST,
                            EntityDirection.SOUTH, EntityDirection.SOUTH_WEST],
                frames=8,
                frame_offset=4,
                loop=True
            ),
            EntityState.STATIONARY: SpriteAnimation(
                sheet=sheet,
                frame_size=self.sprite_size,
                directions=[EntityDirection.WEST, EntityDirection.NORTH_WEST,
                            EntityDirection.NORTH, EntityDirection.NORTH_EAST,
                            EntityDirection.EAST, EntityDirection.SOUTH_EAST,
                            EntityDirection.SOUTH, EntityDirection.SOUTH_WEST],
                frames=4,
                frame_interval=300,
                loop=True
            )
        }

    def update(self, delta_time):
        """
        Compute an update to the actor's state.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        super().update(delta_time)

        self.core.center = self.rect.center
        self.core.centery += (self.rect.height / 4) - (self.core.height / 2)

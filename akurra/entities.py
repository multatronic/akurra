"""Entities module."""
import pygame
from enum import Enum
from .assets import AssetManager, SpriteAnimation


class Direction(Enum):

    """Direction enum."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    NORTH_EAST = NORTH | EAST
    SOUTH_EAST = SOUTH | EAST
    NORTH_WEST = NORTH | WEST
    SOUTH_WEST = SOUTH | WEST


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

    def __init__(self, image, position=[0, 0], animations={}):
        """Constructor."""
        super().__init__()

        self.position = position
        self.position_old = list(self.position)

        self.image = image
        self.rect = self.image.get_rect()
        self.core = pygame.Rect(position[0], position[1], self.rect.width * 0.75, 10)

        self.animations = animations

    @property
    def position(self):
        """Set position."""
        return self._position

    @position.setter
    def position(self, value):
        """Return position."""
        self._position = list(value)


class Actor(Entity):

    """Generic game actor."""

    def __init__(self, velocity=[0, 0], **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.velocity = velocity

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
        super().__init__(image=pygame.Surface(self.sprite_size, flags=pygame.HWSURFACE | pygame.SRCALPHA), **kwargs)

        from . import container

        armor = container.get(AssetManager).get_image('entities/hero/steel_armor.png', alpha=True)
        head = container.get(AssetManager).get_image('entities/hero/male_head2.png', alpha=True)
        shield = container.get(AssetManager).get_image('entities/hero/shield.png', alpha=True)
        sword = container.get(AssetManager).get_image('entities/hero/longsword.png', alpha=True)

        sheet = armor
        sheet.blit(head, [0, 0])
        sheet.blit(shield, [0, 0])
        sheet.blit(sword, [0, 0])

        self.animations = {
            'running': SpriteAnimation(
                sheet=sheet,
                frame_size=self.sprite_size,
                directions=[Direction.WEST, Direction.NORTH_WEST, Direction.NORTH, Direction.NORTH_EAST,
                            Direction.EAST, Direction.SOUTH_EAST, Direction.SOUTH, Direction.SOUTH_WEST],
                frames=8,
                frame_offset=4,
                loop=True
            ),
            'stance': SpriteAnimation(
                sheet=sheet,
                frame_size=self.sprite_size,
                directions=[Direction.WEST, Direction.NORTH_WEST, Direction.NORTH, Direction.NORTH_EAST,
                            Direction.EAST, Direction.SOUTH_EAST, Direction.SOUTH, Direction.SOUTH_WEST],
                frames=4,
                frame_interval=300,
                loop=True
            )
        }

        self.direction = Direction.NORTH

    def update(self, delta_time):
        """
        Compute an update to the actor's state.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        super().update(delta_time)

        direction = Direction.NORTH.value if self.velocity[1] < 0 else Direction.SOUTH.value if self.velocity[1] else 0
        direction |= Direction.EAST.value if self.velocity[0] > 0 else Direction.WEST.value if self.velocity[0] else 0

        if direction:
            self.direction = Direction(direction)

        animation = self.animations['running'] if direction else self.animations['stance']
        animation.direction = self.direction

        self.image.fill([0, 0, 0, 0])
        self.image.blit(animation.get_frame(), [0, 0])

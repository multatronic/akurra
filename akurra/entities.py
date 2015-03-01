"""Entities module."""
import pygame


class Entity(pygame.sprite.Sprite):

    """
    Generic game entity.

    The generic game entity is based off of pyscroll's "Hero" example.

    There are three collision rects: two for the whole sprite ("rect" and
    "old_rect")  and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down' to
    as integers, the sprite would move faster moving left or up.

    Core is half as wide as the normal rect, and half as tall.  This size
    allows the top of the sprite to overlap walls.

    There is also an old_rect that can used to reposition the sprite if it
    collides with level walls.

    """

    def __init__(self, image, position=[0, 0]):
        """Constructor."""
        super().__init__()

        self.position = position
        self.position_old = list(self.position)

        self.image = image
        self.rect = self.image.get_rect()
        self.core = pygame.Rect(position[0], position[1], self.rect.width * 0.5, 5)

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

    def __init__(self, image, velocity=[0, 0], position=[0, 0]):
        """Constructor."""
        super().__init__(image, position)

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

"""Entities module."""
import pygame


class GameEntity(pygame.sprite.Sprite):

    """
    Generic game entity.

    The generic game entity is based off of pyscroll's "Hero" example.

    There are three collision rects: two for the whole sprite ("rect" and
    "old_rect")  and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down' to
    as integers, the sprite would move faster moving left or up.

    Base is 1/2 as wide as the normal rect, and 10 pixels tall.  This size
    allows the top of the sprite to overlap walls.

    There is also an old_rect that can used to reposition the sprite if it
    collides with level walls.

    """

    def __init__(self, image, velocity=[0, 0], position=[0, 0]):
        """Constructor."""
        pygame.sprite.Sprite.__init__(self)

        self.velocity = velocity
        self._position = position
        self._old_position = self.position

        self.image = image
        self.rect = self.image.get_rect()
        self.base = pygame.Rect(position[0], position[1], self.rect.width * 0.5, 10)

    @property
    def position(self):
        """Return position."""
        return list(self._position)

    @position.setter
    def position(self, value):
        """Set position."""
        self._position = list(value)

    def update(self, delta_time):
        """
        Compute an update to the entity's state.

        :param delta_time: Time delta to compute the state update for, in s.

        """
        self._old_position = self._position[:]
        self._position[0] += self.velocity[0] * delta_time
        self._position[1] += self.velocity[1] * delta_time

        self.rect.topleft = self._position
        self.base.midbottom = self.rect.midbottom

    def revert_move(self):
        """Revert movement of an entity."""
        self._position = self._old_position
        self.rect.topleft = self._position
        self.base.midbottom = self.rect.midbottom

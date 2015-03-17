"""Assets module."""
import os
import logging
import pygame
import pyscroll
import pytmx
from injector import inject
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class AssetManager:

    """Asset manager."""

    def get_path(self, asset_path):
        """
        Return a path to an asset while taking distributions and base paths into account.

        :param asset_path: Relative path of asset to process.

        """
        return os.path.join(self.base_path, asset_path)

    def get_image(self, asset_path, colorkey=None, alpha=False):
        """
        Return an image by processing an asset.

        :param asset_path: Relative path of asset to process.

        """
        path = self.get_path(asset_path)
        image = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()

        if colorkey:
            image.set_colorkey(colorkey)

        return image

    def get_tmx_data(self, asset_path):
        """
        Return TMX data by processing an asset.

        :param asset_path: Relative path of asset to process.

        """
        path = self.get_path(asset_path)
        tmx_data = pytmx.load_pygame(path)

        return tmx_data

    def get_map_data(self, asset_path):
        """
        Return map data by processing an asset.

        :param asset_path: Relative path of asset to process.

        """
        tmx_data = self.get_tmx_data(asset_path)
        map_data = pyscroll.data.TiledMapData(tmx_data)

        return map_data

    @inject(base_path=AssetBasePath)
    def __init__(self, base_path='assets'):
        """Constructor."""
        logger.debug('Initializing AssetManager')

        self.base_path = base_path


class SpriteAnimation:

    """Base animation."""

    @property
    def frame(self):
        """Return frame."""
        return self._frame

    @frame.setter
    def frame(self, value):
        """Set frame."""
        if value > self.frames and self.loop:
            value = 1

        self._frame = value

    def __init__(self, sheet, frames=1, directions=[1], frame_size=None, frame_offset=0,
                 frame_interval=60, loop=False):
        """Constructor."""
        self.sheet = sheet
        self.loop = loop

        self.directions = directions
        self.direction = directions[0]

        self.frames = frames

        self.frame = 0
        self.frame_offset = frame_offset
        self.frame_interval = frame_interval

        if not frame_size:
            frame_size = int(self.sheet.get_width() / self.frames), int(self.sheet.get_height() / len(self.directions))

        self.frame_size = frame_size
        self.image = pygame.Surface(self.frame_size, flags=pygame.SRCALPHA)

        self.last_tick = 0

    def get_frame(self):
        """Return a frame of the animation."""
        if self.frame < self.frames or self.loop:
            current_tick = pygame.time.get_ticks()

            if (current_tick - self.last_tick) > self.frame_interval:
                self.frame += 1
                self.last_tick = current_tick

        self.image.fill([0, 0, 0, 0])
        self.image.blit(self.sheet, [0, 0], [
            (self.frame + self.frame_offset - 1) * self.frame_size[0],
            (self.directions.index(self.direction)) * self.frame_size[1],
            self.frame_size[0],
            self.frame_size[1]
        ])

        return self.image

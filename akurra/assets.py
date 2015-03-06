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

    def get_sound(self, asset_path):
        """
        Return an sfx object (OGG only for now).

        :param asset_path: Relative path of asset to process.

        """
        path = self.get_path(asset_path)
        sound = pygame.mixer.Sound(path)

        return sound

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

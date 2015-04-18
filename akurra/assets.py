"""Assets module."""
import os
import logging
import pygame
import pyscroll
import pytmx
from injector import inject
from .locals import *  # noqa
from .utils import ContainerAware


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
        logger.debug('Initializing AssetManager [base_path=%s]', base_path)

        self.base_path = base_path


# class SpriteAnimation(ContainerAware):

#     """Base animation."""

#     @property
#     def frame(self):
#         """Return frame."""
#         return self._frame

#     @frame.setter
#     def frame(self, value):
#         """Set frame."""
#         if value > self.frames and self.loop:
#             value = 1

#         self._frame = value

#     def __init__(self, sheet_path, frames=1, directions=[1], frame_size=None, frame_offset=0,
#                  frame_interval=60, loop=False):
#         """Constructor."""
#         # If a list of sheet paths is passed, blit them over each other
#         if type(sheet_path) is list:
#             self.sheet = self.container.get(AssetManager).get_image(sheet_path[0], alpha=True)

#             for path in sheet_path[1:]:
#                 self.sheet.blit(self.container.get(AssetManager).get_image(path, alpha=True), [0, 0])
#         else:
#             self.sheet = self.container.get(AssetManager).get_image(sheet_path, alpha=True)

#         self.loop = loop

#         self.directions = directions
#         self.direction = directions[0]

#         self.frames = frames

#         self.frame = 0
#         self.frame_offset = frame_offset
#         self.frame_interval = frame_interval

#         if not frame_size:
#             frame_size = int(self.sheet.get_width() / self.frames), int(self.sheet.get_height() / len(self.directions))

#         self.frame_size = frame_size
#         self.image = pygame.Surface(self.frame_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)

#         self.last_tick = 0

#     def get_frame(self):
#         """Return a frame of the animation."""
#         if self.frame < self.frames or self.loop:
#             current_tick = pygame.time.get_ticks()

#             if (current_tick - self.last_tick) > self.frame_interval:
#                 self.frame += 1
#                 self.last_tick = current_tick

#         self.image.fill([0, 0, 0, 0])
#         self.image.blit(self.sheet, [0, 0], [
#             (self.frame + self.frame_offset - 1) * self.frame_size[0],
#             (self.directions.index(self.direction)) * self.frame_size[1],
#             self.frame_size[0],
#             self.frame_size[1]
#         ])

#         return self.image


class SpriteAnimation(ContainerAware):

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

    def __init__(self, sprite_sheets, frames=1, directions=[1], frame_size=None, frame_offset=0,
                 frame_interval=60, loop=False):
        """Constructor."""
        self.frames = frames

        self.frame = 0
        self.frame_offset = frame_offset
        self.frame_interval = frame_interval
        self.frame_size = frame_size

        sprite_sheets = sprite_sheets if type(sprite_sheets) is list else [sprite_sheets]
        self.sprite_sheets = []

        # We support sprite sheet layering
        for sprite_sheet in sprite_sheets:
            # Determine the path to the sprite sheet
            # If we only got a single string assume it's the path, else assume a frame size override is present
            sprite_sheet_path = sprite_sheet[0] if type(sprite_sheet) is list else sprite_sheet

            # Determine correct frame size for this sprite sheet
            sprite_sheet_frame_size = sprite_sheet[1] if type(sprite_sheet) is list else frame_size

            # Calculate sprite sheet frame positioning offset compared to combined image
            sprite_sheet_frame_offset = [(self.frame_size[x] - sprite_sheet_frame_size[x]) / 2 for x in [0, 1]]

            self.sprite_sheets.append([self.container.get(AssetManager).get_image(sprite_sheet_path, alpha=True),
                                       sprite_sheet_frame_size,
                                       sprite_sheet_frame_offset])

        self.loop = loop

        self.directions = directions
        self.direction = directions[0]

        self.image = pygame.Surface(self.frame_size, flags=pygame.HWSURFACE | pygame.SRCALPHA)

        self.last_tick = 0

    def get_frame(self):
        """Return a frame of the animation."""
        if self.frame < self.frames or self.loop:
            current_tick = pygame.time.get_ticks()

            if (current_tick - self.last_tick) > self.frame_interval:
                self.frame += 1
                self.last_tick = current_tick

        self.image.fill([0, 0, 0, 0])

        for sprite_sheet in self.sprite_sheets:
            self.image.blit(sprite_sheet[0], sprite_sheet[2], [
                [
                    (self.frame + self.frame_offset - 1) * sprite_sheet[1][0],
                    (self.directions.index(self.direction)) * sprite_sheet[1][1]
                ],
                sprite_sheet[1]
            ])

        return self.image

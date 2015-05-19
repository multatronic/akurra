"""Audio module."""
import logging
import pygame
from injector import inject

from .assets import AssetManager
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class AudioManager:

    """
    Audio manager.

    The audio manager is in charge of playing music and sound.

    """

    @inject(assets=AssetManager, master_volume=AudioMasterVolume, bgm_volume=AudioBackgroundMusicVolume,
            sfx_volume=AudioSpecialEffectsVolume)
    def __init__(self, assets, master_volume=1.0, bgm_volume=1.0, sfx_volume=1.0):
        """Constructor."""
        logger.debug('Initializing AudioManager')

        self.master_volume = master_volume
        self.bgm_volume = bgm_volume
        self.sfx_volume = sfx_volume

        self.assets = assets
        self.channels = [False for x in range(0, 8)]
        self.sounds = {}
        self.music = {}

    def add_channel(self, name):
        """Add a channel entry."""
        for i in range(0, len(self.channels)):
            if self.channels[i] is False:
                self.channels[i] = name
                logger.debug('Added audio channel "%s" [slot=%s]', name, i + 1)

    def get_channel(self, name):
        """Retrieve a channel."""
        for i in range(0, len(self.channels)):
            if name is self.channels[i]:
                return pygame.mixer.Channel(i + 1)

        return None

    def remove_channel(self, name):
        """Remove a channel entry."""
        for i in range(0, len(self.channels)):
            if self.channels[i] is name:
                self.channels.remove(name)
                logger.debug('Removed audio channel "%s" [slot=%s]', name, i + 1)

    def add_sound(self, relative_path, name):
        """Add a sound."""
        sound = self.assets.get_sound(relative_path)
        self.sounds[name] = sound
        logger.debug('Added sound "%s"', name)

    def remove_sound(self, name):
        """Remove a state."""
        self.sounds.pop(name, None)
        logger.debug('Removed sound "%s"', name)

    def add_music(self, relative_path, name):
        """Add a music path and name."""
        absolute_path = self.assets.get_path(relative_path)
        self.music[name] = absolute_path
        logger.debug('Added music "%s"', name)

    def remove_music(self, name):
        """Remove a music object."""
        self.music.pop(name, None)
        logger.debug('Removed music "%s"', name)

    # Play a piece of music, only one can be played at a time.
    # set loop counter to -1 to loop indefinitely
    def play_music(self, name, loop_counter=-1, starting_point=0.0):
        """Play background music."""
        logger.debug('Playing music "%s"', name)

        pygame.mixer.music.load(self.music[name])
        pygame.mixer.music.set_volume(self.master_volume * self.bgm_volume)
        pygame.mixer.music.play(loop_counter, starting_point)

    def stop_music():
        """Stop playing background music."""
        logger.debug("Stopping background music")
        pygame.mixer.music.stop()

    def play_sound(self, name, channel=None, queue=False):
        """Play sound effect."""
        sound = self.sounds[name]
        sound.set_volume(self.master_volume * self.sfx_volume)

        if channel:
            channel = self.get_channel(channel)

            if queue:
                channel.queue(sound)
            elif not channel.get_busy():
                channel.play(sound)

        else:
            sound.play()

    def stop_sound(self, name):
        """Stop sound effect."""
        logger.debug('Stopping sound "%s"', name)
        self.sounds[name].stop()

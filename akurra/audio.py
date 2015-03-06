"""Audio module."""
import logging
import pygame
from injector import inject
from akurra.assets import AssetManager


logger = logging.getLogger(__name__)


class AudioManager:

    """
    Audio manager.

    The audio manager is in charge of playing music and sound.

    """

    @inject(assets=AssetManager)
    def __init__(self, assets):
        """Constructor."""
        logger.debug('Initializing AudioManager')

        self.assets = assets
        self.sound = {}
        self.music = {}

    def add_sound(self, relative_path, name):
        """Add a sound."""
        # TODO add checks for invalid path
        relative_path = "pyscroll_demo/audio/sfx/test.ogg"
        sound = self.assets.get_sound(relative_path)
        self.sound[name] = sound
        logger.debug('Added sound "%s"', name)

    def remove_sound(self, name):
        """Remove a state."""
        self.sound.pop(name, None)
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
        if name in self.music:
            logger.debug('Playing music "%s"', name)
            pygame.mixer.music.load(self.music[name])
            pygame.mixer.music.play(loop_counter, starting_point)
        else:
            logger.debug("Attempted to play non-extant music file!")

    def stop_music():
        """Stop playing background music."""
        logger.debug("Stopping background music.")
        pygame.mixer.music.stop()

    def play_sound(self, name):
        """Play sound effect."""
        if name in self.sound:
            logger.debug('Playing sound "%s"', name)
            self.sound[name].play()
        else:
            logger.debug("Attempted to play non-extant sound file !")

    def stop_sound(self, name):
        """Stop sound effect."""
        if name in self.music:
            logger.debug('Stopping sound "%s"', name)
            self.music[name].stop()
        else:
            logger.debug("Attempted to stop non-extant sound file!")

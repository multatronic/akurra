"""Audio module."""
import logging
import pygame
from injector import inject
from akurra.events import EventManager


logger = logging.getLogger(__name__)


class AudioManager:

    """
    Audio manager.

    The audio manager is in charge of playing music and sounds.

    """

    @inject(events=EventManager)
    def __init__(self, events):
        """Constructor."""
        logger.debug('Initializing AudioManager')

        self.sounds = {}
        self.music = {}

    def add_sound(self, sound, name):
        """Add a sound."""
        self.sounds[name] = sound
        logger.debug('Added sound "%s"', name)

    def remove_sound(self, name):
        """Remove a state."""
        self.sounds.pop(name, None)
        logger.debug('Removed sound "%s"', name)

    def add_music(self, file_path, name):
        """Add a music path and name."""
        self.music[name] = file_path
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
        pygame.mixer.music.stop()

    def play_sound(self, name):
        """Play sound effect."""
        if name in self.music:
            logger.debug('Playing sound "%s"', name)
            self.music[name].play()
        else:
            logger.debug("Attempted to play non-extant sound file!")

"""Keyboard module."""
import logging
import pygame
from injector import inject
from akurra.events import EventManager
from akurra.utils import hr_key_id


logger = logging.getLogger(__name__)


class KeyboardManager:

    """Keyboard manager."""

    def on_key_down(self, event):
        """Handle a key press."""
        logger.debug('Detected key press [key=%s]', hr_key_id(event.key))

    @inject(events=EventManager)
    def __init__(self, events):
        """Constructor."""
        self.events = events
        self.events.register(pygame.KEYDOWN, self.on_key_down)

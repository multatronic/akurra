"""Keyboard module."""
import logging
import pygame
from injector import inject
from akurra.events import EventManager
from akurra.utils import hr_key_id, hr_event_type


logger = logging.getLogger(__name__)


class KeyboardManager:

    """Keyboard manager."""

    def register(self, key_id, listener, mods=0, event_type=pygame.KEYDOWN):
        """
        Register a listener for a press, hold or release of a key.

        :param event_type: An identifier for an event type.
        :param key_id: A key identifier.
        :param mods: An integer representing a bitmask of all modifier keys that should be held.
        :param listener: An event listener which can accept an event.

        """
        if type(event_type) not in [int, str]:
            event_type = event_type.__module__ + '.' + event_type.__name__

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        if key_id not in self.listeners[event_type]:
            self.listeners[event_type][key_id] = {}

        if mods not in self.listeners[event_type][key_id]:
            self.listeners[event_type][key_id][mods] = {}

        self.listeners[event_type][key_id][mods][listener] = 1
        logger.debug('Registered listener for key "%s" [mods=%s, event=%s]',
                     hr_key_id(key_id), mods, hr_event_type(event_type))

    def unregister(self, listener):
        """
        Unregister a listener for a press, hold or release of a combination of keys.

        :param listener: A listener to unregister.

        """
        for event_type in self.listeners:
            for key_id in self.listeners[event_type]:
                for mods in self.listeners[event_type][key_id]:
                    if self.listeners[event_type][key_id][mods].pop(listener, None):
                        logger.debug('Unregistered listener for key "%s" [mods=%s, event=%s]',
                                     hr_key_id(key_id), mods, hr_event_type(event_type))

    def on_key_down(self, event):
        """Handle a key press."""
        logger.debug('Detected key press [key=%s, mod=%s]', hr_key_id(event.key), event.mod)

        try:
            for mods in self.listeners[event.type][event.key]:
                if not mods or mods & event.mod:
                    for listener in self.listeners[event.type][event.key][mods].copy():
                        listener(event)
        except KeyError:
            logger.debug('No listeners defined for key "%s" [mods=%s, event=%s]',
                         hr_key_id(event.key), event.mod, hr_event_type(event.type))
            pass

    def on_key_up(self, event):
        """Handle a key release."""
        logger.debug('Detected key release [key=%s, mod=%s]', hr_key_id(event.key), event.mod)

        try:
            for mods in self.listeners[event.type][event.key]:
                if not mods or mods & event.mod:
                    for listener in self.listeners[event.type][event.key][mods].copy():
                        listener(event)
        except KeyError:
            logger.debug('No listeners defined for key "%s" [mods=%s, event=%s]',
                         hr_key_id(event.key), event.mod, hr_event_type(event.type))
            pass

    @inject(events=EventManager)
    def __init__(self, events):
        """Constructor."""
        logger.debug('Initializing KeyboardManager')

        self.events = events
        self.events.register(pygame.KEYDOWN, self.on_key_down)
        self.events.register(pygame.KEYUP, self.on_key_up)

        self.listeners = {}

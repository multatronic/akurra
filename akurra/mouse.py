"""Mouse module."""
import logging
import pygame
from injector import inject
from akurra.events import EventManager
from akurra.utils import hr_button_id, hr_event_type, fqcn


logger = logging.getLogger(__name__)


class MouseManager:

    """
    Mouse manager.

    The mouse manager is in charge of managing key bindings and acting upon
    mouse clicks or hovers.

    """

    def register(self, button_id, listener, event_type=pygame.MOUSEBUTTONDOWN):
        """
        Register a listener for a click, hover or release of a mouse button.

        :param event_type: An identifier for an event type.
        :param button_id: A button identifier.
        :param mods: An integer representing a bitmask of all modifier keys that should be held.
        :param listener: An event listener which can accept an event.

        """
        if type(event_type) not in [int, str]:
            event_type = fqcn(event_type)

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        if button_id not in self.listeners[event_type]:
            self.listeners[event_type][button_id] = {}

        self.listeners[event_type][button_id][listener] = 1
        logger.debug('Registered listener for button "%s"[event=%s]', hr_button_id(button_id),
                     hr_event_type(event_type))

    def unregister(self, listener):
        """
        Unregister a listener for a click, hold or release of a mouse button.

        :param listener: A listener to unregister.

        """
        for event_type in self.listeners:
            for button_id in self.listeners[event_type]:
                if self.listeners[event_type][button_id].pop(listener, None):
                    logger.debug('Unregistered listener for button "%s" [event=%s]', hr_button_id(button_id),
                                 hr_event_type(event_type))

    def on_mouse_button_down(self, event):
        """Handle holding down of a mouse button."""
        logger.debug('Detected mouse button down [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        try:
            for listener in self.listeners[event.type][event.button].copy():
                    listener(event)
        except KeyError:
            logger.debug('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                         hr_event_type(event.type))
            pass

    def on_mouse_button_up(self, event):
        """Handle releasing of a mouse button."""
        logger.debug('Detected mouse button up [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        try:
            for listener in self.listeners[event.type][event.button].copy():
                listener(event)
        except KeyError:
            logger.debug('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                         hr_event_type(event.type))
            pass

    def on_mouse_motion(self, event):
        """Handle mouse motion."""
        logger.debug('Detected mouse motion [pos=%s]', event.pos)

    @inject(events=EventManager)
    def __init__(self, events):
        """Constructor."""
        logger.debug('Initializing MouseManager')

        self.events = events
        self.events.register(pygame.MOUSEBUTTONDOWN, self.on_mouse_button_down)
        self.events.register(pygame.MOUSEBUTTONUP, self.on_mouse_button_up)
        self.events.register(pygame.MOUSEMOTION, self.on_mouse_motion)

        self.listeners = {}

"""Keyboard module."""
import logging
import functools
import pygame

from .locals import *  # noqa
from .input import InputSource, InputActionEvent
from .events import EventManager
from .utils import hr_key_id, hr_event_type, fqcn


logger = logging.getLogger(__name__)


class KeyboardInput(InputSource):

    """Keyboard input source, responsible for triggering input actions when keys are pressed, released or held."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.configuration = self.container.get(Configuration)
        self.events = self.container.get(EventManager)
        self.listeners = {}
        self.load_action_bindings()

    def start(self):
        """Start the module."""
        self.events.register(pygame.KEYDOWN, self.on_key_down)
        self.events.register(pygame.KEYUP, self.on_key_up)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_key_down)
        self.events.unregister(self.on_key_up)

    def add_listener(self, key_id, listener, mods=0, event_type=pygame.KEYDOWN, priority=10):
        """
        Register a listener for a press, hold or release of a key.

        :param event_type: An identifier for an event type.
        :param key_id: A key identifier.
        :param mods: An integer representing a bitmask of all modifier keys that should be held.
        :param listener: An event listener which can accept an event.
        :param priority: Priority of event listener.

        """
        if type(event_type) not in [int, str]:
            event_type = fqcn(event_type)

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        if key_id not in self.listeners[event_type]:
            self.listeners[event_type][key_id] = {}

        if mods not in self.listeners[event_type][key_id]:
            self.listeners[event_type][key_id][mods] = 99 * [None]

        if not self.listeners[event_type][key_id][mods][priority]:
            self.listeners[event_type][key_id][mods][priority] = []

        self.listeners[event_type][key_id][mods][priority].append(listener)
        logger.debug('Registered listener for key "%s" [mods=%s, event=%s, priority=%s]',
                     hr_key_id(key_id), mods, hr_event_type(event_type), priority)

    def remove_listener(self, listener):
        """
        Remove a listener for a press, hold or release of a combination of keys.

        :param listener: A listener to remove.

        """
        for event_type in self.listeners:
            for key_id in self.listeners[event_type]:
                for mods in self.listeners[event_type][key_id]:
                    if self.listeners[event_type][key_id][mods]:
                        for listeners in self.listeners[event_type][key_id][mods]:
                            if listeners and listener in listeners:
                                listeners.remove(listener)
                                logger.debug('Unregistered listener for key "%s" [mods=%s, event=%s]',
                                             hr_key_id(key_id), mods, hr_event_type(event_type))

    def on_key_down(self, event):
        """Handle a key press."""
        logger.insane('Detected press of key "%s" [mod=%s]', hr_key_id(event.key), event.mod)

        try:
            for mods in self.listeners[event.type][event.key]:
                if not mods or mods & event.mod:
                    for listeners in self.listeners[event.type][event.key][mods]:
                        if listeners:
                            for listener in listeners.copy():
                                if listener and listener(event) is False:
                                    break
        except KeyError:
            logger.insane('No listeners defined for key "%s" [mods=%s, event=%s]',
                          hr_key_id(event.key), event.mod, hr_event_type(event.type))
            pass

    def on_key_up(self, event):
        """Handle a key release."""
        logger.insane('Detected release of key "%s" [mod=%s]', hr_key_id(event.key), event.mod)

        try:
            for mods in self.listeners[event.type][event.key]:
                if not mods or mods & event.mod:
                    for listeners in self.listeners[event.type][event.key][mods]:
                        if listeners:
                            for listener in listeners.copy():
                                if listener and listener(event) is False:
                                    break
        except KeyError:
            logger.insane('No listeners defined for key "%s" [mods=%s, event=%s]',
                          hr_key_id(event.key), event.mod, hr_event_type(event.type))
            pass

    def load_action_bindings(self):
        """Load action bindings."""
        bindings = self.configuration.get('akurra.input.keyboard.action_bindings', {})

        for action, binding in bindings.items():
            # If no modifier was specified for this binding, default to 0
            binding = binding if type(binding) is list else [binding, ['KMOD_NONE']]

            # Combine modifier array into one bitmask if needed
            if binding[1]:
                binding[1] = functools.reduce(lambda x, y: x | y, [getattr(pygame, x) for x in binding[1]])

            self.add_action_binding(action, getattr(pygame, binding[0]), mods=binding[1])

    def add_action_binding(self, action, key_id, mods=0, priority=10):
        """
        Register an action to be triggered on a press, hold or release of a key.

        :param key_id: A key identifier.
        :param mods: An integer representing a bitmask of all modifier keys that should be held.
        :param action: An action to trigger.
        :param event_type: Event type to trigger action on.
        :param priority: Priority of event listener.

        """
        for event_type in pygame.KEYDOWN, pygame.KEYUP:
            self.add_listener(key_id, lambda x: self.trigger_action(x, action), mods=mods, event_type=event_type,
                              priority=priority)

    def remove_action_binding(self, action):
        """
        Remove a binding for an action.

        :param action: An action whose bindings should be removed.

        """
        self.remove_listener(lambda x: self.trigger_action(x))

    def trigger_action(self, event, action):
        """
        Process a key press, hold or release event and trigger an action.

        :param event: Event to process.
        :param action: Action to trigger.

        """
        self.events.dispatch(InputActionEvent(source='keyboard', action=action,
                                              state=event.type is pygame.KEYDOWN, original_event=event))
        logger.insane('Triggered key action "%s"', action)

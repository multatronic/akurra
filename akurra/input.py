"""Input module."""
import logging

from .locals import *  # noqa
from .modules import Module
from .events import EventManager, Event


logger = logging.getLogger(__name__)


class InputActionEvent(Event):

    """Input action event."""

    def __init__(self, source, action, state, original_event):
        """Constructor."""
        super().__init__()

        self.source = source
        self.action = action
        self.state = state
        self.original_event = original_event.__dict__
        self.original_event['type'] = original_event.type


class InputModule(Module):

    """
    Input module.

    The input module takes care of managing input action listeners, and is the
    central place all input actions triggered by a variety of input sources
    pass through.

    """

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.configuration = self.container.get(Configuration)
        self.events = self.container.get(EventManager)
        self.action_listeners = {}

    def start(self):
        """Start the module."""
        self.events.register(InputActionEvent, self.on_input_action)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_input_action)

    def on_input_action(self, event):
        """
        Handle an input action.

        :param InputActionEvent event: Event to process.

        """
        for listeners in self.action_listeners[event.action]:
            if listeners:
                for listener in listeners:
                    if listener and listener(event) is False:
                        break

        logger.insane('Handled input action "%s"', event.action)

    def add_action_listener(self, action, listener, priority=10):
        """
        Register a listener for an action.

        :param action: An identifier for an action.
        :param listener: An event listener which can accept an event.
        :param priority: Priority of event listener.

        """
        if action not in self.action_listeners:
            self.action_listeners[action] = 99 * [None]

        if not self.action_listeners[action][priority]:
            self.action_listeners[action][priority] = []

        self.action_listeners[action][priority].append(listener)
        logger.debug('Registered listener for action "%s" [priority=%s]', action, priority)

    def remove_action_listener(self, listener):
        """
        Remove a listener for an action.

        :param listener: A listener to remove.

        """
        for action in self.action_listeners:
            for listeners in self.action_listeners[action]:
                if listeners and listener in listeners:
                    listeners.remove(listener)
                    logger.debug('Unregistered listener for action "%s"', action)


class InputSource(Module):

    """
    Base input source module.

    An input source is responsible for triggering input actions based on input.

    """

    dependencies = ['input']

"""Events module."""
import logging


logger = logging.getLogger(__name__)


class Event:

    """Base event class."""

    @classmethod
    def type(cls):
        """Return type."""
        return cls.__module__ + '.' + cls.__name__


class EventManager:

    """Event manager."""

    def register(self, event_type, listener):
        """
        Register a listener for an event type.

        :param event_type: A string identifier for an event type in the
                        "__module__" + "__name__" format or an event class.
        :param listener: An event listener which can accept an event.

        """
        if not isinstance(event_type, str):
            event_type = event_type.type()

        if event_type not in self.listeners:
            self.listeners[event_type] = []

        self.listeners[event_type].append(listener)
        logger.debug('Registered a listener for event type "%s"', event_type)

    def dispatch(self, event):
        """
        Dispatch an event by having it broadcast to its listeners.

        :param event: Event to handle.

        """
        event_type = type(event).type()

        try:
            for listener in self.listeners[event_type]:
                listener(event)
        except KeyError:
            logger.warning('No listeners defined for event "%s"', event_type)
            pass

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing EventManager')
        self.listeners = {}

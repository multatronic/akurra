"""Events module."""
from weakref import WeakValueDictionary


class Event:

    """Base event class."""

    @property
    def type(self):
        """Return type."""
        return self.__class__.__module__ + '.' + self.__class__.__name__


class EventManager:

    """Event manager."""

    def register(self, type, listener):
        """
        Register a listener for an event type.

        :param type: An string identifier for an event type in the "__module__"
                        + "__name__" format or an event class.
        :param listener: An event listener which can accept an event.

        """
        if not isinstance(type, str):
            type = type.type

        if type not in self.listeners:
            self.listeners[type] = WeakValueDictionary()

        self.listeners[type].append(listener)

    def handle(self, event):
        """
        Handle an event by having it broadcast to its listeners.

        :param event: Event to handle.

        """
        for listener in self.listeners[type.type]:
            listener(type)

    def __init__(self):
        """Constructor."""
        self.listeners = WeakValueDictionary()

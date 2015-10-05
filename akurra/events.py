"""Events module."""
import logging
import pygame
import queue
from multiprocessing import Queue
from akurra.utils import hr_event_type, fqcn


logger = logging.getLogger(__name__)


class Event:

    """Base event class."""

    def __init__(self):
        """Constructor."""
        self.type = fqcn(self.__class__)


class TickEvent(Event):

    """Tick event."""

    def __init__(self, delta_time=0):
        """Constructor."""
        super().__init__()

        self.delta_time = delta_time


class EventManager:

    """Event manager."""

    def register(self, event_type, listener, priority=50):
        """
        Register a listener for an event type.

        :param event_type: An identifier for an event type.
        :param listener: An event listener which can accept an event.

        """
        if type(event_type) not in [int, str]:
            event_type = fqcn(event_type)

        if event_type not in self.listeners:
            self.listeners[event_type] = 99 * [None]

        if not self.listeners[event_type][priority]:
            self.listeners[event_type][priority] = []

        self.listeners[event_type][priority].append(listener)
        logger.debug('Registered listener for event type "%s"', hr_event_type(event_type))

    def unregister(self, listener):
        """
        Unregister a listener for an event type.

        :param listener: A listener to unregister.

        """
        for event_type in self.listeners:
            for event_listeners in self.listeners[event_type]:
                if event_listeners:
                    try:
                        event_listeners.remove(listener)
                        logger.debug('Unregistered listener for event type "%s"', hr_event_type(event_type))
                    except ValueError:
                        pass

    def dispatch(self, event):
        """
        Dispatch an event for handling.

        :param event: Event to dispatch.

        """
        self.queue.put(event)

    def handle(self, event):
        """
        Handle an event by having it passed to its listeners.

        :param event: Event to handle.

        """
        try:
            for event_listeners in self.listeners[event.type]:
                if event_listeners:
                    for listener in event_listeners:
                        if listener(event) is False:
                            return False
        except KeyError:
            logger.insane('No listeners defined for event "%s"', hr_event_type(event.type))
            pass

        return True

    def poll(self):
        """
        Poll for an event and have it handled if one is found.

        :param timeout: Timeout after which to cancel polling.

        """
        try:
            while True:
                self.handle(self.queue.get(block=False))
        except queue.Empty:
            pass

        [self.handle(x) for x in pygame.event.get()]

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing EventManager')

        self.listeners = {}
        self.queue = Queue()

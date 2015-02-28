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

    def register(self, event_type, listener):
        """
        Register a listener for an event type.

        :param event_type: An identifier for an event type.
        :param listener: An event listener which can accept an event.

        """
        if type(event_type) not in [int, str]:
            event_type = fqcn(event_type)

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        self.listeners[event_type][listener] = 1
        logger.debug('Registered listener for event type "%s"', hr_event_type(event_type))

    def unregister(self, listener):
        """
        Unregister a listener for an event type.

        :param listener: A listener to unregister.

        """
        for event_type in self.listeners:
            if self.listeners[event_type].pop(listener, None):
                logger.debug('Unregistered listener for event type "%s"', hr_event_type(event_type))

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
            for listener in self.listeners[event.type]:
                listener(event)
        except KeyError:
            logger.debug('No listeners defined for event "%s"', hr_event_type(event.type))
            pass

    def poll(self):
        """
        Poll for an event and have it handled if one is found.

        :param timeout: Timeout after which to cancel polling.

        """
        try:
            event = self.queue.get(block=False)
            self.handle(event)
        except queue.Empty:
            pass

        [self.handle(x) for x in pygame.event.get()]

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing EventManager')

        self.listeners = {}
        self.queue = Queue()

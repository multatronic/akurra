"""Events module."""
import logging
import pygame
import queue
from multiprocessing import Queue
from injector import inject
from akurra.locals import ShutdownFlag
from akurra.utils import hr_event_type


logger = logging.getLogger(__name__)


class Event:

    """Base event class."""

    def __init__(self):
        """Constructor."""
        self.type = self.__class__.__module__ + '.' + self.__class__.__name__


class EventManager:

    """Event manager."""

    def register(self, event_type, listener):
        """
        Register a listener for an event type.

        :param event_type: An identifier for an event type.
        :param listener: An event listener which can accept an event.

        """
        if type(event_type) not in [int, str]:
            event_type = event_type.__module__ + '.' + event_type.__name__

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        l_id = id(listener)
        self.listeners[event_type][l_id] = listener
        logger.debug('Registered listener for event type "%s" [id=%s]', hr_event_type(event_type), l_id)

    def unregister(self, listener):
        """
        Unregister a listener for an event type.

        :param listener: A listener to unregister.

        """
        l_id = id(listener)

        for event_type in self.listeners:
            if self.listeners[event_type].pop(l_id, None):
                logger.debug('Unregistered listener for event type "%s" [id=%s]', hr_event_type(event_type), l_id)

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
            for key in self.listeners[event.type]:
                self.listeners[event.type][key](event)
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

        event = pygame.event.poll()

        if event.type != pygame.NOEVENT:
            self.handle(event)

    @inject(shutdown=ShutdownFlag)
    def __init__(self, shutdown):
        """Constructor."""
        logger.debug('Initializing EventManager')

        self.shutdown = shutdown
        self.listeners = {}
        self.queue = Queue()

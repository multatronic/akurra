"""Ticks module."""
import pygame
import logging
from threading import Thread
from injector import inject
from akurra.locals import ShutdownFlag
from akurra.events import Event, EventManager
from akurra.display import FrameRenderEvent


logger = logging.getLogger(__name__)


class TickEvent(Event):

    """Tick Event."""


class TicksManager:

    """Controller for triggering ticks periodically."""

    def on_tick(self, event):
        """Handle a tick event."""
        # Try to render a frame on every tick
        self.events.dispatch(FrameRenderEvent())

    def generate_ticks(self):
        """Generate ticks until shutdown."""
        while not self.shutdown.is_set():
            self.events.dispatch(TickEvent())
            pygame.time.wait(5)

    @inject(events=EventManager, shutdown=ShutdownFlag)
    def __init__(self, events, shutdown):
        """Constructor."""
        logger.debug('Initializing TicksManager')

        self.events = events
        self.events.register(TickEvent, self.on_tick)

        self.shutdown = shutdown

        self.thread = Thread(target=self.generate_ticks, daemon=False)
        self.thread.start()

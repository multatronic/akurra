"""Ticks module."""
import pygame
import logging
from threading import Thread
from injector import inject
from akurra.locals import ShutdownFlag, PygameClock
from akurra.events import Event, EventManager


logger = logging.getLogger(__name__)


class TickEvent(Event):

    """Tick Event."""


class TicksManager:

    """Controller for triggering ticks periodically."""

    def on_tick(self, event):
        """Handle a tick event."""
        pygame.display.set_caption('FPS: %s' % self.clock.get_fps())
        pygame.display.flip()
        self.clock.tick(200)

    def generate_ticks(self):
        """Generate ticks until shutdown."""
        while not self.shutdown.is_set():
            self.events.handle(TickEvent())
            pygame.time.wait(5)

    @inject(events=EventManager, shutdown=ShutdownFlag, clock=PygameClock)
    def __init__(self, events, shutdown, clock):
        """Constructor."""
        self.events = events
        self.shutdown = shutdown
        self.clock = clock

        # Create a resizable, HW-accelerated window
        # @TODO Determine whether we want to use opengl and lose out .update() calls
        self.screen = pygame.display.set_mode([0, 0], pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE)

        self.events.register(TickEvent, self.on_tick)

        self.thread = Thread(target=self.generate_ticks, daemon=False)
        self.thread.start()

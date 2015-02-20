"""Main module."""
import pygame
import signal

from threading import Event
from logging import getLogger
from injector import Injector, inject, singleton

from akurra.locals import *  # noqa

from akurra.events import EventManager
from akurra.modules import ModuleManager
from akurra.logging import configure_logging

from akurra.ticks import TicksManager


pygame.init()
logger = getLogger(__name__)
configure_logging(debug=True)


class Akurra:

    """Base game class."""

    def start(self):
        """Start."""
        logger.debug('Starting..')

        self.modules.load()
        self.modules.start()

        while not self.shutdown.is_set():
            self.shutdown.wait()

    def stop(self):
        """Stop."""
        logger.debug('Stopping..')
        self.shutdown.set()

        self.modules.stop()
        self.modules.unload()

    def handle_signal(self, signum, frame):
        """Handle a signal."""
        logger.debug('Received signal "%s"', signum)
        self.stop()

    @inject(modules=ModuleManager, ticks=TicksManager, shutdown=ShutdownFlag)
    def __init__(self, modules, ticks, shutdown):
        """Constructor."""
        logger.debug('Initializing..')
        self.modules = modules
        self.ticks = ticks
        self.shutdown = shutdown

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    binder.bind(Akurra, scope=singleton)
    binder.bind(EventManager, scope=singleton)
    binder.bind(ModuleManager, scope=singleton)

    binder.bind(EntryPointGroup, to='akurra.modules')
    binder.bind(ShutdownFlag, to=Event())
    binder.bind(PygameClock, to=pygame.time.Clock)

    binder.bind(TicksManager, scope=singleton)


def main():
    """Main entry point."""
    container = Injector(build_container)
    container.get(Akurra).start()

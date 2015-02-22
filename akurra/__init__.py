"""Main module."""
import os
import pygame
import signal

from threading import Event
from logging import getLogger
from injector import Injector, inject, singleton

from akurra.locals import *  # noqa

from akurra.events import EventManager
from akurra.modules import ModuleManager
from akurra.logging import configure_logging

from akurra.display import DisplayManager, DisplayModule
from akurra.ticks import TicksManager, TicksModule
from akurra.fps import FPSManager, FPSModule
from akurra.keyboard import KeyboardManager


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
            # self.shutdown.wait()
            self.events.poll()

    def stop(self):
        """Stop."""
        logger.info('Stopping..')
        self.shutdown.set()

        self.modules.stop()
        self.modules.unload()

    def handle_signal(self, signum, frame):
        """Handle a signal."""
        logger.debug('Received signal, shutting down [signal=%s]', signum)
        self.stop()

    @inject(modules=ModuleManager, events=EventManager, ticks=TicksManager,
            display=DisplayManager, fps=FPSManager, keyboard=KeyboardManager,
            shutdown=ShutdownFlag)
    def __init__(self, modules, events, ticks, display, fps, keyboard, shutdown):
        """Constructor."""
        logger.info('Initializing..')
        self.shutdown = shutdown

        self.modules = modules
        self.events = events

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        # Set correct working directory
        os.chdir(os.path.dirname(os.path.dirname(__file__)))


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    binder.bind(Akurra, scope=singleton)
    binder.bind(ModuleManager, scope=singleton)

    binder.bind(EntryPointGroup, to='akurra.modules')
    binder.bind(ShutdownFlag, to=Event())
    binder.bind(Clock, to=pygame.time.Clock)

    binder.bind(DisplayResolution, to=[0, 0])
    binder.bind(DisplayFlags, to=pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE)

    binder.bind(EventManager, scope=singleton)
    binder.bind(EventPollTimeout, to=0.1)

    binder.install(TicksModule)
    binder.install(DisplayModule)
    binder.install(FPSModule)

    binder.bind(KeyboardManager, scope=singleton)


def main():
    """Main entry point."""
    container = Injector(build_container)
    container.get(Akurra).start()

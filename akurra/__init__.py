"""Main module."""
import os
import sys
import pygame
import signal
import logging

from threading import Event
from multiprocessing import Value
from injector import Injector, inject, singleton

from akurra.locals import *  # noqa

from akurra.events import EventManager
from akurra.modules import ModuleManager
from akurra.logger import configure_logging

from akurra.display import DisplayManager, create_screen
from akurra.ticks import TicksManager
from akurra.debug import DebugManager
from akurra.keyboard import KeyboardManager
<<<<<<< HEAD
from akurra.gamestate import GameStateManager
=======
from akurra.assets import AssetManager

from akurra.demo import DemoManager

>>>>>>> 25b3d43ab08d5de07f8affd6bc82683d5ea69197

DEBUG = 'debug' in sys.argv
os.chdir(os.path.dirname(os.path.dirname(__file__)))
logger = logging.getLogger(__name__)


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
            display=DisplayManager, debugger=DebugManager, keyboard=KeyboardManager,
            demo=DemoManager, statemanager = GameStateManager,
            shutdown=ShutdownFlag, debug=DebugFlag)
    def __init__(self, modules, events, ticks, display, debugger, keyboard, demo, statemanager, shutdown, debug):
        """Constructor."""
        configure_logging(debug=debug.value)
        logger.info('Initializing..')

        self.debug          = debug
        self.shutdown       = shutdown

        self.modules        = modules
        self.events         = events
        self.statemanager   = statemanager

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    binder.bind(Akurra, scope=singleton)

    # General
    binder.bind(DebugFlag, to=Value('B', DEBUG))
    binder.bind(ShutdownFlag, to=Event())

    # Modules
    binder.bind(ModuleManager, scope=singleton)
    binder.bind(ModuleEntryPointGroup, to='akurra.modules')

    # Display
    binder.bind(DisplayManager, scope=singleton)
    binder.bind(DisplayResolution, to=[0, 0])
    binder.bind(DisplayFlags, to=pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE)
    binder.bind(DisplayMaxFPS, to=60)
    binder.bind(DisplayCaption, to='Akurra DEV')
    binder.bind(DisplayClock, to=pygame.time.Clock, scope=singleton)
    binder.bind(DisplayScreen, to=create_screen, scope=singleton)

    # Event manager
    binder.bind(EventManager, scope=singleton)
    binder.bind(EventPollTimeout, to=0.1)

    # Ticks
    binder.bind(TicksManager, scope=singleton)

    # Debug
    binder.bind(DebugManager, scope=singleton)

    # Keyboard
    binder.bind(KeyboardManager, scope=singleton)

<<<<<<< HEAD
    # State manager
    binder.bind(GameStateManager, scope=singleton)
=======
    # Assets
    binder.bind(AssetManager, scope=singleton)
    binder.bind(AssetBasePath, to='assets')

    # Demo
    # @TODO Remove
    binder.bind(DemoManager, scope=singleton)
>>>>>>> 25b3d43ab08d5de07f8affd6bc82683d5ea69197


def main():
    """Main entry point."""
    pygame.init()

    container = Injector(build_container)
    container.get(Akurra).start()

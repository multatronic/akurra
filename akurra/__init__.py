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

from akurra.events import EventManager, TickEvent, ShutdownEvent
from akurra.modules import ModuleManager
from akurra.logger import configure_logging

from akurra.display import DisplayManager, create_screen
from akurra.debug import DebugManager
from akurra.keyboard import KeyboardManager
from akurra.states import StateManager
from akurra.assets import AssetManager

from akurra.demo import DemoIntroScreen, DemoGameState


DEBUG = 'debug' in sys.argv
os.chdir(os.path.dirname(os.path.dirname(__file__)))
logger = logging.getLogger(__name__)


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    # Overlord
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

    # Events
    binder.bind(EventManager, scope=singleton)

    # Debug
    binder.bind(DebugManager, scope=singleton)

    # Keyboard
    binder.bind(KeyboardManager, scope=singleton)

    # State manager
    binder.bind(StateManager, scope=singleton)

    # Assets
    binder.bind(AssetManager, scope=singleton)
    binder.bind(AssetBasePath, to='assets')

    # Demo
    binder.bind(DemoIntroScreen)
    binder.bind(DemoGameState)


class Akurra:

    """Base game class."""

    def start(self):
        """Start."""
        logger.debug('Starting..')

        self.modules.load()
        self.modules.start()

        # create states, set introscreen as initial state
        game_realm = self.container.get(DemoGameState)
        intro_screen = self.container.get(DemoIntroScreen)

        self.states.add(intro_screen)
        self.states.add(game_realm)
        self.states.set_active(intro_screen)

        while not self.shutdown.is_set():
            self.events.poll()

            delta_time = self.clock.tick(self.max_fps) / 1000
            self.events.dispatch(TickEvent(delta_time=delta_time))

            pygame.time.wait(3)

    def stop(self):
        """Stop."""
        logger.info('Stopping..')
        self.shutdown.set()

        self.modules.stop()
        self.modules.unload()

        self.states.close()

    def on_shutdown(self, event):
        """Handle a shutdown event."""
        logger.debug('Received shutdown event, shutting down')
        self.stop()

    def handle_signal(self, signum, frame):
        """Handle a shutdown signal."""
        logger.debug('Received signal, shutting down [signal=%s]', signum)
        self.stop()

    @inject(modules=ModuleManager, events=EventManager, display=DisplayManager,
            debugger=DebugManager, keyboard=KeyboardManager, states=StateManager,
            clock=DisplayClock, max_fps=DisplayMaxFPS,
            shutdown=ShutdownFlag, debug=DebugFlag)
    def __init__(self, modules, events, display, debugger, keyboard, states, clock, max_fps, shutdown, debug):
        """Constructor."""
        configure_logging(debug=debug.value)
        logger.info('Initializing..')

        self.debug = debug
        self.shutdown = shutdown

        self.modules = modules
        self.events = events
        self.states = states

        self.clock = clock
        self.max_fps = max_fps

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        self.events.register(ShutdownEvent, self.on_shutdown)


def main():
    """Main entry point."""
    pygame.init()

    container = Injector(build_container)

    akurra = container.get(Akurra)
    akurra.container = container
    akurra.start()

"""Main module."""
import os
import sys
import pygame
import signal
import logging
import functools

from threading import Event
from multiprocessing import Value
from injector import Injector, inject, singleton

from ballercfg import ConfigurationManager

from .locals import *  # noqa

from .events import EventManager, TickEvent
from .modules import ModuleManager
from .logger import configure_logging

from .display import DisplayManager
from .debug import DebugManager
from .keyboard import KeyboardManager
from .states import StateManager
from .assets import AssetManager
from .entities import EntityManager
from .items import ItemManager
from .audio import AudioManager
from .utils import get_data_path

from .demo import DemoIntroScreen, DemoGameState


DEBUG = 'debug' in sys.argv
os.chdir(os.path.dirname(os.path.dirname(__file__)))
logger = logging.getLogger(__name__)
container = None


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    # Overlord
    binder.bind(Akurra, scope=singleton)

    # General
    binder.bind(DebugFlag, to=Value('B', DEBUG))
    binder.bind(ShutdownFlag, to=Event())

    # Configuration
    CFG_FILES = [
        os.path.expanduser('~/.config/akurra/config.yml'),
        get_data_path('entities.yml')
    ]

    # If the directories or files don't exist, create them
    for f in CFG_FILES:
        if not os.path.isfile(f):
            os.makedirs(os.path.dirname(f))
            with open(f, 'a+'):
                pass

    cfg = ConfigurationManager.load(CFG_FILES)
    binder.bind(Configuration, to=cfg)

    # Modules
    binder.bind(ModuleManager, scope=singleton)
    binder.bind(ModuleEntryPointGroup, to=cfg.get('akurra.modules.entry_point_group', 'akurra.modules'))

    # Display
    binder.bind(DisplayManager, scope=singleton)
    binder.bind(DisplayResolution, to=cfg.get('akurra.display.resolution', [0, 0]))
    binder.bind(DisplayMaxFPS, to=cfg.get('akurra.display.max_fps', 60))
    binder.bind(DisplayCaption, to=cfg.get('akurra.display.caption', 'Akurra DEV'))

    flags = cfg.get('akurra.display.flags', ['DOUBLEBUF', 'HWSURFACE', 'RESIZABLE'])
    flags = functools.reduce(lambda x, y: x | y, [getattr(pygame, x) for x in flags])

    binder.bind(DisplayFlags, to=flags)
    binder.bind(DisplayClock, to=pygame.time.Clock, scope=singleton)

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
    binder.bind(AssetBasePath, to=cfg.get('akurra.assets.base_path', 'assets'))

    # Entities
    binder.bind(EntityManager, scope=singleton)
    binder.bind(EntitySystemEntryPointGroup, to=cfg.get('akurra.entities.systems.entry_point_group',
                                                        'akurra.entities.systems'))
    binder.bind(EntityComponentEntryPointGroup, to=cfg.get('akurra.entities.components.entry_point_group',
                                                           'akurra.entities.components'))
    binder.bind(EntityTemplates, to=cfg.get('akurra.entities.templates', {}))

    # Audio
    binder.bind(AudioManager, scope=singleton)

    # Items
    binder.bind(ItemManager, scope=singleton)

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

        self.entities.start()

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

            pygame.time.wait(5)

        self.stop()

    def stop(self):
        """Stop."""
        logger.info('Stopping..')
        self.shutdown.set()

        self.entities.stop()

        self.modules.stop()
        self.modules.unload()

        self.states.close()

    def handle_signal(self, signum, frame):
        """Handle a shutdown signal."""
        logger.debug('Received signal, setting shutdown flag [signal=%s]', signum)
        self.shutdown.set()

    @inject(modules=ModuleManager, events=EventManager, display=DisplayManager,
            debugger=DebugManager, keyboard=KeyboardManager, states=StateManager,
            entities=EntityManager,
            clock=DisplayClock, max_fps=DisplayMaxFPS,
            shutdown=ShutdownFlag, debug=DebugFlag)
    def __init__(self, modules, events, display, debugger, keyboard, states, entities, clock, max_fps, shutdown,
                 debug):
        """Constructor."""
        configure_logging(debug=debug.value)
        logger.info('Initializing..')

        self.debug = debug
        self.shutdown = shutdown

        self.modules = modules
        self.events = events
        self.entities = entities
        self.states = states

        self.clock = clock
        self.max_fps = max_fps

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)


def main():
    """Main entry point."""
    # frequency, size, channels, buffersize
    pygame.mixer.pre_init(44100, 16, 2, 4096)
    pygame.init()

    global container
    container = Injector(build_container)

    akurra = container.get(Akurra)
    akurra.container = container
    akurra.start()

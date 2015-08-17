"""Main module."""
import os
import sys
import pygame
import signal
import logging
import functools
import argparse

from threading import Event
from multiprocessing import Value
from injector import Injector, inject, singleton

from ballercfg import ConfigurationManager

from .locals import *  # noqa

from .events import EventManager, TickEvent
from .modules import ModuleManager
from .logger import configure_logging

from .display import DisplayManager
from .states import StateManager, SplashScreen
from .assets import AssetManager
from .entities import EntityManager
from .session import SessionManager
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
    # Parse command-line arguments and set required variables
    parser = argparse.ArgumentParser(description='Run the Akurra game engine.')
    parser.add_argument('--log-level', type=str, choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'INSANE'],
                        default='INFO')
    args = parser.parse_args()

    binder.bind(ArgLogLevel, to=args.log_level)

    # Overlord
    binder.bind(Akurra, scope=singleton)

    # General
    binder.bind(ShutdownFlag, to=Event())
    binder.bind(DebugFlag, to=Value('B', DEBUG))

    # Configuration
    CFG_FILES = [
        os.path.expanduser('~/.config/akurra/config.yml'),
    ]

    # If the directories or files don't exist, create them
    for f in CFG_FILES:
        if not os.path.isfile(f):
            os.makedirs(os.path.dirname(f))
            with open(f, 'a+'):
                pass

    cfg = ConfigurationManager.load(CFG_FILES + [get_data_path('*.yml')])
    binder.bind(Configuration, to=cfg)

    # Modules
    binder.bind(ModuleManager, scope=singleton)
    binder.bind(ModuleEntryPointGroup, to=cfg.get('akurra.modules.entry_point_group', 'akurra.modules'))

    # Display
    binder.bind(DisplayManager, scope=singleton)
    binder.bind(DisplayResolution, to=cfg.get('akurra.display.resolution', [0, 0]))
    binder.bind(DisplayMaxFPS, to=cfg.get('akurra.display.max_fps', 60))
    binder.bind(DisplayCaption, to=cfg.get('akurra.display.caption', 'Akurra DEV'))
    binder.bind(DisplayClock, to=pygame.time.Clock, scope=singleton)

    flags = cfg.get('akurra.display.flags', ['DOUBLEBUF', 'HWSURFACE', 'RESIZABLE'])
    flags = functools.reduce(lambda x, y: x | y, [getattr(pygame, x) for x in flags])
    binder.bind(DisplayFlags, to=flags)

    # Events
    binder.bind(EventManager, scope=singleton)

    # State manager
    binder.bind(StateManager, scope=singleton)

    # Session
    binder.bind(SessionManager, scope=singleton)
    binder.bind(SessionFilePath, to=cfg.get('akurra.session.file_path', '~/.config/akurra/session/main.sav'))

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
    binder.bind(AudioMasterVolume, to=cfg.get('akurra.audio.master.volume', 0.75))
    binder.bind(AudioBackgroundMusicVolume, to=cfg.get('akurra.audio.background_music.volume', 1.0))
    binder.bind(AudioSpecialEffectsVolume, to=cfg.get('akurra.audio.special_effects.volume', 1.0))

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
        self.entities.start()
        self.modules.start()

        # create states, set introscreen as initial state
        game_realm = self.container.get(DemoGameState)
        intro_screen = self.container.get(DemoIntroScreen)
        splash_screen = SplashScreen(image='graphics/logos/multatronic.png', next=intro_screen)
        self.states.add(splash_screen)
        self.states.add(intro_screen)
        self.states.add(game_realm)

        self.states.set_active(splash_screen)

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

        self.modules.stop()
        self.entities.stop()
        self.modules.unload()

        self.states.close()

    def handle_signal(self, signum, frame):
        """Handle a shutdown signal."""
        logger.debug('Received signal, setting shutdown flag [signal=%s]', signum)
        self.shutdown.set()

    @inject(modules=ModuleManager, events=EventManager, display=DisplayManager,
            states=StateManager,
            entities=EntityManager, log_level=ArgLogLevel,
            clock=DisplayClock, max_fps=DisplayMaxFPS,
            shutdown=ShutdownFlag)
    def __init__(self, modules, events, display, states, entities, clock, max_fps, shutdown,
                 log_level):
        """Constructor."""
        configure_logging(log_level=log_level)
        logger.info('Initializing..')

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

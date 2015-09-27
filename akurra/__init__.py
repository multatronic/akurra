"""Main module."""
import os
import pygame
import signal
import logging
import argparse

from threading import Event
from multiprocessing import Value
from injector import Injector, singleton

from ballercfg import ConfigurationManager

from .locals import *  # noqa

from .events import EventManager, TickEvent
from .modules import ModuleLoader
from .logger import configure_logging

from .states import StateManager
from .assets import AssetManager
from .entities import EntityManager
from .session import SessionManager
from .utils import get_data_path


os.chdir(os.path.dirname(os.path.dirname(__file__)))
logger = logging.getLogger(__name__)
container = None


def build_container(binder):
    """Build a service container by binding dependencies to an injector."""
    # General flags and shared objects
    binder.bind(ShutdownFlag, to=Event())
    binder.bind(DisplayClock, to=pygame.time.Clock())

    # Core components
    binder.bind(EventManager, scope=singleton)
    binder.bind(EntityManager, scope=singleton)
    binder.bind(AssetManager, scope=singleton)
    binder.bind(SessionManager, scope=singleton)
    binder.bind(StateManager, scope=singleton)


class Akurra:

    """Base game class."""

    def __init__(self, game, log_level='INFO', debug=False):
        """Constructor."""
        # Set up container
        global container
        self.container = container = Injector(build_container)

        self.game = game
        self.log_level = log_level
        self.debug = debug

        # Load configuration
        cfg_files = [
            os.path.expanduser('~/.config/akurra/*.yml'),
            os.path.expanduser('~/.config/akurra/games/%s/*.yml' % self.game)
        ]

        cfg = ConfigurationManager.load([get_data_path('*.yml')] + cfg_files)
        self.container.binder.bind(Configuration, to=cfg)

        self.container.binder.bind(DebugFlag, to=Value('b', self.debug))
        self.container.binder.bind(Akurra, to=self)

        # Start pygame (+ audio frequency, size, channels, buffersize)
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.init()

        configure_logging(log_level=self.log_level)
        logger.info('Initializing..')

        self.configuration = self.container.get(Configuration)
        self.shutdown = self.container.get(ShutdownFlag)
        self.clock = self.container.get(DisplayClock)

        self.modules = ModuleLoader(
            group=self.configuration.get('akurra.modules.entry_point_group', 'akurra.modules'),
            whitelist=self.configuration.get('akurra.modules.whitelist', None),
            blacklist=self.configuration.get('akurra.modules.blacklist', None),
        )

        self.games = ModuleLoader(
            group=self.configuration.get('akurra.games.entry_point_group', 'akurra.games'),
        )

        self.events = self.container.get(EventManager)
        self.entities = self.container.get(EntityManager)
        self.states = self.container.get(StateManager)
        self.assets = self.container.get(AssetManager)
        self.session = self.container.get(SessionManager)

        self.loop_wait_millis = self.configuration.get('akurra.core.loop_wait_millis', 5)
        self.max_fps = self.configuration.get('akurra.display.max_fps', 60)

        # Handle shutdown signals properly
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def start(self):
        """Start."""
        logger.debug('Starting..')

        # Reset shutdown flag
        self.shutdown.clear()

        self.modules.load()
        self.entities.start()
        self.modules.start()

        try:
            # Attempt to fetch and launch game
            self.games.load_single(self.game)
            game = self.games.modules.get(self.game)
            game.play()
        except AttributeError:
            raise ValueError('No game module named "%s" exists!' % self.game)

        while not self.shutdown.is_set():
            # Pump/handle events (both pygame and akurra)
            self.events.poll()

            # Calculate time (in seconds) that has passed since last tick
            delta_time = self.clock.tick(self.max_fps) / 1000

            # Dispatch tick
            self.events.dispatch(TickEvent(delta_time=delta_time))

            # Wait a bit to lower CPU usage
            pygame.time.wait(self.loop_wait_millis)

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


def main():
    """Main entry point."""
    # Parse command-line arguments and set required variables
    parser = argparse.ArgumentParser(description='Run the Akurra game engine.')
    parser.add_argument('--log-level', type=str, default='INFO', help='set the log level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'INSANE'])
    parser.add_argument('-d', '--debug', action='store_true', help='toggle debugging')
    parser.add_argument('-g', '--game', required=True, type=str, help='game to run')
    args = parser.parse_args()

    akurra = Akurra(game=args.game, log_level=args.log_level, debug=args.debug)
    akurra.start()


if __name__ == '__main__':
    main()

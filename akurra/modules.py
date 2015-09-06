"""Modules module."""
import sys
import logging
from pkg_resources import iter_entry_points

from .utils import ContainerAware
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class Module(ContainerAware):

    """Base module."""

    # Other modules this module depends on
    dependencies = []

    def __init__(self):
        """Constructor."""

    def start(self):
        """Start the module."""
        pass

    def stop(self):
        """Stop the module."""
        pass


class Game(Module):

    """
    Base game module.

    A game module is a module of which only one can be running at a time.
    It is responsible for loading game assets, adding and running game states and the like.

    """

    def play(self):
        """Start the game."""
        raise NotImplementedError('A game must implement a play method!')


class ModuleManager(ContainerAware):

    """The ModuleManager manages the loading, unloading, etc. of modules."""

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing ModuleManager')

        self.configuration = self.container.get(Configuration)
        self.group = self.configuration.get('akurra.modules.entry_point.group', 'akurra.modules')
        self.modules = {}

    def load_single(self, name):
        """
        Load a single module.

        :param name: A string identifier for a module.

        """
        logger.debug('Loading module "%s"', name)

        if name in self.modules:
            logger.debug('Module "%s" already loaded, skipping', name)
            return

        for entry_point in iter_entry_points(group=self.group, name=name):
            module_class = entry_point.load()

            # If the module has any dependencies, ensure those are loaded first
            if module_class.dependencies:
                [self.load_single(x) for x in module_class.dependencies]

            self.modules[name] = module_class()

            # Add the module to the container
            self.container.binder.bind(self.modules[name].__class__, to=self.modules[name])

        logger.debug('Module "%s" loaded', name)

    def unload_single(self, name):
        """
        Unload a single module.

        :param name: A string identifier for a module.

        """
        logger.debug('Unloading module "%s"', name)

        # Remove the module from the python interpreter
        sys.modules.pop(self.modules[name].__module__, None)

        del self.modules[name]
        self.modules.pop("", None)
        self.modules.pop(None, None)

        logger.debug('Unloaded module "%s"', name)

    def load(self):
        """Load all modules."""
        logger.debug('Loading all modules')
        [self.load_single(x.name) for x in iter_entry_points(group=self.group)]

    def unload(self):
        """Unload all modules."""
        logger.debug('Unloading all modules')

        # We need to copy the list of names, because unloading a module
        # removes it from the modules dict
        [self.unload_single(x) for x in list(self.modules.keys())]

    def start_single(self, name):
        """
        Start a single module.

        :param name: A string identifier for a module.

        """
        logger.debug('Starting module "%s"', name)
        self.modules[name].start()
        logger.debug('Module "%s" started', name)

    def stop_single(self, name):
        """
        Stop a single module.

        :param name: A string identifier for a module.

        """
        logger.debug('Stopping module "%s"', name)
        self.modules[name].stop()
        logger.debug('Module "%s" stopped', name)

    def start(self):
        """Start all modules."""
        logger.debug('Starting all modules')
        [self.start_single(x) for x in self.modules.keys()]

    def stop(self):
        """Stop all modules."""
        logger.debug('Stopping all modules')
        [self.stop_single(x) for x in self.modules.keys()]

"""States module."""
import logging
from akurra.utils import fqcn
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class StateManager:

    """Manager class for handling state transitions (e.g. to go from main menu to playing game)."""

    def __init__(self,):
        """Constructor."""
        logger.debug('Initializing StateManager')

        self.active = None
        self.states = {}

    def add(self, state):
        """Add a state and corresponding handler."""
        self.states[state] = 1
        logger.debug('Added state "%s"', fqcn(state.__class__))

    def remove(self, state):
        """Remove a state."""
        self.states.pop(state, None)

        if state == self.active:
            self.active = None

        logger.debug('Removed state "%s"', fqcn(state.__class__))

    def find_one_by_class_name(self, class_name):
        """
        Find and return a state by its class name.

        :param class_name: Fully qualified class name in package.module.name format.

        """
        for state in self.states:
            if fqcn(state.__class__) == class_name:
                return state

    def set_active(self, state):
        """Set the active state."""
        logger.debug('Setting active state to "%s"', fqcn(state.__class__))

        if self.active:
            self.active.disable()

        self.active = state
        self.active.enable()

    def close(self):
        """Shut down the state manager, performing cleanup if needed."""
        logger.debug('Shutting down StateManager')

        if self.active:
            self.active.disable()


class GameState:

    """Base game state class."""

    def __init__(self):
        """Constructor."""

    def enable():
        """Enable this state and perform warmup if needed."""
        raise NotImplementedError('This method should be implemented by a descendant!')

    def disable():
        """Disable this state and perform cleanup if needed."""
        raise NotImplementedError('This method should be implemented by a descendant!')

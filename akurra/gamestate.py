"""Gamestate module."""
import logging
from injector import inject
from abc import ABCMeta, abstractmethod
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class GameStateManager:

    """Manager class for handling state transitions (e.g. to go from main menu to playing game)."""

    @inject(debug=DebugFlag)
    def __init__(self, debug):
        """Constructor."""
        logger.debug('Initializing GameStateManager')

        self.debug = debug
        self.currentState = None
        self.states = {}

    def add_state(self, state):
        """Add a state and corresponding handler."""
        logger.debug('Adding state %s', state.name)

        name = state.name.upper()
        self.states[name] = state

    def set_current_state(self, name):
        """Set the state of the FSM."""
        logger.debug('Setting current state as %s', name)
        if self.currentState is not None:
            self.states[self.currentState].stop()

        self.currentState = name.upper()
        self.states[self.currentState].start()

    def stop(self):
        """Stop the current state."""
        if self.currentState is not None:
            self.states[self.currentState].stop()


class GameState:

    """An abstract baseclass for gamestates."""

    __metaclass__ = ABCMeta

    # TODO: enforcing overrides for start/stop doesn't work for some reason?
    def __init__(self, name, statemanager):
        """Constructor."""
        self.statemanager = statemanager
        self.name = name

    def getName(self):
        """Retrieve the state name."""
        return self.name

    @abstractmethod
    def start():
        """Set up the gamestate (register events and such)."""

    @abstractmethod
    def stop():
        """Stop the gamestate (unregister events and such). """

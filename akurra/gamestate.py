"""Gamestate module."""
import logging
from injector import inject
from akurra.events import EventManager
from akurra.display import DisplayManager
from akurra.keyboard import KeyboardManager
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

    def add_state(self, name):
        """Add a state and corresponding handler."""
        logger.debug('Adding state %s', name)

        name = name.upper()
        self.handlers[name] = handler

    def set_currentState(self, name):
        """Set the state of the FSM."""
        logger.debug('Setting current state as %s', name)

        self.currentState = name.upper()

    def handle(self):
        """Run the FSM, starting from initial state."""
        logger.debug('Running finite state machine')

        # call the handler for the current state
        # which will set the new value for current state if necessary
        try:
            self.currentState.handle()
        except:
            raise InitializationError("Could not retrieve a valid state handler!\
             Did you forget to set the initial state with set_currentState?")


class GameState:

    """A baseclass for gamestates."""

    @inject(statemanager=GameStateManager, keyboard=KeyboardManager, events=EventManager,
            display=DisplayManager, clock=DisplayClock, debug=DebugFlag)
    def __init__(self, keyboard, events, display, clock, debug, statemanager):
        """Constructor."""
        self.keyboard     = keyboard
        self.debug        = debug
        self.events       = events
        self.clock        = clock
        self.display      = display
        self.statemanager = statemanager

    def handle():
        logger.debug('state handle function called');

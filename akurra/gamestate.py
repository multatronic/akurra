"""Gamestate module."""
import logging
import pygame
from injector import inject
from akurra.logging import configure_logging
from akurra.events import EventManager
from akurra.display import FrameRenderCompletedEvent, DisplayManager, DisplayObject
from akurra.keyboard import KeyboardManager
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class GameStateManager:

    """Manager class for handling state transitions (e.g. to go from main menu to playing game)."""

    @inject(keyboard=KeyboardManager, events=EventManager, display=DisplayManager, clock=DisplayClock, debug=DebugFlag)
    def __init__(self, keyboard, events, display, clock, debug):
        """Constructor."""
        logger.debug('Initializing GameStateManager')

        self.keyboard     = keyboard
        self.debug        = debug
        self.events       = events
        self.clock        = clock
        self.display      = display
        self.currentState = None
        self.handlers     = {}

    def add_state(self, name, handler):
        """Add a state and corresponding handler"""
        logger.debug('Adding state %s', name)

        name = name.upper()
        self.handlers[name] = handler

    def set_startState(self, name):
        """Set the initial state of the FSM"""
        logger.debug('Setting initial state as %s', name)

        self.startState = name.upper()

    def run(self):
        """Run the FSM, starting from initial state"""
        logger.debug('Running finite state machine')

        # call the handler for the current state while the game is running
        # which will return the new value for current state
        while True:
            # TODO break out this loop somehow, preferably by listening to some quit event
            try:
                handler = self.handlers[self.currentState]
                handler()
            except:
                raise InitializationError("Could not retrieve a valid state handler! Did you forget to call set_startState?")
                logger.debug


"""Gamestate module."""
import logging
import pygame
from injector import inject
from abc import ABCMeta, abstractmethod
from akurra.display import FrameRenderCompletedEvent, SurfaceDisplayLayer
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
            self.states[currentState.name.upper()].stop()

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


class DemoIntroScreen(GameState):

    """Tester class for gamestates."""

    def __init__(self, gamestatemanager, display, keyboard, events):
        """Constructor."""
        GameState.__init__(self, "introscreen", gamestatemanager)
        logger.info("Initialized state %s", self.name)

        self.display = display
        self.keyboard = keyboard
        self.events = events
        self.font = pygame.font.SysFont('monospace', 14)

    def start(self):
        """Set up the gamestate."""
        logger.info("State %s is starting - shit's about to go down!", self.name)

        # listen for any key press
        self.keyboard.register(pygame.K_F10, self.transition_to_game)

        # draw stuff on screen when frame render is completed
        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.layer = SurfaceDisplayLayer(flags=pygame.SRCALPHA, z_index=9999, display=self.display)
        self.display.add_layer(self.layer)

    def transition_to_game(self, event):
        """Transition to play game state."""
        logger.info("This is normally when the state transition would take place")

    def stop(self):
        """Stop the gamestate."""
        logger.info("State %s is stopping", self.name)

    def on_frame_render_completed(self, event):
        """Handle a frame render completion."""
        self.layer.surface.fill([90, 10, 10, 200])

        info = pygame.display.Info()

        text = [
            "TIS BUT AN INTROSCREEN!",
            "---press the any key---",
            ]

        offset_x = 200
        offset_y = 200
        line_height = 15

        for t in text:
            self.layer.surface.blit(self.font.render(t, 1, (255, 255, 0)), [offset_x, offset_y])
            offset_y += line_height

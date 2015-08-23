"""States module."""
import logging
import pygame

from .display import DisplayLayer, DisplayModule
from .events import EventManager, TickEvent
from .assets import AssetManager
from .utils import fqcn, ContainerAware
from .locals import *  # noqa


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


class GameState(ContainerAware):

    """Base game state class."""

    def __init__(self):
        """Constructor."""

    def enable(self):
        """Enable the game state."""
        raise NotImplementedError('This method should be implemented by a descendant!')

    def disable(self):
        """Disable the game state."""
        raise NotImplementedError('This method should be implemented by a descendant!')


class SplashScreen(GameState):

    """Base splash screen game state."""

    def __init__(self, image, next, fade_duration=2, show_duration=4, background_color=[0, 0, 0]):
        """
        Constructor.

        :param image: Path to the image to show.
        :param next: Game state to activate after the splash screen is disabled.
        :param fade_duration: Duration (in seconds) the fade animation should last.
        :param show_duration: Duration (in seconds) during which the image should be shown, after fading.

        """
        from .keyboard import KeyboardModule

        super().__init__()

        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.assets = self.container.get(AssetManager)
        self.states = self.container.get(StateManager)
        self.keyboard = self.container.get(KeyboardModule)

        self.layer = DisplayLayer(flags=pygame.SRCALPHA)
        self.image = self.assets.get_image(image, alpha=False)

        self.next = next

        self.fade_duration = fade_duration
        self.show_duration = show_duration
        self.background_color = background_color

    def enable(self):
        """Enable the game state."""
        self.fade_counter = 0
        self.show_counter = 0

        self.display.add_layer(self.layer)
        self.events.register(TickEvent, self.on_tick)
        self.keyboard.add_action_listener('splash_screen_skip', self.next_state)

    def disable(self):
        """Disable the game state."""
        self.keyboard.remove_action_listener(self.next_state)
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def next_state(self, *args):
        """Continue onward to the next game state."""
        self.states.set_active(self.next)

    def on_tick(self, event):
        """Handle a tick event."""
        alpha_value = (self.fade_counter / self.fade_duration) * 255

        if alpha_value > 255:
            alpha_value = 510 - alpha_value

        if self.fade_counter > self.fade_duration and self.show_counter < self.show_duration:
            self.show_counter += event.delta_time
        else:
            self.fade_counter += event.delta_time

        if self.fade_counter > (2 * self.fade_duration):
            self.next_state()

        surface = self.layer.surface
        surface.fill(self.background_color)

        self.image.set_alpha(alpha_value)
        surface.blit(self.image, [(surface.get_width() / 2) - (self.image.get_width() / 2),
                                  (surface.get_height() / 2) - (self.image.get_height() / 2)])

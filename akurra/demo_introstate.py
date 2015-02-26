"""Introscreen demo module."""
import pygame
import logging
from akurra.gamestate import GameState
from akurra.display import FrameRenderCompletedEvent, SurfaceDisplayLayer

logger = logging.getLogger(__name__)


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
        self.keyboard.register(pygame.K_SPACE, self.transition_to_game)

        # draw stuff on screen when frame render is completed
        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.layer = SurfaceDisplayLayer(flags=pygame.SRCALPHA, z_index=9999, display=self.display)
        self.display.add_layer(self.layer)

    def transition_to_game(self, event):
        """Transition to play game state."""
        logger.info("This is normally when the state transition would take place")
        self.statemanager.set_current_state("gamescreen")

    def stop(self):
        """Stop the gamestate."""
        logger.info("State %s is stopping", self.name)

        self.events.unregister(self.on_frame_render_completed)
        self.display.remove_layer(self.layer)

    def on_frame_render_completed(self, event):
        """Handle a frame render completion."""
        self.layer.surface.fill([90, 10, 10, 200])

        text = [
            "TIS BUT AN INTROSCREEN!",
            "--press the space bar--",
            ]

        offset_x = 800
        offset_y = 500
        line_height = 15

        for t in text:
            self.layer.surface.blit(self.font.render(t, 1, (255, 255, 0)), [offset_x, offset_y])
            offset_y += line_height

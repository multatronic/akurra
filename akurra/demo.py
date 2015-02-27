"""Demo module."""
import pygame
import logging
from injector import inject
from akurra.assets import AssetManager
from akurra.display import DisplayManager, ScrollingMapDisplayLayer, FrameRenderCompletedEvent, SurfaceDisplayLayer
from akurra.events import EventManager, ShutdownEvent
from akurra.keyboard import KeyboardManager
from akurra.entities import GameEntity
from akurra.states import GameState, StateManager


logger = logging.getLogger(__name__)


class DemoIntroScreen(GameState):

    """Tester class for gamestates."""

    @inject(display=DisplayManager, keyboard=KeyboardManager, events=EventManager, states=StateManager)
    def __init__(self, display, keyboard, events, states):
        """Constructor."""
        super().__init__()

        self.display = display
        self.keyboard = keyboard
        self.events = events
        self.states = states
        self.font = pygame.font.SysFont('monospace', 14)

    def enable(self):
        """Set up the gamestate."""
        # listen for certain key presses
        self.keyboard.register(pygame.K_SPACE, self.on_key_down)

        # draw stuff on screen when frame render is completed
        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.layer = SurfaceDisplayLayer(display=self.display)
        self.display.add_layer(self.layer)

    def disable(self):
        """Stop the gamestate."""
        self.events.unregister(self.on_frame_render_completed)
        self.keyboard.unregister(self.on_key_down)
        self.display.remove_layer(self.layer)

    def on_key_down(self, event):
        """Handle a key press."""
        self.states.set_active(self.states.find_one_by_class_name('akurra.demo.DemoGameState'))

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


class DemoGameState(GameState):

    """Temporary demo middleware."""

    @inject(assets=AssetManager, display=DisplayManager, keyboard=KeyboardManager, events=EventManager)
    def __init__(self, assets, display, keyboard, events):
        """Constructor."""
        super().__init__()

        self.events = events
        self.display = display
        self.assets = assets
        self.keyboard = keyboard

    def on_key_down(self, event):
        """Handle a key press."""
        # exit the game if escape is pressed, otherwise move the player
        if event.key is pygame.K_ESCAPE:
            logger.debug("Escape pressed during demo! Dispatching shutdown event...")
            self.events.dispatch(ShutdownEvent())
        else:
            key_velocity = self.key_velocities[event.key]
            self.player.velocity[key_velocity[0]] = key_velocity[1]

    def on_key_up(self, event):
        """Handle a key release."""
        key_velocity = self.key_velocities[event.key]
        self.player.velocity[key_velocity[0]] = 0

    def enable(self):
        """Initialize the gamestate."""
        self.tmx_data = self.assets.get_tmx_data('pyscroll_demo/grasslands.tmx')
        self.layer = ScrollingMapDisplayLayer(self.tmx_data, default_layer=2, display=self.display)
        self.display.add_layer(self.layer)

        self.image = self.assets.get_image('pyscroll_demo/hero.png')
        self.player = GameEntity(self.image)
        self.player.position = self.layer.map_layer.rect.center

        self.layer.group.add(self.player)
        self.layer.center = self.player

        player_speed = 400

        self.key_velocities = {
            pygame.K_UP: [1, -player_speed],
            pygame.K_DOWN: [1, player_speed],
            pygame.K_LEFT: [0, -player_speed],
            pygame.K_RIGHT: [0, player_speed]
        }

        pygame.key.set_repeat(100, 100)

        # register for all relevant keys
        [self.keyboard.register(x, self.on_key_down, event_type=pygame.KEYDOWN) for x in self.key_velocities.keys()]
        [self.keyboard.register(x, self.on_key_up, event_type=pygame.KEYUP) for x in self.key_velocities.keys()]
        self.keyboard.register(pygame.K_ESCAPE, self.on_key_down)

    def disable(self):
        """Stop the gamestate."""
        self.keyboard.unregister(self.on_key_down)
        self.keyboard.unregister(self.on_key_up)

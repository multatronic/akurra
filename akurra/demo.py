"""Demo module."""
import pygame
import logging
from .assets import AssetManager
from .display import (ScrollingMapEntityDisplayLayer,
                      FrameRenderCompletedEvent, DisplayModule, DisplayLayer)
from .events import EventManager
from .entities import EntityManager, EntityInput
from .session import SessionManager
from .keyboard import KeyboardModule
from .states import GameState, StateManager
from .audio import AudioModule
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class DemoIntroScreen(GameState):

    """Tester class for gamestates."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.display = self.container.get(DisplayModule)
        self.keyboard = self.container.get(KeyboardModule)
        self.events = self.container.get(EventManager)
        self.states = self.container.get(StateManager)
        self.font = pygame.font.SysFont('monospace', 14)

    def enable(self):
        """Set up the gamestate."""
        # listen for certain key presses
        self.keyboard.add_listener(pygame.K_SPACE, self.on_key_down)

        # draw stuff on screen when frame render is completed
        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.layer = DisplayLayer()
        self.display.add_layer(self.layer)

    def disable(self):
        """Stop the gamestate."""
        self.events.unregister(self.on_frame_render_completed)
        self.keyboard.remove_listener(self.on_key_down)
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

        size = self.layer.surface.get_rect().center

        offset_x = size[0] - 90
        offset_y = size[1] - 15
        line_height = 15

        for t in text:
            self.layer.surface.blit(self.font.render(t, 1, (255, 255, 0)), [offset_x, offset_y])
            offset_y += line_height


class DemoGameState(GameState):

    """Temporary demo middleware."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.audio = self.container.get(AudioModule)
        self.assets = self.container.get(AssetManager)
        self.entities = self.container.get(EntityManager)
        self.session = self.container.get(SessionManager)
        self.keyboard = self.container.get(KeyboardModule)
        self.shutdown = self.container.get(ShutdownFlag)

    def on_quit(self, event):
        """Handle quitting."""
        self.shutdown.set()

    def enable(self):
        """Initialize the gamestate."""
        self.keyboard.add_action_listener('game_quit', self.on_quit)

        # self.tmx_data = self.assets.get_tmx_data('pyscroll_demo/grasslands.tmx')
        self.tmx_data = self.assets.get_tmx_data('maps/urdarbrunn/map.tmx')
        self.layer = ScrollingMapEntityDisplayLayer(self.tmx_data, default_layer=2)

        self.ui_layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=101)

        self.display.add_layer(self.ui_layer)
        self.display.add_layer(self.layer)

        player = self.session.get('player')

        if not player:
            player = self.entities.find_entities_by_components(['player'])[0]
            self.session.set('player', player)

            # Set selected skill to fireball
            # @TODO Remove this
            player.components['input'].input[EntityInput.SELECTED_SKILL] = 'skill_fireball'

        self.layer.center = player

        # Load audio files
        # music
        self.audio.add_music("audio/music/magical_theme.ogg", "world01")

        # sound effects
        self.audio.add_sound("audio/sfx/sfx_step_grass.ogg", "terrain_grass")
        self.audio.add_sound("audio/sfx/sfx_step_rock.ogg", "terrain_stone")

        # create channels
        self.audio.add_channel('terrain')

        # start playing the background music
        self.audio.play_music("world01")

    def disable(self):
        """Stop the gamestate."""
        self.keyboard.remove_action_listener(self.on_quit)

"""Demo module."""
import pygame
import logging
from injector import inject
from .assets import AssetManager
from .display import (DisplayManager, EntityDisplayLayer, ScrollingMapEntityDisplayLayer,
                      FrameRenderCompletedEvent, DisplayLayer)
from .events import EventManager
from .entities import EntityManager
from .session import SessionManager
from .keyboard import KeyboardManager
from .states import GameState, StateManager
from .audio import AudioManager
from .locals import *  # noqa


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
        self.layer = DisplayLayer()
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
        self.display = self.container.get(DisplayManager)
        self.audio = self.container.get(AudioManager)
        self.assets = self.container.get(AssetManager)
        self.entities = self.container.get(EntityManager)
        self.session = self.container.get(SessionManager)
        self.keyboard = self.container.get(KeyboardManager)
        self.shutdown = self.container.get(ShutdownFlag)

    def on_quit(self, event):
        """Handle quitting."""
        logger.debug("Escape pressed during demo! Setting shutdown flag...")
        self.shutdown.set()

    def enable(self):
        """Initialize the gamestate."""
        # pygame.key.set_repeat(100, 100)
        self.keyboard.register(pygame.K_ESCAPE, self.on_quit)

        # self.tmx_data = self.assets.get_tmx_data('pyscroll_demo/grasslands.tmx')
        self.tmx_data = self.assets.get_tmx_data('maps/urdarbrunn/map.tmx')
        self.layer = ScrollingMapEntityDisplayLayer(self.tmx_data, default_layer=2)
        self.uiLayer = EntityDisplayLayer(size=[400, 250], flags=pygame.SRCALPHA, z_index=102)

        self.display.add_layer(self.layer)
        self.display.add_layer(self.uiLayer)

        self.player = self.entities.find_entities_by_components(['player'])[0]
        self.layer.center = self.player

        self.dialog = self.entities.create_entity_from_template('dialog')
        self.uiLayer.add_entity(self.dialog)
        self.dialog.remove_component(self.dialog.components['map_layer'])

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
        self.keyboard.unregister(self.on_quit)

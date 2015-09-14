"""Demo module."""
import pygame
import logging

from .assets import AssetManager
from .display import ScrollingMapEntityDisplayLayer, DisplayModule, DisplayLayer
from .events import EventManager
from .entities import EntityManager, EntityInput
from .session import SessionManager
from .modules import Game
from .states import GameState, SplashScreen, StateManager
from .menu import MenuScreen, MenuPrompt
from .input import InputModule
from .audio import AudioModule
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class DemoGame(Game):

    """Demo game."""

    def __init__(self):
        """Constructor."""
        self.states = self.container.get(StateManager)
        self.game_realm = DemoGameState()
        self.splash_screen = SplashScreen(image='graphics/logos/multatronic.png', next=self.game_realm)
        self.states.add(self.splash_screen)
        self.states.add(self.game_realm)
        self.main_menu = None
        self.init_menus()

    def init_menus(self):
        """Perform initialization of menu screens."""
        # set up the main menu screen
        self.main_menu = MenuScreen(title='Main Menu')

        # set up a quit prompt
        quit_prompt = MenuPrompt("Really quit?")
        # quit_prompt.add_option("Yes", self.game_realm.shutdown.set())
        quit_prompt.add_option("No", self.main_menu.disable_prompt())
        self.main_menu.add_prompt("quit", quit_prompt)

        # respond to escape key (meaning exit the game)
        self.main_menu.add_action_listener('game_quit', lambda x: self.main_menu.enable_prompt("quit"))
        self.states.add(self.main_menu)

    def play(self):
        """Play the game."""
        # self.states.set_active(self.splash_screen)
        self.states.set_active(self.main_menu)


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
        self.input = self.container.get(InputModule)
        self.shutdown = self.container.get(ShutdownFlag)

    def on_quit(self, event):
        """Handle quitting."""
        self.shutdown.set()

    def enable(self):
        """Initialize the gamestate."""
        self.input.add_action_listener('game_quit', self.on_quit)

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
        self.input.remove_action_listener(self.on_quit)

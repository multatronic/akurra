"""Demo module."""
import logging

from .assets import AssetManager
from .display import ScrollingTmxMapEntityDisplayLayer, DisplayModule
from .events import EventManager
from .entities import EntityManager, EntityInput
from .session import SessionManager
from .modules import Game
from .states import GameState, SplashScreen, StateManager
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

    def play(self):
        """Play the game."""
        self.states.set_active(self.splash_screen)


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

        main_map = self.session.get('map.main')

        if not main_map:
            main_map = ScrollingTmxMapEntityDisplayLayer('maps/urdarbrunn/map.tmx', default_layer=2)
            self.session.set('map.main', main_map)

        self.display.add_layer(main_map)

        player = self.session.get('player')

        # If we don't have a player, spawn one on the map
        if not player:
            player = self.entities.create_entity_from_template('player')
            player.components['position'].layer_position = [20, 20]
            self.session.set('player', player)
        else:
            self.entities.add_entity(player)

        main_map.add_entity(player)
        main_map.center = player

        # Set selected skill to fireball
        # @TODO Remove this
        player.components['input'].input[EntityInput.SELECTED_SKILL] = 'skill_fireball'

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

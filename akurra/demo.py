"""Demo module."""
import pygame
import logging
from injector import inject
from akurra.assets import AssetManager
from akurra.display import DisplayManager, ScrollingMapDisplayLayer, FrameRenderCompletedEvent, DisplayLayer
from akurra.events import EventManager
from akurra.entities import EntityManager
from akurra.keyboard import KeyboardManager
from akurra.states import GameState, StateManager
from akurra.audio import AudioManager
from akurra.locals import *  # noqa


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

    @inject(assets=AssetManager, entities=EntityManager, display=DisplayManager, keyboard=KeyboardManager,
            events=EventManager, audio=AudioManager, shutdown=ShutdownFlag)
    def __init__(self, assets, entities, display, keyboard, events, audio, shutdown):
        """Constructor."""
        super().__init__()

        self.events = events
        self.display = display
        self.audio = audio
        self.assets = assets
        self.entities = entities
        self.keyboard = keyboard
        self.shutdown = shutdown

        # keep a list mapping terrain types to sfx names
        # and the current terrain type
        self.terrain_sfx = {}
        self.current_terrain = None

        # we want some sound overlap for footsteps,
        # but with a reasonable amount of spacing,
        # so we keep track of the last time a sound effect was played
        self.last_tick = 0
        self.tick_counter = 0
        self.footstep_interval = 400

    def play_sound_effects(self, event):
        """Place a sound effect."""
        sound = self.terrain_sfx[self.current_terrain]

        # Adjust tick counters to determine if it's time to play another sound effect
        currentTick = pygame.time.get_ticks()
        tick_delta = currentTick - self.last_tick
        self.last_tick = currentTick
        self.tick_counter += tick_delta

        if(self.tick_counter >= self.footstep_interval):
            self.tick_counter = 0
            self.audio.play_sound(sound)

    def on_move_start(self, event):
        """Handle the starting of movement."""
        self.player.velocity = self.key_velocities[event.key]

        logger.debug("Player tile position: (%s - %s)", int(self.player.location[0]), int(self.player.location[1]))

        for i in range(0, len(list(self.tmx_data.visible_layers))):
            try:
                tileProps = self.tmx_data.get_tile_properties(int(self.player.location[0]),
                                                              int(self.player.location[1]), i)
                if(tileProps is not None):
                    logger.debug('Detected terrain type: %s', tileProps['terrain_type'])
                    self.current_terrain = tileProps['terrain_type']
            except KeyError:
                pass
        self.play_sound_effects(event)

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
        self.layer = ScrollingMapDisplayLayer(self.tmx_data, default_layer=2)
        self.display.add_layer(self.layer)

        self.player = self.entities.create_entity_from_template('player')
        self.player.components['position'].position = self.layer.map_layer.rect.center
        self.player.components['map_layer'].layer = self.layer
        self.entities.add_entity(self.player)

        self.layer.add_object(self.player)
        self.layer.center = self.player

        # Load audio files
        # music
        self.audio.add_music("audio/music/drums_of_the_deep.mp3", "world01")

        # sound effects
        self.audio.add_sound("audio/sfx/sfx_step_grass.ogg", "step_grass")
        self.audio.add_sound("audio/sfx/sfx_step_rock.ogg", "step_stone")

        # create channels
        self.audio.add_channel('footsteps')

        # map terrain types to sound effect names
        self.terrain_sfx["grass"] = "step_grass"
        self.terrain_sfx["stone"] = "step_stone"

        # start playing the background music
        self.audio.play_music("world01")

    def disable(self):
        """Stop the gamestate."""
        self.keyboard.unregister(self.on_quit)

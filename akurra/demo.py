"""Demo module."""
import pygame
import logging
from injector import inject
from akurra.assets import AssetManager
from akurra.display import DisplayManager, ScrollingMapDisplayLayer
from akurra.keyboard import KeyboardManager
from akurra.entities import GameEntity

logger = logging.getLogger(__name__)


class DemoManager:

    """Temporary demo middleware."""

    def on_key_down(self, event):
        """Handle a key press."""
        key_velocity = self.key_velocities[event.key]
        self.player.velocity[key_velocity[0]] = key_velocity[1]

    def on_key_up(self, event):
        """Handle a key release."""
        key_velocity = self.key_velocities[event.key]
        self.player.velocity[key_velocity[0]] = 0

    @inject(assets=AssetManager, display=DisplayManager, keyboard=KeyboardManager)
    def __init__(self, assets, display, keyboard):
        """Constructor."""
        self.tmx_data = assets.get_tmx_data('pyscroll_demo/grasslands.tmx')
        self.layer = ScrollingMapDisplayLayer(self.tmx_data, default_layer=2, display=display)
        display.add_layer(self.layer)

        self.image = assets.get_image('pyscroll_demo/hero.png')
        self.player = GameEntity(self.image)
        self.player.position = self.layer.map_layer.rect.center

        self.layer.group.add(self.player)
        self.layer.center = self.player

        player_speed = 250

        self.key_velocities = {
            pygame.K_UP: [1, -player_speed],
            pygame.K_DOWN: [1, player_speed],
            pygame.K_LEFT: [0, -player_speed],
            pygame.K_RIGHT: [0, player_speed]
        }

        pygame.key.set_repeat(100, 100)
        [keyboard.register(x, self.on_key_down, event_type=pygame.KEYDOWN) for x in self.key_velocities.keys()]
        [keyboard.register(x, self.on_key_up, event_type=pygame.KEYUP) for x in self.key_velocities.keys()]

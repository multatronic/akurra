"""UI module."""
import pygame
import logging
import math

from .locals import *  # noqa
from .display import DisplayManager, DisplayLayer
from .events import TickEvent, EventManager
from .assets import AssetManager
from .modules import Module
from .session import SessionManager


logger = logging.getLogger(__name__)


class UIModule(Module):

    """UI module."""

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayManager)
        self.session = self.container.get(SessionManager)
        self.assets = self.container.get(AssetManager)

        self.font = pygame.font.SysFont('monospace', 9)

        self.layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=110)

        self.surfaces = {}
        self.surfaces['portrait_main'] = self.assets.get_image('graphics/ui/portrait/main.png', alpha=True)
        self.surfaces['portrait_health_bar'] = self.assets.get_image('graphics/ui/portrait/health_bar.png', alpha=True)

        for type, color in {'earth': 'green', 'water': 'blue', 'air': 'grey', 'fire': 'red'}.items():
            surface = self.assets.get_image('graphics/ui/portrait/magic_buttons/%s.png' % color, alpha=True)
            self.surfaces['portrait_mana_orb_%s' % type] = pygame.transform.smoothscale(surface, [30, 30])

        self.offsets = {}
        self.offsets['portrait'] = [20, 20]
        self.offsets['portrait_health_bar'] = [103, 33]
        self.offsets['portrait_health_text'] = [115, 32]
        self.offsets['portrait_mana_orb'] = [105, 70]
        self.offsets['portrait_mana_orb_text'] = [119, 80]

    def start(self):
        """Start the module."""
        self.display.add_layer(self.layer)
        self.events.register(TickEvent, self.on_tick)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def on_tick(self, event):
        """Handle a tick."""
        player = self.session.get('player')

        if not player:
            return

        health_component = player.components['health']

        self.layer.surface.fill([0, 0, 0, 0])

        self.layer.surface.blit(self.surfaces['portrait_main'], self.offsets['portrait'])

        # The width of the health bar should reflect the player's health percentage
        health_percentage = health_component.health / health_component.max
        self.layer.surface.blit(self.surfaces['portrait_health_bar'], self.offsets['portrait_health_bar'],
                                [0, 0, int(health_percentage * self.surfaces['portrait_health_bar'].get_width()), 900])

        health_text = self.font.render('%s/%s' % (math.floor(health_component.health), health_component.max), 1,
                                       [225, 225, 225])
        self.layer.surface.blit(health_text, self.offsets['portrait_health_text'])

        portrait_mana_orb_offset = list(self.offsets['portrait_mana_orb'])
        portrait_mana_orb_text_offset = list(self.offsets['portrait_mana_orb_text'])

        for mana_type, mana_amount in player.components['mana'].mana.items():
            if mana_amount > 0:
                self.layer.surface.blit(self.surfaces['portrait_mana_orb_%s' % mana_type], portrait_mana_orb_offset)
                portrait_mana_orb_offset[0] += 35

                mana_text = self.font.render('%s' % math.floor(mana_amount), 1, [102, 0, 102])
                self.layer.surface.blit(mana_text, [portrait_mana_orb_text_offset[0] - (mana_text.get_width() / 2),
                                                    portrait_mana_orb_text_offset[1]])
                portrait_mana_orb_text_offset[0] += 35
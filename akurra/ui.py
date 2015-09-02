"""UI module."""
import pygame
import logging
import math
import threading

from .locals import *  # noqa
from .display import DisplayModule, DisplayLayer
from .events import TickEvent, EventManager
from .entities import EntityManager, EntityHealthChangeEvent
from .assets import AssetManager
from .modules import Module
from .session import SessionManager
from .utils import map_point_to_screen


logger = logging.getLogger(__name__)


class UIModule(Module):

    """UI module."""

    dependencies = [
        'display'
    ]

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.session = self.container.get(SessionManager)
        self.assets = self.container.get(AssetManager)
        self.entities = self.container.get(EntityManager)
        self.configuration = self.container.get(Configuration)

        self.font = pygame.font.SysFont('monospace', 9)

        self.layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=110)

        self.surfaces = {}
        self.surfaces['portrait_main'] = self.assets.get_image('graphics/ui/portrait/main.png', alpha=True)
        self.surfaces['portrait_health_bar'] = self.assets.get_image('graphics/ui/portrait/health_bar.png', alpha=True)
        self.surfaces['health_bar_small'] = self.assets.get_image('tmp/health_bar_small.png', alpha=True)

        for type, color in {'earth': 'green', 'water': 'blue', 'air': 'grey', 'fire': 'red'}.items():
            surface = self.assets.get_image('graphics/ui/portrait/magic_buttons/%s.png' % color, alpha=True)
            self.surfaces['portrait_mana_orb_%s' % type] = pygame.transform.smoothscale(surface, [30, 30])

        self.offsets = {}
        self.offsets['portrait'] = [20, 20]
        self.offsets['portrait_health_bar'] = [103, 33]
        self.offsets['portrait_health_text'] = [115, 32]
        self.offsets['portrait_mana_orb'] = [105, 70]
        self.offsets['portrait_mana_orb_text'] = [119, 80]

        self.health_bar_display_time = self.configuration.get('akurra.ui.health_bar.display_time', 5)
        self.health_bar_entities = {}

    def start(self):
        """Start the module."""
        self.display.add_layer(self.layer)
        self.events.register(TickEvent, self.on_tick)
        self.events.register(EntityHealthChangeEvent, self.on_entity_health_change)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_entity_health_change)
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def render_player_ui(self, player):
        """Render player ui elements."""
        health_component = player.components['health']

        # self.layer.surface.fill([0, 0, 0, 0])

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

    def render_entity_contexts(self):
        """Render data related to entity context such as health bars, character names and the like."""
        for entity_id, padding in self.health_bar_entities.items():
            npc = self.entities.find_entity_by_id(entity_id)
            health_component = npc.components['health']

            # The width of the health bar should reflect the npc's health percentage
            health_percentage = health_component.health / health_component.max

            blit_position = map_point_to_screen(npc.components['layer'].layer.map_layer,
                                                npc.components['position'].layer_position)
            # ask k-man for a more pythonic way to pad these values
            blit_position[0] += padding[0]
            blit_position[1] += padding[1]
            self.layer.surface.blit(self.surfaces['health_bar_small'], blit_position,
                                    [0, 0, int(health_percentage * self.surfaces['health_bar_small'].get_width()),
                                    900])

    def on_entity_health_change(self, event):
        """Handle an entity health change event."""
        player = self.session.get('player')

        if not player or event.entity_id == player.id:
            return

        if event.entity_id not in self.health_bar_entities:
            # temporarily display enemy life gauges by putting their entity_id and a padding value for the gauge
            # on the list, then removing it again after a certain period of time
            entity_width = self.entities.find_entity_by_id(event.entity_id).components['sprite'].sprite_size[0]
            gauge_padding = [(entity_width - self.surfaces['health_bar_small'].get_width()) / 2, 60]
            self.health_bar_entities[event.entity_id] = gauge_padding

            threading.Timer(self.health_bar_display_time, lambda x: self.health_bar_entities.pop(x),
                            [event.entity_id]).start()

    def on_tick(self, event):
        """Handle a tick."""
        player = self.session.get('player')

        if not player:
            return

        self.layer.surface.fill([0, 0, 0, 0])
        self.render_player_ui(player)
        self.render_entity_contexts()
